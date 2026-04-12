"""Quick test: upload a PDF to Google Drive and print the result."""
import sys, traceback
sys.path.insert(0, "/app")

try:
    from services.google_drive import upload_pdf
    fid, link = upload_pdf("/app/pdf_output/preview.pdf", "test_upload.pdf")
    print("SUCCESS")
    print("file_id:", fid)
    print("link:", link)
except Exception:
    traceback.print_exc()
