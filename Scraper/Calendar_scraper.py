import os
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import pytz

now_ist = datetime.now()


def update_url_month(url, year, month):
    date_str = f"{year:04d}-{month:02d}-01 00:00:00"
    ts_val = f"{{ts '{date_str}'}}"
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    qs["selCalDate"] = [ts_val]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


def setup_browser():
    from main import get_local_browser_revisions as pl
    import os

    revisions = pl()
    chromium_info = revisions.get("chromium")
    INSTALL_DIR = (
        os.path.expandvars(r"%LOCALAPPDATA%/ms-playwright")
        + f"/chromium-{chromium_info}/chrome-win/chrome.exe"
    )
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=True,
        executable_path=INSTALL_DIR,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-infobars",
            "--start-maximized",
        ],
    )

    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        java_script_enabled=True,
        bypass_csp=True,
        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
    )

    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
    """
    )

    return p, browser, context, context.new_page()


def check_auction_yesterday(page, url):
    yesterday = now_ist - timedelta(days=1)
    yesterday_str = yesterday.strftime("%B-%d-%Y")

    try:
        page.goto(url, timeout=20000)
        page.wait_for_selector(".CALDAYBOX", timeout=10000)
        day_boxes = page.query_selector_all("div.CALBOX")

        for box in day_boxes:
            aria_label = box.get_attribute("aria-label")
            if aria_label == yesterday_str:
                caltext = box.query_selector(".CALTEXT")
                if caltext and caltext.query_selector(".CALMSG"):
                    return True
                return False
        print(f"⚠ Date {yesterday_str} not found in calendar on page: {url}")
        return False
    except PlaywrightTimeout:
        print("❌ Timeout when checking yesterday's auction")
        return False


def check_upcoming_auction_date_for_month(url, page, start_date):
    ist = pytz.timezone("Asia/Kolkata")
    page.goto(url, timeout=20000)
    page.wait_for_selector(".CALDAYBOX", timeout=10000)

    day_boxes = page.query_selector_all("div.CALBOX")
    for box in day_boxes:
        aria_label = box.get_attribute("aria-label")
        if not aria_label:
            continue

        try:
            box_date = datetime.strptime(aria_label, "%B-%d-%Y")
            box_date = ist.localize(box_date)
        except:
            continue

        if box_date < start_date:
            continue

        caltext = box.query_selector(".CALTEXT")
        if not caltext:
            continue

        full_text = caltext.inner_text().lower()
        if not full_text.strip():
            continue

        types = []
        if "foreclosure" in full_text or "fc" in full_text:
            types.append("Foreclosure")
        if "tax deed" in full_text or "taxdeed" in full_text or "td" in full_text:
            types.append("Taxdeed")

        auction_type = "/".join(types) if types else "Unknown"

        if auction_type == "Taxdeed":
            continue

        return box_date.strftime("%m/%d/%Y"), auction_type

    return None, None


def check_upcoming_auction_date(url, page):
    ist = pytz.timezone("Asia/Kolkata")
    today = datetime.now(ist)
    start_date = today - timedelta(days=1)

    year = start_date.year
    month = start_date.month
    end_year = today.year

    while (year < end_year) or (year == end_year and month <= 12):
        new_url = update_url_month(url, year, month)
        date_found, auction_type = check_upcoming_auction_date_for_month(
            new_url, page, start_date
        )

        if date_found:
            return date_found, auction_type

        month = 1 if month == 12 else month + 1
        year += 1 if month == 1 else 0
        start_date = ist.localize(datetime(year, month, 1))

    return None, None


def main():
    from database.url import URL

    p, browser, context, page = setup_browser()
    result = []

    for county, url in URL.items():
        print(f"🔍 Checking {county}...")
        try:
            upcoming_date, auction_type = check_upcoming_auction_date(url, page)
            available = check_auction_yesterday(page, url)
        except Exception as e:
            print(f"❌ Error checking {county}: {e}")
            upcoming_date, auction_type, available = None, None, False

        result.append(
            {
                "County": county,
                "Available": available,
                "Upcoming Date": upcoming_date or "None",
                "Auction Type": auction_type or "None",
            }
        )

    browser.close()
    p.stop()

    yesterday = now_ist - timedelta(days=1)
    filename = yesterday.strftime("availability_of_%m-%d-%Y") + ".xlsx"
    df = pd.DataFrame(result)
    df.to_excel(filename, index=False)
    print(f"✅ Results saved to {filename}")


if __name__ == "__main__":
    main()
