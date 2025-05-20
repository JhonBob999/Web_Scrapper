import re
from urllib.parse import urljoin

# Простые шаблоны для библиотек
LIBRARY_PATTERNS = {
    "jQuery": r"jquery[-.]?(\d+\.\d+\.\d+)",
    "React": r"react[-.]?(\d+\.\d+\.\d+)",
    "AngularJS": r"angular[-.]?(\d+\.\d+\.\d+)",
    "Vue": r"vue[-.]?(\d+\.\d+\.\d+)",
    "Lodash": r"lodash[-.]?(\d+\.\d+\.\d+)",
    "Underscore": r"underscore[-.]?(\d+\.\d+\.\d+)",
    "Moment.js": r"moment[-.]?(\d+\.\d+\.\d+)"
}

def analyze_js_files(js_urls: list[str], base_url: str = "") -> list[dict]:
    """
    Analyze JS URLs and try to detect library names + versions.
    """
    results = []

    for url in js_urls:
        full_url = urljoin(base_url, url)
        lib_name = None
        version = None

        for name, pattern in LIBRARY_PATTERNS.items():
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                lib_name = name
                version = match.group(1)
                break

        results.append({
            "url": full_url,
            "library": lib_name or "Unknown",
            "version": version or "-",
        })

    return results
