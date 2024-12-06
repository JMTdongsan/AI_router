from llm_tool import generate_function_call, tools, execute_function_call
from send_llm import vanila_inference

if __name__ == "__main__":
    MESSAGES = [
        {"role": "system",
         "content": """You're an AI assistant. Respond efficiently using these steps:
1. Use provided context and your knowledge first.
2. If insufficient, use functions in order:
a. Dictionary Search (fast, cheap)
b. Online Search (comprehensive, costly)
3. Stop searching once you have enough info.
4. Check search history to avoid repetition.
5. Cite sources used.
6. Prioritize accuracy and relevance.
Efficiency is key. Minimize function calls. Maximize detail and accuaracy"""},
        {"role": "user", "content": "도로 정비 사업이 뭐지?"},
    ]
    messages = MESSAGES[:]

    # 함수 호출 생성
    function_call_message = generate_function_call(messages, tools)
    messages.append(function_call_message.model_dump())

    # 함수 실행 및 결과 추가
    if tool_calls := messages[-1].get("tool_calls", None):
        messages = execute_function_call(messages, tool_calls)
    if not isinstance(messages, str):
        temp = "".join(messages[i]['content'] for i in range(len(messages)))
        messages = temp
    # 최종 응답 생성
    final_response = vanila_inference(messages)
    print("Assistant's response:", final_response)