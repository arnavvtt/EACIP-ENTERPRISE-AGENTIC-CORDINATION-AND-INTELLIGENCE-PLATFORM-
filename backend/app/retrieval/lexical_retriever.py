"""
Lexical retriever — PostgreSQL full-text search.

Uses PostgreSQL's native full-text search (tsvector + ts_rank_cd).
This is NOT BM25 — it is PostgreSQL's built-in ranking.

Query type: websearch_to_tsquery (handles natural-language queries
gracefully — supports phrases, operators, and plain words).

Design:
- Read-only.
- Returns LexicalHit list sorted by rank.
- Empty/whitespace query → empty result.
- No business logic — pure retrieval.

Notes:
- 'english' text search configuration is used by default. If
  multilingual policy documents are added later, consider
  'simple' or a language-aware config.
"""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.types import LexicalHit


class LexicalRetriever:
    """PostgreSQL full-text retriever over policy_chunks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
    ) -> list[LexicalHit]:
        """
        Retrieve top-K chunks ranked by PostgreSQL ts_rank_cd.

        Args:
            query: Natural-language query string.
            limit: Max number of hits.
        """
        if not query or not query.strip():
            return []

        stmt = text(
            """
            SELECT
                id,
                source_record_id,
                chunk_index,
                chunk_text,
                ts_rank_cd(
                    to_tsvector('english', chunk_text),
                    websearch_to_tsquery('english', :q)
                ) AS rank
            FROM policy_chunks
            WHERE
                to_tsvector('english', chunk_text)
                @@ websearch_to_tsquery('english', :q)
            ORDER BY rank DESC
            LIMIT :lim
            """
        )

        result = await self.session.execute(
            stmt, {"q": query.strip(), "lim": limit}
        )
        rows = result.fetchall()

        hits: list[LexicalHit] = []
        for row in rows:
            hits.append(
                LexicalHit(
                    chunk_id=row.id,
                    source_record_id=row.source_record_id,
                    chunk_index=row.chunk_index,
                    chunk_text=row.chunk_text,
                    rank=float(row.rank),
                )
            )
        return hits