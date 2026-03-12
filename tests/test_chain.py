"""
Tests for backend.chain — RAG retrieval and answer generation.
"""

import os
import sys

import pytest

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend import chain
from backend.chain import answer, retrieve


class TestRetrieve:
    """Tests for the retrieve() function."""

    def test_retrieve_returns_list(self):
        """retrieve() should return a list for a valid query."""
        result = retrieve("Rafael Midolli projects")
        assert isinstance(result, list)

    def test_retrieve_non_empty_for_known_query(self):
        """retrieve() should return non-empty results for a query about Rafael."""
        result = retrieve("Quels sont les projets de Rafael ?")
        assert len(result) > 0, "Expected non-empty results for a query about Rafael"

    def test_retrieve_chunks_have_content(self):
        """Each retrieved chunk should have content and source fields."""
        result = retrieve("Rafael Midolli")
        if result:
            for chunk in result:
                assert "content" in chunk
                assert "source" in chunk
                assert chunk["content"]  # Not empty


class TestAnswer:
    """Tests for the answer() function."""

    def test_answer_returns_dict(self):
        """answer() should return a dict with reply, sources, api_used."""
        result = answer("What are Rafael's projects?")
        assert isinstance(result, dict)
        assert "reply" in result
        assert "sources" in result
        assert "api_used" in result

    def test_answer_reply_is_string(self):
        """The reply field should be a non-empty string."""
        result = answer("Tell me about Rafael")
        assert isinstance(result["reply"], str)
        assert len(result["reply"]) > 0

    def test_answer_empty_query(self):
        """answer('') should return an error message without raising."""
        result = answer("")
        assert isinstance(result, dict)
        assert "reply" in result
        assert result["api_used"] == "none"

    def test_answer_none_query(self):
        """answer(None) should not raise an exception."""
        result = answer(None)
        assert isinstance(result, dict)
        assert "reply" in result

    def test_answer_sources_is_list(self):
        """The sources field should be a list."""
        result = answer("Rafael's education")
        assert isinstance(result["sources"], list)

    def test_answer_bio_fallback_without_api_keys(self, monkeypatch):
        """Direct bio queries should remain fast even when no API key is configured."""
        monkeypatch.delenv("GEMINI_API_KEY_1", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY_2", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY_1", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY_2", raising=False)
        monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
        monkeypatch.delenv("NVIDIA_API_KEY_1", raising=False)
        monkeypatch.delenv("NVIDIA_API_KEY_2", raising=False)

        result = answer("quem é o Rafael?")

        assert result["api_used"] == "local-bio"
        assert "Rafael Midolli" in result["reply"]

    def test_project_query_is_not_treated_as_bio(self):
        """Project questions mentioning Rafael should still use the RAG path."""
        assert chain._is_bio_query("quais são os projetos do Rafael?") is False

    def test_retrieve_accepts_google_api_aliases(self, monkeypatch):
        """retrieve() should accept GOOGLE_API_KEY aliases for Gemini embeddings."""
        monkeypatch.delenv("GEMINI_API_KEY_1", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY_2", raising=False)
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY_1", "test-key")

        captured = {}

        class FakeEmbedding:
            values = [0.1, 0.2, 0.3]

        class FakeEmbedResponse:
            embeddings = [FakeEmbedding()]

        class FakeModels:
            def embed_content(self, *, model, contents, config):
                captured["model"] = model
                captured["content"] = contents
                return FakeEmbedResponse()

        class FakeClient:
            def __init__(self, api_key):
                captured["api_key"] = api_key
                self.models = FakeModels()

            def close(self):
                captured["closed"] = True

        def fake_get_gemini_client(api_key):
            captured["api_key"] = api_key
            return FakeClient(api_key)

        class FakeCollection:
            def query(self, query_embeddings, n_results):
                return {
                    "documents": [["chunk content"]],
                    "metadatas": [[{"source": "knowledge.md"}]],
                }

        monkeypatch.setattr(chain, "_get_gemini_client", fake_get_gemini_client)
        monkeypatch.setattr(chain, "_get_collection", lambda: FakeCollection())

        result = retrieve("projetos do Rafael")

        assert captured["api_key"] == "test-key"
        assert captured["closed"] is True
        assert result == [{"content": "chunk content", "source": "knowledge.md"}]
