import sqlite3

import pytest

from research_portal.services.conversation import ConversationStore


class TestConversationStore:
    @pytest.fixture
    def store(self):
        s = ConversationStore(db_path=":memory:")
        yield s
        s.close()

    def test_create_conversation(self, store):
        conv = store.create_conversation(title="Test Conversation")
        assert "id" in conv
        assert conv["title"] == "Test Conversation"
        assert conv["project_id"] is None

    def test_create_conversation_with_project(self, store):
        conv = store.create_conversation(title="Proj Chat", project_id="p-123")
        assert conv["project_id"] == "p-123"

    def test_list_conversations(self, store):
        store.create_conversation(title="First")
        store.create_conversation(title="Second")
        convs = store.list_conversations()
        assert len(convs) == 2

    def test_list_conversations_respects_limit(self, store):
        for i in range(10):
            store.create_conversation(title=f"Conv {i}")
        convs = store.list_conversations(limit=3)
        assert len(convs) == 3

    def test_get_conversation(self, store):
        conv = store.create_conversation(title="Target")
        fetched = store.get_conversation(conv["id"])
        assert fetched is not None
        assert fetched["title"] == "Target"

    def test_get_conversation_not_found(self, store):
        assert store.get_conversation("nonexistent") is None

    def test_delete_conversation(self, store):
        conv = store.create_conversation(title="Delete Me")
        assert store.delete_conversation(conv["id"]) is True
        assert store.get_conversation(conv["id"]) is None

    def test_delete_nonexistent(self, store):
        assert store.delete_conversation("nonexistent") is False

    def test_add_message(self, store):
        conv = store.create_conversation(title="Msg Test")
        msg = store.add_message(conv["id"], "user", "Hello, world!")
        assert msg["role"] == "user"
        assert msg["content"] == "Hello, world!"
        assert msg["conversation_id"] == conv["id"]

    def test_add_message_with_tool_results(self, store):
        conv = store.create_conversation(title="Tools")
        tool_results = [{"action": "search", "status": "completed"}]
        msg = store.add_message(conv["id"], "assistant", "Done.", tool_results=tool_results)
        assert msg["tool_results"] == tool_results

    def test_messages_appear_in_get_conversation(self, store):
        conv = store.create_conversation(title="Full")
        store.add_message(conv["id"], "user", "Q1")
        store.add_message(conv["id"], "assistant", "A1")
        fetched = store.get_conversation(conv["id"])
        assert len(fetched["messages"]) == 2
        assert fetched["messages"][0]["role"] == "user"
        assert fetched["messages"][1]["role"] == "assistant"

    def test_cascade_delete_removes_messages(self, store):
        conv = store.create_conversation(title="Cascade")
        store.add_message(conv["id"], "user", "msg")
        store.delete_conversation(conv["id"])
        conn = store._get_conn()
        row = conn.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conv["id"],)).fetchone()
        assert row[0] == 0

    def test_tool_results_json_roundtrip(self, store):
        conv = store.create_conversation(title="JSON")
        tr = [
            {"action": "search", "data": {"results": [{"id": "1", "score": 0.9}]}},
            {"action": "extract", "data": {"entities_count": 5}},
        ]
        store.add_message(conv["id"], "assistant", "Results", tool_results=tr)
        fetched = store.get_conversation(conv["id"])
        msg = fetched["messages"][0]
        assert msg["tool_results"] == tr

    def test_close_connection(self, store):
        store.close()
        assert store._conn is None

    def test_updated_at_changes_on_new_message(self, store):
        conv = store.create_conversation(title="Update")
        old_updated = conv["updated_at"]
        store.add_message(conv["id"], "user", "ping")
        fetched = store.get_conversation(conv["id"])
        assert fetched["updated_at"] > old_updated

    def test_roles_validation(self, store):
        conv = store.create_conversation(title="Roles")
        for role in ("user", "assistant", "system"):
            msg = store.add_message(conv["id"], role, f"msg as {role}")
            assert msg["role"] == role

    def test_invalid_role_raises(self, store):
        conv = store.create_conversation(title="Bad Role")
        with pytest.raises(sqlite3.IntegrityError):
            store.add_message(conv["id"], "invalid_role", "bad")
