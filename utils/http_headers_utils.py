import requests

def scan_http_headers(domain: str, timeout: int = 5) -> dict:
    """
    Sends HTTP request to the given domain and returns response headers.
    Tries HTTPS first, then falls back to HTTP.
    """
    urls_to_try = [f"https://{domain}", f"http://{domain}"]
    headers_result = {}

    for url in urls_to_try:
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            headers_result["URL"] = url
            headers_result["Status Code"] = response.status_code
            headers_result.update(response.headers)
            return headers_result
        except requests.exceptions.SSLError:
            headers_result["error"] = f"SSL Error while connecting to {url}"
        except requests.exceptions.ConnectionError:
            continue  # try next (http or https)
        except Exception as e:
            headers_result["error"] = str(e)
            break

    if not headers_result:
        headers_result["error"] = f"Could not connect to {domain}"
    return headers_result
