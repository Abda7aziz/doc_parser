import pathlib
from typing import List
from collections import Counter
import fitz  # PyMuPDF
from .common import Segment, clean_text, normalize_newlines

def parse_pdf(path: str, doc_id: str, ocr: bool = False) -> List[Segment]:
    """Extract text from a PDF, with optional per-page OCR fallback.

    - Uses PyMuPDF text extraction first.
    - If a page yields no text and ocr=True, renders that page and OCRs it.
    - Adds source filename in metadata and marks OCR-backed pages.
    """
    segs: List[Segment] = []
    p = pathlib.Path(path)
    source_name = p.name

    with fitz.open(p) as doc:
        # Pass 1: collect candidate header/footer lines from the first/last few lines of each page
        hf_counter: Counter[str] = Counter()
        for page in doc:
            raw = page.get_text("text") or ""
            lines = [clean_text(l) for l in raw.splitlines() if clean_text(l)]
            if not lines:
                continue
            head = lines[:3]
            tail = lines[-3:]
            hf_counter.update(head + tail)

        # Consider as header/footer any line seen on 2+ pages
        repeated_hf = {line for line, cnt in hf_counter.items() if cnt >= 2}

        # Pass 2: extract text with header/footer lines removed; OCR fallback per page
        for i, page in enumerate(doc, start=1):
            raw = page.get_text("text") or ""
            if raw.strip():
                # Remove repeated header/footer lines
                lines = [clean_text(l) for l in raw.splitlines()]
                filtered = "\n".join(l for l in lines if l and l not in repeated_hf)
                filtered = normalize_newlines(filtered)
                if filtered.strip():
                    segs.append(
                        Segment(
                            doc_id,
                            clean_text(filtered),
                            page=i,
                            kind="text",
                            meta={"source": source_name},
                        )
                    )
                    continue
            if ocr:
                # Per-page OCR fallback only when needed
                try:
                    from PIL import Image
                    import pytesseract
                    pix = page.get_pixmap(dpi=300, alpha=False)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img)
                    ocr_text = normalize_newlines(ocr_text)
                    if ocr_text and ocr_text.strip():
                        segs.append(
                            Segment(
                                doc_id,
                                clean_text(ocr_text),
                                page=i,
                                kind="text",
                                meta={"source": source_name, "ocr": True},
                            )
                        )
                except Exception:
                    # If OCR pipeline isn't available, skip gracefully
                    pass

    return segs
