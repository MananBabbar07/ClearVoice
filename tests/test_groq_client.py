from unittest.mock import MagicMock

import groq_client


def _make_completion(text: str):
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_call_groq_fallback_order(monkeypatch):
    monkeypatch.setattr(groq_client.time, "sleep", lambda *_: None)
    mock_create = MagicMock(
        side_effect=[
            RuntimeError("temporary error"),
            RuntimeError("temporary error"),
            _make_completion('{"ok": true}'),
        ]
    )
    monkeypatch.setattr(groq_client.client.chat.completions, "create", mock_create)

    raw, model = groq_client.call_groq("prompt", retries=2, models=["model-a", "model-b"])
    assert raw == '{"ok": true}'
    assert model == "model-b"
    called_models = [call.kwargs["model"] for call in mock_create.call_args_list]
    assert called_models == ["model-a", "model-a", "model-b"]


def test_call_groq_429_moves_to_next_model(monkeypatch):
    mock_create = MagicMock(
        side_effect=[
            RuntimeError("Error 429 rate_limit exceeded"),
            _make_completion("ok"),
        ]
    )
    monkeypatch.setattr(groq_client.client.chat.completions, "create", mock_create)

    raw, model = groq_client.call_groq("prompt", retries=3, models=["m1", "m2"])
    assert (raw, model) == ("ok", "m2")
    assert mock_create.call_count == 2


def test_call_groq_401_moves_to_next_model(monkeypatch):
    mock_create = MagicMock(
        side_effect=[
            RuntimeError("Error code: 401 unauthorized"),
            _make_completion("ok"),
        ]
    )
    monkeypatch.setattr(groq_client.client.chat.completions, "create", mock_create)

    raw, model = groq_client.call_groq("prompt", retries=3, models=["m1", "m2"])
    assert (raw, model) == ("ok", "m2")
    assert mock_create.call_count == 2


def test_call_groq_404_marks_unavailable_and_skips_future_calls(monkeypatch):
    mock_create = MagicMock(
        side_effect=[
            RuntimeError("Error code: 404 model_not_found"),
            _make_completion("from m2"),
            _make_completion("from m2 again"),
        ]
    )
    monkeypatch.setattr(groq_client.client.chat.completions, "create", mock_create)

    raw1, model1 = groq_client.call_groq("p1", models=["missing-model", "m2"])
    assert (raw1, model1) == ("from m2", "m2")
    assert "missing-model" in groq_client._unavailable

    raw2, model2 = groq_client.call_groq("p2", models=["missing-model", "m2"])
    assert (raw2, model2) == ("from m2 again", "m2")
    called_models = [call.kwargs["model"] for call in mock_create.call_args_list]
    assert called_models == ["missing-model", "m2", "m2"]


def test_call_groq_returns_none_when_all_models_unavailable(monkeypatch):
    groq_client._unavailable.update(["m1", "m2"])
    mock_create = MagicMock()
    monkeypatch.setattr(groq_client.client.chat.completions, "create", mock_create)

    raw, model = groq_client.call_groq("prompt", models=["m1", "m2"])
    assert (raw, model) == (None, None)
    assert mock_create.call_count == 0


def test_call_groq_validator_rejection_moves_on(monkeypatch):
    mock_create = MagicMock(
        side_effect=[
            _make_completion("invalid"),
            _make_completion("invalid"),
            _make_completion("valid"),
        ]
    )
    monkeypatch.setattr(groq_client.client.chat.completions, "create", mock_create)

    raw, model = groq_client.call_groq(
        "prompt",
        retries=2,
        models=["m1", "m2"],
        validator=lambda r: r == "valid",
    )
    assert (raw, model) == ("valid", "m2")


def test_call_groq_all_fail_returns_none(monkeypatch):
    monkeypatch.setattr(groq_client.time, "sleep", lambda *_: None)
    mock_create = MagicMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(groq_client.client.chat.completions, "create", mock_create)

    raw, model = groq_client.call_groq("prompt", retries=2, models=["m1", "m2"])
    assert (raw, model) == (None, None)
