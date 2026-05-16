"""
Generates Kannada legal QA pairs from translated legal sections.
These QA pairs are used to fine-tune the model.

Input:  data/processed/translated_ipc_kn.json
        data/processed/translated_karnataka_kn.json
        data/raw/legal_aid_pamphlets/vikaspedia_kn.json

Output: data/annotated/train/qa_pairs.jsonl
        data/annotated/val/qa_pairs.jsonl
        data/annotated/test/qa_pairs.jsonl

Run: python data/collection/generate_qa_pairs.py
"""

import json
import random
from pathlib import Path
from loguru import logger

# ── Config ──────────────────────────────────────────────────
PROCESSED_DIR   = Path("data/processed")
VIKASPEDIA_FILE = Path("data/raw/legal_aid_pamphlets/vikaspedia_kn.json")

TRAIN_DIR = Path("data/annotated/train")
VAL_DIR   = Path("data/annotated/val")
TEST_DIR  = Path("data/annotated/test")

TRAIN_DIR.mkdir(parents=True, exist_ok=True)
VAL_DIR.mkdir(parents=True, exist_ok=True)
TEST_DIR.mkdir(parents=True, exist_ok=True)

# Split ratios
TRAIN_RATIO = 0.75
VAL_RATIO   = 0.15
TEST_RATIO  = 0.10

random.seed(42)

# ── Hardcoded QA pairs ───────────────────────────────────────
# High quality manually written Kannada QA pairs.
# These are the most important ones for the model to learn from.

MANUAL_QA_PAIRS = [

    # ── IPC 302 ─────────────────────────────────────────────
    {
        "question":   "IPC ಸೆಕ್ಷನ್ 302 ಏನು?",
        "answer": (
            "IPC ಸೆಕ್ಷನ್ 302 ಕೊಲೆಗೆ ಶಿಕ್ಷೆ ವಿಧಿಸುತ್ತದೆ. "
            "ಯಾರಾದರೂ ಕೊಲೆ ಮಾಡಿದರೆ ಅವರಿಗೆ ಮರಣದಂಡನೆ "
            "ಅಥವಾ ಜೀವಾವಧಿ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ ವಿಧಿಸಲಾಗುವುದು "
            "ಮತ್ತು ದಂಡ ಕೂಡ ವಿಧಿಸಬಹುದು."
        ),
        "context": (
            "Section 302 IPC — Punishment for murder. "
            "Whoever commits murder shall be punished with death "
            "or imprisonment for life and shall also be liable to fine."
        ),
        "law":            "IPC",
        "section":        "302",
        "intent":         "section_lookup",
        "language":       "kn",
    },
    {
        "question":   "ಕೊಲೆ ಪ್ರಕರಣದಲ್ಲಿ ಯಾವ ಶಿಕ್ಷೆ ಆಗುತ್ತದೆ?",
        "answer": (
            "ಕೊಲೆ ಪ್ರಕರಣದಲ್ಲಿ IPC ಸೆಕ್ಷನ್ 302 ಅಡಿಯಲ್ಲಿ "
            "ಮರಣದಂಡನೆ ಅಥವಾ ಜೀವಾವಧಿ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ "
            "ವಿಧಿಸಲಾಗುತ್ತದೆ. ನ್ಯಾಯಾಲಯ ಪ್ರಕರಣದ ಸಂದರ್ಭ "
            "ಮತ್ತು ಸಾಕ್ಷ್ಯಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಶಿಕ್ಷೆ ನಿರ್ಧರಿಸುತ್ತದೆ."
        ),
        "context": (
            "Section 302 IPC — Punishment for murder. "
            "Whoever commits murder shall be punished with death "
            "or imprisonment for life and shall also be liable to fine."
        ),
        "law":            "IPC",
        "section":        "302",
        "intent":         "penalty_query",
        "language":       "kn",
    },

    # ── IPC 420 ─────────────────────────────────────────────
    {
        "question":   "IPC ಸೆಕ್ಷನ್ 420 ಏನು?",
        "answer": (
            "IPC ಸೆಕ್ಷನ್ 420 ಮೋಸ ಮತ್ತು ಆಸ್ತಿ ವಿತರಣೆಗೆ "
            "ಅಪ್ರಾಮಾಣಿಕ ಪ್ರೇರಣೆ ನೀಡುವ ಅಪರಾಧಕ್ಕೆ ಸಂಬಂಧಿಸಿದೆ. "
            "ಈ ಅಪರಾಧಕ್ಕೆ 7 ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ "
            "ಮತ್ತು ದಂಡ ವಿಧಿಸಲಾಗುತ್ತದೆ."
        ),
        "context": (
            "Section 420 IPC — Cheating and dishonestly inducing "
            "delivery of property. Punishment: up to 7 years + fine."
        ),
        "law":            "IPC",
        "section":        "420",
        "intent":         "section_lookup",
        "language":       "kn",
    },
    {
        "question":   "ಯಾರಾದರೂ ನನ್ನನ್ನು ಮೋಸ ಮಾಡಿ ಹಣ ತೆಗೆದುಕೊಂಡರೆ ಏನು ಮಾಡಬೇಕು?",
        "answer": (
            "ಯಾರಾದರೂ ನಿಮ್ಮನ್ನು ಮೋಸ ಮಾಡಿ ಹಣ ತೆಗೆದುಕೊಂಡರೆ "
            "IPC ಸೆಕ್ಷನ್ 420 ಅಡಿಯಲ್ಲಿ ಪೊಲೀಸ್ ಠಾಣೆಯಲ್ಲಿ "
            "FIR ದಾಖಲಿಸಬಹುದು. ಮೋಸದ ಎಲ್ಲಾ ದಾಖಲೆಗಳನ್ನು "
            "ಇಟ್ಟುಕೊಳ್ಳಿ. ನಂತರ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ದಾವೆ ಹೂಡಬಹುದು. "
            "ವಕೀಲರ ಸಹಾಯ ಪಡೆಯಲು ಮರೆಯಬೇಡಿ."
        ),
        "context": (
            "Section 420 IPC — Cheating and dishonestly inducing "
            "delivery of property. Punishment: up to 7 years + fine."
        ),
        "law":            "IPC",
        "section":        "420",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── Arrest Rights ────────────────────────────────────────
    {
        "question":   "ಪೊಲೀಸ್ ಅರೆಸ್ಟ್ ಮಾಡಿದರೆ ನನ್ನ ಹಕ್ಕುಗಳೇನು?",
        "answer": (
            "ಪೊಲೀಸ್ ಬಂಧಿಸಿದಾಗ ನಿಮಗೆ ಈ ಹಕ್ಕುಗಳಿವೆ:\n"
            "1. ಬಂಧನದ ಕಾರಣ ತಿಳಿಯುವ ಹಕ್ಕು (CrPC ಸೆಕ್ಷನ್ 50)\n"
            "2. ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸುವ ಹಕ್ಕು\n"
            "3. 24 ಗಂಟೆಯಲ್ಲಿ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಮುಂದೆ ಹಾಜರಾಗುವ ಹಕ್ಕು\n"
            "4. ವೈದ್ಯಕೀಯ ತಪಾಸಣೆ ಮಾಡಿಸಿಕೊಳ್ಳುವ ಹಕ್ಕು\n"
            "5. ಕುಟುಂಬಕ್ಕೆ ತಿಳಿಸುವ ಹಕ್ಕು\n"
            "ಈ ಹಕ್ಕುಗಳನ್ನು ನಿರಾಕರಿಸಿದರೆ ನ್ಯಾಯಾಲಯದಲ್ಲಿ "
            "ದೂರು ದಾಖಲಿಸಬಹುದು."
        ),
        "context": (
            "CrPC Section 50 — Person arrested to be informed of "
            "grounds of arrest and right to bail. "
            "CrPC Section 41D — Right of arrested person to meet "
            "an advocate of his choice during interrogation."
        ),
        "law":            "CrPC",
        "section":        "50",
        "intent":         "rights_query",
        "language":       "kn",
    },
    {
        "question":   "ಪೊಲೀಸ್ ವಾರಂಟ್ ಇಲ್ಲದೆ ಅರೆಸ್ಟ್ ಮಾಡಬಹುದೇ?",
        "answer": (
            "ಹೌದು, CrPC ಸೆಕ್ಷನ್ 41 ಅಡಿಯಲ್ಲಿ ಸಂಜ್ಞೇಯ "
            "ಅಪರಾಧಗಳಲ್ಲಿ ಪೊಲೀಸ್ ವಾರಂಟ್ ಇಲ್ಲದೆ ಬಂಧಿಸಬಹುದು. "
            "ಆದರೆ ಬಂಧನದ ಕಾರಣ ಹೇಳಬೇಕು ಮತ್ತು "
            "24 ಗಂಟೆಯಲ್ಲಿ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಮುಂದೆ ಹಾಜರುಪಡಿಸಬೇಕು. "
            "ಅಸಂಜ್ಞೇಯ ಅಪರಾಧಗಳಲ್ಲಿ ವಾರಂಟ್ ಅಗತ್ಯ."
        ),
        "context": (
            "CrPC Section 41 — When police may arrest without warrant. "
            "Any police officer may without an order from a Magistrate "
            "and without a warrant, arrest any person who has been "
            "concerned in any cognizable offence."
        ),
        "law":            "CrPC",
        "section":        "41",
        "intent":         "rights_query",
        "language":       "kn",
    },

    # ── FIR ─────────────────────────────────────────────────
    {
        "question":   "FIR ದಾಖಲಿಸುವುದು ಹೇಗೆ?",
        "answer": (
            "FIR ದಾಖಲಿಸಲು:\n"
            "1. ಹತ್ತಿರದ ಪೊಲೀಸ್ ಠಾಣೆಗೆ ಹೋಗಿ\n"
            "2. ಘಟನೆಯ ವಿವರ ಬರೆದ ದೂರು ನೀಡಿ\n"
            "3. FIR ಪ್ರತಿ ಪಡೆಯಿರಿ (ಉಚಿತ)\n"
            "ಪೊಲೀಸ್ ನಿರಾಕರಿಸಿದರೆ SP ಅಥವಾ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್‌ಗೆ "
            "ದೂರು ನೀಡಿ. CrPC ಸೆಕ್ಷನ್ 154 ಅನ್ವಯ FIR "
            "ದಾಖಲಿಸುವುದು ಪೊಲೀಸ್ ಕರ್ತವ್ಯ."
        ),
        "context": (
            "CrPC Section 154 — Information in cognizable cases. "
            "Every information relating to the commission of a "
            "cognizable offence shall be reduced to writing by "
            "the officer in charge of a police station."
        ),
        "law":            "CrPC",
        "section":        "154",
        "intent":         "procedure_query",
        "language":       "kn",
    },
    {
        "question":   "ಪೊಲೀಸ್ FIR ತೆಗೆದುಕೊಳ್ಳಲು ನಿರಾಕರಿಸಿದರೆ ಏನು ಮಾಡಬೇಕು?",
        "answer": (
            "ಪೊಲೀಸ್ FIR ತೆಗೆದುಕೊಳ್ಳಲು ನಿರಾಕರಿಸಿದರೆ:\n"
            "1. ಜಿಲ್ಲಾ ಪೊಲೀಸ್ ವರಿಷ್ಠಾಧಿಕಾರಿ (SP) ಗೆ ದೂರು ನೀಡಿ\n"
            "2. ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಕಚೇರಿಗೆ ನೇರ ದೂರು ನೀಡಿ\n"
            "3. ರಾಜ್ಯ ಮಾನವ ಹಕ್ಕುಗಳ ಆಯೋಗಕ್ಕೆ ದೂರು ನೀಡಿ\n"
            "4. ಹೈಕೋರ್ಟ್‌ನಲ್ಲಿ ರಿಟ್ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು"
        ),
        "context": (
            "CrPC Section 154 — Information in cognizable cases. "
            "If the officer in charge of a police station refuses "
            "to record the information, such person may send the "
            "substance of such information to the Superintendent "
            "of Police."
        ),
        "law":            "CrPC",
        "section":        "154",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── Bail ────────────────────────────────────────────────
    {
        "question":   "ಜಾಮೀನು ಪಡೆಯುವುದು ಹೇಗೆ?",
        "answer": (
            "ಜಾಮೀನು ಪಡೆಯಲು:\n"
            "1. ವಕೀಲರ ಮೂಲಕ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ಜಾಮೀನು ಅರ್ಜಿ ಸಲ್ಲಿಸಿ\n"
            "2. ಜಾಮೀನು ಅರ್ಜಿಯಲ್ಲಿ ಬಂಧನದ ಕಾರಣ ಮತ್ತು "
            "ಓಡಿ ಹೋಗದ ಭರವಸೆ ನೀಡಿ\n"
            "CrPC ಸೆಕ್ಷನ್ 436 — ಜಾಮೀನು ಪಡೆಯಬಹುದಾದ "
            "ಅಪರಾಧಗಳಲ್ಲಿ ಜಾಮೀನು ಕಡ್ಡಾಯ.\n"
            "CrPC ಸೆಕ್ಷನ್ 437 — ಜಾಮೀನು ಪಡೆಯಲಾಗದ "
            "ಅಪರಾಧಗಳಲ್ಲಿ ನ್ಯಾಯಾಲಯ ನಿರ್ಧರಿಸುತ್ತದೆ."
        ),
        "context": (
            "CrPC Section 436 — In what cases bail to be taken. "
            "When any person other than a person accused of a "
            "non-bailable offence is arrested or detained without "
            "warrant, such person shall be released on bail."
        ),
        "law":            "CrPC",
        "section":        "436",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── RTI ─────────────────────────────────────────────────
    {
        "question":   "RTI ಅರ್ಜಿ ಹೇಗೆ ಹಾಕಬೇಕು?",
        "answer": (
            "RTI ಅರ್ಜಿ ಸಲ್ಲಿಸಲು:\n"
            "1. ಸಂಬಂಧಿತ ಇಲಾಖೆಯ ಮಾಹಿತಿ ಅಧಿಕಾರಿಗೆ ಬರೆಯಿರಿ\n"
            "2. ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಬರೆಯಿರಿ\n"
            "3. 10 ರೂಪಾಯಿ ಶುಲ್ಕ ಪಾವತಿಸಿ\n"
            "4. 30 ದಿನಗಳಲ್ಲಿ ಉತ್ತರ ಬರಬೇಕು\n"
            "ಉತ್ತರ ಬಾರದಿದ್ದರೆ ಮೊದಲ ಮೇಲ್ಮನವಿ ಮತ್ತು "
            "ನಂತರ ಮಾಹಿತಿ ಆಯೋಗಕ್ಕೆ ದೂರು ನೀಡಬಹುದು."
        ),
        "context": (
            "RTI Act 2005 Section 6 — Request for obtaining information. "
            "A person who desires to obtain any information shall make "
            "a request in writing to the Public Information Officer. "
            "Section 7 — Information to be provided within 30 days."
        ),
        "law":            "RTI",
        "section":        "6",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── Property ────────────────────────────────────────────
    {
        "question":   "ನನ್ನ ಆಸ್ತಿಯನ್ನು ಯಾರೋ ಆಕ್ರಮಿಸಿಕೊಂಡರೆ ಏನು ಮಾಡಬೇಕು?",
        "answer": (
            "ಆಸ್ತಿ ಅತಿಕ್ರಮಣ ಆದಾಗ:\n"
            "1. IPC ಸೆಕ್ಷನ್ 441/447 ಅಡಿಯಲ್ಲಿ ಪೊಲೀಸ್ "
            "ಠಾಣೆಯಲ್ಲಿ FIR ದಾಖಲಿಸಿ\n"
            "2. ತಹಸೀಲ್ದಾರ್ ಕಚೇರಿಯಲ್ಲಿ ದೂರು ನೀಡಿ\n"
            "3. ಸಿವಿಲ್ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ತಾತ್ಕಾಲಿಕ ತಡೆ "
            "ಆದೇಶಕ್ಕಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ\n"
            "4. ಆಸ್ತಿ ದಾಖಲೆಗಳನ್ನು ಸಂಗ್ರಹಿಸಿ ಇಟ್ಟುಕೊಳ್ಳಿ"
        ),
        "context": (
            "IPC Section 441 — Criminal trespass. "
            "IPC Section 447 — Punishment for criminal trespass: "
            "up to 3 months imprisonment or fine up to Rs.500."
        ),
        "law":            "IPC",
        "section":        "441",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── Domestic Violence ────────────────────────────────────
    {
        "question":   "ಕೌಟುಂಬಿಕ ಹಿಂಸೆ ಆದರೆ ಎಲ್ಲಿ ದೂರು ನೀಡಬೇಕು?",
        "answer": (
            "ಕೌಟುಂಬಿಕ ಹಿಂಸೆ ಅನುಭವಿಸಿದ ಮಹಿಳೆ:\n"
            "1. ಮಹಿಳಾ ಸಹಾಯವಾಣಿ 181 ಗೆ ಕರೆ ಮಾಡಿ\n"
            "2. ಹತ್ತಿರದ ಪೊಲೀಸ್ ಠಾಣೆಗೆ ದೂರು ನೀಡಿ\n"
            "3. ರಕ್ಷಣಾ ಅಧಿಕಾರಿ (Protection Officer) ಗೆ ಅರ್ಜಿ ನೀಡಿ\n"
            "4. ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ರಕ್ಷಣಾ ಆದೇಶ "
            "ಕೋರಬಹುದು. PWDVA 2005 ಸೆಕ್ಷನ್ 12 ಅಡಿಯಲ್ಲಿ "
            "ರಕ್ಷಣೆ, ವಾಸಸ್ಥಾನ ಮತ್ತು ಪರಿಹಾರ ಪಡೆಯಬಹುದು."
        ),
        "context": (
            "Protection of Women from Domestic Violence Act 2005. "
            "Section 12 — Application to Magistrate for protection "
            "order, residence order, monetary relief, custody order."
        ),
        "law":            "PWDVA",
        "section":        "12",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── Consumer Rights ──────────────────────────────────────
    {
        "question":   "ಅಂಗಡಿಯಲ್ಲಿ ಕೆಟ್ಟ ವಸ್ತು ಮಾರಿದರೆ ದೂರು ಎಲ್ಲಿ ನೀಡಬೇಕು?",
        "answer": (
            "ಕೆಟ್ಟ ವಸ್ತು ಮಾರಿದರೆ ಗ್ರಾಹಕ ಸಂರಕ್ಷಣಾ ಕಾಯ್ದೆ 2019 "
            "ಅಡಿಯಲ್ಲಿ ದೂರು ನೀಡಬಹುದು:\n"
            "20 ಲಕ್ಷ ರೂ. ವರೆಗೆ — ಜಿಲ್ಲಾ ಗ್ರಾಹಕ ಆಯೋಗ\n"
            "1 ಕೋಟಿ ರೂ. ವರೆಗೆ — ರಾಜ್ಯ ಗ್ರಾಹಕ ಆಯೋಗ\n"
            "1 ಕೋಟಿ ರೂ. ಮೇಲೆ — ರಾಷ್ಟ್ರೀಯ ಗ್ರಾಹಕ ಆಯೋಗ\n"
            "ದೂರು ಸಲ್ಲಿಸಲು ವಕೀಲರ ಅಗತ್ಯವಿಲ್ಲ. "
            "ಖರೀದಿ ರಸೀದಿ ಮತ್ತು ದಾಖಲೆ ಇಟ್ಟುಕೊಳ್ಳಿ."
        ),
        "context": (
            "Consumer Protection Act 2019 Section 35 — "
            "Manner in which complaint shall be made to "
            "District Consumer Disputes Redressal Commission."
        ),
        "law":            "Consumer Protection Act",
        "section":        "35",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── Legal Aid ────────────────────────────────────────────
    {
        "question":   "ಉಚಿತ ವಕೀಲರ ಸಹಾಯ ಹೇಗೆ ಪಡೆಯಬಹುದು?",
        "answer": (
            "ಕರ್ನಾಟಕ ರಾಜ್ಯ ಕಾನೂನು ಸೇವೆಗಳ ಪ್ರಾಧಿಕಾರ (KSLSA) "
            "ಉಚಿತ ಕಾನೂನು ಸಹಾಯ ನೀಡುತ್ತದೆ. "
            "ಈ ಕೆಳಗಿನವರು ಅರ್ಹರು:\n"
            "1. ವಾರ್ಷಿಕ 1 ಲಕ್ಷ ರೂ.ಗಿಂತ ಕಡಿಮೆ ಆದಾಯವಿರುವವರು\n"
            "2. ಮಹಿಳೆಯರು ಮತ್ತು ಮಕ್ಕಳು\n"
            "3. SC/ST ವರ್ಗದವರು\n"
            "4. ಅಂಗವಿಕಲರು\n"
            "ಜಿಲ್ಲಾ ಕಾನೂನು ಸೇವಾ ಪ್ರಾಧಿಕಾರ ಕಚೇರಿಗೆ ಹೋಗಿ."
        ),
        "context": (
            "Legal Services Authorities Act 1987. "
            "Karnataka State Legal Services Authority provides "
            "free legal aid to eligible persons."
        ),
        "law":            "Legal Services Act",
        "section":        "12",
        "intent":         "rights_query",
        "language":       "kn",
    },

    # ── IPC 379 ─────────────────────────────────────────────
    {
        "question":   "ಕಳ್ಳತನ ಮಾಡಿದವರಿಗೆ ಏನು ಶಿಕ್ಷೆ?",
        "answer": (
            "IPC ಸೆಕ್ಷನ್ 379 ಅಡಿಯಲ್ಲಿ ಕಳ್ಳತನ ಮಾಡಿದವರಿಗೆ "
            "ಮೂರು ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ ಅಥವಾ ದಂಡ "
            "ಅಥವಾ ಎರಡನ್ನೂ ವಿಧಿಸಲಾಗುತ್ತದೆ. "
            "ದರೋಡೆ (Robbery) ಆದರೆ ಸೆಕ್ಷನ್ 392 ಅಡಿಯಲ್ಲಿ "
            "10 ವರ್ಷದವರೆಗೆ ಕಠಿಣ ಶಿಕ್ಷೆ ಆಗುತ್ತದೆ."
        ),
        "context": (
            "IPC Section 379 — Punishment for theft: "
            "up to 3 years imprisonment or fine or both. "
            "IPC Section 392 — Punishment for robbery: "
            "up to 10 years rigorous imprisonment + fine."
        ),
        "law":            "IPC",
        "section":        "379",
        "intent":         "penalty_query",
        "language":       "kn",
    },

    # ── IPC 354 ─────────────────────────────────────────────
    {
        "question":   "ಮಹಿಳೆಗೆ ಕಿರುಕುಳ ನೀಡಿದರೆ ಯಾವ ಕಾಯ್ದೆ ಅನ್ವಯಿಸುತ್ತದೆ?",
        "answer": (
            "ಮಹಿಳೆಗೆ ಕಿರುಕುಳ ನೀಡಿದರೆ ಈ ಕಾಯ್ದೆಗಳು ಅನ್ವಯಿಸುತ್ತವೆ:\n"
            "IPC ಸೆಕ್ಷನ್ 354 — ಮಾನಭಂಗ ಉದ್ದೇಶದ ಹಲ್ಲೆ "
            "(2 ವರ್ಷ ಜೈಲು)\n"
            "IPC ಸೆಕ್ಷನ್ 509 — ಮಾನ ಕ್ಷುಣ್ಣ ಮಾಡುವ ಮಾತು "
            "(3 ವರ್ಷ ಜೈಲು)\n"
            "IPC ಸೆಕ್ಷನ್ 354A — ಲೈಂಗಿಕ ಕಿರುಕುಳ "
            "(3 ವರ್ಷ ಜೈಲು)\n"
            "ಪೊಲೀಸ್ ಠಾಣೆಯಲ್ಲಿ FIR ದಾಖಲಿಸಿ ಅಥವಾ "
            "181 ಮಹಿಳಾ ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ."
        ),
        "context": (
            "IPC Section 354 — Assault or criminal force to woman "
            "with intent to outrage her modesty. "
            "IPC Section 509 — Word, gesture or act intended to "
            "insult the modesty of a woman."
        ),
        "law":            "IPC",
        "section":        "354",
        "intent":         "rights_query",
        "language":       "kn",
    },

    # ── Defamation ───────────────────────────────────────────
    {
        "question":   "ಯಾರಾದರೂ ನನ್ನ ಬಗ್ಗೆ ಸುಳ್ಳು ಹರಡಿದರೆ ಏನು ಮಾಡಬೇಕು?",
        "answer": (
            "ಯಾರಾದರೂ ನಿಮ್ಮ ಬಗ್ಗೆ ಸುಳ್ಳು ಹರಡಿ ಮಾನ ಹಾನಿ "
            "ಮಾಡಿದರೆ IPC ಸೆಕ್ಷನ್ 499 ಅಡಿಯಲ್ಲಿ ಮಾನನಷ್ಟ "
            "ದೂರು ದಾಖಲಿಸಬಹುದು. ಇದು ಕ್ರಿಮಿನಲ್ ಅಪರಾಧ ಮತ್ತು "
            "ಎರಡು ವರ್ಷ ಜೈಲು ಶಿಕ್ಷೆ ಆಗಬಹುದು. "
            "ಜೊತೆಗೆ ಸಿವಿಲ್ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ಪರಿಹಾರ ಕೋರಬಹುದು."
        ),
        "context": (
            "IPC Section 499 — Defamation. "
            "IPC Section 500 — Punishment for defamation: "
            "simple imprisonment up to 2 years or fine or both."
        ),
        "law":            "IPC",
        "section":        "499",
        "intent":         "procedure_query",
        "language":       "kn",
    },

    # ── Land encroachment ────────────────────────────────────
    {
        "question":   "ಸರ್ಕಾರಿ ಜಮೀನು ಆಕ್ರಮಿಸಿದರೆ ಏನು ಆಗುತ್ತದೆ?",
        "answer": (
            "ಕರ್ನಾಟಕ ಭೂ ಕಂದಾಯ ಕಾಯ್ದೆ 1964 ಸೆಕ್ಷನ್ 94 "
            "ಅಡಿಯಲ್ಲಿ ಸರ್ಕಾರಿ ಜಮೀನು ಆಕ್ರಮಿಸಿದರೆ "
            "ತಕ್ಷಣ ಒಕ್ಕಲೆಬ್ಬಿಸಲಾಗುತ್ತದೆ ಮತ್ತು ದಂಡ ವಿಧಿಸಲಾಗುತ್ತದೆ. "
            "ಉಪ ಆಯುಕ್ತರು ನೇರ ಕ್ರಮ ತೆಗೆದುಕೊಳ್ಳಬಹುದು. "
            "IPC ಸೆಕ್ಷನ್ 441 ಅಡಿಯಲ್ಲಿ ಅಪರಾಧಿ ಅತಿಕ್ರಮಣ "
            "ಪ್ರಕರಣ ದಾಖಲಾಗಬಹುದು."
        ),
        "context": (
            "Karnataka Land Revenue Act 1964 Section 94 — "
            "Encroachment on government land. "
            "IPC Section 441 — Criminal trespass."
        ),
        "law":            "Karnataka Land Revenue Act",
        "section":        "94",
        "intent":         "penalty_query",
        "language":       "kn",
    },
]


# ── Auto-generate QA from translated sections ────────────────
def generate_from_sections(records: list[dict]) -> list[dict]:
    """
    Auto-generate basic QA pairs from translated legal sections.
    Creates simple section lookup and penalty queries.
    """
    generated = []
    for record in records:
        sec_num  = record.get("section_number", "")
        law_name = record.get("law", "IPC")
        title_en = record.get("title", "")
        text_kn  = record.get("text_kn", record.get("text", ""))

        if not sec_num or not text_kn:
            continue

        # Q1 — Section lookup
        generated.append({
            "question": f"{law_name} ಸೆಕ್ಷನ್ {sec_num} ಏನು?",
            "answer":   text_kn[:400],
            "context":  record.get("text", ""),
            "law":      law_name,
            "section":  sec_num,
            "intent":   "section_lookup",
            "language": "kn",
        })

        # Q2 — Penalty query (if punishment info available)
        punishment_kn = record.get("punishment_kn", "")
        if punishment_kn:
            generated.append({
                "question": (
                    f"{law_name} ಸೆಕ್ಷನ್ {sec_num} "
                    f"ಅಡಿಯಲ್ಲಿ ಶಿಕ್ಷೆ ಏನು?"
                ),
                "answer":   punishment_kn,
                "context":  record.get("text", ""),
                "law":      law_name,
                "section":  sec_num,
                "intent":   "penalty_query",
                "language": "kn",
            })

    return generated


# ── Load translated files ────────────────────────────────────
def load_translated_records() -> list[dict]:
    all_records = []
    files = [
        PROCESSED_DIR / "translated_ipc_kn.json",
        PROCESSED_DIR / "translated_karnataka_kn.json",
        PROCESSED_DIR / "translated_judgments_kn.json",
    ]
    for f in files:
        if f.exists():
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            all_records.extend(data)
            logger.info(f"Loaded {len(data)} records from {f.name}")
        else:
            logger.warning(f"File not found: {f}")
    return all_records


# ── Split into train / val / test ────────────────────────────
def split_data(pairs: list[dict]) -> tuple:
    random.shuffle(pairs)
    total = len(pairs)
    train_end = int(total * TRAIN_RATIO)
    val_end   = train_end + int(total * VAL_RATIO)
    return (
        pairs[:train_end],
        pairs[train_end:val_end],
        pairs[val_end:]
    )


# ── Save JSONL ───────────────────────────────────────────────
def save_jsonl(pairs: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    logger.success(f"Saved {len(pairs)} pairs → {path}")


# ── Main ────────────────────────────────────────────────────
def main():
    logger.info("Generating Kannada legal QA pairs...")

    # Start with manual high-quality pairs
    all_pairs = MANUAL_QA_PAIRS.copy()
    logger.info(f"Manual QA pairs: {len(all_pairs)}")

    # Auto-generate from translated sections
    records   = load_translated_records()
    generated = generate_from_sections(records)
    logger.info(f"Auto-generated QA pairs: {len(generated)}")

    all_pairs.extend(generated)
    logger.info(f"Total QA pairs: {len(all_pairs)}")

    # Split and save
    train, val, test = split_data(all_pairs)

    save_jsonl(train, TRAIN_DIR / "qa_pairs.jsonl")
    save_jsonl(val,   VAL_DIR   / "qa_pairs.jsonl")
    save_jsonl(test,  TEST_DIR  / "qa_pairs.jsonl")

    logger.success(
        f"\n✅ Dataset ready!\n"
        f"   Train : {len(train)} pairs\n"
        f"   Val   : {len(val)}   pairs\n"
        f"   Test  : {len(test)}  pairs\n"
        f"\nNext step: run nlp/preprocessing_pipeline.py"
    )


if __name__ == "__main__":
    main()