from Assistant import Assistant

assistant = Assistant(core_memory="./Memory/core_memory.md", medium_memory_path="./Memory/medium_memory.md")

print(assistant.heart_beat())
while True:
    user_input = input("用户: ")
    if user_input.lower() in ["exit", "quit"]:
        assistant.clear_context()
        print("结束对话。")
        break
    elif user_input.lower() in ["clear", "reset"]:
        assistant.clear_context()
        print("上下文已清空。")
    else:
        print("AI:", end="")
        gen = assistant.stream_answer(user_input)
        

        try:
            while True:
                # 使用 next() 手动获取下一个块
                chunk = next(gen)
                print(chunk, end="", flush=True)
        except StopIteration as e:
            
            final_output = e.value
            # content = final_output.get("content")
            # reasoning = final_output.get("reasoning_content")
            # print("\n\n完整响应：", e.value)
