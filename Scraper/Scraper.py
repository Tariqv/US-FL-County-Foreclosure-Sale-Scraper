import os
import pandas as pd
import time, pytz
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as tl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


# Setup date
real_date = datetime.now()
now_ist = real_date
first_day_of_month = real_date.replace(day=1)
yesterday = real_date - timedelta(days=1)
AUCTION_DATE = yesterday.strftime("%m/%d/%Y")
FOLDER_NAME = AUCTION_DATE.replace("/", "-")
os.makedirs(FOLDER_NAME, exist_ok=True)


def create_browser_context():
    from main import get_local_browser_revisions as pl

    revisions = pl()
    chromium_info = revisions.get("chromium")
    install_path = (
        os.path.expandvars(r"%LOCALAPPDATA%/ms-playwright")
        + f"/chromium-{chromium_info}/chrome-win/chrome.exe"
    )

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=True,
        executable_path=install_path,
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
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
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
    return playwright, browser, context


def scrape_auctions_on_page(page, county_name):
    page.wait_for_selector('div[id^="AITEM_"]', timeout=10000)
    auction_boxes = page.query_selector_all('div[id^="AITEM_"]')
    print(f"✅ Found {len(auction_boxes)} auction boxes on current page.\n")
    all_data = []

    for idx, box in enumerate(auction_boxes, 1):
        entry = {
            "Auction Sold": "",
            "Amount": "",
            "Sold To": "",
            "Case #": "",
            "Parcel ID": "",
            "Property Address": "",
            "Final Judgment Amount": "",
            "Assessed Value": "",
            "Plaintiff Max Bid": "",
            "Opening Bid": "",
            "Auction Type": "",
        }

        try:
            stat_labels = box.query_selector_all(".AUCTION_STATS .ASTAT_LBL")
            stat_values = box.query_selector_all(".AUCTION_STATS .Astat_DATA")
            for label, value in zip(stat_labels, stat_values):
                key = label.inner_text().strip()
                val = value.inner_text().strip()
                if "Auction Sold" in key:
                    entry["Auction Sold"] = val
                elif "Amount" in key and "Max Bid" not in key:
                    entry["Amount"] = val
                elif "Sold To" in key:
                    entry["Sold To"] = val

            labels = box.query_selector_all(".AUCTION_DETAILS .AD_LBL")
            values = box.query_selector_all(".AUCTION_DETAILS .AD_DTA")
            address_buffer = ""
            for label, value in zip(labels, values):
                key = label.inner_text().strip().rstrip(":")
                val = value.inner_text().strip()
                if key == "Case #":
                    entry["Case #"] = val
                elif key == "Parcel ID":
                    entry["Parcel ID"] = val
                elif key == "Auction Type":
                    entry["Auction Type"] = val
                elif key == "Opening Bid":
                    entry["Opening Bid"] = val
                elif key == "Property Address":
                    address_buffer = val
                elif key == "" and val:
                    if address_buffer:
                        entry["Property Address"] = f"{address_buffer}, {val}"
                        address_buffer = ""
                elif "Final Judgment" in key:
                    entry["Final Judgment Amount"] = val
                elif "Assessed Value" in key:
                    entry["Assessed Value"] = val
                elif "Max Bid" in key:
                    entry["Plaintiff Max Bid"] = val

            if address_buffer:
                entry["Property Address"] = address_buffer

            all_data.append(entry)

        except Exception as e:
            print(f"[!] Error parsing box {idx}: {e}")
            continue

    return all_data


def click_next_page(page):
    try:
        next_button = page.query_selector(
            '//*[@id="BID_WINDOW_CONTAINER"]/div[4]/div[6]/span[5]'
        )
        if next_button:
            next_button.scroll_into_view_if_needed()
            time.sleep(1)
            next_button.click()
            return True
        return False
    except Exception as e:
        print(f"[-] Pagination failed: {e}")
        return False


def scrape_county(county_name, base_url):
    print(f"\n=== Scraping {county_name} ===\n")
    full_url = f"{base_url}/index.cfm?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE={AUCTION_DATE}"
    playwright, browser, context = create_browser_context()
    page = context.new_page()

    all_auctions = []
    try:
        print("🔄 Loading page...\n")
        page.goto(full_url, timeout=10000)
        time.sleep(5)

        print("🔄 Scraping page 1 🕸️...\n")
        all_auctions.extend(scrape_auctions_on_page(page, county_name))

        try:
            total_pages = int(page.query_selector("#maxCA").inner_text().strip())
            print(f"✅ Total pages: {total_pages}\n")
        except:
            total_pages = 1
            print("✅ Defaulting to 1 page.\n")

        for page_num in range(2, total_pages + 1):
            print(f"🔄 Navigating to page {page_num}...\n")
            if not click_next_page(page):
                break
            time.sleep(10)
            all_auctions.extend(scrape_auctions_on_page(page, county_name))

        if all_auctions:
            df = pd.DataFrame(all_auctions)
            filename = os.path.join(
                FOLDER_NAME, f"{county_name.lower()}_{FOLDER_NAME}.xlsx"
            )
            df.to_excel(filename, index=False)
            print(f"✅ Saved to '{filename}'\n")
        else:
            print("⚠️ No auctions found.\n")

    except Exception as e:
        print(f"⚠️ Scrape failed for {county_name}: {e}\n")
    finally:
        context.close()
        browser.close()
        playwright.stop()


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
    except tl:
        print("❌ Timeout when checking yesterday's auction")
        return False


def check_last_day_prev_month_auction_simple(page, base_url):
    if now_ist.day != 1:
        return False  # Only relevant on the 1st day

    first_day = now_ist.replace(day=1)
    last_day_prev_month = first_day - timedelta(days=1)
    last_day_str = last_day_prev_month.strftime("%B-%d-%Y")

    year = last_day_prev_month.year
    month = last_day_prev_month.month
    url = update_url_month(base_url, year, month)

    try:
        page.goto(url, timeout=20000)
        page.wait_for_selector("div.CALDAYBOX", timeout=10000)
        boxes = page.query_selector_all("div.CALBOX")

        for box in boxes:
            aria_label = box.get_attribute("aria-label")
            if aria_label == last_day_str:
                caltext = box.query_selector(".CALTEXT")
                if caltext and caltext.query_selector(".CALMSG"):
                    return True
                return False
        print(f"⚠ Date {last_day_str} not found in calendar on page: {url}")
        return False

    except tl:
        print("❌ Timeout when checking last day of previous month")
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


def available():
    from database.url import URL

    p, browser, context = create_browser_context()
    page = context.new_page()
    result = []

    for county, url in URL.items():
        print(f"🔍 Checking {county}...")
        try:
            if now_ist.day != 1:
                available = check_auction_yesterday(page, url)
            else:
                available = check_last_day_prev_month_auction_simple(page, url)
            upcoming_date, auction_type = check_upcoming_auction_date(url, page)
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


def scraping():
    from database.url import COUNTY_URLS

    availability_file = f"availability_of_{FOLDER_NAME}.xlsx"
    if not os.path.exists(availability_file):
        print(f"⚠️ Missing availability file: '{availability_file}'\n")
        return

    df_availability = pd.read_excel(availability_file)

    for county, url in COUNTY_URLS.items():
        match = df_availability[df_availability["County"].str.lower() == county.lower()]
        if not match.empty:
            available = str(match.iloc[0]["Available"]).strip().lower() == "true"
            if available:
                print(f"🔄 Start Scraping {county} 🕸️...\n\n")
                scrape_county(county, url)
            else:
                print(f"▶️ Skipping {county} (NO Data Found)\n")
        else:
            print(f"⚠️ No match for {county}\n")


def main():
    available()
    scraping()


if __name__ == "__main__":
    main()
