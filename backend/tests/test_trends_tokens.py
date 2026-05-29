from backend.app.pipelines.trends import _tokens


def test_tokens_filters_stopwords_and_short():
    toks = _tokens("The new LLM is faster than the old GPT model")
    assert "the" not in toks
    assert "llm" in toks
    assert "model" in toks
