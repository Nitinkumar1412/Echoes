# -*- coding: utf-8 -*-
"""
Echoes Search — Database Initialization Script
Creates all collections and indexes on MongoDB Atlas.

Usage:
    .\\.venv\\Scripts\\python.exe scripts/init_db.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add backend to path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
from pymongo.errors import OperationFailure

from backend.app.core.config import settings
from backend.app.services.database import connect_sync, disconnect_sync

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("init_db")

# ─────────────────────────────────────────────────────────────────────────────
# INDEX SPECIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────
COLLECTION_INDEXES: dict[str, list[IndexModel]] = {
    "users": [
        IndexModel([("user_id", ASCENDING)], unique=True, name="idx_users_user_id"),
        IndexModel([("email", ASCENDING)], unique=True, name="idx_users_email"),
    ],
    "workspaces": [
        IndexModel([("workspace_id", ASCENDING)], unique=True, name="idx_workspaces_id"),
        IndexModel([("owner_id", ASCENDING)], name="idx_workspaces_owner_id"),
        IndexModel([("members.user_id", ASCENDING)], name="idx_workspaces_member_user_id"),
        IndexModel([("is_deleted", ASCENDING)], name="idx_workspaces_is_deleted"),
    ],
    "documents": [
        IndexModel([("document_id", ASCENDING)], unique=True, name="idx_docs_document_id"),
        IndexModel([("workspace_id", ASCENDING), ("processing.status", ASCENDING)], name="idx_docs_workspace_status"),
        IndexModel([("workspace_id", ASCENDING), ("file.sha256_hash", ASCENDING)], unique=True, name="idx_docs_workspace_sha256"),
        IndexModel([("workspace_id", ASCENDING), ("is_deleted", ASCENDING)], name="idx_docs_workspace_deleted"),
        IndexModel([("workspace_id", ASCENDING), ("file.file_type", ASCENDING)], name="idx_docs_workspace_file_type"),
        IndexModel([("file.sha256_hash", ASCENDING)], name="idx_docs_file_sha256"),
    ],
    "chunks": [
        IndexModel([("chunk_id", ASCENDING)], unique=True, name="idx_chunks_chunk_id"),
        IndexModel([("document_id", ASCENDING), ("location.chunk_index", ASCENDING)], name="idx_chunks_doc_chunk_idx"),
        IndexModel([("workspace_id", ASCENDING), ("vector.is_indexed", ASCENDING)], name="idx_chunks_workspace_indexed"),
        IndexModel([("workspace_id", ASCENDING)], name="idx_chunks_workspace_id"),
        IndexModel([("content.text", TEXT)], name="idx_chunks_content_text"),
    ],
    "entities": [
        IndexModel([("entity_id", ASCENDING)], unique=True, name="idx_entities_entity_id"),
        IndexModel([("workspace_id", ASCENDING), ("identity.entity_type", ASCENDING)], name="idx_entities_workspace_type"),
        IndexModel([("workspace_id", ASCENDING), ("identity.canonical_name", ASCENDING)], name="idx_entities_workspace_name"),
        IndexModel([("identity.canonical_name", TEXT), ("identity.aliases", TEXT)], name="idx_entities_text_search"),
    ],
    "events": [
        IndexModel([("event_id", ASCENDING)], unique=True, name="idx_events_event_id"),
        IndexModel([("workspace_id", ASCENDING), ("temporal.normalized_date", ASCENDING)], name="idx_events_workspace_date"),
        IndexModel([("workspace_id", ASCENDING), ("event_type", ASCENDING)], name="idx_events_workspace_event_type"),
        IndexModel([("participants", ASCENDING)], name="idx_events_participants"),
        IndexModel([("related_documents", ASCENDING)], name="idx_events_related_docs"),
    ],
    "relationships": [
        IndexModel([("relationship_id", ASCENDING)], unique=True, name="idx_rel_relationship_id"),
        IndexModel([("workspace_id", ASCENDING), ("from_entity_id", ASCENDING)], name="idx_rel_from_entity"),
        IndexModel([("workspace_id", ASCENDING), ("to_entity_id", ASCENDING)], name="idx_rel_to_entity"),
        IndexModel(
            [
                ("workspace_id", ASCENDING),
                ("from_entity_id", ASCENDING),
                ("to_entity_id", ASCENDING),
                ("relationship_type", ASCENDING),
            ],
            unique=True,
            name="idx_rel_unique_edge",
        ),
        IndexModel([("workspace_id", ASCENDING), ("confidence", DESCENDING)], name="idx_rel_confidence"),
    ],
    "queries": [
        IndexModel([("query_id", ASCENDING)], unique=True, name="idx_queries_query_id"),
        IndexModel([("workspace_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)], name="idx_queries_user_history"),
        IndexModel([("workspace_id", ASCENDING), ("created_at", DESCENDING)], name="idx_queries_workspace_history"),
        IndexModel([("status", ASCENDING)], name="idx_queries_status"),
    ],
}


def initialize_database() -> None:
    """Connect to Atlas and build all collections and indexes."""
    uri = settings.MONGODB_URI
    db_name = settings.MONGODB_DATABASE

    print("=" * 65)
    print(f"  Echoes Database Initializer")
    print(f"  Database : {db_name}")
    print(f"  Target   : {uri[:42]}...")
    print("=" * 65)

    if not uri or "YOUR_USERNAME" in uri:
        print("[ERROR] Please provide a valid MONGODB_URI in .env")
        sys.exit(1)

    try:
        db = connect_sync(uri, db_name)
        existing_collections = set(db.list_collection_names())
        print(f"[CONNECTED] Existing collections: {sorted(list(existing_collections))}\n")

        total_indexes_created = 0

        for coll_name, index_models in COLLECTION_INDEXES.items():
            print(f"--> Processing collection: [{coll_name}]")
            col = db[coll_name]

            # Ensure collection exists by writing a probe if needed, or create_collection
            if coll_name not in existing_collections:
                try:
                    db.create_collection(coll_name)
                    print(f"    [CREATED] Collection '{coll_name}' created.")
                except Exception:
                    pass  # might already exist via another operation

            # Create each index
            for model in index_models:
                idx_name = model.document.get("name", "unnamed")
                try:
                    col.create_indexes([model])
                    print(f"    [OK] Index '{idx_name}' verified/created.")
                    total_indexes_created += 1
                except OperationFailure as err:
                    # Index with different options already exists or similar
                    print(f"    [WARN] Index '{idx_name}': {err}")

            # Report index count
            current_indexes = list(col.list_indexes())
            print(f"    Total indexes in '{coll_name}': {len(current_indexes)}\n")

        disconnect_sync()
        print("=" * 65)
        print(f"[SUCCESS] Database initialization completed! {total_indexes_created} indexes verified/created.")
        print("=" * 65)

    except Exception as exc:
        print(f"[FATAL ERROR] Failed to initialize database: {exc}")
        disconnect_sync()
        sys.exit(1)


if __name__ == "__main__":
    initialize_database()
