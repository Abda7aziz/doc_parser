import pathlib, uuid
from parsers.pdf import parse_pdf
from parsers.docx import parse_docx
from parsers.common import Segment

def read_file(path: str, ocr: bool = False):
    ext = pathlib.Path(path).suffix.lower()
    doc_id = f"{uuid.uuid4().hex[:8]}:{pathlib.Path(path).stem}"
    if ext == ".pdf":
        return parse_pdf(path, doc_id, ocr=ocr)
    elif ext == ".docx":
        return parse_docx(path, doc_id)
    elif ext in {".txt", ".md"}:
        text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
        return [Segment(doc_id, text)]
    elif ext == ".csv":
        text = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
        return [Segment(doc_id, text, kind="table", meta={"format": "csv"})]
    else:
        raise ValueError(f"Unsupported file type: {ext}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python reader.py <file-path>")
        sys.exit(1)
    path = sys.argv[1]
    segments = read_file(path, ocr=False)
    for s in segments:
        print("---")
        print("doc_id:", s.doc_id)
        print("page:", s.page, "section:", s.section, "kind:", s.kind)
        print("meta:", s.meta)
        print("text snippet:", s.text[:200].replace("\n"," "))
