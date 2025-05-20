import requests
from bs4 import BeautifulSoup

def parse_page(domain: str, timeout: int = 5) -> dict:
    """
    Download and parse the HTML of the domain.
    Returns links, scripts, forms, images, etc.
    """
    result = {}
    urls_to_try = [f"https://{domain}", f"http://{domain}"]

    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=timeout)
            result["URL"] = url
            result["Status"] = response.status_code

            soup = BeautifulSoup(response.text, "html.parser")

            # Ссылки
            result["Links"] = [a.get("href") for a in soup.find_all("a", href=True)]

            # JS-файлы
            result["Scripts"] = [s.get("src") for s in soup.find_all("script", src=True)]

            # Формы
            result["Forms"] = []
            for form in soup.find_all("form"):
                action = form.get("action")
                method = form.get("method", "GET").upper()
                inputs = [inp.get("name") for inp in form.find_all("input")]
                result["Forms"].append(f"{method} → {action} | Inputs: {', '.join(inputs)}")

            # Изображения
            result["Images"] = [img.get("src") for img in soup.find_all("img", src=True)]

            return result

        except Exception as e:
            result["error"] = f"Error while loading {url}: {str(e)}"
            break

    if not result:
        result["error"] = f"Could not connect to {domain}"
    return result
