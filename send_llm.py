from typing import List
from haystack import component
from config import client,model_name
from token_calc import truncate_to_max_tokens


def vanila_inference(message: str):
    if not isinstance(message, str):
        raise TypeError(f"Expected a string, but got {type(message)}")
    message = truncate_to_max_tokens(message)
    message =  [{"role": "system", "content": "you are a smart assistant.please reply in korean"},
                {"role": "user", "content": message}]
    completion = client.chat.completions.create(
        model=model_name,
        temperature=0.7,
        top_p=0.8,
        extra_body={
            "repetition_penalty": 1.05,
        },
        messages=message)
    # try: # 중국어가 나왔을 경우 맨 마지막 것만 선택
    #     completion = completion.choices[0].message.content.split("翻译成韩语：")[-1]
    # except :
    #     pass
    return completion.choices[0].message.content


@component
class CustomGenerator:
    @component.output_types(replies=List[str])
    def run(self, prompt: str):
        reply = vanila_inference(message=prompt)
        # LLM 서버의 응답에서 텍스트 추출
        if isinstance(reply, dict) and 'content' in reply:
            reply_content = reply['content']
        else:
            reply_content = str(reply)
        return {"replies": [reply_content]}
