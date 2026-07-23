from utils.utils import (get_current_time, get_system_status, check_location,
                   get_weather, web_search_for_llm, query_academic_papers, read_academic_paper,
                   capture_single_image,
                   take_screenshot, read_file_content, explore_directory, modify_file, modify_word_element,
                   control_mouse, control_keyboard, manage_clipboard,
                   launch_app, safe_terminate_process, execute_in_sandbox,
                   search_deep_memory)
from utils.LLM_Tools import Tools_Dict
from utils.ys_utils import TodoAgentClient

from utils.task_manager import TaskManager

import queue

from config import config

# 实例化待办工具客户端
todo_tool = TodoAgentClient(
    base_url=config.TODO_BASE_URL,
    user_id=config.TODO_USER_ID,
    password=config.TODO_PASSWORD
)

# 1. 全局任务队列
event_queue = queue.Queue()

# 2. 初始化并启动任务管理器
task_manager = TaskManager(event_queue=event_queue)

# 定义工具
System_Tools = ["Get_Time", "Get_System_Status"]
Web_Tools = ["Web_Search", "Get_Weather", "Query_Academic_Papers", "Read_Academic_Paper"]
Operating_Tools = ["Take_Screenshot", "Read_File_Content", "Explore_Directory", "Modify_File",
                   "Control_Mouse", "Modify_Word_Element", "Control_Keyboard", "Manage_Clipboard",
                   "Launch_App", "Close_Process", "Execute_Command"]
YS_Tools = ["Add_Task_To_User_Todo", "Update_Task_In_User_Todo", "Delete_Task_In_User_Todo", "Get_Task_In_User_Todo"]
Task_Tools = ["Add_Task", "Get_Tasks", "Cancel_Todo"]
Self_Tools = ["Search_Deep_Memory"]

tool_names = System_Tools + Web_Tools + Operating_Tools + YS_Tools + Task_Tools + Self_Tools

Privacy_Mode = False
tools = [Tools_Dict[tool_name] for tool_name in tool_names]

for tool in tools:
    if not tool["function"]["parameters"]:
        del tool["function"]["parameters"]

name2func = {
    "Get_Time": get_current_time,
    "Get_Weather": get_weather,
    "Get_System_Status": get_system_status,
    "Take_Screenshot": take_screenshot,
    "Read_File_Content": read_file_content,
    "Explore_Directory": explore_directory,
    "Modify_File": modify_file,
    "Control_Mouse": control_mouse,
    "Web_Search": web_search_for_llm,
    "Modify_Word_Element": modify_word_element,
    "Control_Keyboard": control_keyboard,
    "Manage_Clipboard": manage_clipboard,
    "Launch_App": launch_app,
    "Close_Process": safe_terminate_process,
    "Query_Academic_Papers": query_academic_papers,
    "Read_Academic_Paper": read_academic_paper,
    "Execute_Command": execute_in_sandbox,
    "Add_Task_To_User_Todo": todo_tool.add_task,
    "Update_Task_In_User_Todo": todo_tool.update_task,
    "Delete_Task_In_User_Todo": todo_tool.delete_task,
    "Get_Task_In_User_Todo": todo_tool.get_tasks,
    "Check_Location": check_location,
    "Add_Task": task_manager.ai_add_task,
    "Get_Tasks": task_manager.ai_list_tasks,
    "Cancel_Todo": task_manager.ai_cancel_task,
    "Search_Deep_Memory": search_deep_memory,
}
