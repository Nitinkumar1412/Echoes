# -*- coding: utf-8 -*-
"""
NetworkX Graph service for in-memory multi-hop traversal and graph retrieval expansion.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

import networkx as nx
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("echoes.graph.networkx")


class NetworkXGraphService:
    """Manages workspace graph representation in NetworkX."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def build_workspace_digraph(self, workspace_id: str) -> nx.DiGraph:
        """Construct a NetworkX directed graph from MongoDB entities and relationships."""
        graph = nx.DiGraph(workspace_id=workspace_id)

        # 1. Fetch entities (nodes)
        cursor = self.db["entities"].find(
            {"workspace_id": workspace_id},
            {"entity_id": 1, "identity": 1, "stats": 1, "provenance": 1},
        )
        entities = await cursor.to_list(length=3000)

        for ent in entities:
            eid = ent["entity_id"]
            ident = ent.get("identity", {})
            name = ident.get("canonical_name", "Unknown")
            etype = ident.get("entity_type", "OTHER")
            mentions = ent.get("stats", {}).get("mention_count", 1)

            # Collect evidence chunk IDs
            chunk_ids = [p["chunk_id"] for p in ent.get("provenance", []) if "chunk_id" in p]

            graph.add_node(
                eid,
                name=name,
                entity_type=etype,
                mentions=mentions,
                chunk_ids=chunk_ids,
            )

        # 2. Fetch relationships (edges)
        rel_cursor = self.db["relationships"].find(
            {"workspace_id": workspace_id},
            {"relationship_id": 1, "from_entity_id": 1, "to_entity_id": 1, "relationship_type": 1, "confidence": 1, "evidence": 1},
        )
        relationships = await rel_cursor.to_list(length=5000)

        for rel in relationships:
            u = rel["from_entity_id"]
            v = rel["to_entity_id"]
            rel_type = rel.get("relationship_type", "RELATED_TO")
            conf = rel.get("confidence", 1.0)
            evidence = rel.get("evidence", [])

            if graph.has_node(u) and graph.has_node(v):
                graph.add_edge(
                    u,
                    v,
                    relationship_id=rel["relationship_id"],
                    relationship_type=rel_type,
                    confidence=conf,
                    evidence=evidence,
                    evidence_count=len(evidence),
                )

        logger.info(
            "[NETWORKX] Graph built for workspace '%s': %d nodes, %d edges",
            workspace_id,
            graph.number_of_nodes(),
            graph.number_of_edges(),
        )
        return graph

    async def get_graph_visualization_data(self, workspace_id: str) -> Dict[str, Any]:
        """Format graph data for frontend visualization libraries."""
        graph = await self.build_workspace_digraph(workspace_id)

        nodes = []
        for n, data in graph.nodes(data=True):
            nodes.append(
                {
                    "id": n,
                    "label": data.get("name", n),
                    "type": data.get("entity_type", "CONCEPT"),
                    "mentions": data.get("mentions", 1),
                }
            )

        edges = []
        for u, v, data in graph.edges(data=True):
            edges.append(
                {
                    "id": data.get("relationship_id", f"{u}_{v}"),
                    "from": u,
                    "to": v,
                    "label": data.get("relationship_type", "CONNECTED_TO"),
                    "confidence": data.get("confidence", 1.0),
                    "evidence_count": data.get("evidence_count", 1),
                }
            )

        return {"workspace_id": workspace_id, "nodes": nodes, "edges": edges}

    async def get_ego_subgraph(self, workspace_id: str, entity_id: str, radius: int = 1) -> Dict[str, Any]:
        """Extract ego subgraph around an entity."""
        graph = await self.build_workspace_digraph(workspace_id)
        if not graph.has_node(entity_id):
            return {"workspace_id": workspace_id, "nodes": [], "edges": []}

        # Ego graph converts to undirected for neighborhood lookup
        undirected = graph.to_undirected()
        subgraph = nx.ego_graph(undirected, entity_id, radius=radius)

        nodes = [
            {
                "id": n,
                "label": graph.nodes[n].get("name", n),
                "type": graph.nodes[n].get("entity_type", "CONCEPT"),
                "mentions": graph.nodes[n].get("mentions", 1),
            }
            for n in subgraph.nodes()
        ]
        edges = []
        for u, v in subgraph.edges():
            if graph.has_edge(u, v):
                data = graph.edges[u, v]
                edges.append({"from": u, "to": v, "label": data.get("relationship_type")})
            elif graph.has_edge(v, u):
                data = graph.edges[v, u]
                edges.append({"from": v, "to": u, "label": data.get("relationship_type")})

        return {"workspace_id": workspace_id, "nodes": nodes, "edges": edges}

    async def expand_entities_for_query(
        self,
        workspace_id: str,
        entity_names: List[str],
    ) -> Dict[str, Any]:
        """
        Find 1-hop connected entities and their source chunk IDs for knowledge graph expansion.
        """
        graph = await self.build_workspace_digraph(workspace_id)
        if graph.number_of_nodes() == 0:
            return {"expanded_entity_ids": [], "expanded_chunk_ids": []}

        name_to_node = {data.get("name", "").lower(): n for n, data in graph.nodes(data=True)}
        seed_nodes: Set[str] = set()

        for q_name in entity_names:
            matched = name_to_node.get(q_name.lower())
            if matched:
                seed_nodes.add(matched)

        expanded_entity_ids: Set[str] = set(seed_nodes)
        expanded_chunk_ids: Set[str] = set()

        # Collect 1-hop neighbors and their chunk evidence
        for seed in seed_nodes:
            # Outgoing neighbors
            for neighbor in graph.successors(seed):
                expanded_entity_ids.add(neighbor)
                edge_data = graph.edges[seed, neighbor]
                for ev in edge_data.get("evidence", []):
                    if "chunk_id" in ev:
                        expanded_chunk_ids.add(ev["chunk_id"])

            # Incoming neighbors
            for neighbor in graph.predecessors(seed):
                expanded_entity_ids.add(neighbor)
                edge_data = graph.edges[neighbor, seed]
                for ev in edge_data.get("evidence", []):
                    if "chunk_id" in ev:
                        expanded_chunk_ids.add(ev["chunk_id"])

            # Chunks from the seed node itself
            for cid in graph.nodes[seed].get("chunk_ids", []):
                expanded_chunk_ids.add(cid)

        return {
            "expanded_entity_ids": list(expanded_entity_ids),
            "expanded_chunk_ids": list(expanded_chunk_ids),
        }
