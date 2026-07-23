import sqlite3
import threading
import time
import uuid
import queue
from datetime import datetime
from croniter import croniter

class TaskManager:
    def __init__(self, event_queue: queue.Queue, db_path: str = "./Memory/tasks.db"):
        """
        初始化任务管理器
        :param event_queue: 全局事件队列
        :param db_path: SQLite 数据库路径，默认存放在 Memory 文件夹下
        """
        self.event_queue = event_queue
        self.db_path = db_path
        self.lock = threading.Lock() # 全局锁，防止多线程读写数据库冲突
        self._running = False
        
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库表结构"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        scheduled_time TEXT NOT NULL,
                        status TEXT NOT NULL, 
                        cron_expr TEXT
                    )
                """)
                # status 枚举: 'pending', 'completed', 'cancelled'

    # =========================================================================
    # AI 自主管理接口 (暴露给大模型的 Tool Calling / Function Calling)
    # 这里的 Docstring 可以直接提取给 LLM 生成 Schema
    # =========================================================================

    def ai_add_task(self, content: str, time_str: str, cron_expr: str = None) -> str:
        """
        创建一个新的定时任务或循环任务。
        :param content: 任务提醒的具体内容。
        :param time_str: 首次执行时间，格式必须为 "YYYY-MM-DD HH:MM:SS"。
        :param cron_expr: (可选) 循环任务的 Cron 表达式，例如 "0 9 * * *" 表示每天早上9点。如果不填则为单次任务。
        :return: 任务执行结果反馈给 AI。
        """
        try:
            # 校验时间格式
            scheduled_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            
            # 校验 Cron 表达式
            if cron_expr and not croniter.is_valid(cron_expr):
                return f"[失败] 提供的 cron_expr '{cron_expr}' 格式不正确。"

            task_id = str(uuid.uuid4())[:8]
            
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO tasks (task_id, content, scheduled_time, status, cron_expr) VALUES (?, ?, ?, ?, ?)",
                        (task_id, content, time_str, "pending", cron_expr)
                    )
            
            msg = f"[成功] 任务已创建。ID: {task_id}, 首次执行时间: {time_str}"
            if cron_expr:
                msg += f", 循环规则: {cron_expr}"
            return msg
            
        except ValueError:
            return f"[失败] 时间格式错误，请严格使用 YYYY-MM-DD HH:MM:SS 格式，收到的是：{time_str}"
        except Exception as e:
            return f"[失败] 数据库写入异常: {e}"

    def ai_list_tasks(self) -> str:
        """
        获取当前所有处于待办状态(pending)的任务列表。
        :return: 包含任务详情的字符串列表，供 AI 阅读。
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM tasks WHERE status = 'pending' ORDER BY scheduled_time ASC")
                tasks = cursor.fetchall()

        if not tasks:
            return "当前没有任何待办任务。"

        result = []
        for t in tasks:
            cron_info = f" | 循环: {t['cron_expr']}" if t['cron_expr'] else ""
            result.append(f"- [ID: {t['task_id']}] 时间: {t['scheduled_time']} | 内容: {t['content']}{cron_info}")
        
        return "\n".join(result)

    def ai_cancel_task(self, task_id: str) -> str:
        """
        取消指定的任务。
        :param task_id: 需要取消的任务的唯一 ID。
        :return: 操作结果反馈。
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("UPDATE tasks SET status = 'cancelled' WHERE task_id = ? AND status = 'pending'", (task_id,))
                if cursor.rowcount > 0:
                    return f"[成功] 任务 {task_id} 已取消。"
                else:
                    return f"[失败] 找不到待办任务 {task_id}，它可能已被执行或本身不存在。"

    # =========================================================================
    # 后台守护线程与内部逻辑
    # =========================================================================

    def start(self):
        """启动后台轮询线程"""
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._watcher_loop, daemon=True, name="TaskManagerWatcher").start()

    def _watcher_loop(self):
        """后台轮询，每秒检查一次数据库中是否有到期的任务"""
        while self._running:
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")

            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    # 找出所有 scheduled_time <= 当前时间 且状态为 pending 的任务
                    cursor = conn.execute(
                        "SELECT * FROM tasks WHERE status = 'pending' AND scheduled_time <= ?", 
                        (now_str,)
                    )
                    due_tasks = cursor.fetchall()

                    for task in due_tasks:
                        # 1. 向全局队列推送任务事件
                        self.event_queue.put({
                            "type": "external_task",
                            "content": f"【系统任务触发】 {task['content']}"
                        })

                        # 2. 处理状态更新或计算下一次循环时间
                        if task['cron_expr']:
                            try:
                                # 计算下一次执行时间 (基于当前时间推算)
                                cron = croniter(task['cron_expr'], now)
                                next_time_str = cron.get_next(datetime).strftime("%Y-%m-%d %H:%M:%S")
                                
                                conn.execute(
                                    "UPDATE tasks SET scheduled_time = ? WHERE task_id = ?",
                                    (next_time_str, task['task_id'])
                                )
                            except Exception as e:
                                print(f"\n[任务管理器错误] Cron计算失败，停止该循环任务: {e}")
                                conn.execute("UPDATE tasks SET status = 'completed' WHERE task_id = ?", (task['task_id'],))
                        else:
                            # 单次任务，直接标记完成
                            conn.execute("UPDATE tasks SET status = 'completed' WHERE task_id = ?", (task['task_id'],))
            
            time.sleep(10)