"""
Fast PDF preview — runs directly in the celery container, bypasses Celery queue.
Called by preview_pdf.ps1.  Usage inside container:
    python /app/preview_render.py [analysis_id]
"""
import sys
import os

sys.path.insert(0, '/app')

analysis_id = int(sys.argv[1]) if len(sys.argv) > 1 else 74

from db.database import SessionLocal
from models.shopify_order import Analysis, SolarReturnReport
from services.pdf_tasks import _build_pdf_html
from weasyprint import HTML

db = SessionLocal()
analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
report   = db.query(SolarReturnReport).filter(SolarReturnReport.analysis_id == analysis_id).first()

if not analysis:
    print(f"ERROR: Analysis {analysis_id} not found")
    sys.exit(1)

html = _build_pdf_html(analysis, report)
output_path = '/app/pdf_output/preview.pdf'
HTML(string=html).write_pdf(output_path)
print(f"OK: PDF written to {output_path}")
