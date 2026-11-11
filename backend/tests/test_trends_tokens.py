from backend.app.pipelines.trends import _tokens


def test_tokens_filters_stopwords_and_short():
    toks = _tokens("The new LLM is faster than the old GPT model")
    assert "the" not in toks
    assert "llm" in toks
    assert "model" in toks


def test_tokens_ignore_html_entities_urls_and_english_filler():
    toks = _tokens(
        "<p>Don&#x27;t read https://example.com/&#x2F;path which models</p> across"
    )
    assert "x27" not in toks and "x2f" not in toks
    assert "https" not in toks and "example" not in toks
    assert "which" not in toks and "across" not in toks
    assert "models" in toks


def test_tokens_keep_tech_terms():
    toks = _tokens("C++ and Rust beat the computer vision system, again.")
    assert {"c++", "rust", "computer", "vision", "system"} <= set(toks)
