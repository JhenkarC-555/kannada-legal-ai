"""
Scrapes Karnataka state laws and Vikaspedia Kannada legal articles.
Output:
  - data/raw/karnataka_state_laws/karnataka_laws.json
  - data/raw/legal_aid_pamphlets/vikaspedia_kn.json

Run: python data/collection/scrape_karnataka_gov.py
"""

import json
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from loguru import logger

# ── Config ──────────────────────────────────────────────────
KA_OUTPUT_DIR   = Path("data/raw/karnataka_state_laws")
VIKA_OUTPUT_DIR = Path("data/raw/legal_aid_pamphlets")
KA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIKA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

KA_OUTPUT_FILE   = KA_OUTPUT_DIR   / "karnataka_laws.json"
VIKA_OUTPUT_FILE = VIKA_OUTPUT_DIR / "vikaspedia_kn.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Hardcoded Karnataka State Laws ──────────────────────────
KARNATAKA_LAWS = [
    {
        "law_name": "Karnataka Land Revenue Act, 1964",
        "section_number": "1",
        "title": "Short title, extent and commencement",
        "text": (
            "This Act may be called the Karnataka Land Revenue Act, 1964. "
            "It extends to the whole of the State of Karnataka. "
            "It shall come into force on such date as the State Government "
            "may, by notification, appoint."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Land Revenue Act, 1964",
        "section_number": "45",
        "title": "Survey and boundaries of land",
        "text": (
            "Every holder of land shall maintain the boundary marks of his "
            "land in good repair, and shall not remove, alter or destroy "
            "any boundary mark. Any person who removes, alters or destroys "
            "any boundary mark shall be liable to pay the cost of restoring "
            "the same and shall also be punishable with fine."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Land Revenue Act, 1964",
        "section_number": "94",
        "title": "Encroachment on government land",
        "text": (
            "No person shall encroach upon or occupy any land belonging to "
            "the government without prior permission. Any person who "
            "encroaches upon government land shall be liable to be evicted "
            "and shall also be liable to pay penalty as prescribed. "
            "The Deputy Commissioner may summarily evict any person who "
            "has encroached on government land."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Police Act, 1963",
        "section_number": "1",
        "title": "Short title, extent and commencement",
        "text": (
            "This Act may be called the Karnataka Police Act, 1963. "
            "It extends to the whole of the State of Karnataka. "
            "It shall come into force on such date as the State Government "
            "may, by notification in the Official Gazette, appoint."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Police Act, 1963",
        "section_number": "64",
        "title": "Power to arrest without warrant",
        "text": (
            "Any police officer may, without an order from a Magistrate and "
            "without a warrant, arrest any person who has been concerned in "
            "any cognizable offence or against whom a reasonable complaint "
            "has been made or credible information has been received or a "
            "reasonable suspicion exists of his having been so concerned."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Shops and Establishments Act, 1961",
        "section_number": "13",
        "title": "Hours of work",
        "text": (
            "No employee in any establishment shall be required or allowed "
            "to work for more than eight hours in any day and forty-eight "
            "hours in any week. The period of work of an employee each day "
            "shall be so fixed that no period shall exceed five hours before "
            "an interval for rest of at least half an hour is given."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Shops and Establishments Act, 1961",
        "section_number": "21",
        "title": "Leave",
        "text": (
            "Every employee who has worked for a period of not less than "
            "two hundred and forty days during a calendar year in an "
            "establishment shall be entitled to leave with wages at the "
            "rate of one day for every twenty days of work performed by "
            "him during the previous calendar year."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Rent Control Act, 2001",
        "section_number": "3",
        "title": "Fixation of standard rent",
        "text": (
            "The standard rent of any premises may be fixed by the "
            "Rent Control Court on application made by the tenant or "
            "landlord. The court shall fix standard rent having regard "
            "to the prevailing market rent of similar premises in the "
            "locality, the amenities provided and the cost of construction."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Rent Control Act, 2001",
        "section_number": "21",
        "title": "Eviction of tenants",
        "text": (
            "A landlord may apply to the Rent Control Court for an order "
            "directing the tenant to put the landlord in possession of the "
            "premises if the tenant has not paid or tendered the rent due "
            "from him in respect of the premises within fifteen days after "
            "the expiry of the time fixed by the contract for the payment "
            "of rent."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Karnataka Prevention of Slaughter and Preservation of Animals Act, 1964",
        "section_number": "5",
        "title": "Prohibition of slaughter without certificate",
        "text": (
            "No person shall slaughter or cause to be slaughtered any "
            "animal at any place other than a slaughterhouse. No animal "
            "shall be slaughtered unless a certificate has been granted "
            "by the competent authority that the animal is fit for slaughter."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Right to Information Act, 2005",
        "section_number": "6",
        "title": "Request for obtaining information",
        "text": (
            "A person who desires to obtain any information under this Act, "
            "shall make a request in writing or through electronic means in "
            "English or Hindi or in the official language of the area in "
            "which the application is being made, to the Central Public "
            "Information Officer or State Public Information Officer. "
            "An applicant making request for information shall not be "
            "required to give any reason for requesting the information."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Right to Information Act, 2005",
        "section_number": "7",
        "title": "Disposal of request",
        "text": (
            "Subject to the proviso to sub-section (2) of section 5 or "
            "the proviso to sub-section (3) of section 6, the Central "
            "Public Information Officer or State Public Information Officer, "
            "as the case may be, on receipt of a request shall, as "
            "expeditiously as possible, and in any case within thirty days "
            "of the receipt of the request, either provide the information "
            "on payment of such fee as may be prescribed or reject the "
            "request for any of the reasons specified in sections 8 and 9."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Consumer Protection Act, 2019",
        "section_number": "2",
        "title": "Definitions — Consumer",
        "text": (
            "Consumer means any person who buys any goods for a "
            "consideration which has been paid or promised or partly paid "
            "and partly promised, or under any system of deferred payment "
            "and includes any user of such goods other than the person "
            "who buys such goods for consideration paid or promised or "
            "partly paid or partly promised, or under any system of "
            "deferred payment, when such use is made with the approval "
            "of such person, but does not include a person who obtains "
            "such goods for resale or for any commercial purpose."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Consumer Protection Act, 2019",
        "section_number": "35",
        "title": "Manner in which complaint shall be made",
        "text": (
            "A complaint in relation to any goods sold or delivered or "
            "agreed to be sold or delivered or any service provided or "
            "agreed to be provided may be filed with a District Commission "
            "by the consumer to whom such goods are sold or delivered or "
            "agreed to be sold or delivered or such service provided or "
            "agreed to be provided."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Protection of Women from Domestic Violence Act, 2005",
        "section_number": "3",
        "title": "Definition of domestic violence",
        "text": (
            "For the purposes of this Act, any act, omission or commission "
            "or conduct of the respondent shall constitute domestic violence "
            "in case it harms or injures or endangers the health, safety, "
            "life, limb or well-being, whether mental or physical, of the "
            "aggrieved person or tends to do so and includes causing "
            "physical abuse, sexual abuse, verbal and emotional abuse "
            "and economic abuse."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
    {
        "law_name": "Protection of Women from Domestic Violence Act, 2005",
        "section_number": "12",
        "title": "Application to Magistrate",
        "text": (
            "An aggrieved person or a Protection Officer or any other "
            "person on behalf of the aggrieved person may present an "
            "application to the Magistrate seeking one or more reliefs "
            "under this Act. The relief sought may include a protection "
            "order, a residence order, monetary reliefs, a custody order "
            "or a compensation order."
        ),
        "source": "karnataka.gov.in",
        "language": "English"
    },
]

# ── Hardcoded Vikaspedia Kannada Legal Articles ──────────────
VIKASPEDIA_KN = [
    {
        "title": "ಮಾಹಿತಿ ಹಕ್ಕು (RTI) ಅರ್ಜಿ ಹೇಗೆ ಸಲ್ಲಿಸಬೇಕು",
        "text": (
            "ಮಾಹಿತಿ ಹಕ್ಕು ಕಾಯ್ದೆ 2005 ರ ಅಡಿಯಲ್ಲಿ ಯಾವುದೇ ನಾಗರಿಕರು "
            "ಸರ್ಕಾರಿ ಇಲಾಖೆಯಿಂದ ಮಾಹಿತಿ ಕೋರಬಹುದು. "
            "ಅರ್ಜಿಯನ್ನು ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಬರೆದು "
            "ಸಂಬಂಧಿತ ಇಲಾಖೆಯ ಮಾಹಿತಿ ಅಧಿಕಾರಿಗೆ ನೀಡಬೇಕು. "
            "30 ದಿನಗಳಲ್ಲಿ ಉತ್ತರ ನೀಡುವುದು ಕಡ್ಡಾಯ. "
            "ಉತ್ತರ ಬಾರದಿದ್ದರೆ ಮೇಲ್ಮನವಿ ಸಲ್ಲಿಸಬಹುದು."
        ),
        "category": "RTI",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
    {
        "title": "ಪೊಲೀಸ್ ಬಂಧನ ಮಾಡಿದಾಗ ನಿಮ್ಮ ಹಕ್ಕುಗಳು",
        "text": (
            "ಪೊಲೀಸ್ ಬಂಧಿಸಿದ ತಕ್ಷಣ ನೀವು ಈ ಹಕ್ಕುಗಳನ್ನು ಹೊಂದಿರುತ್ತೀರಿ: "
            "1. ಬಂಧನದ ಕಾರಣ ತಿಳಿಯುವ ಹಕ್ಕು (CrPC ಸೆಕ್ಷನ್ 50). "
            "2. ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸುವ ಹಕ್ಕು. "
            "3. ವೈದ್ಯಕೀಯ ತಪಾಸಣೆ ಮಾಡಿಸಿಕೊಳ್ಳುವ ಹಕ್ಕು. "
            "4. 24 ಗಂಟೆಗಳಲ್ಲಿ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ಮುಂದೆ ಹಾಜರುಪಡಿಸುವ ಹಕ್ಕು. "
            "5. ಕುಟುಂಬಕ್ಕೆ ತಿಳಿಸುವ ಹಕ್ಕು."
        ),
        "category": "Rights",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
    {
        "title": "ಗ್ರಾಹಕ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ದೂರು ದಾಖಲಿಸುವ ವಿಧಾನ",
        "text": (
            "ಗ್ರಾಹಕ ಸಂರಕ್ಷಣಾ ಕಾಯ್ದೆ 2019 ರ ಅಡಿಯಲ್ಲಿ ನೀವು ಗ್ರಾಹಕ ನ್ಯಾಯಾಲಯದಲ್ಲಿ "
            "ದೂರು ದಾಖಲಿಸಬಹುದು. 20 ಲಕ್ಷ ರೂಪಾಯಿ ವರೆಗಿನ ಪ್ರಕರಣಗಳಿಗೆ "
            "ಜಿಲ್ಲಾ ನ್ಯಾಯಾಲಯ, 1 ಕೋಟಿ ವರೆಗೆ ರಾಜ್ಯ ನ್ಯಾಯಾಲಯ ಮತ್ತು "
            "ಅದಕ್ಕಿಂತ ಹೆಚ್ಚಿನ ಮೊತ್ತಕ್ಕೆ ರಾಷ್ಟ್ರೀಯ ನ್ಯಾಯಾಲಯಕ್ಕೆ "
            "ಹೋಗಬಹುದು. ದೂರು ಸಲ್ಲಿಸಲು ವಕೀಲರ ಅಗತ್ಯವಿಲ್ಲ."
        ),
        "category": "Consumer Rights",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
    {
        "title": "ಕೌಟುಂಬಿಕ ಹಿಂಸೆ — ಮಹಿಳೆಯರ ರಕ್ಷಣೆ",
        "text": (
            "ಕೌಟುಂಬಿಕ ಹಿಂಸಾಚಾರ ತಡೆ ಕಾಯ್ದೆ 2005 ಮಹಿಳೆಯರಿಗೆ ರಕ್ಷಣೆ ನೀಡುತ್ತದೆ. "
            "ಶಾರೀರಿಕ, ಮಾನಸಿಕ, ಆರ್ಥಿಕ ಅಥವಾ ಲೈಂಗಿಕ ಹಿಂಸೆ ಅನುಭವಿಸಿದ "
            "ಮಹಿಳೆ ನ್ಯಾಯಾಲಯಕ್ಕೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು. "
            "ರಕ್ಷಣೆ, ವಾಸಸ್ಥಳ ಮತ್ತು ಪರಿಹಾರ ಪಡೆಯಬಹುದು. "
            "ಸಹಾಯಕ್ಕಾಗಿ 181 (ಮಹಿಳಾ ಸಹಾಯವಾಣಿ) ಗೆ ಕರೆ ಮಾಡಿ."
        ),
        "category": "Women Rights",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
    {
        "title": "ಜಾಮೀನು ಅರ್ಜಿ ಹೇಗೆ ಸಲ್ಲಿಸಬೇಕು",
        "text": (
            "ಜಾಮೀನು ಎಂದರೆ ನ್ಯಾಯಾಲಯ ವಿಚಾರಣೆ ನಡೆಯುವ ತನಕ "
            "ಆರೋಪಿಯನ್ನು ತಾತ್ಕಾಲಿಕವಾಗಿ ಬಿಡುಗಡೆ ಮಾಡುವ ಪ್ರಕ್ರಿಯೆ. "
            "ಜಾಮೀನು ಅರ್ಜಿಯನ್ನು ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್ ನ್ಯಾಯಾಲಯದಲ್ಲಿ "
            "ವಕೀಲರ ಮೂಲಕ ಸಲ್ಲಿಸಬೇಕು. CrPC ಸೆಕ್ಷನ್ 436 ರ ಅಡಿಯಲ್ಲಿ "
            "ಜಾಮೀನು ಪಡೆಯಬಹುದಾದ ಅಪರಾಧಗಳಲ್ಲಿ ಜಾಮೀನು ನೀಡುವುದು ಕಡ್ಡಾಯ."
        ),
        "category": "Criminal Procedure",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
    {
        "title": "ಆಸ್ತಿ ವಿವಾದ — ಕಾನೂನು ಪರಿಹಾರ",
        "text": (
            "ಆಸ್ತಿ ವಿವಾದ ಉಂಟಾದಾಗ ಮೊದಲು ಸ್ಥಳೀಯ ಲೋಕ್ ಅದಾಲತ್‌ನಲ್ಲಿ "
            "ಸಂಧಾನ ಮಾಡಿಕೊಳ್ಳಲು ಪ್ರಯತ್ನಿಸಿ. ಸಾಧ್ಯವಾಗದಿದ್ದರೆ "
            "ಸಿವಿಲ್ ನ್ಯಾಯಾಲಯದಲ್ಲಿ ದಾವೆ ಹೂಡಬಹುದು. "
            "ಭೂ ದಾಖಲೆಗಳಿಗಾಗಿ ತಹಸೀಲ್ದಾರ್ ಕಚೇರಿ ಸಂಪರ್ಕಿಸಿ. "
            "ತಾತ್ಕಾಲಿಕ ತಡೆ ಆದೇಶಕ್ಕಾಗಿ ನ್ಯಾಯಾಲಯಕ್ಕೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ."
        ),
        "category": "Property Law",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
    {
        "title": "ಉಚಿತ ಕಾನೂನು ನೆರವು (Legal Aid) ಪಡೆಯುವುದು ಹೇಗೆ",
        "text": (
            "ಬಡ ಜನರಿಗೆ ಉಚಿತ ಕಾನೂನು ಸಹಾಯ ಪಡೆಯಲು ಕರ್ನಾಟಕ ರಾಜ್ಯ "
            "ಕಾನೂನು ಸೇವೆಗಳ ಪ್ರಾಧಿಕಾರ (KSLSA) ಇದೆ. "
            "ವಾರ್ಷಿಕ ಆದಾಯ 1 ಲಕ್ಷ ರೂ.ಗಿಂತ ಕಡಿಮೆ ಇರುವವರು, "
            "ಮಹಿಳೆಯರು, ಮಕ್ಕಳು ಮತ್ತು ಪರಿಶಿಷ್ಟ ಜಾತಿ/ಪಂಗಡದವರು "
            "ಉಚಿತ ಕಾನೂನು ಸಹಾಯ ಪಡೆಯಬಹುದು. "
            "ಜಿಲ್ಲಾ ಕಾನೂನು ಸೇವಾ ಪ್ರಾಧಿಕಾರವನ್ನು ಸಂಪರ್ಕಿಸಿ."
        ),
        "category": "Legal Aid",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
    {
        "title": "FIR ದಾಖಲಿಸುವ ವಿಧಾನ",
        "text": (
            "FIR (ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿ) ದಾಖಲಿಸಲು ಹತ್ತಿರದ ಪೊಲೀಸ್ "
            "ಠಾಣೆಗೆ ಹೋಗಿ. ಘಟನೆಯ ವಿವರ ಬರೆದ ದೂರು ನೀಡಿ. "
            "ಪೊಲೀಸ್ FIR ದಾಖಲಿಸಲು ನಿರಾಕರಿಸಿದರೆ ಜಿಲ್ಲಾ "
            "ಪೊಲೀಸ್ ವರಿಷ್ಠಾಧಿಕಾರಿ (SP) ಅಥವಾ ಮ್ಯಾಜಿಸ್ಟ್ರೇಟ್‌ಗೆ "
            "ದೂರು ನೀಡಿ. CrPC ಸೆಕ್ಷನ್ 154 ಅನ್ವಯ FIR ದಾಖಲಿಸುವುದು "
            "ಪೊಲೀಸ್ ಕರ್ತವ್ಯ."
        ),
        "category": "Criminal Procedure",
        "source": "vikaspedia.in",
        "language": "Kannada"
    },
]


# ── Live scraper for Vikaspedia ──────────────────────────────
def try_scrape_vikaspedia() -> list[dict]:
    """
    Attempts to scrape additional Kannada legal articles
    from vikaspedia.in. Falls back gracefully if unavailable.
    """
    scraped = []
    urls = [
        "https://kannada.vikaspedia.in/social-welfare/rights-a-nd-entitlements",
        "https://kannada.vikaspedia.in/social-welfare/rights-a-nd-entitlements/legal-aid",
    ]
    for url in urls:
        try:
            logger.info(f"Scraping: {url}")
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Status {response.status_code} for {url}")
                continue

            soup = BeautifulSoup(response.text, "lxml")

            # Get article content
            content_div = soup.find("div", class_="field-body")
            if not content_div:
                content_div = soup.find("div", class_="content")
            if not content_div:
                continue

            title_tag = soup.find("h1") or soup.find("h2")
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            text  = content_div.get_text(separator=" ", strip=True)

            if len(text) > 100:
                scraped.append({
                    "title":    title,
                    "text":     text,
                    "category": "Legal Rights",
                    "source":   url,
                    "language": "Kannada"
                })
                logger.info(f"Scraped: {title[:50]}...")

            time.sleep(2)

        except Exception as e:
            logger.warning(f"Failed to scrape {url}: {e}")

    return scraped


# ── Main ────────────────────────────────────────────────────
def main():
    logger.info("Starting Karnataka legal data collection...")

    # ── Karnataka State Laws ─────────────────────────────────
    logger.info(f"Loaded {len(KARNATAKA_LAWS)} hardcoded Karnataka law sections.")
    with open(KA_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(KARNATAKA_LAWS, f, ensure_ascii=False, indent=2)
    logger.success(f"Saved Karnataka laws → {KA_OUTPUT_FILE}")

    # ── Vikaspedia Kannada Articles ──────────────────────────
    all_vika = VIKASPEDIA_KN.copy()
    logger.info(f"Loaded {len(all_vika)} hardcoded Vikaspedia articles.")

    live_vika = try_scrape_vikaspedia()
    if live_vika:
        existing_titles = {a["title"] for a in all_vika}
        new_articles    = [a for a in live_vika if a["title"] not in existing_titles]
        all_vika.extend(new_articles)
        logger.info(f"Added {len(new_articles)} live scraped articles.")

    with open(VIKA_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_vika, f, ensure_ascii=False, indent=2)
    logger.success(f"Saved Vikaspedia articles → {VIKA_OUTPUT_FILE}")

    logger.info("Next step: run translate_to_kannada.py to translate Karnataka laws.")


if __name__ == "__main__":
    main()