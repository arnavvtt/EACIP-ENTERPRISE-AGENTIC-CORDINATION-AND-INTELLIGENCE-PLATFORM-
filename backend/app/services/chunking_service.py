"""
Chunking service.

Splits long text (policy documents) into overlapping chunks suitable
for embedding and retrieval.

Design:
- Fixed character window with overlap.
- Splits on natural boundaries (paragraph/sentence) when possible.
- Pure function, no I/O — testable in isolation.
- Chunk size and overlap come from settings (tunable).
"""

from dataclasses import dataclass
from typing import Optional

from app.config import settings


@dataclass
class TextChunk:
    """A single chunk with its position in the source document."""

    chunk_index: int
    text: str
    start_char: int
    end_char: int


class ChunkingService:
    """
    Split text into overlapping chunks.

    Usage:
        chunks = ChunkingService.chunk_text("long text ...")
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.overlap < 0 or self.overlap >= self.chunk_size:
            raise ValueError(
                "overlap must be >= 0 and < chunk_size"
            )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def chunk_text(self, text: str) -> list[TextChunk]:
        """
        Split text into chunks.

        Behavior:
        - Empty/whitespace-only text → []
        - Short text (<= chunk_size) → 1 chunk
        - Long text → sliding window with overlap, snapped to nearest
          sentence boundary if possible.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        if len(text) <= self.chunk_size:
            return [
                TextChunk(
                    chunk_index=0,
                    text=text,
                    start_char=0,
                    end_char=len(text),
                )
            ]

        chunks: list[TextChunk] = []
        start = 0
        idx = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # Snap to a sentence boundary if possible (within last 100 chars)
            if end < text_len:
                snapped = self._snap_to_boundary(text, start, end)
                if snapped is not None:
                    end = snapped

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_index=idx,
                        text=chunk_text,
                        start_char=start,
                        end_char=end,
                    )
                )
                idx += 1

            if end >= text_len:
                break

            next_start = end - self.overlap
            if next_start <= start:
                next_start = start + 1
            start = next_start

        return chunks

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _snap_to_boundary(
        text: str, start: int, end: int
    ) -> Optional[int]:
        """
        Try to end the chunk at a sentence/paragraph boundary.

        Look back up to 100 chars for '.', '!', '?', or '\\n'.
        Returns None if no good boundary found.
        """
        lookback = min(100, end - start)
        window = text[end - lookback : end]

        for marker in ("\n\n", "\n", ". ", "! ", "? "):
            pos = window.rfind(marker)
            if pos != -1:
                return end - lookback + pos + len(marker)
        return None