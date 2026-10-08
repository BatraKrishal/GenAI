"""
Docling-based PDF parser for layout-aware document ingestion.
Extracts text, headings, tables (in markdown format), and page numbers
to guarantee high-precision retrieval and dataset grounding.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("docling_parser")
logging.basicConfig(level=logging.INFO)

class CampusDocParser:
    def __init__(self, use_ocr: bool = False):
        self.use_ocr = use_ocr
        self._converter = None

    def _init_converter(self):
        if self._converter is None:
            try:
                from docling.document_converter import DocumentConverter
                self._converter = DocumentConverter()
                logger.info("Docling DocumentConverter initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Docling: {e}. Fallback parser will be used.")
                self._converter = None

    def parse_document(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Parses a PDF using Docling.
        Returns:
            dict containing:
                - 'full_markdown': Complete markdown representation with tables
                - 'pages': List of page-level texts with page numbers
                - 'tables': Extracted markdown tables
                - 'docling_doc': The raw DoclingDocument object (if available)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        self._init_converter()

        if self._converter:
            try:
                logger.info(f"Parsing '{path.name}' with Docling (layout + table extraction)...")
                conv_result = self._converter.convert(path)
                doc = conv_result.document

                full_markdown = doc.export_to_markdown()

                # Extract page-by-page mapping
                pages_data: List[Dict[str, Any]] = []
                # Docling items contain provenance (page_no)
                current_page_text: Dict[int, List[str]] = {}
                for item, _ in doc.iterate_items():
                    text = item.text.strip() if hasattr(item, "text") and item.text else ""
                    if not text:
                        continue
                    
                    page_no = 1
                    if hasattr(item, "prov") and item.prov and len(item.prov) > 0:
                        page_no = item.prov[0].page_no

                    if page_no not in current_page_text:
                        current_page_text[page_no] = []
                    current_page_text[page_no].append(text)

                for p_no in sorted(current_page_text.keys()):
                    pages_data.append({
                        "page_number": p_no,
                        "text": "\n\n".join(current_page_text[p_no]),
                        "source": path.name
                    })

                # Extract tables
                tables_markdown: List[str] = []
                for table in doc.tables:
                    try:
                        table_md = table.export_to_markdown()
                        if table_md:
                            tables_markdown.append(table_md)
                    except Exception:
                        pass

                logger.info(f"Docling parsed {len(pages_data)} pages and {len(tables_markdown)} tables.")
                return {
                    "parser": "docling",
                    "full_markdown": full_markdown,
                    "pages": pages_data,
                    "tables": tables_markdown,
                    "docling_doc": doc,
                    "source": path.name
                }
            except Exception as e:
                logger.error(f"Docling conversion failed: {e}. Falling back to PyPDF.")

        # Fallback to PyPDF
        return self._fallback_parse_pdf(path)

    def _fallback_parse_pdf(self, path: Path) -> Dict[str, Any]:
        """Fast fallback parser using PyPDF."""
        import pypdf
        logger.info(f"Parsing '{path.name}' with PyPDF fallback...")
        reader = pypdf.PdfReader(str(path))
        pages_data = []
        all_text = []

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            page_no = idx + 1
            pages_data.append({
                "page_number": page_no,
                "text": text,
                "source": path.name
            })
            all_text.append(f"## Page {page_no}\n{text}")

        return {
            "parser": "pypdf_fallback",
            "full_markdown": "\n\n".join(all_text),
            "pages": pages_data,
            "tables": [],
            "docling_doc": None,
            "source": path.name
        }
