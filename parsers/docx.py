from typing import List
from docx import Document as Docx
from .common import Segment, clean_text

def parse_docx(path: str, doc_id: str) -> List[Segment]:
    d = Docx(path)
    segs: List[Segment] = []
    heading_path: List[str] = []

    def current_section():
        return " > ".join(heading_path) if heading_path else None

    for para in d.paragraphs:
        style = (para.style.name or "").lower()
        if style.startswith("heading"):
            parts = style.split()
            lvl = int(parts[-1]) if parts and parts[-1].isdigit() else 1
            heading_path[:] = heading_path[:lvl-1] + [para.text.strip()]
        else:
            text = para.text.strip()
            if text:
                segs.append(Segment(doc_id, clean_text(text), section=current_section(), kind="text"))

    for t_idx, table in enumerate(d.tables):
        rows = []
        for row in table.rows:
            rows.append([clean_text(c.text) for c in row.cells])
        if rows:
            head = rows[0]
            body = rows[1:]
            table_md = "|" + "|".join(head) + "|\n"
            table_md += "|" + "|".join("---" for _ in head) + "|\n"
            for r in body:
                table_md += "|" + "|".join(r) + "|\n"
            segs.append(Segment(doc_id, table_md, section=current_section(), kind="table", meta={"table_id": t_idx}))
    return segs
