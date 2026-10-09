from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

pdf_path = BASE_DIR / "data" / "uploads" / "GenAI_Build_GUIDELINES.pdf"
opts = PdfPipelineOptions()
opts.do_ocr = False
converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
conv_res = converter.convert(pdf_path)
doc = conv_res.document

print("export_to_markdown length:", len(doc.export_to_markdown()))
print("num tables:", len(doc.tables))
items = list(doc.iterate_items())
print("total iterate_items count:", len(items))
for idx, (item, level) in enumerate(items[:10]):
    print(f"Item {idx}: type={type(item).__name__}, attrs={[a for a in dir(item) if not a.startswith('_')]}")
    print(f"  text={getattr(item, 'text', None)!r}")
    print(f"  prov={getattr(item, 'prov', None)!r}")
