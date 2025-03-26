import requests
import re
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import List, Optional

from notdienst_finder.pharmacy import Pharmacy

# 🔹 Constants
BASE_URL = "https://lakbb-typo3.notdienst-portal.de/schnellsuche/index.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/",
}
    
def get_emergency_pharmacies(plz: str = "01987", date: Optional[int] = None, limit: int = 4, morning_change: bool = True) -> List[Pharmacy]:
    """Fetches emergency pharmacies for a given postal code (PLZ) and date."""
    
    date = adjust_date(date, morning_change)
    url = f"{BASE_URL}?suchbegriff={plz}&datum={date}"

    html = fetch_html(url)
    if not html:
        return [Pharmacy(name="Notdienst nicht verfügbar", street="N/A", town="Daten konnten nicht abgerufen werden.")]

    pharmacies = parse_pharmacies(html, limit)
    return pharmacies if pharmacies else [Pharmacy(name="Keine Notdienst-Apotheken gefunden", street="N/A", town="N/A")]

def adjust_date(date: Optional[int], morning_change: bool) -> str:
    """Adjusts the date based on morning change rule (before 8 AM => show yesterday)."""
    
    if date is None:
        date = int(time.time())  # Current timestamp

    if morning_change:
        today_8am = datetime.fromtimestamp(date).replace(hour=8, minute=0, second=0)
        if datetime.fromtimestamp(date) < today_8am:
            date -= 86400  # Go back one day

    return datetime.fromtimestamp(date).strftime("%d.%m.%Y")

def fetch_html(url: str) -> Optional[str]:
    """Fetches the HTML content of the given URL."""
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        # Attempt to detect encoding
        response.encoding = response.apparent_encoding  # Auto-detect encoding

         # Force UTF-8 conversion (handles "ö", "ü", "ß", etc.)
        return response.text.encode(response.encoding).decode("utf-8", errors="ignore")
    
    except requests.RequestException:
        return None
    
def parse_pharmacies(html: str, limit: int) -> List[Pharmacy]:
    """Parses pharmacy details from the HTML."""
    
    soup = BeautifulSoup(html, "html.parser")
    pharmacies = []

    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) < 3 or len(pharmacies) >= limit:
            continue
        
        pharmacy = extract_pharmacy_details(cols)
        pharmacies.append(pharmacy)

    return pharmacies

def extract_pharmacy_details(cols) -> Pharmacy:
    """Extracts details from a single pharmacy row and returns a Pharmacy object."""
    
    # Extract name
    name_tag = cols[0].find("b")
    name = name_tag.text.strip() if name_tag else "Unbekannt"

    # Extract address
    address_lines = cols[0].decode_contents().split("<br/>")
    street = address_lines[1].strip() if len(address_lines) > 1 else "Unbekannt"
    town = address_lines[2].strip() if len(address_lines) > 2 else "Unbekannt"

    # Extract phone, fax, website, email
    contact_info = cols[1].decode_contents()
    phone = extract_match(r'Tel\.: ([\d\s/]+)', contact_info)
    fax = extract_match(r'Fax: ([\d\s/]+)', contact_info)
    web = extract_match(r'Homepage: <a href="(.+?)"', contact_info)
    mail = extract_match(r'<a href="mailto:(.+?)">', contact_info)

    # Remove "/" and "-" from phone and fax numbers, and remove extra spaces
    if phone:
        phone = re.sub(r'\s+', ' ', phone.replace("/", "").replace("-", "").strip())
    if fax:
        fax = re.sub(r'\s+', ' ', fax.replace("/", "").replace("-", "").strip())

    # Extract Google Maps link
    maps_tag = cols[2].find("a", {"title": "Anfahrtsplan bei Google Maps"})
    gmaps = maps_tag["href"] if maps_tag else None

    return Pharmacy(name=name, street=street, state="Brandenburg", town=town, phone=phone, fax=fax, web=web, mail=mail, gmaps=gmaps)

def extract_match(pattern: str, text: str) -> Optional[str]:
    """Extracts a match from the given text using regex."""
    
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None
