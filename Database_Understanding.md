# Echoes Search — Database & Architecture Guide (Milestone 1)

Yeh document Echoes Search ke **Milestone 1: Foundation & Database Layer** ka complete reference aur explanation hai.

---

## 1. High-Level Tech Stack (Kaunsi cheez kiske liye hai)

| Component | Technology | Kaam (Role) |
|---|---|---|
| **Primary Database** | **MongoDB Atlas** (`echoes_db`) | System ka source of truth. Users, documents metadata, chunks text, entities, events, relationships aur query history store karta hai. |
| **Vector Database** | **ChromaDB** (`storage/vectors`) | High-dimensional text embeddings store karta hai semantic search (meaning-based retrieval) ke liye. |
| **Graph Engine** | **NetworkX** | MongoDB ke relationships data ko memory me load karke Multi-hop graph traversal aur entity connection dhoondhta hai. |
| **LLM & Reasoning** | **Google Gemini 2.5 Flash** | Retrieved chunks + timeline + graph facts ko synthesize karke accurate, evidence-backed answer banata hai. |
| **Backend API** | **FastAPI + Motor (async)** | High-performance asynchronous API server jo requests handle karta hai aur startup/shutdown manage karta hai. |
| **Frontend UI** | **React + Vite** | Clean, fast aur interactive UI jisme user timeline, graph aur citations dekh sake. |

---

## 2. Milestone 1 me Kya-Kya Hua Hai? (What Was Built)

Milestone 1 me application ka base foundation aur database architecture completely tayyar aur verify kiya gaya hai:

### A. MongoDB Atlas Connection & Windows SSL Fix
- **Async Motor Client** (`backend/app/services/database.py`): FastAPI ke liye non-blocking client banaya taaki high traffic me server freeze na ho.
- **Sync PyMongo Client**: CLI scripts aur test runs ke liye direct sync client.
- **Windows Python 3.13 SSL Handshake Fix**: Windows par OpenSSL 3.0 ke sath Atlas connection handshake issue ko solve kiya (`tlsAllowInvalidCertificates=True` + `certifi`).
- Live Atlas cluster (`echoescluster`) ke `echoes_db` se successfully connect ho chuka hai.

### B. Complete Database Architecture (All 8 Collections & 35 Indexes)
`scripts/init_db.py` run karke Atlas par total **8 collections** aur **35 indexes** create aur verify kiye gaye:

1. **`users`**: User identity, login emails, preferences.
   - *Indexes*: Unique `user_id`, Unique `email`.
2. **`workspaces`**: Multi-tenancy container. Har user ke documents aur knowledge graph alag workspace me isolated rehte hain.
   - *Indexes*: Unique `workspace_id`, `owner_id`, `members.user_id`, `is_deleted`.
3. **`documents`**: Upload ki hui har file ka record (PDF, DOCX, TXT, etc.).
   - *Indexes*: Unique `document_id`, Unique `(workspace_id, sha256_hash)` (taaki duplicate file upload na ho), status index.
4. **`chunks`**: Document ko chote-chote tukdon me divide karke text store karta hai.
   - *Indexes*: Unique `chunk_id` (`{document_id}__chunk_{index:04d}`), `workspace_id`, Full-text search index (`content.text`).
5. **`entities`**: Documents se nikale gaye People, Organisations, Projects, Concepts.
   - *Indexes*: Unique `entity_id`, `canonical_name`, Text search on aliases.
6. **`events`**: Time-bound occurrences ("Kickoff meeting", "Signed contract") with normalized dates.
   - *Indexes*: Unique `event_id`, chronological index `(workspace_id, temporal.normalized_date)`.
7. **`relationships`**: Entities aur events ke beech ke connections (Graph edges, e.g., "Rahul MANAGED Project X") with excerpt evidence.
   - *Indexes*: Unique `relationship_id`, Unique compound `(workspace_id, from_entity_id, to_entity_id, relationship_type)`.
8. **`queries`**: Har user question ka immutable audit log (retrieval scores, answer, citations, timing).
   - *Indexes*: Unique `query_id`, `(workspace_id, user_id, created_at)`.

### C. 8 Pydantic Domain Models
Saare models `backend/app/models/` me strongly-typed aur production-grade rule sets ke sath banaye gaye:
- `user.py`, `workspace.py`, `document.py`, `chunk.py`, `entity.py`, `event.py`, `relationship.py`, `query.py`.
- Har model me automatic UUID creation, strict validation (jaise email format, confidence range 0.0-1.0), aur timezone-aware UTC timestamps hain.

### D. FastAPI Application & Healthcheck
- `backend/app/main.py`: Lifespan context manager jo app start hote hi MongoDB Atlas se connect karta hai aur app band hone par cleanly close karta hai.
- `backend/app/api/routes/health.py`:
  - `GET /health`: Database ko live ping karta hai aur 200 OK deta hai agar DB operational hai.
  - `GET /`: API version aur root status deta hai.

### E. 100% Passing Automated Tests
`pytest tests/ -v` run karne par **15 ke 15 tests pass** huye:
- Config tests (settings, paths, CORS)
- Models tests (8 models ka data validation)
- Database tests (Atlas sync/async insert, read, delete, ping)
- Health API tests (FastAPI lifespan ke sath live ping)

---

## 3. Isse Aage Kya-Kya Hoga? (What This Unlocks)

Yeh foundation banne ke baad ab application me aage ki cheezein kaise kaam karengi:

### 1. No Data Corruption / Duplicate Files (SHA-256 Hashing)
- Jab user koi file upload karega, uska SHA-256 hash check hoga. Agar wahi file pehle se uploaded hai, toh system duplicate upload reject karega ya link karega bina double processing ke.

### 2. 100% Evidence Grounding (No Hallucinations)
- Chunki har `chunk` ka deterministic ID (`doc_id__chunk_0001`) hai, aur har entity/relationship/answer me `chunk_id` + `document_name` link rehta hai, system jo bhi answer dega usme user ko exact paragraph aur document dikhega jahan se wo baat aayi hai.

### 3. Chronological Timelines ("Kab kya hua tha?")
- `events` collection me har event ki `normalized_date` aur raw text expression dono hain. Jab user puchega *"What happened in Q2 2024?"*, system date index se turant sorted timeline nikal lega.

### 4. Knowledge Graph Traversal (Multi-hop Reasoning)
- `relationships` collection me graph edges hone se hum NetworkX me graph build kar sakte hain. Example: *"Who worked with Nitin on the Healthcare app?"* -> Pehle Nitin ka entity niklega, fir relationships se Healthcare app, fir uske collaborators connect honge.

### 5. Fast Hybrid Retrieval (BM25 + Semantic + Reranking)
- `chunks` me full-text index hone se keyword search (BM25) fast hoga.
- ChromaDB me embeddings hone se concept-based semantic search fast hoga.
- Dono ke results combine hoke rerank honge, jisse best accuracy milegi.

---

## 4. Next Step: Milestone 2 (Document Ingestion Pipeline)
Ab hum directly **Milestone 2** shuru kar sakte hain:
1. File parsers: PDF, DOCX, TXT files se text aur metadata extract karna.
2. Chunking engine: Document ko 512-token chunks me overlap ke sath split karna.
3. Upload API: Frontend se file receive karke storage me save karna aur database me register karna.
