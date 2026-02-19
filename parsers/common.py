import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

@dataclass
class Segment:
    """A parser extraction unit.

    One Segment represents a contiguous piece of content pulled from a source
    document (e.g., a PDF page's text, a DOCX paragraph, or a table). Segments
    are later transformed into delivery-sized chunks for downstream use.
vb
    Fields:
    - doc_id: Logical id for the document (stable across all chunks).
    - text: Raw extracted text (may be long; will be chunked later).
    - page: Page number for PDFs, if available.
    - section: Section/heading path for DOCX, if available.
    - kind: Content kind (e.g., "text", "table").
    - meta: Arbitrary parser-provided metadata for this segment.
    """

    doc_id: Optional[str]
    text: str
    page: Optional[int] = None
    section: Optional[str] = None
    kind: str = "text"
    meta: Optional[Dict] = None

def clean_text(s: str) -> str:
    """Normalize small nuisances and trim whitespace.

    - Removes common zero-width marks (e.g., RTL/LTR marks) that leak from
      some extractors/encodings.
    - Returns a safe empty string for None inputs.
    """
    if s is None:
        return ""
    # Drop LRM/RLM and similar directional markers.
    s = s.replace("\u200f", "").replace("\u200e", "")
    return s.strip()

def normalize_newlines(text: str) -> str:
    """Collapse mid-paragraph line breaks to spaces, keep paragraph breaks.

    - Converts CRLF to LF.
    - Replaces single newlines with a space.
    - Collapses 3+ newlines down to a double newline.
    - Trims extra spaces around newlines.
    """
    if not text:
        return ""
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace any single (isolated) newline with a space
    t = re.sub(r"(?<!\n)\n(?!\n)", " ", t)
    # Collapse runs of 3+ newlines to exactly 2 (paragraph break)
    t = re.sub(r"\n{3,}", "\n\n", t)
    # Remove extra spaces around newlines
    t = re.sub(r"[ \t]*\n[ \t]*", "\n", t)
    return t.strip()

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 0) -> List[str]:
    """Split text into ~sentence/paragraph-aware chunks capped at max_chars.

    Heuristic:
    - First split on sentence boundaries (., !, ?) and paragraph breaks.
    - Greedily pack sentences into a buffer until adding one would exceed
      max_chars; then flush the buffer as a chunk.
    - If a single sentence is longer than max_chars, fall back to fixed-size
      windowing for that sentence so no chunk exceeds the limit.
    """
    text = clean_text(text)
    if not text:
        return []

    # Split on sentence breaks (lookbehind) or on 2+ newlines (paragraphs).
    pieces = re.split(r'(?<=[.!?])\s+|\n{2,}', text)

    chunks: List[str] = []
    buf: List[str] = []  # current chunk's sentences
    size = 0             # current chunk's character count

    for p in (s.strip() for s in pieces):
        if not p:
            continue

        # Very long sentence: flush current buffer and slice it into windows.
        if len(p) > max_chars:
            if buf:
                chunks.append(" ".join(buf))
                buf, size = [], 0
            for i in range(0, len(p), max_chars):
                chunks.append(p[i:i + max_chars])
            continue

        # +1 accounts for the space between sentences when joining.
        add = len(p) + (1 if buf else 0)
        if size + add <= max_chars:
            buf.append(p)
            size += add
        else:
            chunks.append(" ".join(buf))
            buf, size = [p], len(p)

    if buf:
        chunks.append(" ".join(buf))

    # Apply simple character-based overlap between consecutive chunks by
    # prefixing each chunk (except the first) with the trailing `overlap`
    # characters of the previous chunk.
    if overlap and chunks:
        overlapped: List[str] = []
        prev_tail = ""
        for idx, ch in enumerate(chunks):
            if idx == 0:
                overlapped.append(ch)
            else:
                tail = prev_tail[-overlap:] if overlap > 0 else ""
                if tail:
                    overlapped.append((tail + " " + ch).strip())
                else:
                    overlapped.append(ch)
            prev_tail = overlapped[-1]
        return overlapped

    return chunks

def segments_to_chunks(
    segments: List[Segment],
    max_chars: int = 1200,
    overlap: int = 0,
) -> Dict[str, List[Dict[str, Any]]]:
    """Convert parser segments into the target chunk schema.

    - Carries parser context (page/section/kind/meta) into a single metadata
      dict per chunk.
    - Text segments are further split with `chunk_text`; non-text (e.g., table)
      segments are emitted as a single chunk to preserve structure.
    - Chunk ids are stable within a document: f"{doc_id}:{index:04d}".
    """
    out: List[Dict[str, Any]] = []
    for seg in segments:
        # Base metadata copied across all chunks derived from this segment.
        base: Dict[str, Any] = {}
        if seg.page is not None:
            base["page"] = seg.page
        if seg.section:
            base["section"] = seg.section
        if seg.kind:
            base["kind"] = seg.kind
        if seg.meta:
            base.update(seg.meta)

        # Split long text; keep non-text as a single piece (e.g., tables as MD).
        parts = chunk_text(seg.text, max_chars, overlap) if seg.kind == "text" else [seg.text]

        for i, part in enumerate(parts):
            out.append(
                {
                    "id": f"{seg.doc_id}:{i:04d}",
                    "doc_id": seg.doc_id,
                    "text": part,
                    "metadata": {**base, "chunk_index": i},
                }
            )

    return {"chunks": out}
