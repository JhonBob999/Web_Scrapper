import re
import requests

def extract_technologies(headers: dict) -> dict:
    """
    Parse headers and extract technology name + version.
    """
    techs = {}

    patterns = {
        "Server": r"([a-zA-Z\-]+)[/ ]([\d\.]+)",
        "X-Powered-By": r"([a-zA-Z\-]+)[/ ]([\d\.]+)",
        "X-AspNet-Version": r"(ASP\.NET)[/ ]?([\d\.]+)",
        "X-Runtime": r"(Ruby)[/ ]?([\d\.]+)",
        "X-Generator": r"([a-zA-Z\-]+)[/ ]?([\d\.]+)",
    }

    for header, pattern in patterns.items():
        value = headers.get(header)
        if value:
            match = re.search(pattern, value)
            if match:
                techs[match.group(1)] = match.group(2)

    return techs

def check_cves_from_headers(domain: str, timeout: int = 5) -> dict:
    """
    Sends HEAD request to domain, extracts headers and identifies technologies.
    """
    result = {}
    urls = [f"https://{domain}", f"http://{domain}"]

    for url in urls:
        try:
            r = requests.head(url, timeout=timeout, allow_redirects=True)
            headers = dict(r.headers)

            result["URL"] = url
            result["Status"] = r.status_code
            result["Raw-Headers"] = headers
            result["Technologies"] = extract_technologies(headers)
            return result

        except Exception as e:
            result["error"] = f"{url} → {str(e)}"
            break

    if not result:
        result["error"] = f"Failed to connect to {domain}"

    return result
