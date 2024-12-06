import json
from haystack import component
from config import client,model_name
from typing import Dict, Any, List, Union

from crawler import search2naver
from send_llm import vanila_inference
from word_definition import get_word_definition

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_word_definition",
            "description": "Get the definition of a word,only support korean,",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to look up",
                    },
                },
                "required": ["word"],
            },
        }
    },
{
        "type": "function",
        "function": {
            "name": "search_on_online",
            "description": "search a word on online search engine, provide real time information and information that is not in the dictionary."
                           " But search cost is very high, use this carefully",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to look up",
                    },
                },
                "required": ["word"],
            },
        }
    }
]


@component
class ToolGenerator:
    @component.output_types(replies=List[str])
    def run(self, prompt: str):
        reply = vanila_inference(message=prompt)
        # LLM 서버의 응답에서 텍스트 추출
        if isinstance(reply, dict) and 'content' in reply:
            reply_content = reply['content']
        else:
            reply_content = str(reply)
        return {"replies": [reply_content]}


def get_function_by_name(name:str):
    if name == "get_word_definition":
        return get_word_definition
    if name == "search_on_online":
        return search2naver


def send2llm(messages: List[Dict[str, Union[str, Any]]]) -> str :
    if messages is None:
        messages = [{"role": "user", "content": "who are you? "}]
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2,
            tools=tools ) # tools를 LLM에게 전달
    except Exception as e:
        return "error :" + str(e)
    # print(completion.choices[0].message)
    return completion.choices[0].message.content


def generate_function_call(messages, tools):
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        temperature=0.7,
        top_p=0.8,
        max_tokens=512,
        extra_body={
            "repetition_penalty": 1.05,
        },
    )
    return response.choices[0].message


# 함수 실행 및 결과 추가
def execute_function_call(messages, tool_calls):
    for tool_call in tool_calls:
        call_id = tool_call["id"]
        if fn_call := tool_call.get("function"):
            fn_name = fn_call["name"]
            fn_args = json.loads(fn_call["arguments"])
            fn_res = json.dumps(get_function_by_name(fn_name)(**fn_args))
            messages.append({
                "role": "tool",
                "content": fn_res,
                "tool_call_id": call_id,
            })
    return messages





