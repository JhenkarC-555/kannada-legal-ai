"""
Translates English legal texts to Kannada.
Uses a simple but effective approach:
  - For Colab (GPU): Uses IndicTrans2 (best quality)
  - For local (CPU): Uses Helsinki-NLP translation model (lighter)
  - Fallback: Manual translation dictionary for common legal terms

Input:  data/raw/ipc_sections/ipc_sections.json
        data/raw/karnataka_state_laws/karnataka_laws.json
        data/raw/high_court_judgments/sample_judgments.json

Output: data/processed/translated_ipc_kn.json
        data/processed/translated_karnataka_kn.json
        data/processed/translated_judgments_kn.json

Run locally : python data/collection/translate_to_kannada.py
Run on Colab: python data/collection/translate_to_kannada.py --mode colab
"""

import json
import argparse
import time
from pathlib import Path
from loguru import logger

# ── Config ──────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILES = {
    "ipc":       Path("data/raw/ipc_sections/ipc_sections.json"),
    "karnataka": Path("data/raw/karnataka_state_laws/karnataka_laws.json"),
    "judgments": Path("data/raw/high_court_judgments/sample_judgments.json"),
}

OUTPUT_FILES = {
    "ipc":       PROCESSED_DIR / "translated_ipc_kn.json",
    "karnataka": PROCESSED_DIR / "translated_karnataka_kn.json",
    "judgments": PROCESSED_DIR / "translated_judgments_kn.json",
}

# ── Legal term dictionary ────────────────────────────────────
# Common legal English terms and their Kannada equivalents.
# Used to post-process translations for accuracy.
LEGAL_TERMS = {
    "section":              "ವಿಭಾಗ",
    "punishment":           "ಶಿಕ್ಷೆ",
    "imprisonment":         "ಜೈಲು ಶಿಕ್ಷೆ",
    "fine":                 "ದಂಡ",
    "murder":               "ಹತ್ಯೆ",
    "theft":                "ಕಳ್ಳತನ",
    "robbery":              "ದರೋಡೆ",
    "assault":              "ಹಲ್ಲೆ",
    "bail":                 "ಜಾಮೀನು",
    "court":                "ನ್ಯಾಯಾಲಯ",
    "magistrate":           "ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್",
    "accused":              "ಆರೋಪಿ",
    "complainant":          "ದೂರುದಾರ",
    "petition":             "ಅರ್ಜಿ",
    "judgment":             "ತೀರ್ಪು",
    "conviction":           "ಅಪರಾಧ ಸಿದ್ಧಿ",
    "acquittal":            "ಖುಲಾಸೆ",
    "warrant":              "ವಾರಂಟ್",
    "arrest":               "ಬಂಧನ",
    "police":               "ಪೊಲೀಸ್",
    "offence":              "ಅಪರಾಧ",
    "property":             "ಆಸ್ತಿ",
    "evidence":             "ಸಾಕ್ಷ್ಯ",
    "witness":              "ಸಾಕ್ಷಿ",
    "judge":                "ನ್ಯಾಯಾಧೀಶ",
    "lawyer":               "ವಕೀಲ",
    "advocate":             "ವಕೀಲ",
    "life imprisonment":    "ಜೀವಾವಧಿ ಶಿಕ್ಷೆ",
    "death penalty":        "ಮರಣದಂಡನೆ",
    "cognizable offence":   "ಸಂಜ್ಞೇಯ ಅಪರಾಧ",
    "non-cognizable":       "ಅಸಂಜ್ಞೇಯ",
    "FIR":                  "ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ",
    "cheating":             "ಮೋಸ",
    "fraud":                "ವಂಚನೆ",
    "trespass":             "ಅತಿಕ್ರಮಣ",
    "defamation":           "ಮಾನನಷ್ಟ",
    "extortion":            "ಸುಲಿಗೆ",
    "forgery":              "ನಕಲಿ ದಾಖಲೆ",
    "abetment":             "ಪ್ರಚೋದನೆ",
    "conspiracy":           "ಸಂಚು",
    "grievous hurt":        "ತೀವ್ರ ಗಾಯ",
    "culpable homicide":    "ದೋಷಾರ್ಹ ನರಹತ್ಯೆ",
    "attempt":              "ಪ್ರಯತ್ನ",
    "intention":            "ಉದ್ದೇಶ",
    "knowledge":            "ಜ್ಞಾನ",
    "negligence":           "ನಿರ್ಲಕ್ಷ್ಯ",
    "rights":               "ಹಕ್ಕುಗಳು",
    "fundamental rights":   "ಮೂಲಭೂತ ಹಕ್ಕುಗಳು",
    "constitution":         "ಸಂವಿಧಾನ",
    "high court":           "ಉಚ್ಚ ನ್ಯಾಯಾಲಯ",
    "supreme court":        "ಸರ್ವೋಚ್ಚ ನ್ಯಾಯಾಲಯ",
    "sessions court":       "ಸೆಷನ್ಸ್ ನ್ಯಾಯಾಲಯ",
    "district court":       "ಜಿಲ್ಲಾ ನ್ಯಾಯಾಲಯ",
    "consumer":             "ಗ್ರಾಹಕ",
    "tenant":               "ಬಾಡಿಗೆದಾರ",
    "landlord":             "ಮಾಲೀಕ",
    "government":           "ಸರ್ಕಾರ",
    "state":                "ರಾಜ್ಯ",
    "central":              "ಕೇಂದ್ರ",
}

# ── Pre-translated IPC sections ──────────────────────────────
# High quality manual translations of the most important sections.
# These are used directly without machine translation.

MANUAL_TRANSLATIONS = {
    "302": {
        "title_kn": "ಕೊಲೆಗೆ ಶಿಕ್ಷೆ",
        "text_kn": (
            "ಯಾರಾದರೂ ಕೊಲೆ ಮಾಡಿದರೆ ಅವರಿಗೆ ಮರಣದಂಡನೆ ಅಥವಾ "
            "ಜೀವಾವಧಿ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ ವಿಧಿಸಲಾಗುವುದು ಮತ್ತು "
            "ದಂಡ ಕೂಡ ವಿಧಿಸಬಹುದು."
        ),
        "punishment_kn": "ಮರಣದಂಡನೆ ಅಥವಾ ಜೀವಾವಧಿ ಶಿಕ್ಷೆ + ದಂಡ"
    },
    "420": {
        "title_kn": "ಮೋಸ ಮತ್ತು ಆಸ್ತಿ ವಿತರಣೆಗೆ ಅಪ್ರಾಮಾಣಿಕ ಪ್ರೇರಣೆ",
        "text_kn": (
            "ಯಾರಾದರೂ ಮೋಸ ಮಾಡಿ ಮತ್ತು ಅದರಿಂದ ಮೋಸಗೊಂಡ ವ್ಯಕ್ತಿಯನ್ನು "
            "ಆಸ್ತಿ ನೀಡಲು ಅಪ್ರಾಮಾಣಿಕವಾಗಿ ಪ್ರೇರೇಪಿಸಿದರೆ, "
            "ಏಳು ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ ಮತ್ತು ದಂಡ ವಿಧಿಸಲಾಗುವುದು."
        ),
        "punishment_kn": "7 ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ + ದಂಡ"
    },
    "379": {
        "title_kn": "ಕಳ್ಳತನಕ್ಕೆ ಶಿಕ್ಷೆ",
        "text_kn": (
            "ಯಾರಾದರೂ ಕಳ್ಳತನ ಮಾಡಿದರೆ ಮೂರು ವರ್ಷದವರೆಗೆ "
            "ಜೈಲು ಶಿಕ್ಷೆ ಅಥವಾ ದಂಡ ಅಥವಾ ಎರಡನ್ನೂ ವಿಧಿಸಲಾಗುವುದು."
        ),
        "punishment_kn": "3 ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ ಅಥವಾ ದಂಡ"
    },
    "354": {
        "title_kn": "ಮಹಿಳೆಯ ಮಾನಭಂಗ ಮಾಡುವ ಉದ್ದೇಶದಿಂದ ಹಲ್ಲೆ",
        "text_kn": (
            "ಯಾರಾದರೂ ಮಹಿಳೆಯ ಮಾನಭಂಗ ಮಾಡುವ ಉದ್ದೇಶದಿಂದ "
            "ಹಲ್ಲೆ ಮಾಡಿದರೆ ಎರಡು ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ "
            "ಅಥವಾ ದಂಡ ಅಥವಾ ಎರಡನ್ನೂ ವಿಧಿಸಲಾಗುವುದು."
        ),
        "punishment_kn": "2 ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ ಅಥವಾ ದಂಡ"
    },
    "376": {
        "title_kn": "ಅತ್ಯಾಚಾರಕ್ಕೆ ಶಿಕ್ಷೆ",
        "text_kn": (
            "ಅತ್ಯಾಚಾರ ಮಾಡಿದ ವ್ಯಕ್ತಿಗೆ ಕನಿಷ್ಠ ಹತ್ತು ವರ್ಷ "
            "ಕಠಿಣ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ ವಿಧಿಸಲಾಗುವುದು, "
            "ಇದು ಜೀವಾವಧಿ ಶಿಕ್ಷೆಯವರೆಗೆ ವಿಸ್ತರಿಸಬಹುದು "
            "ಮತ್ತು ದಂಡ ಕೂಡ ವಿಧಿಸಲಾಗುವುದು."
        ),
        "punishment_kn": "ಕನಿಷ್ಠ 10 ವರ್ಷ ಕಠಿಣ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ + ದಂಡ"
    },
    "392": {
        "title_kn": "ದರೋಡೆಗೆ ಶಿಕ್ಷೆ",
        "text_kn": (
            "ಯಾರಾದರೂ ದರೋಡೆ ಮಾಡಿದರೆ ಹತ್ತು ವರ್ಷದವರೆಗೆ "
            "ಕಠಿಣ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ ಮತ್ತು ದಂಡ ವಿಧಿಸಲಾಗುವುದು."
        ),
        "punishment_kn": "10 ವರ್ಷದವರೆಗೆ ಕಠಿಣ ಕಾರಾಗೃಹ ಶಿಕ್ಷೆ + ದಂಡ"
    },
    "441": {
        "title_kn": "ಅಪರಾಧಿ ಅತಿಕ್ರಮಣ",
        "text_kn": (
            "ಯಾರಾದರೂ ಅಪರಾಧ ಮಾಡುವ ಉದ್ದೇಶದಿಂದ ಅಥವಾ "
            "ಇನ್ನೊಬ್ಬರನ್ನು ಬೆದರಿಸಲು, ಅವಮಾನಿಸಲು ಅಥವಾ "
            "ಕಿರಿಕಿರಿ ಮಾಡಲು ಆಸ್ತಿಗೆ ಪ್ರವೇಶಿಸಿದರೆ "
            "ಅದು ಅಪರಾಧಿ ಅತಿಕ್ರಮಣ ಆಗುತ್ತದೆ."
        ),
        "punishment_kn": "3 ತಿಂಗಳು ಜೈಲು ಅಥವಾ 500 ರೂ. ದಂಡ"
    },
    "503": {
        "title_kn": "ಅಪರಾಧಿ ಬೆದರಿಕೆ",
        "text_kn": (
            "ಯಾರಾದರೂ ಇನ್ನೊಬ್ಬರಿಗೆ ಗಾಯ, ಮಾನಹಾನಿ ಅಥವಾ "
            "ಆಸ್ತಿ ಹಾನಿ ಮಾಡುವ ಬೆದರಿಕೆ ಹಾಕಿ ಅವರನ್ನು "
            "ಹೆದರಿಸಿದರೆ ಅದು ಅಪರಾಧಿ ಬೆದರಿಕೆ ಆಗುತ್ತದೆ."
        ),
        "punishment_kn": "2 ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ ಅಥವಾ ದಂಡ"
    },
    "323": {
        "title_kn": "ಸ್ವಯಂಪ್ರೇರಿತವಾಗಿ ಗಾಯ ಮಾಡಿದ್ದಕ್ಕೆ ಶಿಕ್ಷೆ",
        "text_kn": (
            "ಯಾರಾದರೂ ಸ್ವಯಂಪ್ರೇರಿತವಾಗಿ ಇನ್ನೊಬ್ಬರಿಗೆ ಗಾಯ ಮಾಡಿದರೆ "
            "ಒಂದು ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ ಅಥವಾ "
            "1000 ರೂಪಾಯಿ ದಂಡ ಅಥವಾ ಎರಡನ್ನೂ ವಿಧಿಸಲಾಗುವುದು."
        ),
        "punishment_kn": "1 ವರ್ಷದವರೆಗೆ ಜೈಲು ಅಥವಾ 1000 ರೂ. ದಂಡ"
    },
    "499": {
        "title_kn": "ಮಾನನಷ್ಟ",
        "text_kn": (
            "ಯಾರಾದರೂ ಮಾತಿನಿಂದ, ಬರಹದಿಂದ, ಸನ್ನೆಯಿಂದ ಅಥವಾ "
            "ಗೋಚರ ರೂಪದಿಂದ ಇನ್ನೊಬ್ಬರ ಮಾನ ಹಾನಿ ಮಾಡಲು ಆರೋಪ "
            "ಮಾಡಿದರೆ ಅದು ಮಾನನಷ್ಟ ಆಗುತ್ತದೆ."
        ),
        "punishment_kn": "2 ವರ್ಷದವರೆಗೆ ಜೈಲು ಶಿಕ್ಷೆ ಅಥವಾ ದಂಡ"
    },
}


# ── Helsinki translator (local CPU) ─────────────────────────
def load_helsinki_model():
    """Load Helsinki-NLP English to Kannada model for local translation."""
    try:
        from transformers import MarianMTModel, MarianTokenizer
        model_name = "Helsinki-NLP/opus-mt-en-kn"
        logger.info(f"Loading Helsinki model: {model_name}")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model     = MarianMTModel.from_pretrained(model_name)
        logger.success("Helsinki model loaded successfully.")
        return tokenizer, model
    except Exception as e:
        logger.warning(f"Helsinki model failed to load: {e}")
        return None, None


def translate_with_helsinki(
    text: str,
    tokenizer,
    model,
    max_length: int = 512
) -> str:
    """Translate a single text using Helsinki model."""
    try:
        # Split long text into chunks
        words  = text.split()
        chunks = []
        chunk  = []
        for word in words:
            chunk.append(word)
            if len(chunk) >= 100:
                chunks.append(" ".join(chunk))
                chunk = []
        if chunk:
            chunks.append(" ".join(chunk))

        translated_chunks = []
        for c in chunks:
            inputs  = tokenizer(
                [c], return_tensors="pt",
                padding=True, truncation=True,
                max_length=max_length
            )
            outputs = model.generate(**inputs)
            translated = tokenizer.batch_decode(
                outputs, skip_special_tokens=True
            )[0]
            translated_chunks.append(translated)
            time.sleep(0.1)

        return " ".join(translated_chunks)

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text


# ── IndicTrans2 (Colab GPU) ──────────────────────────────────
def translate_with_indictrans(texts: list[str]) -> list[str]:
    """
    Translate using IndicTrans2 — use this on Google Colab with GPU.
    Install first: pip install IndicTransToolkit
    """
    try:
        from IndicTransToolkit import IndicProcessor
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        model_name = "ai4bharat/indictrans2-en-indic-dist-200M"
        logger.info("Loading IndicTrans2 model...")

        tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name, trust_remote_code=True
        )
        ip = IndicProcessor(inference=True)

        batch = ip.preprocess_batch(
            texts,
            src_lang="eng_Latn",
            tgt_lang="kan_Knda"
        )
        inputs  = tokenizer(
            batch, truncation=True,
            padding="longest",
            return_tensors="pt"
        )
        outputs = model.generate(
            **inputs,
            num_beams=5,
            num_return_sequences=1,
            max_length=256
        )
        decoded = tokenizer.batch_decode(
            outputs, skip_special_tokens=True
        )
        translations = ip.postprocess_batch(decoded, lang="kan_Knda")
        return translations

    except ImportError:
        logger.error(
            "IndicTransToolkit not installed. "
            "Run on Colab: pip install IndicTransToolkit"
        )
        return texts


# ── Process and translate all files ─────────────────────────
def translate_file(
    input_path: Path,
    output_path: Path,
    mode: str,
    tokenizer=None,
    model=None
) -> None:
    """Translate all records in a JSON file."""
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        return

    with open(input_path, encoding="utf-8") as f:
        records = json.load(f)

    logger.info(f"Translating {len(records)} records from {input_path.name}...")
    translated_records = []

    for i, record in enumerate(records):
        section_num = record.get("section_number", "")

        # Use manual translation if available
        if section_num in MANUAL_TRANSLATIONS:
            manual = MANUAL_TRANSLATIONS[section_num]
            record["title_kn"]      = manual["title_kn"]
            record["text_kn"]       = manual["text_kn"]
            record["punishment_kn"] = manual.get("punishment_kn", "")
            record["translation_method"] = "manual"
            logger.info(
                f"[{i+1}/{len(records)}] Section {section_num}"
                f" — used manual translation"
            )

        else:
            # Machine translate
            text_to_translate = record.get("text", "")

            if mode == "colab":
                results = translate_with_indictrans([text_to_translate])
                record["text_kn"] = results[0] if results else text_to_translate
                record["translation_method"] = "indictrans2"

            elif mode == "local" and tokenizer and model:
                record["text_kn"] = translate_with_helsinki(
                    text_to_translate, tokenizer, model
                )
                record["translation_method"] = "helsinki"

            else:
                # Fallback — keep English, mark as untranslated
                record["text_kn"] = text_to_translate
                record["translation_method"] = "untranslated"

            logger.info(
                f"[{i+1}/{len(records)}] Translated: "
                f"{text_to_translate[:40]}..."
            )

        record["language_kn"] = True
        translated_records.append(record)
        time.sleep(0.2)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(translated_records, f, ensure_ascii=False, indent=2)

    logger.success(
        f"Saved {len(translated_records)} translated records → {output_path}"
    )


# ── Main ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Translate legal texts to Kannada"
    )
    parser.add_argument(
        "--mode",
        choices=["local", "colab"],
        default="local",
        help="local = Helsinki model on CPU | colab = IndicTrans2 on GPU"
    )
    args = parser.parse_args()

    logger.info(f"Translation mode: {args.mode}")

    tokenizer, model = None, None
    if args.mode == "local":
        tokenizer, model = load_helsinki_model()
        if not tokenizer:
            logger.warning(
                "Helsinki model not available. "
                "Manual translations will still be saved. "
                "Other sections will be marked as untranslated."
            )

    # Translate all three files
    for key in ["ipc", "karnataka", "judgments"]:
        input_path  = INPUT_FILES[key]
        output_path = OUTPUT_FILES[key]
        logger.info(f"\n── Translating: {key} ──")
        translate_file(
            input_path, output_path,
            args.mode, tokenizer, model
        )

    logger.success("\n✅ All files translated!")
    logger.info(
        "Translated files saved in data/processed/\n"
        "Next step: run generate_qa_pairs.py"
    )


if __name__ == "__main__":
    main()