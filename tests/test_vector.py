import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from northstar_vector import VectorStore, VectorStoreError
from northstar_vector.schemas import CollectionInfo, DocumentChunk, SearchResult

# Module-level mark removed to avoid warnings on sync-only classes.
# Each async class has its own pytestmark.


class TestDocumentChunk:
    def test_defaults(self):
        doc = DocumentChunk(id="1", text="hello")
        assert doc.metadata == {}
        assert doc.embedding is None
        assert doc.source_id is None
        assert doc.project_id is None

    def test_full(self):
        doc = DocumentChunk(
            id="1",
            text="hello",
            metadata={"key": "val"},
            embedding=[0.1, 0.2],
            source_id="src1",
            project_id="proj1",
        )
        assert doc.embedding == [0.1, 0.2]
        assert doc.source_id == "src1"


class TestSearchResult:
    def test_defaults(self):
        r = SearchResult(id="1", text="t", score=0.5, metadata={})
        assert r.source_id is None

    def test_full(self):
        r = SearchResult(
            id="1", text="t", score=0.9, metadata={"k": "v"},
            source_id="src1", project_id="proj1",
        )
        assert r.score == 0.9
        assert r.project_id == "proj1"


class TestCollectionInfo:
    def test_defaults(self):
        info = CollectionInfo(name="test", count=0)
        assert info.dimension is None

    def test_full(self):
        info = CollectionInfo(name="test", count=5, dimension=768)
        assert info.dimension == 768


class TestVectorStoreInit:
    pytestmark = pytest.mark.asyncio

    async def test_not_initialized_raises(self):
        store = VectorStore(chroma_persist_dir="/tmp/nonexistent")
        with pytest.raises(VectorStoreError, match="not initialized"):
            store._require_client()

    async def test_health_false_when_not_initialized(self):
        store = VectorStore()
        result = await store.health()
        assert result is False

    async def test_initialized_health(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            with patch.object(store, "_client") as mock_client:
                mock_client.heartbeat.return_value = 1
                result = await store.health()
                assert result is True


class TestVectorStoreOperations:
    pytestmark = pytest.mark.asyncio

    async def test_add_documents_needs_embedding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            store._embedding_service = None
            with pytest.raises(VectorStoreError, match="EmbeddingService not available"):
                await store.add_documents("test", [])

    async def test_search_needs_embedding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            store._embedding_service = None
            with pytest.raises(VectorStoreError, match="EmbeddingService not available"):
                await store.search("test", "query")

    async def test_search_missing_collection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            mock_emb = AsyncMock()
            mock_emb.embed = AsyncMock(return_value=[0.1] * 4)
            store._embedding_service = mock_emb
            mock_collection = MagicMock()
            mock_collection.get_collection.side_effect = ValueError("not found")
            store._client.get_collection = MagicMock(side_effect=ValueError("not found"))
            with pytest.raises(VectorStoreError, match="not found"):
                await store.search("nonexistent", "query")

    async def test_delete_documents_missing_collection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            store._client.get_collection = MagicMock(side_effect=ValueError("not found"))
            with pytest.raises(VectorStoreError, match="not found"):
                await store.delete_documents("nonexistent", ["1"])

    async def test_delete_collection_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            store._client.delete_collection = MagicMock(side_effect=ValueError("not found"))
            with pytest.raises(VectorStoreError, match="not found"):
                await store.delete_collection("nonexistent")

    async def test_list_collections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            mock_col = MagicMock()
            mock_col.name = "default"
            mock_col.count.return_value = 5
            mock_col.peek.return_value = {"embeddings": [[0.1] * 4]}
            store._client.list_collections.return_value = [mock_col]
            result = await store.list_collections()
            assert len(result) == 1
            assert result[0].name == "default"
            assert result[0].count == 5
            assert result[0].dimension == 4

    async def test_collection_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            mock_col = MagicMock()
            mock_col.count.return_value = 10
            store._client.get_collection.return_value = mock_col
            count = await store.collection_count("default")
            assert count == 10

    async def test_collection_count_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            store._client.get_collection = MagicMock(side_effect=ValueError("not found"))
            with pytest.raises(VectorStoreError, match="not found"):
                await store.collection_count("nonexistent")

    async def test_get_document_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            mock_col = MagicMock()
            mock_col.get.return_value = {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
            store._client.get_collection.return_value = mock_col
            result = await store.get_document("default", "nonexistent")
            assert result is None

    async def test_get_document_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            mock_col = MagicMock()
            mock_col.get.return_value = {
                "ids": ["doc1"],
                "documents": ["hello world"],
                "metadatas": [{"source_id": "src1", "project_id": "proj1", "key": "val"}],
                "embeddings": [[0.1, 0.2]],
            }
            store._client.get_collection.return_value = mock_col
            doc = await store.get_document("default", "doc1")
            assert doc is not None
            assert doc.id == "doc1"
            assert doc.text == "hello world"
            assert doc.source_id == "src1"
            assert doc.project_id == "proj1"

    async def test_get_document_collection_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(chroma_persist_dir=tmpdir)
            store._client = MagicMock()
            store._client.get_collection = MagicMock(side_effect=ValueError("not found"))
            result = await store.get_document("nonexistent", "1")
            assert result is None
