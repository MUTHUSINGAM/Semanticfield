import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import lancedb
import pyarrow as pa

from config import get_settings
from services.embeddings import chunk_text, cosine_similarity, embed_text, get_embedding, keyword_overlap_score


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        settings.lancedb_abs_path.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(settings.lancedb_abs_path))
        self.table_name = settings.lancedb_table_name
        self._table = None

    def _get_table(self):
        if self._table is not None:
            return self._table
        if self.table_name in self.db.table_names():
            self._table = self.db.open_table(self.table_name)
        return self._table

    async def ingest_documents(self, documents: list[dict[str, Any]]) -> int:
        settings = get_settings()
        rows: list[dict[str, Any]] = []

        for doc in documents:
            chunks = chunk_text(doc["content"], settings.chunk_size, settings.chunk_overlap)
            for idx, chunk in enumerate(chunks):
                embedding = await get_embedding(chunk)
                rows.append(
                    {
                        "id": f"{doc['source']}_{doc['title']}_{idx}".replace(" ", "_"),
                        "source": doc["source"],
                        "title": doc["title"],
                        "content": chunk,
                        "classification": doc.get("classification", "confidential"),
                        "resource_uri": doc.get("resource_uri", ""),
                        "connection_type": doc.get("connection_type", ""),
                        "vector": embedding,
                    }
                )

        if not rows:
            return 0

        dim = len(rows[0]["vector"])
        schema = pa.schema(
            [
                ("id", pa.string()),
                ("source", pa.string()),
                ("title", pa.string()),
                ("content", pa.string()),
                ("classification", pa.string()),
                ("resource_uri", pa.string()),
                ("connection_type", pa.string()),
                ("vector", pa.list_(pa.float32(), dim)),
            ]
        )

        if self.table_name in self.db.table_names():
            self.db.drop_table(self.table_name)

        self._table = self.db.create_table(self.table_name, data=rows, schema=schema)
        return len(rows)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        keyword_results = self._keyword_search(query, top_k * 2)
        table = self._get_table()
        if table is None:
            return keyword_results[:top_k]

        query_vector = await get_embedding(query)
        try:
            results = table.search(query_vector).limit(top_k * 2).to_list()
        except Exception:
            return keyword_results[:top_k]

        enriched: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for row in results:
            row_id = f"{row['source']}:{row['title']}"
            seen_ids.add(row_id)
            vector = row.get("vector") or embed_text(row["content"])
            embedding_sim = cosine_similarity(query_vector, vector)
            keyword_sim = keyword_overlap_score(query, row["content"])
            similarity = round(max(embedding_sim, keyword_sim * 0.95), 4)
            enriched.append(
                {
                    "source": row["source"],
                    "title": row["title"],
                    "content": row["content"],
                    "similarity": similarity,
                    "classification": row.get("classification", "confidential"),
                    "resource_uri": row.get("resource_uri") or "",
                    "connection_type": row.get("connection_type") or "",
                }
            )

        for item in keyword_results:
            row_id = f"{item['source']}:{item['title']}"
            if row_id not in seen_ids:
                enriched.append(item)

        enriched.sort(key=lambda x: x["similarity"], reverse=True)
        return enriched[:top_k]

    def _keyword_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        from services.embeddings import keyword_overlap_score

        documents = load_mock_enterprise_documents()
        scored: list[dict[str, Any]] = []
        for doc in documents:
            score = keyword_overlap_score(query, doc["content"])
            title_boost = keyword_overlap_score(query, doc["title"]) * 0.5
            combined = min(1.0, score + title_boost)
            if combined > 0.04:
                scored.append(
                    {
                        "source": doc["source"],
                        "title": doc["title"],
                        "content": doc["content"][:500],
                        "similarity": round(combined, 4),
                        "classification": doc.get("classification", "confidential"),
                    }
                )
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]


def load_mock_enterprise_documents() -> list[dict[str, Any]]:
    settings = get_settings()
    data_path = settings.enterprise_data_abs_path
    documents: list[dict[str, Any]] = []

    if not data_path.exists():
        return documents

    for file_path in sorted(data_path.rglob("*")):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix not in {".json", ".txt", ".md", ".csv"}:
            continue

        source_type = file_path.parent.name.replace("_", " ").title()
        title = file_path.stem.replace("_", " ").title()

        try:
            if suffix == ".json":
                payload = json.loads(file_path.read_text(encoding="utf-8"))
                if isinstance(payload, list):
                    for item in payload:
                        documents.append(
                            {
                                "source": item.get("source", source_type),
                                "title": item.get("title", title),
                                "content": item.get("content", json.dumps(item)),
                                "classification": item.get("classification", "confidential"),
                            }
                        )
                else:
                    documents.append(
                        {
                            "source": payload.get("source", source_type),
                            "title": payload.get("title", title),
                            "content": payload.get("content", json.dumps(payload)),
                            "classification": payload.get("classification", "confidential"),
                        }
                    )
            else:
                content = file_path.read_text(encoding="utf-8")
                classification = "confidential"
                if "salary" in file_path.name.lower() or "budget" in file_path.name.lower():
                    classification = "highly_confidential"
                documents.append(
                    {
                        "source": source_type,
                        "title": title,
                        "content": content,
                        "classification": classification,
                    }
                )
        except Exception:
            continue

    return documents


vector_store = VectorStore()
