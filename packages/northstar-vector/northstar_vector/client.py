import asyncio
from pathlib import Path

import chromadb
from chromadb.config import Settings
import structlog

from northstar_vector.schemas import CollectionInfo, DocumentChunk, SearchResult

logger = structlog.get_logger(__name__)

try:
    from northstar_llm.service import EmbeddingService
except ImportError:
    EmbeddingService = None


class VectorStoreError(Exception):
    pass


class VectorStore:
    def __init__(
        self,
        chroma_persist_dir: str = "~/.cache/northstar/chromadb",
        embedding_service: EmbeddingService | None = None,
    ):
        self._persist_dir = str(Path(chroma_persist_dir).expanduser().resolve())
        self._embedding_service = embedding_service
        self._client: chromadb.PersistentClient | None = None

    async def initialize(self) -> None:
        self._client = await asyncio.to_thread(
            chromadb.PersistentClient,
            path=self._persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        try:
            await asyncio.to_thread(
                self._client.get_or_create_collection,
                name="default",
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to create default collection: {exc}"
            ) from exc

        if self._embedding_service is None and EmbeddingService is not None:
            logger.info("no_embedding_service_provided_creating_default")
            self._embedding_service = EmbeddingService()

        logger.info("vector_store_initialized", path=self._persist_dir)

    def _require_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            raise VectorStoreError(
                "VectorStore not initialized. Call initialize() first."
            )
        return self._client

    async def add_documents(
        self,
        collection_name: str,
        documents: list[DocumentChunk],
    ) -> list[str]:
        client = self._require_client()
        collection = await asyncio.to_thread(
            client.get_or_create_collection,
            name=collection_name,
        )

        if self._embedding_service is None:
            raise VectorStoreError(
                "EmbeddingService not available. Cannot embed documents."
            )

        ids: list[str] = []
        metadatas: list[dict] = []
        documents_text: list[str] = []
        embeddings: list[list[float]] | None = []

        for doc in documents:
            ids.append(doc.id)
            metadatas.append({**doc.metadata, "source_id": doc.source_id, "project_id": doc.project_id})
            documents_text.append(doc.text)
            if doc.embedding is not None:
                embeddings.append(doc.embedding)
            else:
                emb = await self._embedding_service.embed(doc.text)
                embeddings.append(emb)

        if any(e is None for e in embeddings):
            raise VectorStoreError("Failed to generate embeddings for one or more documents")

        ids_list = ids
        metadatas_list = metadatas
        documents_list = documents_text
        embeddings_list = embeddings

        try:
            await asyncio.to_thread(
                collection.add,
                ids=ids_list,
                metadatas=metadatas_list,
                documents=documents_list,
                embeddings=embeddings_list,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to add documents to collection '{collection_name}': {exc}"
            ) from exc

        logger.info(
            "documents_added",
            collection=collection_name,
            count=len(documents),
        )
        return ids_list

    async def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
        filters: dict | None = None,
    ) -> list[SearchResult]:
        client = self._require_client()

        if self._embedding_service is None:
            raise VectorStoreError(
                "EmbeddingService not available. Cannot search."
            )

        try:
            collection = await asyncio.to_thread(
                client.get_collection,
                name=collection_name,
            )
        except ValueError as exc:
            raise VectorStoreError(
                f"Collection '{collection_name}' not found: {exc}"
            ) from exc

        query_embedding = await self._embedding_service.embed(query)
        if query_embedding is None:
            raise VectorStoreError("Failed to generate query embedding")

        where = filters or {}

        try:
            results = await asyncio.to_thread(
                collection.query,
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to search collection '{collection_name}': {exc}"
            ) from exc

        search_results: list[SearchResult] = []
        if not results["ids"]:
            return search_results

        ids_batch = results["ids"][0]
        distances = results["distances"][0]
        documents_text_batch = results["documents"][0]
        metadatas_batch = results["metadatas"][0]

        for i in range(len(ids_batch)):
            doc_id = ids_batch[i]
            score = 1.0 - distances[i] if distances else 0.0
            text = documents_text_batch[i] if documents_text_batch else ""
            meta = metadatas_batch[i] if metadatas_batch else {}
            search_results.append(
                SearchResult(
                    id=doc_id,
                    text=text,
                    score=score,
                    metadata=meta,
                    source_id=meta.get("source_id"),
                    project_id=meta.get("project_id"),
                )
            )

        return search_results

    async def delete_documents(
        self,
        collection_name: str,
        ids: list[str],
    ) -> None:
        client = self._require_client()

        try:
            collection = await asyncio.to_thread(
                client.get_collection,
                name=collection_name,
            )
        except ValueError as exc:
            raise VectorStoreError(
                f"Collection '{collection_name}' not found: {exc}"
            ) from exc

        try:
            await asyncio.to_thread(collection.delete, ids=ids)
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to delete documents from '{collection_name}': {exc}"
            ) from exc

        logger.info("documents_deleted", collection=collection_name, count=len(ids))

    async def delete_collection(self, collection_name: str) -> None:
        client = self._require_client()

        try:
            await asyncio.to_thread(client.delete_collection, name=collection_name)
        except ValueError as exc:
            raise VectorStoreError(
                f"Collection '{collection_name}' not found: {exc}"
            ) from exc

        logger.info("collection_deleted", collection=collection_name)

    async def list_collections(self) -> list[CollectionInfo]:
        client = self._require_client()

        try:
            collections = await asyncio.to_thread(client.list_collections)
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to list collections: {exc}"
            ) from exc

        result: list[CollectionInfo] = []
        for col in collections:
            try:
                count = await asyncio.to_thread(col.count)
            except Exception:
                count = 0

            try:
                peek = await asyncio.to_thread(col.peek, limit=1)
                embeddings_list = peek.get("embeddings", [])
                dimension = len(embeddings_list[0]) if embeddings_list else None
            except Exception:
                dimension = None

            result.append(
                CollectionInfo(
                    name=col.name,
                    count=count,
                    dimension=dimension,
                )
            )

        return result

    async def collection_count(self, collection_name: str) -> int:
        client = self._require_client()

        try:
            collection = await asyncio.to_thread(
                client.get_collection,
                name=collection_name,
            )
        except ValueError as exc:
            raise VectorStoreError(
                f"Collection '{collection_name}' not found: {exc}"
            ) from exc

        try:
            count = await asyncio.to_thread(collection.count)
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to count collection '{collection_name}': {exc}"
            ) from exc

        return count

    async def get_document(
        self,
        collection_name: str,
        doc_id: str,
    ) -> DocumentChunk | None:
        client = self._require_client()

        try:
            collection = await asyncio.to_thread(
                client.get_collection,
                name=collection_name,
            )
        except ValueError:
            return None

        try:
            result = await asyncio.to_thread(
                collection.get,
                ids=[doc_id],
                include=["documents", "metadatas", "embeddings"],
            )
        except Exception:
            return None

        if not result["ids"] or len(result["ids"]) == 0:
            return None

        doc_text = result["documents"][0] if result["documents"] else ""
        meta = result["metadatas"][0] if result["metadatas"] else {}
        emb = result["embeddings"][0] if result.get("embeddings") else None

        return DocumentChunk(
            id=doc_id,
            text=doc_text,
            metadata={k: v for k, v in meta.items() if k not in ("source_id", "project_id")},
            embedding=emb,
            source_id=meta.get("source_id"),
            project_id=meta.get("project_id"),
        )

    async def health(self) -> bool:
        if self._client is None:
            return False

        try:
            await asyncio.to_thread(self._client.heartbeat)
            return True
        except Exception:
            return False
