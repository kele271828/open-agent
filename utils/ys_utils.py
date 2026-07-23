import requests
from typing import Dict, List, Any, Optional
import json
import urllib3
from datetime import datetime

# <--- [新增] 禁用 SSL 警告，否则控制台会狂刷 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TodoAgentClient:
    """
    Todo 系统 AI Agent 工具链挂载客户端。
    负责维护会话状态，并提供标准化的增删改查接口供 LLM 调用。
    """
    
    def __init__(self, base_url: str, user_id: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.password = password
        
        # 核心：创建一个持久化的 Session 对象，它会自动管理 Cookie
        self.session = requests.Session()
        self.is_logged_in = False

        # <--- [核心修改] 让整个 Session 忽略 SSL 证书验证
        self.session.verify = False
        
        # 预定义路由
        self.login_url = f"{self.base_url}/users/" 
        self.tasks_url = f"{self.base_url}/todo/api/tasks"

    def login(self) -> bool:
        """执行登录并保存 Cookie 到 Session 中"""
        print(f"[系统] 正在为用户 {self.user_id} 建立连接...")
        try:
            credentials = {"user_id": self.user_id, "password": self.password}
            response = self.session.post(self.login_url, data=credentials)
            
            if response.status_code not in [200, 302] or "账号或密码错误" in response.text:
                raise Exception(f"登录失败: 状态码 {response.status_code}")
                
            self.is_logged_in = True
            print("[系统] 登录成功，会话已持久化。")
            return True
            
        except requests.exceptions.ConnectionError:
            raise Exception(f"无法连接到服务器 {self.base_url}，请检查 Flask 是否启动。")

    def _ensure_auth(self):
        """内部鉴权拦截器：确保执行操作前处于登录状态"""
        if not self.is_logged_in:
            self.login()

    def _convert_time_to_local(self, data: Any) -> Any:
        """
        [新增] 递归遍历 JSON 数据，将 UTC 时间(以 'Z' 结尾)转换为系统当前时区时间。
        """
        # 你可以根据实际后端的字段名在这里添加/删减需要转换的字段
        time_fields = {"deadline", "start_time", "end_time", "recurrence_until", "created_at", "updated_at"}
        
        if isinstance(data, list):
            return [self._convert_time_to_local(item) for item in data]
        elif isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if k in time_fields and isinstance(v, str) and v.endswith('Z'):
                    try:
                        # 兼容 Python 3.7+：把 'Z' 换成 '+00:00' 来解析 UTC
                        dt_utc = datetime.fromisoformat(v.replace('Z', '+00:00'))
                        # astimezone() 不带参数会自动转换为当前系统所在的本地时区
                        dt_local = dt_utc.astimezone()
                        # 这里将时间格式化为易读格式，如果你想保留 ISO 格式，可改为 dt_local.isoformat()
                        new_dict[k] = dt_local.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # 解析失败则原样返回
                        new_dict[k] = v  
                else:
                    new_dict[k] = self._convert_time_to_local(v)
            return new_dict
        return data

    # ==========================================
    # 下方是暴露给 AI Agent 调用的标准 Tool 接口
    # ==========================================

    def get_tasks(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        获取指定日期范围内的待办事项。
        :param start_date: 格式 YYYY-MM-DD，可选。
        :param end_date: 格式 YYYY-MM-DD，可选。
        """
        self._ensure_auth()
        params = {}
        if start_date: params['start_date'] = start_date
        if end_date: params['end_date'] = end_date
            
        response = self.session.get(self.tasks_url, params=params)
        if response.status_code == 200:
            raw_data = response.json()
            # <--- [修改] 在转成字符串前，先将字典里的时间转换为本地时区
            local_data = self._convert_time_to_local(raw_data)
            return json.dumps(local_data, ensure_ascii=False)
        raise Exception(f"获取任务失败: {response.status_code} - {response.text}")

    def add_task(self, 
                 title: str, 
                 task_type: str, 
                 description: Optional[str] = "",  # <--- [新增] 描述字段，默认为空字符串
                 deadline: Optional[str] = None,
                 estimated_duration_minutes: int = 0,
                 start_time: Optional[str] = None,
                 end_time: Optional[str] = None,
                 is_recurring: bool = False,
                 recurrence_frequency: Optional[str] = None,
                 recurrence_until: Optional[str] = None,
                 recurrence_by_day: Optional[List[str]] = None) -> str:
        """
        新增待办事项。
        
        :param title: 任务名称 (必需)
        :param task_type: 任务类型，可选值: 'floating_task', 'window_task', 'fixed_event' (必需)
        :param description: 任务描述/备注信息 (可选)  <--- [新增] 注释
        :param deadline: 截止时间 (UTC ISO格式)，仅当 task_type='window_task' 时必需
        :param estimated_duration_minutes: 预计耗时(分钟)，用于 window_task (可选)
        :param start_time: 开始时间 (UTC ISO格式)，仅当 task_type='fixed_event' 时必需
        :param end_time: 结束时间 (UTC ISO格式)，仅当 task_type='fixed_event' 时必需
        :param is_recurring: 是否为循环任务
        :param recurrence_frequency: 循环频率，'daily' 或 'weekly'
        :param recurrence_until: 循环结束日期 (UTC ISO格式)
        :param recurrence_by_day: 周循环的日期列表，如 ['MO', 'WE', 'FR']
        """
        self._ensure_auth()
        
        # 1. 构建基础载荷
        payload = {
            "title": title,
            "type": task_type,
            "description": description,  # <--- [新增] 将描述加入载荷
            "status": "pending",
            "is_recurring": is_recurring
        }
        
        # 2. 根据类型严格校验并挂载时间参数
        if task_type == "window_task":
            if not deadline:
                raise ValueError("错误: 创建 'window_task' (窗口任务) 必须提供 deadline 参数。")
            payload["deadline"] = deadline
            payload["estimated_duration_minutes"] = estimated_duration_minutes
            
        elif task_type == "fixed_event":
            if not start_time or not end_time:
                raise ValueError("错误: 创建 'fixed_event' (固定事件) 必须提供 start_time 和 end_time 参数。")
            payload["start_time"] = start_time
            payload["end_time"] = end_time
            
        elif task_type == "floating_task":
            # 弹性任务不需要时间参数，直接放行
            pass
        else:
            raise ValueError(f"错误: 未知的任务类型 '{task_type}'。")

        # 3. 如果是循环任务，自动拼装 recurrence_rule 字典供后端使用
        if is_recurring:
            if not recurrence_frequency:
                raise ValueError("错误: 开启了循环 (is_recurring=True)，必须提供 recurrence_frequency ('daily' 或 'weekly')。")
            
            rule = {
                "frequency": recurrence_frequency,
                "interval": 1,
                "end_type": "until"
            }
            if recurrence_until:
                rule["until_date"] = recurrence_until
                
            if recurrence_frequency == "weekly":
                if not recurrence_by_day:
                    raise ValueError("错误: 按周循环 ('weekly') 必须提供 recurrence_by_day 参数，例如 ['MO', 'WE']。")
                rule["by_day"] = recurrence_by_day
                
            payload["recurrence_rule"] = rule

        # 4. 发送给后端的 Flask API
        response = self.session.post(self.tasks_url, json=payload)
        
        if response.status_code == 201:
            return response.json().get('id')
            
        raise Exception(f"创建任务失败: {response.status_code} - {response.text}")

    def update_task(self, task_id: str, update_data: Dict[str, Any], is_series: bool = False, template_id: Optional[str] = None) -> str:
        """
        更新待办事项的状态或内容。
        :param task_id: 任务的唯一ID
        :param update_data: 需要更新的字段字典，如 {"status": "completed"}
        :param is_series: 是否修改整个循环系列
        :param template_id: 如果是修改系列，需提供 template_id
        """
        self._ensure_auth()
        url = f"{self.tasks_url}/{task_id}"
        if is_series and template_id:
            url += f"?type=template&template_id={template_id}"
            
        response = self.session.put(url, json=update_data)
        return f"更新{"成功" if response.status_code == 200 else "失败"}"

    def delete_task(self, task_id: str, is_series: bool = False, template_id: Optional[str] = None) -> str:
        """
        删除待办事项。
        :param task_id: 任务的唯一ID
        :param is_series: 是否删除整个循环系列
        :param template_id: 如果删除系列，需提供 template_id
        """
        self._ensure_auth()
        url = f"{self.tasks_url}/{task_id}"
        if is_series and template_id:
            url += f"?type=template&template_id={template_id}"
            
        response = self.session.delete(url)
        return f"删除{"成功" if response.status_code == 200 else "失败"}"