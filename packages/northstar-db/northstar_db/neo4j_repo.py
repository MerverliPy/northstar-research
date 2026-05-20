import uuid

import neo4j
import structlog
from neo4j import AsyncGraphDatabase

from northstar_models.models import Claim, Entity

logger = structlog.get_logger(__name__)

# Allowlist of valid Cypher relationship types to prevent injection
VALID_RELATIONSHIP_TYPES: frozenset[str] = frozenset({
    "MENTIONS", "RELATES_TO", "MAKES_CLAIM", "CITES", "REFERENCES",
    "SUPPORTS", "CONTRADICTS", "ASSOCIATED_WITH", "PART_OF", "LEADS_TO",
})


class GraphError(Exception):
    pass


class Neo4jRepository:
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "",
    ):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: neo4j.AsyncDriver | None = None

    async def initialize(self) -> None:
        self._driver = AsyncGraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password),
        )
        async with self._driver.session() as session:
            await session.run("RETURN 1")
            try:
                await session.run("CALL apoc.help('help')")
            except Exception:
                raise GraphError(
                    "APOC library is not installed in Neo4j. Install it to enable graph operations: "
                    "https://neo4j.com/labs/apoc/"
                )
            await session.run("CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.id)")
            await session.run("CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)")
            await session.run("CREATE INDEX source_id_index IF NOT EXISTS FOR (s:Source) ON (s.id)")
            await session.run("CREATE INDEX source_project_index IF NOT EXISTS FOR (s:Source) ON (s.project_id)")
            await session.run("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
            await session.run("CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE")
        logger.info("neo4j_initialized")

    async def close(self) -> None:
        if self._driver is not None:
            await self._driver.close()
            logger.info("neo4j_disposed")

    def _session(self):
        if self._driver is None:
            raise GraphError("Neo4j driver not initialized")
        return self._driver.session()

    async def create_entity_node(self, entity: Entity) -> None:
        async with self._session() as session:
            await session.run(
                """
                MERGE (e:Entity {id: $id})
                SET e.name = $name,
                    e.entity_type = $entity_type,
                    e.source_id = $source_id,
                    e.description = $description,
                    e.updated_at = timestamp()
                """,
                id=str(entity.id),
                name=entity.name,
                entity_type=entity.entity_type.value,
                source_id=str(entity.source_id) if entity.source_id else None,
                description=entity.description,
            )

    async def create_claim_relationship(self, claim: Claim) -> None:
        async with self._session() as session:
            if claim.source_id:
                source_node_id = str(claim.source_id)
                await session.run(
                    """
                    MERGE (s:Source {id: $source_id})
                    """,
                    source_id=source_node_id,
                )
            if claim.entity_id:
                await session.run(
                    """
                    MERGE (e:Entity {id: $entity_id})
                    """,
                    entity_id=str(claim.entity_id),
                )
            if claim.source_id and claim.entity_id:
                await session.run(
                    """
                    MATCH (s:Source {id: $source_id})
                    MATCH (e:Entity {id: $entity_id})
                    MERGE (s)-[r:MAKES_CLAIM]->(e)
                    SET r.claim_id = $claim_id,
                        r.claim_text = $claim_text,
                        r.claim_type = $claim_type,
                        r.confidence = $confidence
                    """,
                    source_id=str(claim.source_id),
                    entity_id=str(claim.entity_id),
                    claim_id=str(claim.id),
                    claim_text=claim.claim_text,
                    claim_type=claim.claim_type,
                    confidence=claim.confidence,
                )

    async def link_source_to_entity(
        self,
        source_id: uuid.UUID,
        entity_id: uuid.UUID,
        relationship_type: str = "MENTIONS",
    ) -> None:
        if relationship_type not in VALID_RELATIONSHIP_TYPES:
            raise GraphError(f"Invalid relationship type: {relationship_type}")
        async with self._session() as session:
            await session.run(
                f"""
                MATCH (s:Source {{id: $source_id}})
                MATCH (e:Entity {{id: $entity_id}})
                MERGE (s)-[r:{relationship_type}]->(e)
                """,
                source_id=str(source_id),
                entity_id=str(entity_id),
            )

    async def link_entities(
        self,
        entity_id_1: uuid.UUID,
        entity_id_2: uuid.UUID,
        relationship_type: str,
        properties: dict | None = None,
    ) -> None:
        if relationship_type not in VALID_RELATIONSHIP_TYPES:
            raise GraphError(f"Invalid relationship type: {relationship_type}")
        async with self._session() as session:
            params = {
                "id1": str(entity_id_1),
                "id2": str(entity_id_2),
            }
            if properties:
                params["props"] = properties
                await session.run(
                    f"""
                    MATCH (a:Entity {{id: $id1}})
                    MATCH (b:Entity {{id: $id2}})
                    MERGE (a)-[r:{relationship_type}]->(b)
                    SET r += $props
                    """,
                    **params,
                )
            else:
                await session.run(
                    f"""
                    MATCH (a:Entity {{id: $id1}})
                    MATCH (b:Entity {{id: $id2}})
                    MERGE (a)-[r:{relationship_type}]->(b)
                    """,
                    **params,
                )

    async def get_entity_graph(
        self, entity_id: uuid.UUID, depth: int = 2
    ) -> dict:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH (e:Entity {id: $id})
                CALL apoc.path.subgraphNodes(e, {
                    maxLevel: $depth,
                    relationshipFilter: '>'
                })
                YIELD node
                RETURN collect(DISTINCT node) AS nodes
                """,
                id=str(entity_id),
                depth=depth,
            )
            record = await result.single()
            if record is None:
                return {"nodes": [], "edges": [], "root_id": str(entity_id)}
            raw_nodes = record.get("nodes", [])
            nodes = [
                {
                    "id": n.get("id"),
                    "labels": list(n.labels),
                    "properties": dict(n),
                }
                for n in raw_nodes
                if n is not None
            ]
            node_ids = [n["id"] for n in nodes if n["id"]]
            edges_result = await session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.id IN $ids AND b.id IN $ids
                RETURN collect(DISTINCT {
                    source: a.id,
                    target: b.id,
                    type: type(r),
                    properties: properties(r)
                }) AS edges
                """,
                ids=node_ids,
            )
            edges_record = await edges_result.single()
            edges = edges_record.get("edges", []) if edges_record else []
            return {"nodes": nodes, "edges": edges, "root_id": str(entity_id)}

    async def get_project_graph(self, project_id: uuid.UUID) -> dict:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH (s:Source)
                WHERE s.project_id = $project_id
                OPTIONAL MATCH (s)-[r]-(e:Entity)
                WITH s, r, e
                LIMIT 2000
                WITH collect(DISTINCT s) AS source_nodes,
                     collect(DISTINCT e) AS entity_nodes,
                     collect(DISTINCT r) AS rels
                RETURN source_nodes, entity_nodes, rels
                """,
                project_id=str(project_id),
            )
            record = await result.single()
            if record is None:
                return {"nodes": [], "edges": [], "project_id": str(project_id)}
            source_nodes = record.get("source_nodes", []) or []
            entity_nodes = record.get("entity_nodes", []) or []
            rels = record.get("rels", []) or []
            nodes = []
            for n in source_nodes:
                if n is not None:
                    nodes.append({
                        "id": n.get("id"),
                        "labels": list(n.labels),
                        "properties": dict(n),
                    })
            for n in entity_nodes:
                if n is not None:
                    nodes.append({
                        "id": n.get("id"),
                        "labels": list(n.labels),
                        "properties": dict(n),
                    })
            edges = []
            for r in rels:
                if r is not None:
                    edges.append({
                        "source": r.start_node.get("id"),
                        "target": r.end_node.get("id"),
                        "type": r.type,
                        "properties": dict(r),
                    })
            return {"nodes": nodes, "edges": edges, "project_id": str(project_id)}

    async def delete_entity_node(self, entity_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH (e:Entity {id: $id})
                DETACH DELETE e
                RETURN count(e) AS deleted
                """,
                id=str(entity_id),
            )
            record = await result.single()
            return record.get("deleted", 0) > 0 if record else False

    async def delete_claim_relationship(self, claim_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH ()-[r:MAKES_CLAIM {claim_id: $claim_id}]-()
                DELETE r
                RETURN count(r) AS deleted
                """,
                claim_id=str(claim_id),
            )
            record = await result.single()
            return record.get("deleted", 0) > 0 if record else False

    async def clear_project_graph(self, project_id: uuid.UUID) -> None:
        async with self._session() as session:
            await session.run(
                """
                MATCH (n)
                WHERE n.project_id = $project_id
                DETACH DELETE n
                """,
                project_id=str(project_id),
            )

    async def query_entities_by_type(
        self, entity_type: str, limit: int = 50
    ) -> list[dict]:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH (e:Entity)
                WHERE e.entity_type = $entity_type
                RETURN e
                ORDER BY e.updated_at DESC
                LIMIT $limit
                """,
                entity_type=entity_type,
                limit=limit,
            )
            nodes = []
            async for record in result:
                n = record.get("e")
                if n is not None:
                    nodes.append({
                        "id": n.get("id"),
                        "labels": list(n.labels),
                        "properties": dict(n),
                    })
            return nodes

    async def find_paths(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        max_depth: int = 5,
    ) -> list[dict]:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH p = shortestPath(
                    (a)-[*1..$max_depth]-(b)
                )
                WHERE a.id = $source_id AND b.id = $target_id
                RETURN nodes(p) AS path_nodes, relationships(p) AS path_rels
                """,
                source_id=str(source_id),
                target_id=str(target_id),
                max_depth=max_depth,
            )
            paths = []
            async for record in result:
                path_nodes = record.get("path_nodes", []) or []
                path_rels = record.get("path_rels", []) or []
                nodes = [
                    {
                        "id": n.get("id"),
                        "labels": list(n.labels),
                        "properties": dict(n),
                    }
                    for n in path_nodes
                    if n is not None
                ]
                edges = [
                    {
                        "source": r.start_node.get("id"),
                        "target": r.end_node.get("id"),
                        "type": r.type,
                        "properties": dict(r),
                    }
                    for r in path_rels
                    if r is not None
                ]
                paths.append({"nodes": nodes, "edges": edges})
            return paths

    async def get_entity_count(self) -> int:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH (e:Entity)
                RETURN count(e) AS count
                """
            )
            record = await result.single()
            return record.get("count", 0) if record else 0

    async def get_relationship_count(self) -> int:
        async with self._session() as session:
            result = await session.run(
                """
                MATCH ()-[r]->()
                RETURN count(r) AS count
                """
            )
            record = await result.single()
            return record.get("count", 0) if record else 0
