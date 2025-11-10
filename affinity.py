import os
import requests
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

AFFINITY_BASE_URL = os.environ.get("AFFINITY_BASE_URL", "https://api.affinity.co")
AFFINITY_TOKEN = os.environ.get("AFFINITY_ACCESS_TOKEN")

AFFINITY_HEADERS = {
    "Authorization": f"Bearer {AFFINITY_TOKEN}",
    "Content-Type": "application/json"
}

def get_affinity_list_entries(list_id: str) -> List[Dict]:
    """Get all entries from an Affinity list."""
    url = f"{AFFINITY_BASE_URL}/v2/lists/{list_id}/list-entries"
    params = {"limit": 100}
    all_entries = []
    
    while url:
        r = requests.get(url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        params = None  # Only use params on first request
        r.raise_for_status()
        
        payload = r.json()
        all_entries.extend(payload.get("data", []))
        
        pagination = payload.get("pagination", {}) or {}
        next_url = pagination.get("nextUrl")
        
        if next_url:
            url = next_url if next_url.startswith("http") else f"{AFFINITY_BASE_URL}{next_url}"
        else:
            url = None
    
    return all_entries


def get_affinity_list_fields(list_id: str) -> List[Dict]:
    """Get all fields for an Affinity list."""
    url = f"{AFFINITY_BASE_URL}/v2/lists/{list_id}/fields"
    params = {"limit": 100}
    all_fields = []
    
    while url:
        r = requests.get(url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        params = None
        r.raise_for_status()
        
        payload = r.json()
        all_fields.extend(payload.get("data", []))
        
        pagination = payload.get("pagination", {}) or {}
        next_url = pagination.get("nextUrl")
        
        if next_url:
            url = next_url if next_url.startswith("http") else f"{AFFINITY_BASE_URL}{next_url}"
        else:
            url = None
    
    return all_fields


def update_affinity_field(list_id: str, list_entry_id: str, field_id: str, value: float) -> bool:
    """Update a single field for a list entry in Affinity."""
    url = f"{AFFINITY_BASE_URL}/v2/lists/{list_id}/list-entries/{list_entry_id}/fields"
    
    payload = {
        "operation": "update-fields",
        "updates": [
            {
                "id": field_id,
                "value": {
                    "type": "number",
                    "data": value
                }
            }
        ]
    }
    
    try:
        r = requests.patch(url, json=payload, headers=AFFINITY_HEADERS, timeout=30)
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            error_msg = e.response.text
        print(f"    X Error: {error_msg[:100]}")
        return False
    
def get_affinity_lists() -> List[Dict]:
    """Fetch all available lists in Affinity."""
    url = f"{AFFINITY_BASE_URL}/v2/lists"
    params = {"limit": 100}
    all_lists = []

    while url:
        r = requests.get(url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        params = None
        r.raise_for_status()
        payload = r.json()
        all_lists.extend(payload.get("data", []))

        pagination = payload.get("pagination", {}) or {}
        next_url = pagination.get("nextUrl")

        if next_url:
            url = next_url if next_url.startswith("http") else f"{AFFINITY_BASE_URL}{next_url}"
        else:
            url = None

    return all_lists

def get_affinity_list_fields(list_id: str) -> List[Dict]:
    """Get all fields (metadata) for a specific Affinity list."""
    url = f"{AFFINITY_BASE_URL}/v2/lists/{list_id}/fields"
    params = {"limit": 100}
    all_fields = []

    while url:
        r = requests.get(url, headers=AFFINITY_HEADERS, params=params, timeout=30)
        params = None
        r.raise_for_status()

        payload = r.json()
        all_fields.extend(payload.get("data", []))

        pagination = payload.get("pagination", {}) or {}
        next_url = pagination.get("nextUrl")

        if next_url:
            url = next_url if next_url.startswith("http") else f"{AFFINITY_BASE_URL}{next_url}"
        else:
            url = None

    return all_fields
