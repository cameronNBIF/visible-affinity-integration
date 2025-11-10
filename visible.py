import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

from utils import normalize_domain

load_dotenv()

VISIBLE_BASE_URL = os.environ.get("VISIBLE_BASE_URL", "https://api.visible.vc")
VISIBLE_TOKEN = os.environ.get("VISIBLE_ACCESS_TOKEN")
VISIBLE_COMPANY_ID = os.environ.get("VISIBLE_COMPANY_ID")

VISIBLE_HEADERS = {
    "Authorization": f"Bearer {VISIBLE_TOKEN}",
    "Content-Type": "application/json"
}

def get_visible_portfolio_companies() -> List[Dict]:
    """Fetch all portfolio companies from Visible."""
    companies = []
    page = 1
    
    while True:
        params = {"company_id": VISIBLE_COMPANY_ID, "page": page}
        r = requests.get(
            f"{VISIBLE_BASE_URL}/portfolio_company_profiles",
            headers=VISIBLE_HEADERS,
            params=params,
            timeout=30
        )
        
        if not r.ok:
            print(f"X Error fetching Visible companies (page {page}): {r.status_code}")
            break
        
        data = r.json()
        companies.extend(data.get("portfolio_company_profiles", []))
        meta = data.get("meta", {})
        
        if page >= meta.get("total_pages", 1):
            break
        page += 1
    
    print(f"✓ Retrieved {len(companies)} companies from Visible")
    return companies

def get_visible_metrics() -> List[Dict]:
    """Fetch all available metrics in Visible for the configured company."""
    all_metrics = []
    page = 1

    while True:
        params = {"company_id": VISIBLE_COMPANY_ID, "page": page}
        r = requests.get(
            f"{VISIBLE_BASE_URL}/metrics",
            headers=VISIBLE_HEADERS,
            params=params,
            timeout=30
        )
        if not r.ok:
            print(f"X Error fetching metrics (page {page}): {r.status_code}")
            break

        data = r.json()
        metrics = data.get("metrics", [])
        all_metrics.extend(metrics)

        meta = data.get("meta", {})
        if page >= meta.get("total_pages", 1):
            break
        page += 1

    return all_metrics

def get_visible_metric_names() -> List[str]:
    """Return a deduplicated list of metric names for user selection."""
    metrics = get_visible_metrics()
    unique_names = sorted({m["name"] for m in metrics if m.get("name")})
    return unique_names

def get_visible_company_metrics(company_profile_id: str) -> List[Dict]:
    """Get all metrics for a specific Visible company."""
    metrics = []
    page = 1
    
    while True:
        params = {
            "company_id": VISIBLE_COMPANY_ID,
            "page": page,
            "filter[portfolio_company_profile_id]": company_profile_id
        }
        r = requests.get(
            f"{VISIBLE_BASE_URL}/metrics",
            headers=VISIBLE_HEADERS,
            params=params,
            timeout=30
        )
        
        if not r.ok:
            break
        
        data = r.json()
        metrics.extend(data.get("metrics", []))
        meta = data.get("meta", {})
        
        if page >= meta.get("total_pages", 1):
            break
        page += 1
    
    return metrics


def get_latest_data_point(metric_id: str) -> Dict:
    """Get the most recent data point for a metric."""
    page = 1
    latest_value = None
    latest_date = "0000-00-00"
    
    while True:
        params = {"metric_id": metric_id, "page": page, "page_size": 100}
        r = requests.get(
            f"{VISIBLE_BASE_URL}/data_points",
            headers=VISIBLE_HEADERS,
            params=params,
            timeout=30
        )
        
        if not r.ok:
            break
        
        data = r.json()
        points = data.get("data_points", [])
        meta = data.get("meta", {})
        
        for dp in points:
            date = dp.get("date")
            value = dp.get("value")
            if value not in [None, "None"] and date and date > latest_date:
                latest_date = date
                latest_value = value
        
        if page >= meta.get("total_pages", 1):
            break
        page += 1
    
    return {"date": latest_date, "value": latest_value}


def get_website_property_id() -> Optional[str]:
    """Get the portfolio property ID for 'Website'."""
    r = requests.get(
        f"{VISIBLE_BASE_URL}/portfolio_properties",
        headers=VISIBLE_HEADERS,
        params={"company_id": VISIBLE_COMPANY_ID},
        timeout=30
    )
    
    if not r.ok:
        return None
    
    properties = r.json().get("portfolio_properties", [])
    website_property = next(
        (p for p in properties if p["name"].lower().startswith("website")),
        None
    )
    
    return website_property["id"] if website_property else None


def get_company_website(profile_id: str, website_property_id: str) -> Optional[str]:
    """Get the website value for a company."""
    r = requests.get(
        f"{VISIBLE_BASE_URL}/portfolio_property_values",
        headers=VISIBLE_HEADERS,
        params={"portfolio_company_profile_id": profile_id},
        timeout=30
    )
    
    if not r.ok:
        return None
    
    values = r.json().get("portfolio_property_values", [])
    return next(
        (v.get("value") for v in values if v.get("portfolio_property_id") == website_property_id),
        None
    )


def fetch_visible_metric_data(metric_name: str) -> Dict[str, float]:
    """
    Fetch data for a specific metric name across all companies.
    Returns: {normalized_domain: metric_value}
    """
    print("\n" + "="*60)
    print(f" FETCHING DATA FROM VISIBLE FOR METRIC: {metric_name}")
    print("="*60)

    companies = get_visible_portfolio_companies()
    website_property_id = get_website_property_id()
    if not website_property_id:
        print("!  Warning: No 'Website' property found in Visible")
        return {}

    domain_to_value = {}

    for company in companies:
        company_name = company.get("name")
        company_id = company.get("id")

        website = get_company_website(company_id, website_property_id)
        if not website or website == "N/A":
            continue

        normalized_domain = normalize_domain(website)
        if not normalized_domain:
            continue

        metrics = get_visible_company_metrics(company_id)
        metric = next(
            (m for m in metrics if m.get("name", "").strip().lower() == metric_name.lower().strip()),
            None
        )
        if not metric:
            print(f"  !  {company_name}: Metric '{metric_name}' not found")
            continue

        latest = get_latest_data_point(metric["id"])
        if latest["value"] not in [None, "None"]:
            try:
                value = float(latest["value"])
                domain_to_value[normalized_domain] = value
                print(f"  ✓ {company_name:35} ({normalized_domain:30}) → {value:6.1f}")
            except (ValueError, TypeError):
                print(f"  !  {company_name}: Invalid value: {latest['value']}")
        else:
            print(f"  !  {company_name}: No data for metric '{metric_name}'")

    print(f"\n✓ Loaded {len(domain_to_value)} companies with '{metric_name}' data from Visible")
    return domain_to_value

