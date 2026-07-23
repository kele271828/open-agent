Tools_Dict = {
    "Get_Time": {
        "type": "function",
        "function": {
            "name": "Get_Time",
            "description": "获取当前时间",
            "parameters": {}
        }
    },
    "Get_Weather": {
        "type": "function",
        "function": {
            "name": "Get_Weather",
            "description": "获取天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "需要获取的天气位置，使用英文，例如：'Beijing',留空则自动定位。",
                    }
                },
                "required": ["location"],
            },
        },
    },
    "Get_System_Status": {
        "type": "function",
        "function": {
            "name": "Get_System_Status",
            "description": "获取当前系统状态",
            "parameters": {}
        },
    },
    "Take_Screenshot": {
        "type": "function",
        "function": {
            "name": "Take_Screenshot",
            "description": "获取当前屏幕截图",
            "parameters": {}
        },
    },
    "Read_File_Content": {
        "type": "function",
        "function": {
            "name": "Read_File_Content",
            "description": "读取文件内容,支持文本文件、.docx、.pdf和图片文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "需要读取的文件绝对路径，例如：'D:\\pytest\\AIGF\\tmp\\text\\test.txt'",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    "Explore_Directory": {
        "type": "function",
        "function": {
            "name": "Explore_Directory",
            "description": "查看目录内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {
                        "type": "string",
                        "description": "需要读取的文件夹绝对路径，例如：'D:\\pytest\\AIGF\\tmp\\'",
                    }
                },
                "required": ["dir_path"],
            },
        },
    },
    "Modify_File": {
        "type": "function",
        "function": {
            "name": "Modify_File",
            "description": "修改或新建文件,支持写入、追加和替换操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "需要修改的文件绝对路径，例如：'D:\\pytest\\AIGF\\tmp\\text\\test.txt'",
                    },
                    "action": {
                        "type": "string",
                        "description": "修改操作，必须是 'write', 'append', 或 'replace'",
                    },
                    "content": {
                        "type": "string",
                        "description": "需要写入的文件内容",
                    },
                    "old_text": {
                        "type": "string",
                        "description": "如果是 'replace' 操作，需要替换的旧文本，仅传入需要修改的部分",
                    }
                },
                "required": ["file_path", "action", "content"],
            },
        },
    },
    "Control_Mouse": {
        "type": "function",
        "function": {
            "name": "Control_Mouse",
            "description": "控制鼠标执行操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "执行的动作，支持: 'position' (获取坐标), 'move' (移动), 'click' (点击), 'drag' (拖拽), 'scroll' (滚动)",
                    },
                    "x": {
                        "type": "integer",
                        "description": "目标X坐标 (move, click, drag 需要)",
                    },
                    "y": {
                        "type": "integer",
                        "description": "目标Y坐标 (move, click, drag 需要)",
                    },
                    "button": {
                        "type": "string",
                        "description": "鼠标按键: 'left', 'right', 'middle'",
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "点击次数 (click需要)",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "滚动量 (scroll需要)",
                    },
                },
                "required": ["action"],
            },
        },
    },
    "Web_Search": {
        "type": "function",
        "function": {
            "name": "Web_Search",
            "description": "联网搜索",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "需要搜索的查询字符串",
                    }
                },
                "required": ["query"],
            },
        },
    },
    "Modify_Word_Element": {
        "type": "function",
        "function": {
            "name": "Modify_Word_Element",
            "description": "新建 word 文档或者修改 Word 文档中的元素",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_path": {
                        "type": "string",
                        "description": "需要修改的 Word 文档绝对路径，例如：'D:\\pytest\\AIGF\\tmp\\text\\test.docx'",
                    },
                    "action": {
                        "type": "string",
                        "description": "修改操作，必须是 'MODIFY', 'DELETE', 'ADD_AFTER'",
                    },
                    "key": {
                        "type": "integer",
                        "description": "目标元素的索引，从 0 开始",
                    },
                    "text": {
                        "type": "string",
                        "description": "如果是 'MODIFY' 操作，需要替换的文本；如果是 'ADD_AFTER' 操作，需要添加的新文本",
                    }
                },
                "required": ["doc_path", "action", "key"],
            },
        },
    },
    "Take_Photo": {
        "type": "function",
        "function": {
            "name": "Take_Photo",
            "description": "使用摄像头拍照",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    "Control_Keyboard": {
        "type": "function",
        "function": {
            "name": "Control_Keyboard",
            "description": "控制键盘执行操作",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "执行的动作，支持: 'write' (输入文本), 'press' (按下按键), 'hotkey' (组合按键)",
                    },
                    "text": {
                        "type": "string",
                        "description": "需要输入的文本 (type 需要)",
                    },
                    "keys": {
                        "type": "array",
                        "description": "需要按下的按键列表 (press, hotkey 需要)",
                    },
                },
                "required": ["action"],
            },
        },
    },
    "Manage_Clipboard": {
        "type": "function",
        "function": {
            "name": "Manage_Clipboard",
            "description": "管理系统剪贴板",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "执行的动作，支持: 'read' (读取剪贴板), 'write' (写入剪贴板)",
                    },
                    "text": {
                        "type": "string",
                        "description": "需要写入到剪贴板的文本 (write 需要)",
                    },
                },
                "required": ["action"],
            },
        },
    },
    "Launch_App": {
        "type": "function",
        "function": {
            "name": "Launch_App",
            "description": "启动本地应用程序",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "需要启动的应用程序名称或程序名，例如：'微信', 'msedge.exe'",
                    },
                },
                "required": ["app_name"],
            },
        },
    },
    "Close_Process": {
        "type": "function",
        "function": {
            "name": "Close_Process",
            "description": "关闭应用进程",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {
                        "type": "string",
                        "description": "需要关闭的进程名称，例如：'msedge.exe', 'chrome'",
                    },
                },
                "required": ["process_name"],
            },
        },
    },
    "Query_Academic_Papers": {
        "type": "function",
        "function": {
            "name": "Query_Academic_Papers",
            "description": "查询学术论文",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询的关键词，例如：'Attention is all you need'",
                    },
                    "author": {
                        "type": "string",
                        "description": "可选的作者姓名，例如：'Vaswani, A.'",
                    },
                    "year": {
                        "type": "string",
                        "description": "可选的出版年份，例如：'2023'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回的论文数量，默认值为 8",
                    },
                },
                "required": ["query"],
            },
        },
    },
    "Read_Academic_Paper": {
        "type": "function",
        "function": {
            "name": "Read_Academic_Paper",
            "description": "根据 ArXiv 链接下载论文 PDF 到指定目录，并提取全文文本",
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_url": {
                        "type": "string",
                        "description": "ArXiv 论文链接，例如：'https://arxiv.org/abs/2305.14274'",
                    },
                },
                "required": ["arxiv_url"],
            },
        },
    },
    "Execute_Command": {
        "type": "function",
        "function": {
            "name": "Execute_Command",
            "description": "在一个安全的 Ubuntu Linux 隔离环境中临时执行 Bash 脚本，你可以用它来运行 Python 代码执行计算，但注意：所有结果不会保留，不建议用于其他用途。",
            "parameters": {
                "type": "object",
                "properties": {
                    "bash_script": {
                        "type": "string",
                        "description": "需要执行的完整 Bash 脚本内容。如果你想运行 Python 代码，请先在 Bash 中使用 cat << 'EOF' > script.py 将代码写入文件，然后再使用 python3 script.py 执行它。"
                    }
                },
            "required": ["bash_script"]
            }
        }
    },
    "Add_Task_To_User_Todo": {
        "type": "function",
        "function": {
            "name": "Add_Task_To_User_Todo",
            "description": "向日程表中添加新任务。务必根据 task_type 传入对应的时间参数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "任务名称"
                    },
                    "task_type": {
                        "type": "string",
                        "enum": ["floating_task", "window_task", "fixed_event"],
                        "description": "任务类型。floating_task(无时间限制), window_task(有截止时间), fixed_event(强占起止时间)"
                    },
                    "description": {
                        "type": "string",
                        "description": "任务描述/备注信息，简短关键词为宜"
                    },
                    "deadline": {
                        "type": "string",
                        "description": "仅当 task_type 为 window_task 时提供。格式: YYYY-MM-DDTHH:MM:SS"
                    },
                    "estimated_duration_minutes": {
                        "type": "integer",
                        "description": "预计耗时分钟数"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "仅当 task_type 为 fixed_event 时提供。格式同上"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "仅当 task_type 为 fixed_event 时提供。格式同上"
                    },
                    "is_recurring": {
                        "type": "boolean",
                        "description": "是否为循环任务"
                    },
                    "recurrence_frequency": {
                        "type": "string",
                        "enum": ["daily", "weekly"],
                        "description": "仅当 is_recurring 为 true 时提供"
                    },
                    "recurrence_until": {
                        "type": "string",
                        "description": "循环结束时间，格式同上"
                    },
                    "recurrence_by_day": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]},
                        "description": "仅当频率为 weekly 时提供，例如 ['MO', 'WE'] 表示周一和周三"
                    }
                },
                "required": ["title", "task_type"]
            }
        }
    },
    "Get_Task_In_User_Todo": {
        "type": "function",
        "function": {
            "name": "Get_Task_In_User_Todo",
            "description": "获取用户的待办清单", # ，除特殊情况不建议指定日期范围。
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "开始日期，可选，格式: YYYY-MM-DD"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "结束日期，可选，格式: YYYY-MM-DD"
                    },
                },
                "required": []
            }
        }
    },
    "Delete_Task_In_User_Todo": {
        "type": "function",
        "function": {
            "name": "Delete_Task_In_User_Todo",
            "description": "删除用户待办清单中的任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID"
                    },
                    "is_series": {
                        "type": "boolean",
                        "description": "是否为循环任务，删除时是否同时删除所有循环任务"
                    },
                    "template_id": {
                        "type": "string",
                        "description": "仅当 is_series 为 true 时提供，指定循环任务的模板 ID"
                    }
                },
                "required": ["task_id", "is_series"]
            }
        }
    },
    "Update_Task_In_User_Todo": {
        "type": "function",
        "function": {
            "name": "Update_Task_In_User_Todo",
            "description": "更新用户待办清单中的任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID"
                    },
                    "update_data": {
                        "type": "object",
                        "description": "需要更新的任务字段字典，如 {\"status\": \"completed\"}"
                    },
                    "is_series": {
                        "type": "boolean",
                        "description": "是否为循环任务，是否为更新所对应的循环任务"
                    },
                    "template_id": {
                        "type": "string",
                        "description": "仅当 is_series 为 true 时提供，指定循环任务的模板 ID"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    "Check_Location": {
        "type": "function",
        "function": {
            "name": "Check_Location",
            "description": "获取用户当前位置",
            "parameters": {},
        }
    },
    "Add_Task": {
        "type": "function",
        "function": {
            "name": "Add_Task",
            "description": "添加任务到你的任务清单",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "任务提醒的具体内容"
                    },
                    "time_str": {
                        "type": "string",
                        "description": "首次执行时间，格式必须为 \"YYYY-MM-DD HH:MM:SS\""
                    },
                    "cron_expr": {
                        "type": "string",
                        "description": " (可选) 循环任务的 Cron 表达式,例如\"0 9 * * *\" 表示每天早上9点。如果不填则为单次任务。"
                    }
                },
                "required": ["content", "time_str"]
            }
        }
    },
    "Get_Tasks": {
        "type": "function",
        "function": {
            "name": "Get_Tasks",
            "description": "获取你的任务清单",
            "parameters": {},
        }
    },
    "Cancel_Todo": {
        "type": "function",
        "function": {
            "name": "Cancel_Todo",
            "description": "取消你的任务清单中的任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务 ID"
                    },
                },
                "required": ["task_id"]
            }
        }
    },
    "Search_Deep_Memory": {
        "type": "function",
        "function": {
            "name": "Search_Deep_Memory",
            "description": "深度搜索你的记忆",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_key": {
                        "type": "string",
                        "description": "搜索关键词,用于搜索记忆中的内容,如果为空则返回最近时间的记忆"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "返回的结果数量,默认3个"
                    }
                },
                "required": []
            }
        }
    },
    "Send_Message": {
        "type": "function",
        "function": {
            "name": "Send_Message",
            "description": "发送消息给其他用户",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_name": {
                        "type": "string",
                        "description": "目标用户的用户名"
                    },
                    "message": {
                        "type": "string",
                        "description": "要发送的消息内容"
                    },
                },
                "required": ["target_name", "message"]
            }
        }
    },
}