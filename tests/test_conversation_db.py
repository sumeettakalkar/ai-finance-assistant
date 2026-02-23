"""Tests for SQLite conversation database with in-memory DB."""

import pytest

from src.storage.conversation_db import ConversationDB


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    return ConversationDB(":memory:")


class TestCreateConversation:
    def test_creates_with_title(self, db):
        conv = db.create_conversation("chat", "My Chat")
        assert conv.title == "My Chat"
        assert conv.tab == "chat"
        assert conv.id

    def test_creates_with_default_title(self, db):
        conv = db.create_conversation("portfolio")
        assert conv.title == "New Conversation"


class TestListConversations:
    def test_empty_list(self, db):
        assert db.list_conversations() == []

    def test_lists_all(self, db):
        db.create_conversation("chat", "Chat 1")
        db.create_conversation("portfolio", "Portfolio 1")
        convs = db.list_conversations()
        assert len(convs) == 2

    def test_filter_by_tab(self, db):
        db.create_conversation("chat", "Chat 1")
        db.create_conversation("portfolio", "Portfolio 1")
        convs = db.list_conversations(tab="chat")
        assert len(convs) == 1
        assert convs[0].tab == "chat"


class TestGetConversation:
    def test_returns_none_for_missing(self, db):
        assert db.get_conversation("nonexistent") is None

    def test_returns_with_messages(self, db):
        conv = db.create_conversation("chat")
        db.add_message(conv.id, "user", "Hello")
        db.add_message(conv.id, "assistant", "Hi there!")

        loaded = db.get_conversation(conv.id)
        assert loaded is not None
        assert len(loaded.messages) == 2
        assert loaded.messages[0].role == "user"
        assert loaded.messages[1].role == "assistant"


class TestDeleteConversation:
    def test_deletes_existing(self, db):
        conv = db.create_conversation("chat")
        assert db.delete_conversation(conv.id) is True
        assert db.get_conversation(conv.id) is None

    def test_returns_false_for_missing(self, db):
        assert db.delete_conversation("nonexistent") is False


class TestAddMessage:
    def test_adds_message_with_seq(self, db):
        conv = db.create_conversation("chat")
        msg1 = db.add_message(conv.id, "user", "First")
        msg2 = db.add_message(conv.id, "assistant", "Second")
        assert msg1.seq == 1
        assert msg2.seq == 2

    def test_auto_titles_from_first_user_message(self, db):
        conv = db.create_conversation("chat")
        db.add_message(conv.id, "user", "What is dollar-cost averaging?")
        loaded = db.get_conversation(conv.id)
        assert loaded.title == "What is dollar-cost averaging?"

    def test_truncates_long_titles(self, db):
        conv = db.create_conversation("chat")
        long_msg = "A" * 100
        db.add_message(conv.id, "user", long_msg)
        loaded = db.get_conversation(conv.id)
        assert len(loaded.title) <= 63  # 60 chars + "..."
        assert loaded.title.endswith("...")

    def test_stores_sources_and_metadata(self, db):
        conv = db.create_conversation("chat")
        db.add_message(
            conv.id, "assistant", "Answer",
            sources=["Investopedia"],
            metadata={"risk": "low"},
        )
        loaded = db.get_conversation(conv.id)
        msg = loaded.messages[0]
        assert msg.sources == ["Investopedia"]
        assert msg.metadata == {"risk": "low"}


class TestGetRecentMessages:
    def test_returns_in_chronological_order(self, db):
        conv = db.create_conversation("chat")
        for i in range(5):
            db.add_message(conv.id, "user", f"Message {i}")

        recent = db.get_recent_messages(conv.id, limit=3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[-1].content == "Message 4"


class TestUpdateConversationTitle:
    def test_updates_title(self, db):
        conv = db.create_conversation("chat", "Old Title")
        db.update_conversation_title(conv.id, "New Title")
        loaded = db.get_conversation(conv.id)
        assert loaded.title == "New Title"
