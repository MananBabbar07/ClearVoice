from utils import smart_slice


def test_smart_slice_short():
    text = "Short abstract text."
    assert smart_slice(text, 250, 450) == text


def test_smart_slice_long():
    head = "A" * 10
    middle = "M" * 20
    tail = "Z" * 10
    result = smart_slice(head + middle + tail, 10, 10)
    assert result == f"{head} ... {tail}"


def test_smart_slice_empty():
    assert smart_slice("", 100, 100) == ""
    assert smart_slice(None, 100, 100) == ""


def test_smart_slice_tail_non_positive():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    assert smart_slice(text, 5, 0) == "ABCDE"
    assert smart_slice(text, 5, -3) == "ABCDE"

