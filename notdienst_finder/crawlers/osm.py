import requests
import re
import json
from typing import Optional, Dict
from notdienst_finder.pharmacy import Pharmacy

def request_osm_data(pharmacy: Pharmacy) -> Optional[Dict]:
    """Fetch OpenStreetMap (OSM) data for a given pharmacy address."""
    
    # Remove 'OT [something]' from address
    pharmacy_address = pharmacy.street + ", " + pharmacy.town
    pharmacy_address = re.sub(r'OT (.+?)\s', '', pharmacy_address)

    # Format address for query
    query_address = pharmacy_address.replace("<br/>", " ")
    request_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query_address)}&format=json&polygon=1&addressdetails=1"
    
    headers = {"User-Agent": "pharmacy_screen"}

    try:
        response = requests.get(request_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data:
            return data[0]  # Return the first result
        return None

    except requests.RequestException as e:
        print(f"Error fetching OSM data: {e}")
        return None