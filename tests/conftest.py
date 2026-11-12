import os
import sys
from unittest.mock import MagicMock, patch

import fakeredis
import numpy as np
import pytest

_fake_embedder = MagicMock()
_fake_embedder.encode.side_effect = lambda texts, **kwargs: (
    np.array([[1.0, 0.0, 0.0] for _ in texts]) if isinstance(texts, list) else np.array([1.0, 0.0, 0.0])
)

_patches = [
    patch("sentence_transformers.SentenceTransformer", return_value=_fake_embedder),
    patch("groq.Groq", return_value=MagicMock()),
    patch("dotenv.load_dotenv", return_value=False),
    patch(
        "redis.Redis.from_url",
        side_effect=lambda *args, **kwargs: fakeredis.FakeRedis(decode_responses=True),
    ),
]

for _p in _patches:
    _p.start()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app")))

import groq_client
import retrieval
import verify
from agents import decomposer, explainer, judge

import backend.main as main_module


@pytest.fixture(autouse=True)
def reset_unavailable_models():
    groq_client._unavailable.clear()
    yield
    groq_client._unavailable.clear()


@pytest.fixture
def fake_redis(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(main_module, "cache", fake)
    return fake


@pytest.fixture
def client(fake_redis):
    from fastapi.testclient import TestClient

    return TestClient(main_module.app)


@pytest.fixture
def mock_sentence_transformer(monkeypatch):
    mock_model = MagicMock()
    mock_model.encode.side_effect = lambda texts, **kwargs: (
        np.array([[1.0, 0.0, 0.0] for _ in texts]) if isinstance(texts, list) else np.array([1.0, 0.0, 0.0])
    )
    monkeypatch.setattr(retrieval, "model", mock_model)
    return mock_model


@pytest.fixture
def mock_entrez(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(retrieval.Entrez, "esearch", mock.esearch)
    monkeypatch.setattr(retrieval.Entrez, "efetch", mock.efetch)
    monkeypatch.setattr(retrieval.Entrez, "read", mock.read)
    monkeypatch.setattr(retrieval.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(retrieval, "_last_entrez_call", 0.0)
    return mock


@pytest.fixture
def mock_call_groq(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(groq_client, "call_groq", mock)
    monkeypatch.setattr(verify, "call_groq", mock)
    monkeypatch.setattr(judge, "call_groq", mock)
    monkeypatch.setattr(decomposer, "call_groq", mock)
    monkeypatch.setattr(explainer, "call_groq", mock)
    return mock
