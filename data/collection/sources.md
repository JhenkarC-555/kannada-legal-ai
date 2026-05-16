# ಕನ್ನಡ ಕಾನೂನು AI — Data Sources Guide

This file lists all data sources for the Kannada Legal AI project.
For each source, it explains what to collect, how to collect it,
and which script to use.

---

## 📌 Source 1 — India Code (IPC Sections)
**URL:** https://indiacode.nic.in  
**Language:** English  
**Needs Translation:** Yes (English → Kannada)  
**Script:** `scrape_india_code.py`  
**Output:** `data/raw/ipc_sections/ipc_sections.json`

### What to collect
- All IPC sections (1 to 511)
- Each section: number, title, full text, punishment

### How to collect
Run the scraper script:
```bash
python data/collection/scrape_india_code.py
```

---

## 📌 Source 2 — Karnataka Government Portal
**URL:** https://karnataka.gov.in/english  
**Language:** English  
**Needs Translation:** Yes (English → Kannada)  
**Script:** `scrape_karnataka_gov.py`  
**Output:** `data/raw/karnataka_state_laws/karnataka_laws.json`

### What to collect
- Karnataka Land Revenue Act
- Karnataka Police Act
- Karnataka Shops and Establishments Act
- Karnataka Rent Control Act

### How to collect
```bash
python data/collection/scrape_karnataka_gov.py
```

---

## 📌 Source 3 — Vikaspedia Kannada (Best Source — Already in Kannada)
**URL:** https://kannada.vikaspedia.in/social-welfare/rights-a-nd-entitlements  
**Language:** Kannada ✅ (no translation needed)  
**Script:** `scrape_karnataka_gov.py` (handles this too)  
**Output:** `data/raw/legal_aid_pamphlets/vikaspedia_kn.json`

### What to collect
- Citizen rights articles in Kannada
- Legal aid information in Kannada
- RTI guides in Kannada

---

## 📌 Source 4 — AI4Bharat IndicCorp (Kannada Corpus)
**URL:** https://huggingface.co/datasets/ai4bharat/IndicCorp  
**Language:** Kannada ✅ (no translation needed)  
**How to collect:** Download directly from HuggingFace

```python
# Run this in a Colab notebook (large dataset)
from datasets import load_dataset
dataset = load_dataset("ai4bharat/IndicCorp", "kn")
```

**Output:** Use for general Kannada language understanding

---

## 📌 Source 5 — High Court of Karnataka Judgments
**URL:** https://judgments.ecourts.gov.in  
**Language:** English  
**Needs Translation:** Yes  
**Script:** `download_pdfs.py` + `pdf_to_text.py`  
**Output:** `data/raw/high_court_judgments/`

### What to collect
- Recent Karnataka High Court judgments (PDFs)
- Focus on criminal cases (IPC related)

### How to collect
```bash
# Step 1 — Download PDFs
python data/collection/download_pdfs.py

# Step 2 — Extract text from PDFs
python data/collection/pdf_to_text.py
```

---

## 📌 Source 6 — Manual QA Pairs (Most Important)
**Language:** Kannada ✅  
**Script:** `generate_qa_pairs.py`  
**Output:** `data/annotated/train/qa_pairs.jsonl`

### What to collect
Manually written question-answer pairs like:
```json
{
  "question": "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
  "answer": "ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ವಿಧಿಸುತ್ತದೆ...",
  "context": "Section 302 IPC...",
  "law": "IPC",
  "section": "302"
}
```

### How to collect
- Ask Kannada-speaking law students to write Q&A pairs
- Use `generate_qa_pairs.py` to generate synthetic pairs
  from scraped sections using an LLM

---

## 📊 Data Collection Order (Follow This Sequence)

| Step | Source         | Script                    | Priority |
|------|---------------|---------------------------|----------|
| 1    | India Code     | scrape_india_code.py      | 🔴 Critical |
| 2    | Vikaspedia     | scrape_karnataka_gov.py   | 🔴 Critical |
| 3    | Karnataka Gov  | scrape_karnataka_gov.py   | 🟠 High |
| 4    | High Court     | download_pdfs.py          | 🟡 Medium |
| 5    | IndicCorp      | Colab notebook            | 🟡 Medium |
| 6    | Manual QA      | generate_qa_pairs.py      | 🔴 Critical |

---

## 📁 Final Expected Folder Structure After Collection