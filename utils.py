from urllib.parse import urlparse

def normalize_domain(url: str) -> str:
    """Extract and normalize domain from URL or domain string."""
    if not url or url == "N/A":
        return ""
    
    if "://" in url:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
    else:
        domain = url
    
    domain = domain.lower().replace("www.", "").strip().rstrip("/")
    return domain