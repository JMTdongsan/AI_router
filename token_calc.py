from transformers import AutoTokenizer
from config import MAX_TOKENS, DEFAULT_MODEL


tokenizer = AutoTokenizer.from_pretrained(DEFAULT_MODEL)


def count_tokens(text: str) -> int:
    """텍스트의 토큰 수를 계산하는 함수."""
    if not isinstance(text, str):
        raise TypeError(f"Expected a string, but got {type(text)}")
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)


def truncate_to_max_tokens(text: str, max_tokens: int = MAX_TOKENS) -> str:
    token_count = count_tokens(text)
    if token_count <= MAX_TOKENS:
        return text
    """텍스트가 최대 토큰 수를 넘지 않도록 자르는 함수."""
    tokens = tokenizer.encode(text, add_special_tokens=False)
    # 토큰 수가 최대 수를 넘으면 자르기
    if len(tokens) > max_tokens:
        print("token over droped : "+tokenizer.decode(tokens[max_tokens:], skip_special_tokens=True))
        tokens = tokens[:max_tokens]
    # 잘린 토큰을 다시 텍스트로 변환
    truncated_text = tokenizer.decode(tokens, skip_special_tokens=True)
    return truncated_text