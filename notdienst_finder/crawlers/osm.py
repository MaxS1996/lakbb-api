import requests
import re
import json
from typing import Optional, Dict
from notdienst_finder.pharmacy import Pharmacy

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def request_osm_data(pharmacy: Pharmacy) -> Optional[Dict]:
    """Fetch OpenStreetMap (OSM) data for a given pharmacy address."""
    
    pharmacy_address = f"{pharmacy.street}, {pharmacy.town}"
    pharmacy_address = re.sub(r'OT\s+\w+', '', pharmacy_address)

    query_address = pharmacy_address.replace("<br/>", " ")
    request_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query_address)}&format=json&polygon=1&addressdetails=1"
    
    headers = {"User-Agent": "pharmacy_screen"}

    try:
        response = requests.get(request_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            logger.warning(f"No results found for: {query_address}")
            return None

        # Prefer exact match
        for place in data:
            if "address" in place and "road" in place["address"] and "city" in place["address"]:
                if pharmacy.street in place["address"]["road"] and pharmacy.town in place["address"]["city"]:
                    return place

        # Fallback: return first result if no exact match
        return data[0]

    except requests.Timeout:
        logger.error(f"Request timed out for: {query_address}")
    except requests.RequestException as e:
        logger.error(f"Error fetching OSM data: {e}")

    return None