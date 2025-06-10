import os
import pytz
import subprocess
import contextlib
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC

def get_driver():
    options = Options()
    service = Service()
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--start-minimized") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=2")  # Suppress Chrome internal logs
    service.creation_flags = subprocess.CREATE_NO_WINDOW

    service = Service(log_path=os.devnull)  # Silence ChromeDriver output

    # Suppress all stdout/stderr (covers underlying native libs like TensorFlow Lite)
    with open(os.devnull, 'w') as fnull, contextlib.redirect_stdout(fnull), contextlib.redirect_stderr(fnull):
        driver = webdriver.Chrome(options=options, service=service)
        driver.minimize_window()
    return driver

def check_auction_yesterday(url, driver):
    # IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    yesterday = now_ist - timedelta(days=1)

    # Format date to match aria-label e.g. "May-31-2025"
    yesterday_str = yesterday.strftime("%B-%d-%Y")  # Month-fullname-Day-Year

    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # Wait for calendar container to load
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "CALDAYBOX")))

    # Note: Removed day==1 check here because we handle it in main()
    
    # Find all day boxes
    day_boxes = driver.find_elements(By.CSS_SELECTOR, "div.CALBOX.CALW5")

    yesterday_box = None
    for box in day_boxes:
        aria_label = box.get_attribute("aria-label")
        if aria_label == yesterday_str:
            yesterday_box = box
            break

    if not yesterday_box:
        print(f"⚠️ Date {yesterday_str} not found in calendar on page: {url}")
        return False

    # Check for presence of <span class="CALTEXT"> with <span class="CALMSG"> inside
    try:
        caltext = yesterday_box.find_element(By.CLASS_NAME, "CALTEXT")
        calmsg = caltext.find_element(By.CLASS_NAME, "CALMSG")
        # If found, auction data is available
        return True
    except NoSuchElementException:
        # If CALTEXT or CALMSG not found, no auction data for that day
        return False
def update_url_month(url, year, month):
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    """
    Replace selCalDate param in the URL with the first day of given year-month,
    format needed: {ts 'YYYY-MM-DD 00:00:00'}
    URL encoded as %7Bts%20%27YYYY-MM-DD%2000%3A00%3A00%27%7D
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    date_str = f"{year:04d}-{month:02d}-01 00:00:00"
    ts_val = f"{{ts '{date_str}'}}"  # raw format before url encoding

    # Encode ts_val properly for URL param
    # urllib.parse.urlencode will encode correctly, but parse_qs uses list of values
    qs['selCalDate'] = [ts_val]

    new_query = urlencode(qs, doseq=True)
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    return new_url

def check_upcoming_auction_date_for_month(url, driver, start_date):
    ist = pytz.timezone('Asia/Kolkata')
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "CALDAYBOX")))

    day_boxes = driver.find_elements(By.CSS_SELECTOR, "div.CALBOX.CALW5")

    earliest_date = None
    earliest_type = None

    for box in day_boxes:
        aria_label = box.get_attribute("aria-label")
        if not aria_label:
            continue

        try:
            box_date = datetime.strptime(aria_label, "%B-%d-%Y")
            box_date = ist.localize(box_date)
        except Exception:
            continue

        if box_date < start_date:
            continue

        try:
            caltext = box.find_element(By.CLASS_NAME, "CALTEXT")
            full_text = caltext.text.lower()

            if not full_text.strip():
                continue

            types = []
            if "foreclosure" in full_text or "fc" in full_text:
                types.append("Foreclosure")
            if "tax deed" in full_text or "taxdeed" in full_text or "td" in full_text:
                types.append("Taxdeed")

            auction_type = "/".join(types) if types else "Unknown"

            # Skip if only Taxdeed (no Foreclosure)
            if auction_type == "Taxdeed":
                continue

            # Accept if Foreclosure or Foreclosure/Taxdeed
            if earliest_date is None or box_date < earliest_date:
                earliest_date = box_date
                earliest_type = auction_type

        except NoSuchElementException:
            continue

    if earliest_date:
        return earliest_date.strftime("%m/%d/%Y"), earliest_type
    else:
        return None, None

def check_upcoming_auction_date(url, driver):
    """
    Try months from yesterday's month till December 2025.
    Update URL to month using selCalDate param.
    Return first found upcoming auction date and type.
    """
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist)
    start_date = today - timedelta(days=1)  # start from yesterday

    year = start_date.year
    month = start_date.month

    # Limit search to Dec 2025
    while (year < 2025) or (year == 2025 and month <= 12):
        new_url = update_url_month(url, year, month)

        date_found, auction_type = check_upcoming_auction_date_for_month(new_url, driver, start_date)
        if date_found:
            return date_found, auction_type

        # Increment month
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        # After first month, reset start_date to first of next month
        start_date = ist.localize(datetime(year, month, 1))

    return None, None

def main():
    from database.calendar_database import URL  # your county URLs
    from Scraper import day_1_Scraper
    
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)

    # RUN day_1_Scraper ONLY if today is 1, then EXIT immediately
    if now_ist.day == 1:
        day_1_Scraper.main()
        return  # exit, don't run anything else

    driver = get_driver()
    result = []
    for county, url in URL.items():
        print(f"Checking {county} 🔍...")
        upcoming_date, auction_type = check_upcoming_auction_date(url, driver)
        available = check_auction_yesterday(url, driver)
        result.append({
            "County":county,
            "Available": available,
            "County": county,
            "Upcoming Date": upcoming_date or "None",
            "Auction Type": auction_type or "None"
        })
    driver.quit()

    import pandas as pd
    df = pd.DataFrame(result)
    yesterday = now_ist - timedelta(days=1)
    filename = yesterday.strftime("availability_of_%m-%d-%Y") + ".xlsx"
    df.to_excel(filename, index=False)
    print(f"✅ Results saved to {filename}")
    print(result)
if __name__ == "__main__":
    main()