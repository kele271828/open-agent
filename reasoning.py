import os
import openai
import json
import logging
import httpx

from utils.tools_init import *
from utils.utils import upload_file_and_get_url
from config import config

custom_client = httpx.Client(
    proxy=None,
    trust_env=False,
    timeout=30.0
)

# API key: 优先使用环境变量，其次使用配置文件
api_key = os.getenv("ALI_API_KEY") or config.LLM_API_KEY

client = openai.OpenAI(
    api_key=api_key,
    base_url=config.LLM_BASE_URL,
    http_client=custom_client,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler("agent_chat.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def Reasoning(messages, model="qwen3.5-plus", temperature=0.7, thinking=False, tools=None):
    logger.info(f"开始请求大模型 (Reasoning模式)，模型: {model}, thinking: {thinking}, tools: {len(tools) if tools else 0}")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            extra_body={"enable_thinking": thinking},
            tools=tools,
        )
    except Exception as e:
        logger.error(f"大模型请求失败: {e}")
        return None

    if response.choices[0].message.content is None:
        response.choices[0].message.content = ""
    messages.append(response.choices[0].message)

    while response.choices[0].message.tool_calls is not None:
        for tool_call in response.choices[0].message.tool_calls:
            tool_call_id = tool_call.id
            func_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            logger.info(f"正在调用工具 [{func_name}]，参数：{arguments}")

            if not arguments:
                tool_result = name2func[func_name]()
            else:
                tool_result = name2func[func_name](**arguments)

            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": tool_result,
            }
            logger.info(f"工具 [{func_name}] 返回")
            messages.append(tool_message)

        logger.info("工具执行完毕，携工具结果再次请求大模型...")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                extra_body={"enable_thinking": thinking},
                tools=tools,
            )
        except Exception as e:
            logger.error(f"大模型请求失败: {e}")
            return None

        if response.choices[0].message.content is None:
            response.choices[0].message.content = ""
        messages.append(response.choices[0].message)

    logger.info("Reasoning 模式请求结束。")
    output = {
        "content": response.choices[0].message.content,
        "reasoning_content": response.choices[0].message.reasoning_content
        if hasattr(response.choices[0].message, 'reasoning_content') else None,
    }
    return output


def Stream_Reasoning(messages, model="qwen3.5-plus", temperature=0.7, thinking=False, tools=None):
    """
    生成器：支持多轮工具调用的流式响应。
    自动拼接工具参数、执行本地函数，并将结果送回模型继续流式生成。
    """
    logger.info(f"开始流式请求，模型: {model}, tools: {len(tools) if tools else 0}")

    final_content = ""
    final_reasoning = ""

    try:
        while True:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                temperature=temperature,
                extra_body={"enable_thinking": thinking},
                tools=tools,
            )

            start_reasoning = False
            start_answer = False
            start_tool = False

            current_content = ""
            current_reasoning = ""
            tool_calls_dict = {}

            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                    if not start_reasoning:
                        yield "\n\n[思考]\n"
                        start_reasoning = True
                    text = delta.reasoning_content
                    current_reasoning += text
                    final_reasoning += text
                    yield text

                if hasattr(delta, 'content') and delta.content is not None:
                    if not start_answer:
                        yield "\n\n[回答]\n"
                        start_answer = True
                    text = delta.content
                    current_content += text
                    final_content += text
                    yield text

                if hasattr(delta, 'tool_calls') and delta.tool_calls is not None:
                    if not start_tool:
                        yield "\n\n[模型决定调用工具]\n"
                        start_tool = True

                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_dict:
                            tool_calls_dict[idx] = {"id": tc.id, "name": "", "arguments": ""}

                        if tc.function.name:
                            tool_calls_dict[idx]["name"] += tc.function.name
                            yield f"- 准备调用函数: `{tc.function.name}`...\n"

                        if tc.function.arguments:
                            tool_calls_dict[idx]["arguments"] += tc.function.arguments

            assistant_message = {
                "role": "assistant",
                "content": current_content if current_content else ""
            }

            if tool_calls_dict:
                parsed_tool_calls = []
                for idx, tc in tool_calls_dict.items():
                    parsed_tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": tc["arguments"]
                        }
                    })
                assistant_message["tool_calls"] = parsed_tool_calls

            messages.append(assistant_message)

            if not tool_calls_dict:
                logger.info("流式输出完毕。")
                break

            for idx, tc in tool_calls_dict.items():
                func_name = tc["name"]
                tool_call_id = tc["id"]

                try:
                    arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
                except json.JSONDecodeError:
                    arguments = {}
                    yield f"\n[错误] JSON解析失败\n"

                yield f"\n[执行工具] `{func_name}`\n"

                if func_name in name2func:
                    tool_result = name2func[func_name](**arguments) if arguments else name2func[func_name]()
                else:
                    tool_result = f"Error: 找不到工具 {func_name}"

                yield f"\n[工具返回] {tool_result}\n"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_result,
                })

            yield "\n\n[大模型继续生成...]\n"

    except Exception as e:
        logger.error(f"流式请求失败: {e}")
        yield f"\n\n[异常: {str(e)}]\n"
        return {"content": "", "reasoning_content": None}

    return {
        "content": final_content,
        "reasoning_content": final_reasoning if final_reasoning else None,
    }


if __name__ == "__main__":
    # 简单测试
    messages = [
        {"role": "user", "content": "你好，请介绍一下你自己。"}
    ]
    output = Reasoning(messages, model=config.MODEL_NAME, temperature=0.7, thinking=False)
    if output:
        print("回复:", output["content"])
