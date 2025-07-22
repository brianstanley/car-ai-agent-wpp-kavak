import pytest
from utils.tokenizer import truncate_text_to_max_tokens, OpenAITokenizerWrapper

def test_truncate_text_to_max_tokens_truncates_long_text():
    text = "hola " * 200  # 200 tokens if each 'hola' is a token
    max_tokens = 50
    truncated = truncate_text_to_max_tokens(text, max_tokens)
    tokenizer = OpenAITokenizerWrapper()
    assert len(tokenizer.tokenizer.encode(truncated)) <= max_tokens

def test_truncate_text_to_max_tokens_does_not_truncate_short_text():
    text = "esto es un mensaje corto"
    max_tokens = 50
    truncated = truncate_text_to_max_tokens(text, max_tokens)
    assert truncated == text 