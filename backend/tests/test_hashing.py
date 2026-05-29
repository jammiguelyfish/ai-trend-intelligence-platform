from backend.app.utils.hashing import content_hash


def test_content_hash_is_stable_and_normalized():
    a = content_hash("reddit", "abc", " Hello World ", "Body")
    b = content_hash("reddit", "abc", "hello world", "body")
    assert a == b
    assert len(a) == 64


def test_content_hash_changes_on_input():
    a = content_hash("reddit", "abc", "Hello", "Body")
    b = content_hash("reddit", "abc", "Hello", "Body2")
    assert a != b
