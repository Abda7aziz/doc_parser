import pathlib, uuid
from parsers.pdf import parse_pdf
from parsers.docx import parse_docx
from parsers.common import Segment,segments_to_chunks

def read_file(path: str, ocr: bool = False):
    ext = pathlib.Path(path).suffix.lower()
    # Use a hyphen to avoid ':' inside doc_id, since chunk IDs are
    # formed as f"{doc_id}:{index}" and downstream split on ':'.
    doc_id = f"{uuid.uuid4().hex[:8]}-{pathlib.Path(path).stem}"
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

def read_chunks(path: str, ocr: bool = False, max_chars: int = 1200):
    """Read a file and return the {"chunks": [...]} schema.
    This fuses reading + chunking for convenience while keeping read_file as a
    reusable primitive elsewhere.
    """
    return segments_to_chunks(read_file(path, ocr=ocr), max_chars)

if __name__ == "__main__":
    import argparse, json,sys
    parser = argparse.ArgumentParser(description="Read documents and optionally emit chunks JSON.")
    parser.add_argument("path", help="Path to input file")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR for PDFs when needed")
    parser.add_argument("--chunks", action="store_true", help="Output {\"chunks\": [...]} JSON instead of segments preview")
    parser.add_argument("--max-chars", type=int, default=1200, help="Max characters per chunk when using --chunks")
    args = parser.parse_args()
    if args.chunks:
        result = read_chunks(args.path, ocr=args.ocr, max_chars=args.max_chars)
        json.dump(result, fp=sys.stdout, ensure_ascii=False)
        print()
    else:
        segments = read_file(args.path, ocr=args.ocr)
        for s in segments:
            print("---")
            print("doc_id:", s.doc_id)
            print("page:", s.page, "section:", s.section, "kind:", s.kind)
            print("meta:", s.meta)
            print("text snippet:", s.text[:200].replace("\n"," "))
