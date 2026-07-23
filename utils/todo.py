import requests

# === 配置区域 ===
# 你的 Flask 服务监听端口
BASE_URL = "http://127.0.0.1:5001"

# 登录接口：蓝图前缀 /users + 路由 /
LOGIN_URL = f"{BASE_URL}/users/" 

# 待办事项接口：蓝图前缀 /todo + 路由 /api/tasks
TASKS_URL = f"{BASE_URL}/todo/api/tasks"

# 登录凭证：完全匹配 request.form['user_id'] 和 request.form['password']
USER_CREDENTIALS = {
    "user_id": "822001",    # 使用了你数据库里的 KL 测试账号
    "password": "20060725"
}

# 目标日期区间
START_DATE = "2026-03-25"
END_DATE = "2026-04-25"

def get_todo_tasks():
    # 使用 Session 自动维持 Cookie (处理 session 验证)
    client = requests.Session()

    print(f"正在尝试连接 {LOGIN_URL} 进行登录...")
    
    try:
        # 发送表单格式的 POST 请求进行登录
        login_response = client.post(LOGIN_URL, data=USER_CREDENTIALS)
        
        # 校验登录结果 (如果是错误，后端会渲染包含 "账号或密码错误" 的模板)
        if login_response.status_code not in [200, 302] or "账号或密码错误" in login_response.text:
            print(f"登录失败！请检查账号密码或后端状态。状态码: {login_response.status_code}")
            return
            
        print("登录成功！正在请求待办事项...")

        # 构造时间区间查询参数
        params = {
            "start_date": START_DATE,
            "end_date": END_DATE
        }

        # 发送 GET 请求获取任务，Session 会自动带上刚才登录的 Cookie
        response = client.get(TASKS_URL, params=params)

        # 处理响应
        if response.status_code == 200:
            tasks = response.json()
            print(f"成功获取到 {len(tasks)} 条待办事项:")
            for task in tasks:
                print(task)
                
        elif response.status_code == 401:
            print("未授权 (401)! Session 验证失败。")
            
        elif response.status_code == 404:
            print(f"找不到接口 (404)! 请求地址: {TASKS_URL}")
            print("请确认你的 todo 蓝图是否也成功注册到了这个监听 5001 端口的 Flask app 上。")
            
        else:
            print(f"请求失败！状态码: {response.status_code}, 响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"连接失败！无法连接到 {BASE_URL}。请确保你的 Flask 后端确实已经启动并正在监听 5001 端口。")

if __name__ == "__main__":
    get_todo_tasks()
