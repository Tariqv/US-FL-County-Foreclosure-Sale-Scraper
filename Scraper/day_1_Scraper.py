import pytz
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright

IST = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(IST)


def update_calendar_url(base_url: str, year: int, month: int) -> str:
    date_str = f"{year:04d}-{month:02d}-01 00:00:00"
    ts_val = quote_plus(f"{{ts '{date_str}'}}")
    return f"{base_url}/index.cfm?zaction=user&zmethod=calendar&selCalDate={ts_val}"


def check_last_day_auction(page, base_url: str):
    if now_ist.day != 1:
        return None, None

    first_day = now_ist.replace(day=1)
    last_day_prev_month = first_day - timedelta(days=1)
    year = last_day_prev_month.year
    month = last_day_prev_month.month
    full_url = update_calendar_url(base_url, year, month)

    try:
        page.goto(full_url, timeout=60000)
        page.wait_for_selector("div.CALDAYBOX", timeout=10000)
    except:
        print(f"⚠️ Calendar failed to load Url. Please check internet.\n")
        return False, "None"

    boxes = page.query_selector_all("div.CALBOX")
    for box in boxes:
        aria_label = box.get_attribute("aria-label")
        if not aria_label:
            continue
        try:
            box_date = parser.parse(aria_label).date()
            if box_date == last_day_prev_month.date():
                caltext = box.query_selector(".CALTEXT")
                text = caltext.inner_text().strip().lower()
                types = []
                if "foreclosure" in text or "fc" in text:
                    types.append("Foreclosure")
                if "tax deed" in text or "taxdeed" in text or "td" in text:
                    types.append("Taxdeed")
                auction_type = "/".join(types) if types else "Unknown"
                return True, auction_type
        except:
            continue

    return False, "None"


def check_upcoming_foreclosure_auction(page, base_url: str):
    today = datetime.now(IST)
    start_date = today

    year = start_date.year
    month = start_date.month

    for _ in range(6):  # ✅ Check next 6 months
        url = update_calendar_url(base_url, year, month)
        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector("div.CALDAYBOX", timeout=10000)
            page.wait_for_timeout(500)  # ✅ Small delay to ensure rendering
        except:
            print(f"⚠️ Could not load calendar for {month}/{year}. Skipping...\n")
            # ✅ Move to next month even if this fails
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            continue

        boxes = page.query_selector_all("div.CALBOX")
        for box in boxes:
            aria_label = box.get_attribute("aria-label")
            if not aria_label:
                continue

            try:
                box_date = parser.parse(aria_label)
                if box_date.tzinfo is None:
                    box_date = IST.localize(
                        datetime.combine(box_date.date(), datetime.min.time())
                    )
                else:
                    box_date = box_date.astimezone(IST)

                if box_date < start_date:
                    continue

                caltext = box.query_selector(".CALTEXT")
                if not caltext:
                    continue

                full_text = caltext.inner_text().strip().lower()
                if not full_text:
                    continue
                if (
                    "tax deed" in full_text
                    or "taxdeed" in full_text
                    or "td" in full_text
                ):
                    continue
                if "foreclosure" in full_text or "fc" in full_text:
                    return box_date.strftime("%m/%d/%Y")
            except:
                continue

        # ✅ Move to next month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return "None"


def main():
    if now_ist.day != 1:
        print("⏩ Not the 1st day of the month. Skipping check.\n")
        return

    results = []

    with sync_playwright() as p:
        import os
        from main import get_local_browser_revisions as pl

        revisions = pl()
        chromium_info = revisions.get("chromium")
        INSTALL_DIR = (
            os.path.expandvars(r"%LOCALAPPDATA%/ms-playwright")
            + f"/chromium-{chromium_info}/chrome-win/chrome.exe"
        )
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
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        # 🧠 Anti-bot JS patches
        context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            window.chrome = { runtime: {} };
        """
        )

        page = context.new_page()
        from database.url import COUNTY_URLS

        for county, url in COUNTY_URLS.items():
            print(f"🔍 Checking {county}...\n")
            available, auction_type = check_last_day_auction(page, url)
            if available is None:
                print(f"⏭️ Skipping {county}, not applicable.\n")
                continue

            upcoming_date = check_upcoming_foreclosure_auction(page, url)
            results.append(
                {
                    "County": county,
                    "Available": available,
                    "Auction Type": auction_type,
                    "Upcoming Date": upcoming_date,
                }
            )

        browser.close()

    # Save results to Excel
    yesterday = now_ist - timedelta(days=1)
    filename = f"availability_of_{yesterday.strftime('%m-%d-%Y')}.xlsx"
    df = pd.DataFrame(results)
    df.to_excel(filename, index=False)
    print(f"✅ Results saved to: {filename}\n")


if __name__ == "__main__":
    main()
