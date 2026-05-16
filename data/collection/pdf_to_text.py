"""
Extracts text from High Court judgment PDFs.
Input:  data/raw/high_court_judgments/*.pdf
Output: data/raw/high_court_judgments/*.json

Run: python data/collection/pdf_to_text.py
"""

import json
import re
from pathlib import Path
from loguru import logger

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    logger.warning("pypdf not installed. Run: pip install pypdf")

# ── Config ──────────────────────────────────────────────────
INPUT_DIR  = Path("data/raw/high_court_judgments")
OUTPUT_DIR = Path("data/raw/high_court_judgments")
INPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Hardcoded sample judgment data ──────────────────────────
# Used when no PDFs are available yet.
# Replace with real judgment data as you collect PDFs.

SAMPLE_JUDGMENTS = [
    {
        "case_number":  "CRL.A 1234/2022",
        "court":        "High Court of Karnataka",
        "date":         "2022-08-15",
        "petitioner":   "State of Karnataka",
        "respondent":   "Accused Person",
        "ipc_sections": ["302", "34"],
        "judgment":     "Conviction",
        "summary": (
            "The High Court of Karnataka upheld the conviction of the "
            "accused under IPC Section 302 read with Section 34. "
            "The court found that the prosecution had established beyond "
            "reasonable doubt that the accused had committed murder with "
            "common intention. The sentence of life imprisonment was confirmed."
        ),
        "text": (
            "IN THE HIGH COURT OF KARNATAKA AT BENGALURU "
            "CRIMINAL APPEAL NO. 1234 OF 2022 "
            "Between: State of Karnataka ... Appellant "
            "And: Accused Person ... Respondent "
            "This criminal appeal is filed by the State challenging the "
            "order of acquittal passed by the Sessions Court. "
            "The accused was charged under Section 302 read with 34 of IPC. "
            "After careful consideration of evidence, this Court finds that "
            "the prosecution has established its case beyond reasonable doubt. "
            "The appeal is allowed. The accused is convicted under "
            "Section 302 IPC and sentenced to imprisonment for life."
        ),
        "source": "Karnataka High Court",
        "language": "English"
    },
    {
        "case_number":  "CRL.P 5678/2021",
        "court":        "High Court of Karnataka",
        "date":         "2021-11-20",
        "petitioner":   "Accused Person",
        "respondent":   "State of Karnataka",
        "ipc_sections": ["420", "406"],
        "judgment":     "Bail Granted",
        "summary": (
            "The High Court of Karnataka granted bail to the petitioner "
            "accused of offences under IPC Sections 420 and 406. "
            "The court considered the nature of the offence, the evidence "
            "on record and the period of detention and found that the "
            "petitioner was entitled to bail subject to conditions."
        ),
        "text": (
            "IN THE HIGH COURT OF KARNATAKA AT BENGALURU "
            "CRIMINAL PETITION NO. 5678 OF 2021 "
            "Between: Accused Person ... Petitioner "
            "And: State of Karnataka ... Respondent "
            "The petitioner is accused of offences punishable under "
            "Sections 420 and 406 of IPC. "
            "Having regard to the nature of the offence, the materials "
            "on record and the period of incarceration, this Court is "
            "of the opinion that the petitioner is entitled to bail. "
            "The petition is allowed. The petitioner is ordered to be "
            "released on bail subject to the following conditions: "
            "1. Shall execute a personal bond for Rs.1,00,000. "
            "2. Shall not leave the jurisdiction without prior permission. "
            "3. Shall appear before the trial court on all hearing dates."
        ),
        "source": "Karnataka High Court",
        "language": "English"
    },
    {
        "case_number":  "WP 9012/2023",
        "court":        "High Court of Karnataka",
        "date":         "2023-03-10",
        "petitioner":   "Citizen",
        "respondent":   "State of Karnataka",
        "ipc_sections": [],
        "judgment":     "RTI Order",
        "summary": (
            "The High Court directed the State Public Information Officer "
            "to provide information sought by the petitioner under the "
            "Right to Information Act 2005 within 15 days. "
            "The court held that denial of information without valid reason "
            "is a violation of the petitioner's fundamental right."
        ),
        "text": (
            "IN THE HIGH COURT OF KARNATAKA AT BENGALURU "
            "WRIT PETITION NO. 9012 OF 2023 "
            "Between: Citizen ... Petitioner "
            "And: State of Karnataka & Others ... Respondents "
            "The petitioner sought information under the RTI Act 2005 "
            "which was denied by the Public Information Officer. "
            "This Court holds that every citizen has the right to "
            "information under Article 19(1)(a) of the Constitution "
            "read with the RTI Act 2005. "
            "The writ petition is allowed. The respondent is directed "
            "to furnish the information sought within 15 days."
        ),
        "source": "Karnataka High Court",
        "language": "English"
    },
]


# ── PDF Text Extractor ───────────────────────────────────────
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    if not PYPDF_AVAILABLE:
        logger.error("pypdf not available.")
        return ""
    try:
        reader = PdfReader(str(pdf_path))
        full_text = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text.append(text)
            logger.debug(f"Page {page_num + 1}/{len(reader.pages)} extracted.")
        return "\n".join(full_text)
    except Exception as e:
        logger.error(f"Failed to extract {pdf_path.name}: {e}")
        return ""


def clean_text(text: str) -> str:
    """Clean extracted PDF text."""
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove page numbers
    text = re.sub(r"\n\d+\n", "\n", text)
    # Remove headers/footers (common patterns)
    text = re.sub(r"HIGH COURT OF KARNATAKA", "", text, flags=re.IGNORECASE)
    return text.strip()


def extract_metadata(text: str, filename: str) -> dict:
    """Try to extract case metadata from judgment text."""
    metadata = {
        "filename":     filename,
        "court":        "High Court of Karnataka",
        "language":     "English",
        "source":       "Karnataka High Court",
        "ipc_sections": [],
    }

    # Extract case number
    case_match = re.search(
        r"(CRL\.[A-Z]+\s*\d+/\d+|WP\s*\d+/\d+|CRL\.P\s*\d+/\d+)",
        text, re.IGNORECASE
    )
    if case_match:
        metadata["case_number"] = case_match.group(1)

    # Extract IPC sections mentioned
    sections = re.findall(r"[Ss]ection[s]?\s*(\d+[A-Z]?)", text)
    if sections:
        metadata["ipc_sections"] = list(set(sections))

    # Extract date
    date_match = re.search(
        r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})", text
    )
    if date_match:
        metadata["date"] = date_match.group(1)

    return metadata


def process_pdfs() -> list[dict]:
    """Process all PDFs in the input directory."""
    pdf_files = list(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        logger.warning("No PDF files found in data/raw/high_court_judgments/")
        logger.info(
            "To add PDFs: Download judgment PDFs from "
            "https://judgments.ecourts.gov.in and place them in "
            "data/raw/high_court_judgments/"
        )
        return []

    results = []
    for pdf_path in pdf_files:
        logger.info(f"Processing: {pdf_path.name}")
        raw_text   = extract_text_from_pdf(pdf_path)
        clean      = clean_text(raw_text)
        metadata   = extract_metadata(clean, pdf_path.name)

        results.append({
            **metadata,
            "text":    clean,
            "summary": clean[:500] + "..." if len(clean) > 500 else clean,
        })

        # Save individual JSON per PDF
        out_file = OUTPUT_DIR / (pdf_path.stem + ".json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({**metadata, "text": clean}, f, ensure_ascii=False, indent=2)
        logger.success(f"Saved → {out_file}")

    return results


# ── Main ────────────────────────────────────────────────────
def main():
    logger.info("Starting PDF text extraction...")

    # Try to process real PDFs first
    pdf_results = process_pdfs()

    if pdf_results:
        logger.success(f"Extracted text from {len(pdf_results)} PDFs.")
    else:
        # Use sample data as fallback
        logger.info("Using sample judgment data as fallback...")
        sample_file = OUTPUT_DIR / "sample_judgments.json"
        with open(sample_file, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_JUDGMENTS, f, ensure_ascii=False, indent=2)
        logger.success(
            f"Saved {len(SAMPLE_JUDGMENTS)} sample judgments → {sample_file}"
        )
        logger.info(
            "To add real judgments: Download PDFs from "
            "https://judgments.ecourts.gov.in and re-run this script."
        )

    logger.info("Next step: run translate_to_kannada.py")


if __name__ == "__main__":
    main()