# Document Parser

A Python utility for parsing and extracting content from various document formats (PDF, DOCX, TXT, MD, CSV) with support for OCR capabilities.

## Features

- Supports multiple document formats:
  - PDF (with optional OCR support)
  - Microsoft Word (DOCX)
  - Text files (TXT)
  - Markdown files (MD)
  - CSV files
- Extracts structured content including:
  - Text segments
  - Tables (from DOCX)
  - Document sections and headings
  - Page numbers (for PDFs)

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

```sh
python reader.py <file-path>
```

### Python API

```python
from reader import read_file

# Basic usage
segments = read_file("document.pdf")

# With OCR enabled (for PDFs)
segments = read_file("document.pdf", ocr=True)

# Process other formats
segments = read_file("document.docx")
segments = read_file("data.csv")

# Each segment contains:
for segment in segments:
    print(segment.doc_id)    # Document identifier
    print(segment.text)      # Extracted text
    print(segment.page)      # Page number (PDF only)
    print(segment.section)   # Document section (DOCX only)
    print(segment.kind)      # Content type (text/table)
    print(segment.meta)      # Additional metadata
```

## Output Format

The parser returns a list of `Segment` objects with the following attributes:

- `doc_id`: Unique identifier for the document
- `text`: Extracted text content
- `page`: Page number (PDF only)
- `section`: Section heading path (DOCX only)
- `kind`: Content type ("text" or "table")
- `meta`: Additional metadata dictionary

## License

This project is open source and available under the MIT License.