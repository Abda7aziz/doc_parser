import pathlib
from typing import List
import fitz  # PyMuPDF
from .common import Segment, clean_text

def parse_pdf(path: str, doc_id: str, ocr: bool = False) -> List[Segment]:
    segs: List[Segment] = []
    p = pathlib.Path(path)
    with fitz.open(p) as doc:
        for i, page in enumerate(doc, start=1):
            txt = page.get_text("text")
            if txt and txt.strip():
                segs.append(Segment(doc_id, clean_text(txt), page=i, kind="text", meta={"source": str(p)}))
    if not segs and ocr:
        from PIL import Image
        import pytesseract
        with fitz.open(p) as doc:
            for i, page in enumerate(doc, start=1):
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                txt = pytesseract.image_to_string(img, lang="ara+eng")
                if txt.strip():
                    segs.append(Segment(doc_id, clean_text(txt), page=i, kind="text", meta={"source": str(p), "ocr": True}))
    return segs
