from memory import AddMemory, SearchMemory, GetRecentMemory
from reasoning import Reasoning, Stream_Reasoning
from datetime import datetime
# from settings import MODEL_NAME
from config import config


class Assistant:
    def __init__(self, core_memory, medium_memory_path):

        # 读取核心记忆
        with open(core_memory, 'r', encoding='utf-8') as f:
            self.core_memory = f.read()
        
        # 读取中期记忆
        self.medium_memory_path = medium_memory_path
        with open(medium_memory_path, 'r', encoding='utf-8') as f:
            self.medium_memory = f.read()

        # 短期记忆 用于存储对话上下文的列表
        self.context_memory = []
        

    def answer(self, user_input, tools=None):

        # 加载核心记忆 和 中期记忆
        prompt = self.core_memory + self.medium_memory

        # 搜索相关历史对话内容
        history_context = ""
        search_context = ""
        if isinstance(user_input, list):
            for item in user_input:
                if item["type"] == "text":
                    search_context = item["text"]
        if search_context:
            history = SearchMemory(search_context, n_results=3, type="history", date=None, distance_threshold=0.5)
            if history['metadatas']:
                for metadatas in history['metadatas']:
                    if metadatas['date'] and metadatas['original_context']:
                        history_context += f"{metadatas['date']} {metadatas['original_context']}\n"
        
        if history_context:
            prompt = f"{prompt}\n以下是相关历史对话内容，可能会有帮助。\n{history_context}\n"

        print("相关历史对话内容:\n", history_context)

        # 加入时间提示
        prompt += f"\n当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}"

        # 合成输入消息
        messages = [
            {"role": "system", "content": prompt},
            *self.context_memory,
            {"role": "user", "content": user_input}
        ]

        # 调用大模型
        output = Reasoning(messages, model=config.MODEL_NAME, temperature=0.7, thinking=True, tools=tools)
        if not output:
            return None
        
        # 更新对话上下文
        self.context_memory.append({"role": "user", "content": user_input})
        self.context_memory.append({"role": "assistant", "content": output["content"]})

        return output
    
    def stream_answer(self, user_input, tools=None):

        # 加载核心记忆 和 中期记忆
        prompt = self.core_memory + self.medium_memory
        
        # 搜索相关历史对话内容
        history_context = ""
        search_context = ""
        if isinstance(user_input, list):
            for item in user_input:
                if item["type"] == "text":
                    search_context = item["text"]
        if search_context:
            history = SearchMemory(search_context, n_results=3, type="history", date=None, distance_threshold=0.5)
            if history['metadatas']:
                for metadatas in history['metadatas']:
                    if metadatas['date'] and metadatas['original_context']:
                        history_context += f"{metadatas['date']} {metadatas['original_context']}\n"
        
        if history_context:
            prompt = f"{prompt}\n以下是相关历史对话内容，可能会有帮助。\n{history_context}\n"

        print("相关历史对话内容:\n", history_context)
        
        # 加入时间提示
        prompt += f"\n当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}"
        
        # 合成输入消息
        messages = [
            {"role": "system", "content": prompt},
            *self.context_memory,
            {"role": "user", "content": user_input}
        ]

        # 调用大模型
        gen = Stream_Reasoning(messages, model=config.MODEL_NAME, temperature=0.7, thinking=True, tools=tools)

        try:
            while True:
                chunk = next(gen)
                yield chunk
        except StopIteration as e:
            final_output = e.value

        # 更新对话上下文
        self.context_memory.append({"role": "user", "content": user_input})
        self.context_memory.append({"role": "assistant", "content": final_output["content"]})

        return final_output

    def heart_beat(self, tools=None):

        # 加载核心记忆 + 中期记忆
        prompt = self.core_memory + self.medium_memory

        # 加入上下文
        if self.context_memory:
            prompt += f"\n以下是你当前与用户的对话内容：{self.context_memory}"
        else:
            prompt += f"\n用户没有主动发起对话。"

        # 加入时间提示
        prompt += f"\n当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}"
        
        # 加入心跳提示
        prompt += f"\n请根据当前的情况决定是否要主动行动。若不行动，直接输出“PASS”。"

        messages = [
            {"role": "system", "content": prompt},
        ]
        output = Reasoning(messages, model=config.MODEL_NAME, temperature=0.7, thinking=True, tools=tools)
        if not output:
            return None
        elif output["content"].strip().lower().startswith("pass"):
            return "PASS"
        else:
            self.context_memory.append({"role": "assistant", "content": output["content"]})
            return f"\n\n[回答]\n{output["content"]}"
    
    def deal_task(self,task_content, tools=None):

        # 加载核心记忆 + 中期记忆
        prompt = self.core_memory + self.medium_memory

        # 加入上下文
        if self.context_memory:
            prompt += f"\n以下是你当前与用户的对话内容：{self.context_memory}"

        # 加入时间提示
        prompt += f"\n当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}"
        
        # 加入任务提示
        prompt += f"\n你现在需要：{task_content},如果任务在之前已经完成，请直接输出“PASS”，否则请向用户汇报。"

        messages = [
            {"role": "system", "content": prompt},
        ]
        output = Reasoning(messages, model=config.MODEL_NAME, temperature=0.7, thinking=True, tools=tools)
        if not output:
            return None
        elif output["content"].strip().lower().startswith("pass"):
            return "PASS"
        else:
            self.context_memory.append({"role": "assistant", "content": output["content"]})
            return f"\n\n[回答]\n{output["content"]}"

    def summary_medium_memory(self):
        input_text = f"以下是你的核心记忆（无法修改）：{self.core_memory}\n以下是你的中期记忆（需要修改）：{self.medium_memory}\n以下是你当前与用户的对话内容：{self.context_memory}，请根据对话内容对中期记忆进行适当的修改，注意时效信息和重要记忆，控制输出量。请输出完整的中期记忆，包括现在的时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}"
        messages = [
            {"role": "system", "content": "请按照以下内容总结中期记忆。"},
            {"role": "user", "content": input_text}
        ]
        output = Reasoning(messages, model=config.MODEL_NAME, temperature=0.7, thinking=False, tools=None)
        if not output:
            return None
        if output["content"]:
            return output["content"]

    def summary(self):
        
        input_text = f"{self.context_memory}"
        messages = [
            {"role": "system", "content": "请总结以下内容，20字以内"},
            {"role": "user", "content": input_text}
        ]
        output = Reasoning(messages, model=config.MODEL_NAME, temperature=0.7, thinking=False, tools=None)
        if not output:
            return None
        if output["content"]:
            return output["content"]
    
    def clear_context(self):
        # 总结短期记忆，保存到长期记忆
        if self.context_memory:
            summary = self.summary()
            if not summary:
                return
            AddMemory(summary, type="history", date=datetime.now().strftime("%Y-%m-%d"), id=None, original_context=str(self.context_memory))
        
        # 总结短期记忆，保存到中期记忆
        new_medium_memory = self.summary_medium_memory()
        if not new_medium_memory:
            return
        self.medium_memory = new_medium_memory
        with open(self.medium_memory_path, 'w', encoding='utf-8') as f:
            f.write(new_medium_memory)

        # 清空短期记忆
        self.context_memory = []
        return "SUCCESS"

    def search_deep_memory(self, query, n_results):
        if not query:
            return GetRecentMemory(limit=n_results, type="history")
        
        contexts = []
        # 调用 SearchMemory，返回的结果已按相关度（distance）从高到低排序，且为一维列表
        history = SearchMemory(query, n_results=n_results, type="history", date=None, distance_threshold=0.6)
        
        # 确保 metadatas 和 documents 都不为空
        if history and history.get('metadatas') and history.get('documents'):
            # 使用 zip() 同时遍历元数据和对应的文档内容
            for metadata, document in zip(history['metadatas'], history['documents']):
                
                # 使用 .get() 安全提取字段，防止某些记录缺失 'title' 或 'date' 导致 KeyError 报错
                title = metadata.get('title', '无标题')
                date = metadata.get('date', '未知日期')
                
                context = {
                    "title": document,
                    "date": date,
                    "original_context": metadata.get('original_context', '无效内容')
                }

                contexts.append(context)
                
        return contexts