# Document Parser

Python utilities for parsing documents (PDF, DOCX, TXT, MD, CSV), normalizing text, and emitting chunked JSON suitable for RAG ingestion. Includes optional OCR.

## Features

- Supports multiple document formats:
  - PDF (with optional OCR support)
  - Microsoft Word (DOCX)
  - Text files (TXT)
  - Markdown files (MD)
  - CSV files
- Extracts structured content including:
  - Text segments and table blocks
  - Document sections (DOCX headings)
  - Page numbers (PDFs)
  - Optional chunked output with configurable size and overlap
- PDF niceties:
  - Per-page OCR fallback (when `--ocr` is enabled)
  - Simple header/footer de-duplication
  - Newline normalization for cleaner paragraphs

## Requirements

```txt
PyMuPDF==1.24.9
python-docx==1.1.2
Pillow==10.4.0
pytesseract==0.3.13
```

## Installation

1. Clone the repository
2. Install dependencies:
```sh
pip install -r requirements.txt
```

3. For OCR support, ensure Tesseract is installed on your system:
   - On Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - On macOS: `brew install tesseract`
   - On Windows: Download and install from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

### Command Line Interface

Preview segments (default):
```sh
python reader.py path/to/file.pdf
```

Emit chunks JSON (for RAG ingestion):
```sh
python reader.py --chunks --max-chars 1200 path/to/file.pdf
```

Enable OCR for scanned PDFs:
```sh
python reader.py --chunks --ocr path/to/scanned.pdf
```

### Python API

```python
from reader import read_file, read_chunks
from parsers.common import segments_to_chunks

# 1) Get raw segments
segments = read_file("document.pdf", ocr=False)

# 2) Convert to chunks (code path)
result = segments_to_chunks(segments, max_chars=1200, overlap=120)
print(result["chunks"][0])

# 3) One-call convenience
chunks_json = read_chunks("document.pdf", ocr=False, max_chars=1200)
```

## Output Format

Segments (internal representation):

- `doc_id`: Document identifier (generated as `<uuid8>-<filename_stem>` unless you supply your own)
- `text`: Extracted text content
- `page`: Page number (PDF only)
- `section`: Section heading path (DOCX only)
- `kind`: Content type ("text" or "table")
- `meta`: Additional metadata dictionary (e.g., `{"source": "file.pdf"}`)

Chunks (for ingestion):

```json
{
  "chunks": [
    {
      "id": "<doc_id>:0000",
      "doc_id": "<doc_id>",
      "text": "...chunk text...",
      "metadata": { "page": 1, "kind": "text", "source": "file.pdf", "chunk_index": 0 }
    }
  ]
}
```

## Notes

- `reader.py` also supports `--chunks` and `--max-chars` via CLI. Overlap is configurable via code (see `segments_to_chunks`).
- PDF extraction automatically removes repeated headers/footers and normalizes newlines. Enable `--ocr` for scanned pages.

## License

This project is open source and available under the MIT License.
