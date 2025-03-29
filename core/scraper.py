import requests
from bs4 import BeautifulSoup
from lxml import html
from urllib.parse import urljoin

def scrape_website(
    url,
    selector,
    use_xpath=False,
    proxy=None,
    headers=None,
    user_agent=None,
    timeout=10,
    cookies=None
):
    """Парсит сайт с поддержкой прокси, заголовков, куки и таймаута"""

    # Добавляем https://, если нет
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Подготовка заголовков
    headers = headers or {}
    if user_agent:
        headers["User-Agent"] = user_agent
    elif "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0"

    # Прокси
    proxies = {"http": proxy, "https": proxy} if proxy else None

    # Куки и сессия
    session = requests.Session()

    if cookies:
        session.cookies.update(cookies)

    # Выполняем запрос
    response = session.get(url, headers=headers, proxies=proxies, timeout=timeout)
    response.raise_for_status()

    # Результаты
    results = []

    if use_xpath:
        tree = html.fromstring(response.text)
        elements = tree.xpath(selector)

        for el in elements:
            if el.tag == "a" and "href" in el.attrib:
                full_link = urljoin(url, el.attrib["href"])
                text = el.text_content().strip() or full_link
                results.append(f'<a href="{full_link}" target="_blank">{text}</a>')
            else:
                results.append(html.tostring(el, encoding="unicode"))
    else:
        soup = BeautifulSoup(response.text, "html.parser")
        elements = soup.select(selector)

        for element in elements:
            if element.name == "a" and element.get("href"):
                full_link = urljoin(url, element["href"])
                text = element.get_text(strip=True) or full_link
                results.append(f'<a href="{full_link}" target="_blank">{text}</a>')
            else:
                results.append(str(element.prettify()))

    # ✅ Возвращаем также куки
    return results, session.cookies.get_dict()
