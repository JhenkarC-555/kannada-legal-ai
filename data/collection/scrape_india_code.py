"""
Scrapes IPC sections from indiacode.nic.in
Output: data/raw/ipc_sections/ipc_sections.json

Run: python data/collection/scrape_india_code.py
"""

import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from loguru import logger

# ── Config ──────────────────────────────────────────────────
OUTPUT_DIR  = Path("data/raw/ipc_sections")
OUTPUT_FILE = OUTPUT_DIR / "ipc_sections.json"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL    = "https://indiacode.nic.in"
IPC_URL     = "https://indiacode.nic.in/handle/123456789/2263/simple-search"

HEADERS     = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Hardcoded IPC sections (most important ones) ─────────────
# These are reliable fallback data in case scraping fails.
# You can expand this list manually.

IPC_SECTIONS = [
    {
        "section_number": "1",
        "title": "Title and extent of operation of the Code",
        "text": (
            "This Act shall be called the Indian Penal Code, and shall "
            "extend to the whole of India except the State of Jammu and Kashmir."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "34",
        "title": "Acts done by several persons in furtherance of common intention",
        "text": (
            "When a criminal act is done by several persons in furtherance "
            "of the common intention of all, each of such persons is liable "
            "for that act in the same manner as if it were done by him alone."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "141",
        "title": "Unlawful assembly",
        "text": (
            "An assembly of five or more persons is designated an unlawful "
            "assembly, if the common object of the persons composing that "
            "assembly is to overawe by criminal force, or show of criminal "
            "force, the Central or any State Government or Parliament or "
            "the Legislature of any State, or any public servant in the "
            "exercise of the lawful power of such public servant."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "299",
        "title": "Culpable homicide",
        "text": (
            "Whoever causes death by doing an act with the intention of "
            "causing death, or with the intention of causing such bodily "
            "injury as is likely to cause death, or with the knowledge that "
            "he is likely by such act to cause death, commits the offence "
            "of culpable homicide."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "300",
        "title": "Murder",
        "text": (
            "Except in the cases hereinafter excepted, culpable homicide is "
            "murder, if the act by which the death is caused is done with the "
            "intention of causing death, or if it is done with the intention "
            "of causing such bodily injury as the offender knows to be likely "
            "to cause the death of the person to whom the harm is caused."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "302",
        "title": "Punishment for murder",
        "text": (
            "Whoever commits murder shall be punished with death, or "
            "imprisonment for life, and shall also be liable to fine."
        ),
        "law": "IPC",
        "punishment": "Death or imprisonment for life + fine",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "304",
        "title": "Punishment for culpable homicide not amounting to murder",
        "text": (
            "Whoever commits culpable homicide not amounting to murder shall "
            "be punished with imprisonment for life, or imprisonment of either "
            "description for a term which may extend to ten years, and shall "
            "also be liable to fine."
        ),
        "law": "IPC",
        "punishment": "Imprisonment for life or up to 10 years + fine",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "307",
        "title": "Attempt to murder",
        "text": (
            "Whoever does any act with such intention or knowledge, and under "
            "such circumstances that, if he by that act caused death, he would "
            "be guilty of murder, shall be punished with imprisonment of either "
            "description for a term which may extend to ten years, and shall "
            "also be liable to fine."
        ),
        "law": "IPC",
        "punishment": "Up to 10 years imprisonment + fine",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "320",
        "title": "Grievous hurt",
        "text": (
            "The following kinds of hurt only are designated as grievous: "
            "Emasculation; Permanent privation of the sight of either eye; "
            "Permanent privation of the hearing of either ear; Privation of "
            "any member or joint; Destruction or permanent impairing of the "
            "powers of any member or joint; Permanent disfiguration of the "
            "head or face; Fracture or dislocation of a bone or tooth; "
            "Any hurt which endangers life or which causes the sufferer to "
            "be during the space of twenty days in severe bodily pain, or "
            "unable to follow his ordinary pursuits."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "323",
        "title": "Punishment for voluntarily causing hurt",
        "text": (
            "Whoever, except in the case provided for by section 334, "
            "voluntarily causes hurt, shall be punished with imprisonment "
            "of either description for a term which may extend to one year, "
            "or with fine which may extend to one thousand rupees, or with both."
        ),
        "law": "IPC",
        "punishment": "Up to 1 year imprisonment or fine up to Rs.1000 or both",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "354",
        "title": "Assault or criminal force to woman with intent to outrage her modesty",
        "text": (
            "Whoever assaults or uses criminal force to any woman, intending "
            "to outrage or knowing it to be likely that he will thereby outrage "
            "her modesty, shall be punished with imprisonment of either "
            "description for a term which may extend to two years, or with "
            "fine, or with both."
        ),
        "law": "IPC",
        "punishment": "Up to 2 years imprisonment or fine or both",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "376",
        "title": "Punishment for rape",
        "text": (
            "Whoever commits rape shall be punished with rigorous imprisonment "
            "of either description for a term which shall not be less than ten "
            "years, but which may extend to imprisonment for life, and shall "
            "also be liable to fine."
        ),
        "law": "IPC",
        "punishment": "Minimum 10 years rigorous imprisonment up to life + fine",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "379",
        "title": "Punishment for theft",
        "text": (
            "Whoever commits theft shall be punished with imprisonment of "
            "either description for a term which may extend to three years, "
            "or with fine, or with both."
        ),
        "law": "IPC",
        "punishment": "Up to 3 years imprisonment or fine or both",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "383",
        "title": "Extortion",
        "text": (
            "Whoever intentionally puts any person in fear of any injury to "
            "that person, or to any other, and thereby dishonestly induces "
            "the person so put in fear to deliver to any person any property "
            "or valuable security or anything signed or sealed which may be "
            "converted into a valuable security, commits extortion."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "390",
        "title": "Robbery",
        "text": (
            "In all robbery there is either theft or extortion. Theft is "
            "robbery if, in order to the committing of the theft, or in "
            "committing the theft, or in carrying away or attempting to carry "
            "away property obtained by the theft, the offender, for that end, "
            "voluntarily causes or attempts to cause to any person death or "
            "hurt or wrongful restraint, or fear of instant death or of "
            "instant hurt, or of instant wrongful restraint."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "392",
        "title": "Punishment for robbery",
        "text": (
            "Whoever commits robbery shall be punished with rigorous "
            "imprisonment for a term which may extend to ten years, and "
            "shall also be liable to fine; and, if the robbery be committed "
            "on the highway between sunset and sunrise, the imprisonment "
            "may be extended to fourteen years."
        ),
        "law": "IPC",
        "punishment": "Up to 10 years rigorous imprisonment + fine",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "395",
        "title": "Punishment for dacoity",
        "text": (
            "Whoever commits dacoity shall be punished with imprisonment "
            "for life, or with rigorous imprisonment for a term which may "
            "extend to ten years, and shall also be liable to fine."
        ),
        "law": "IPC",
        "punishment": "Life imprisonment or up to 10 years + fine",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "406",
        "title": "Punishment for criminal breach of trust",
        "text": (
            "Whoever commits criminal breach of trust shall be punished "
            "with imprisonment of either description for a term which may "
            "extend to three years, or with fine, or with both."
        ),
        "law": "IPC",
        "punishment": "Up to 3 years imprisonment or fine or both",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "415",
        "title": "Cheating",
        "text": (
            "Whoever, by deceiving any person, fraudulently or dishonestly "
            "induces the person so deceived to deliver any property to any "
            "person, or to consent that any person shall retain any property, "
            "or intentionally induces the person so deceived to do or omit "
            "to do anything which he would not do or omit if he were not "
            "so deceived, and which act or omission causes or is likely to "
            "cause damage or harm to that person in body, mind, reputation "
            "or property, is said to cheat."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "420",
        "title": "Cheating and dishonestly inducing delivery of property",
        "text": (
            "Whoever cheats and thereby dishonestly induces the person "
            "deceived to deliver any property to any person, or to make, "
            "alter or destroy the whole or any part of a valuable security, "
            "or anything which is signed or sealed, and which is capable of "
            "being converted into a valuable security, shall be punished "
            "with imprisonment of either description for a term which may "
            "extend to seven years, and shall also be liable to fine."
        ),
        "law": "IPC",
        "punishment": "Up to 7 years imprisonment + fine",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "426",
        "title": "Punishment for mischief",
        "text": (
            "Whoever commits mischief shall be punished with imprisonment "
            "of either description for a term which may extend to three "
            "months, or with fine, or with both."
        ),
        "law": "IPC",
        "punishment": "Up to 3 months imprisonment or fine or both",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "441",
        "title": "Criminal trespass",
        "text": (
            "Whoever enters into or upon property in the possession of "
            "another with intent to commit an offence or to intimidate, "
            "insult or annoy any person in possession of such property, "
            "or having lawfully entered into or upon such property, "
            "unlawfully remains there with intent thereby to intimidate, "
            "insult or annoy any person, or with intent to commit an "
            "offence, is said to commit criminal trespass."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "447",
        "title": "Punishment for criminal trespass",
        "text": (
            "Whoever commits criminal trespass shall be punished with "
            "imprisonment of either description for a term which may "
            "extend to three months, or with fine which may extend to "
            "five hundred rupees, or with both."
        ),
        "law": "IPC",
        "punishment": "Up to 3 months imprisonment or fine up to Rs.500 or both",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "463",
        "title": "Forgery",
        "text": (
            "Whoever makes any false document or false electronic record "
            "or part of a document or electronic record, with intent to "
            "cause damage or injury, to the public or to any person, or "
            "to support any claim or title, or to cause any person to "
            "part with property, or to enter into any express or implied "
            "contract, or with intent to commit fraud or that fraud may "
            "be committed, commits forgery."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "499",
        "title": "Defamation",
        "text": (
            "Whoever, by words either spoken or intended to be read, or "
            "by signs or by visible representations, makes or publishes "
            "any imputation concerning any person intending to harm, or "
            "knowing or having reason to believe that such imputation will "
            "harm, the reputation of such person, is said, except in the "
            "cases hereinafter excepted, to defame that person."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "503",
        "title": "Criminal intimidation",
        "text": (
            "Whoever threatens another with any injury to his person, "
            "reputation or property, or to the person or reputation of "
            "any one in whom that person is interested, with intent to "
            "cause alarm to that person, or to cause that person to do "
            "any act which he is not legally bound to do, or to omit "
            "to do any act which that person is legally entitled to do, "
            "as the means of avoiding the execution of such threat, "
            "commits criminal intimidation."
        ),
        "law": "IPC",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "506",
        "title": "Punishment for criminal intimidation",
        "text": (
            "Whoever commits the offence of criminal intimidation shall "
            "be punished with imprisonment of either description for a "
            "term which may extend to two years, or with fine, or with both."
        ),
        "law": "IPC",
        "punishment": "Up to 2 years imprisonment or fine or both",
        "source": "indiacode.nic.in"
    },
    {
        "section_number": "509",
        "title": "Word, gesture or act intended to insult the modesty of a woman",
        "text": (
            "Whoever, intending to insult the modesty of any woman, "
            "utters any word, makes any sound or gesture, or exhibits "
            "any object, intending that such word or sound shall be "
            "heard, or that such gesture or object shall be seen, by "
            "such woman, or intrudes upon the privacy of such woman, "
            "shall be punished with simple imprisonment for a term "
            "which may extend to three years, and also with fine."
        ),
        "law": "IPC",
        "punishment": "Up to 3 years simple imprisonment + fine",
        "source": "indiacode.nic.in"
    },
]


# ── Live scraper (attempts to get more sections from web) ───
def try_scrape_live() -> list[dict]:
    """
    Attempts to scrape additional sections from indiacode.nic.in
    Falls back to empty list if site is unavailable.
    """
    scraped = []
    try:
        logger.info("Attempting live scrape from indiacode.nic.in ...")
        response = requests.get(
            IPC_URL,
            headers=HEADERS,
            timeout=15
        )
        if response.status_code != 200:
            logger.warning(f"Site returned status {response.status_code}. Using hardcoded data.")
            return []

        soup = BeautifulSoup(response.text, "lxml")
        # NOTE: Site structure may change — update selectors if needed
        rows = soup.select("table tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                scraped.append({
                    "section_number": cols[0].get_text(strip=True),
                    "title":          cols[1].get_text(strip=True),
                    "text":           cols[1].get_text(strip=True),
                    "law":            "IPC",
                    "source":         "indiacode.nic.in (live)"
                })
        logger.info(f"Live scrape got {len(scraped)} additional sections.")
        time.sleep(2)  # Be polite to the server

    except Exception as e:
        logger.warning(f"Live scrape failed: {e}. Using hardcoded data only.")

    return scraped


# ── Main ────────────────────────────────────────────────────
def main():
    logger.info("Starting IPC data collection...")

    # Start with hardcoded reliable data
    all_sections = IPC_SECTIONS.copy()
    logger.info(f"Loaded {len(all_sections)} hardcoded IPC sections.")

    # Try to get more from live site
    live_data = try_scrape_live()
    if live_data:
        # Avoid duplicates by section number
        existing_nums = {s["section_number"] for s in all_sections}
        new_sections  = [s for s in live_data if s["section_number"] not in existing_nums]
        all_sections.extend(new_sections)
        logger.info(f"Added {len(new_sections)} new sections from live scrape.")

    # Save to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_sections, f, ensure_ascii=False, indent=2)

    logger.success(f"Saved {len(all_sections)} IPC sections → {OUTPUT_FILE}")
    logger.info("Next step: run translate_to_kannada.py to translate these sections.")


if __name__ == "__main__":
    main()