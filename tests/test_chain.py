"""
Tests for backend.chain — RAG retrieval and answer generation.
"""

import os
import sys

import pytest

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
