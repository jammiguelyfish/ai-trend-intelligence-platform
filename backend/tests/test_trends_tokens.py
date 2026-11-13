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
    assert "model" in toks


def test_tokens_keep_tech_terms():
    toks = _tokens("C++ and Rust beat the computer vision system, again.")
    assert {"c++", "rust", "computer", "vision", "system"} <= set(toks)


def test_terms_build_bigrams_that_do_not_cross_stopwords():
    from backend.app.pipelines.trends import _terms

    terms = _terms("Vector database for retrieval augmented generation")
    assert "vector database" in terms
    assert "retrieval augmented" in terms and "augmented generation" in terms
    assert "database retrieval" not in terms  # "for" sits between them


def test_prune_subsumed_keeps_phrase_and_drops_its_words():
    from collections import Counter

    from backend.app.pipelines.trends import _prune_subsumed

    pruned = _prune_subsumed(
        Counter({"vector database": 5, "vector": 5, "database": 6, "agents": 4, "rare phrase": 1})
    )
    assert "vector database" in pruned
    assert "vector" not in pruned and "database" not in pruned  # 6 vs 5 -> covered
    assert "agents" in pruned
    assert "rare phrase" not in pruned


def test_plurals_fold_to_one_term():
    toks = _tokens("Agents and an agent use tools; one tool, many models, one model")
    assert toks.count("agent") == 2 and toks.count("tool") == 2 and toks.count("model") == 2
    assert "bias" in _tokens("hidden bias") and "class" in _tokens("one class")
