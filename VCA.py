# VC Portfolio Analyzer Agent (with Google-powered Crunchbase scraping + delay handling)

"""Analyze a VC fund website and perform simple Crunchbase analysis."""

import importlib


def _ensure_dependencies() -> list[str]:
    """Return a list of missing packages from ``requirements.txt``."""
    required = [
        "aiohttp",
        "bs4",
        "playwright.async_api",
        "PIL",
        "pytesseract",
        "tqdm",
        "googlesearch",
    ]
    missing = []
    for pkg in required:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    return missing




import argparse
import asyncio
import os
import threading
try:
    import aiohttp
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    from playwright.async_api import async_playwright
    from PIL import Image
    import pytesseract
    from tqdm import tqdm
    from googlesearch import search
except ImportError:
    aiohttp = None
    BeautifulSoup = None
    async_playwright = None
    Image = None
    pytesseract = None
    tqdm = None
    search = None
import re
from io import BytesIO
from base64 import b64decode
import curses
import io
from contextlib import redirect_stdout
import sys


# Helper to run async coroutines in environments with a running event loop
def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result = {}

    def _thread_runner():
        result["value"] = asyncio.run(coro)

    t = threading.Thread(target=_thread_runner)
    t.start()
    t.join()
    return result.get("value")


# === OCR helpers ===
def extract_text_from_base64_img(data_url):
    try:
        if data_url.startswith("data:image"):
            _, encoded = data_url.split(",", 1)
            img_data = b64decode(encoded)
            img = Image.open(BytesIO(img_data))
            return pytesseract.image_to_string(img)
    except:
        pass
    return ""


async def extract_text_from_image_url(img_url, base_url):
    try:
        full_url = urljoin(base_url, img_url)
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, timeout=10) as r:
                if r.status == 200:
                    content = await r.read()
                    img = Image.open(BytesIO(content))
                    return pytesseract.image_to_string(img)
    except Exception:
        pass
    return ""


def extract_text_from_svg(svg_tag):
    """Extract text from <text> elements in an SVG tag."""
    try:
        soup = BeautifulSoup(str(svg_tag), "html.parser")
        text_elements = soup.find_all(["text", "tspan"])
        texts = [t.get_text(" ", strip=True) for t in text_elements]
        return " ".join(texts)
    except Exception:
        return ""


# === Heuristic to detect valid company names ===
def is_probable_company_name(name):
    name = name.strip(" $•-–—·\xb7|→●\t\n\r")
    name = re.sub(r"(?i)\\blogo+\\b", "", name).strip()
    banned = [
        "home",
        "team",
        "contact",
        "blog",
        "services",
        "portfolio",
        "email",
        "english",
        "arabic",
        "en",
        "ar",
        "career",
        "subscribe",
        "loading",
        "apply",
        "login",
        "follow",
    ]
    if name.lower() in banned:
        return False
    if len(name) > 60 or len(name) < 2:
        return False
    if not re.search(r"[A-Za-z]", name):
        return False
    if len(name.split()) > 5:
        return False
    if any(char in name for char in "<>{}[]|"):
        return False
    return True


# === Page rendering ===
async def fetch_page_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(2000)
        content = await page.content()
        await browser.close()
        return content


async def find_portfolio_section(base_url):
    html = await fetch_page_content(base_url)
    soup = BeautifulSoup(html, "html.parser")
    keywords = ["portfolio", "investments", "companies"]
    candidates = []
    for a in soup.find_all("a", href=True):
        if any(k in a.text.lower() or k in a["href"].lower() for k in keywords):
            full_url = urljoin(base_url, a["href"])
            candidates.append(full_url)
    return candidates or [base_url]


async def parse_portfolio(url):
    html = await fetch_page_content(url)
    soup = BeautifulSoup(html, "html.parser")
    companies = set()

    def extract_near_text(img_tag):
        texts = []
        for attr in ["alt", "title", "aria-label"]:
            if img_tag.has_attr(attr):
                texts.append(img_tag[attr])
        parent = img_tag.find_parent()
        if parent:
            siblings = parent.find_all(["p", "div", "span", "a"], recursive=True)
            for sib in siblings:
                txt = sib.get_text(strip=True)
                texts.append(txt)
        return texts

    for img in soup.find_all("img"):
        src = img.get("src", "")
        nearby_names = extract_near_text(img)
        for name in nearby_names:
            name = name.strip()
            if is_probable_company_name(name):
                companies.add(name)

        text = ""
        if src.startswith("data:image"):
            text = extract_text_from_base64_img(src)
        elif src.startswith("/") or src.startswith("http"):
            text = await extract_text_from_image_url(src, url)
        for line in text.split("\n"):
            line = line.strip()
            if is_probable_company_name(line):
                companies.add(line)

    for div in soup.find_all("div"):
        style = div.get("style", "")
        match = re.search(r"background-image:\s*url\((.*?)\)", style)
        if match:
            bg_url = match.group(1).strip("\"'")
            text = await extract_text_from_image_url(bg_url, url)
            for line in text.split("\n"):
                line = line.strip()
                if is_probable_company_name(line):
                    companies.add(line)

    for svg in soup.find_all("svg"):
        text = extract_text_from_svg(svg)
        for line in text.split("\n"):
            line = line.strip()
            if is_probable_company_name(line):
                companies.add(line)

    for tag in soup.find_all(["p", "li", "div", "span", "a"]):
        txt = tag.get_text(strip=True)
        if txt and is_probable_company_name(txt):
            companies.add(txt)

    print(f"[DEBUG] Найдено компаний: {len(companies)}")
    return sorted(companies)


# === Crunchbase via Google Search ===
async def fetch_crunchbase_html(company_name):
    try:
        query = f'site:crunchbase.com "{company_name}"'
        for url in search(query, num=3):
            if "crunchbase.com/organization/" in url:
                headers = {"User-Agent": "Mozilla/5.0"}
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(url, timeout=10) as r:
                        if r.status == 200:
                            text = await r.text()
                            soup = BeautifulSoup(text, "html.parser")
                            return soup.get_text()
        await asyncio.sleep(3)  # задержка между поисками
    except Exception as e:
        print(f"[ERROR] Crunchbase fetch failed for {company_name}: {e}")
    return ""


# === Main Agent Logic ===
async def analyze_vc_fund(site_url):
    portfolio_links = await find_portfolio_section(site_url)
    all_companies = set()
    for link in portfolio_links:
        companies = await parse_portfolio(link)
        all_companies.update(companies)

    companies = sorted(all_companies)

    print("\n======= ИТОГОВЫЙ СПИСОК КОМПАНИЙ НА САЙТЕ =======")
    for name in companies:
        print(name)
    print(f"\nВсего: {len(companies)} компаний\n")

    investment_years = {"2023": 0, "2024": 0, "2025": 0}
    sectors = {"AI": [], "SaaS": [], "FoodTech/F&B": []}
    countries = []
    amounts = []

    print("\n🔍 Анализ компаний на Crunchbase...")
    for name in tqdm(companies, desc="Обработка компаний"):
        html = await fetch_crunchbase_html(name)
        text = html.lower()

        for year in investment_years:
            if year in text:
                investment_years[year] += 1

        if "ai" in text:
            sectors["AI"].append(name)
        if "saas" in text:
            sectors["SaaS"].append(name)
        if any(k in text for k in ["food", "restaurant", "kitchen"]):
            sectors["FoodTech/F&B"].append(name)

        for country in ["uae", "ksa", "egypt", "jordan", "qatar", "kuwait"]:
            if country in text:
                countries.append(country.upper())

        for line in html.splitlines():
            if "$" in line or "usd" in line:
                try:
                    num = "".join(filter(str.isdigit, line))
                    if num:
                        amt = int(num)
                        if 10_000 < amt < 100_000_000:
                            amounts.append(amt)
                except:
                    pass
        await asyncio.sleep(3)  # задержка между итерациями компаний

    print("\n========= АНАЛИТИКА PO CRUNCHBASE =========")
    print("Инвестиции по годам:", investment_years)
    print("\nИнвестиции в AI:", sectors["AI"])
    print("\nИнвестиции в SaaS:", sectors["SaaS"])
    print("\nИнвестиции в FoodTech/F&B:", sectors["FoodTech/F&B"])
    top_countries = sorted(set(countries), key=countries.count, reverse=True)[:3]
    print("\nТоп-3 страны:", top_countries)
    mena_countries = list(
        set([c for c in countries if c in ["UAE", "KSA", "EGYPT", "JORDAN", "QATAR", "KUWAIT"]])
    )
    print("MENA страны:", mena_countries)
    if amounts:
        print("\nСредний инвестиционный чек:", round(sum(amounts) / len(amounts), 2))


async def _capture_analysis(url: str) -> str:
    """Run analysis and capture printed output."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        await analyze_vc_fund(url)
    return buffer.getvalue()


def display_input_screen(stdscr) -> str:
    """Ask user for a URL and return it."""
    curses.curs_set(1)
    stdscr.clear()
    stdscr.addstr(0, 0, "Введите URL сайта фонда:")
    stdscr.refresh()
    curses.echo()
    url = stdscr.getstr(2, 0, 200).decode().strip()
    curses.noecho()
    curses.curs_set(0)
    return url


def display_results_screen(stdscr, results_text: str) -> None:
    """Show analysis output in a scrollable window."""
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    lines = results_text.splitlines()
    pad_height = max(len(lines) + 1, height)
    pad = curses.newpad(pad_height, width)
    for i, line in enumerate(lines):
        try:
            pad.addstr(i, 0, line[: width - 1])
        except curses.error:
            pass
    position = 0
    instruction = "Use UP/DOWN to scroll, q to quit"
    while True:
        pad.refresh(position, 0, 0, 0, height - 2, width - 1)
        stdscr.addstr(height - 1, 0, instruction[: width - 1])
        stdscr.clrtoeol()
        key = stdscr.getch()
        if key == curses.KEY_DOWN and position < pad_height - height:
            position += 1
        elif key == curses.KEY_UP and position > 0:
            position -= 1
        elif key in (ord("q"), ord("Q")):
            break


def _curses_main(stdscr) -> None:
    url = display_input_screen(stdscr)
    results = _run_async(_capture_analysis(url))
    display_results_screen(stdscr, results)


# === Entry Point ===
def main() -> None:
    missing = _ensure_dependencies()
    if missing:
        print(
            "Missing required packages: {}. "
            "Install them with `pip install -r requirements.txt`. "
            "If you only see a blank screen, it's usually because these packages are not available.".format(
                ", ".join(missing)
            )
        )
        return
    parser = argparse.ArgumentParser(description="VC Portfolio Analyzer")
    parser.add_argument("--url", help="VC fund website URL")
    args = parser.parse_args()

    if args.url:
        results = _run_async(_capture_analysis(args.url))
        print(results)
        return

    try:
        if sys.stdin.isatty() and sys.stdout.isatty():
            curses.wrapper(_curses_main)
        else:
            raise curses.error("Not a TTY")
    except curses.error:
        try:
            url = input("Введите URL сайта фонда: ").strip()
            if url:
                results = _run_async(_capture_analysis(url))
                print(results)
            else:
                raise EOFError
        except (EOFError, KeyboardInterrupt):
            print(
                "Нет интерактивного терминала и не указан --url. "
                "Запустите с параметром --url или используйте 'streamlit run streamlit_app.py'."
            )


if __name__ == "__main__":
    # Detect if the script is executed via ``streamlit run``. The environment
    # variable ``STREAMLIT_SERVER_HEADLESS`` is set by Streamlit when running
    # in server mode.
    if os.environ.get("STREAMLIT_SERVER_HEADLESS"):
        from streamlit_app import main as streamlit_main

        streamlit_main()
    else:
        main()
