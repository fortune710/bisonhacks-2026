from backend.db.mongo import db
from pathlib import Path
import pdfplumber
from datetime import datetime, timezone

def is_page_snap_relevant(page_text):
    """Skip pages explicitly marked for other programs only."""
    excluded_headers = [
        "(TANF and Medical Assistance Only)",
        "(Medical Assistance Only)"
    ]
    return not any(header.lower() in page_text.lower() for header in excluded_headers)

def main():
    pdf_folder = Path("backend/resources")
    pdf_files = list(pdf_folder.glob("*.pdf"))
    print("Found PDFs:", [f.name for f in pdf_files])

    for pdf_file in pdf_files:
        # Extract program, state, resource type from filename
        parts = pdf_file.stem.split("_")
        state = parts[0].upper() if len(parts) > 0 else "UNKNOWN"
        program = parts[1].upper() if len(parts) > 1 else "SNAP"
        resource_type = parts[2] if len(parts) > 2 else "form"  # guide, checklist, application

        snap_content = []

        # Open PDF and extract pages
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if is_page_snap_relevant(text):
                    snap_content.append(text)

        full_snap_text = "\n".join(snap_content)

        # UPSERT into MongoDB to avoid duplicates
        db.program_resources.update_one(
            {"program": program, "state": state, "filename": pdf_file.name},
            {"$set": {
                "resource_type": resource_type,
                "format": "pdf",
                "content": full_snap_text,
                "scraped_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )

        print(f"Upserted {pdf_file.name} as {resource_type} for program {program}, state {state}")

if __name__ == "__main__":
    main()