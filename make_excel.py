import sys
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from scraper import scrape_county
from upcoming import find_next_upcoming
from db.base_url import COUNTY_URLS
from utils import get_auction_date, extract_from_address, SESSION, init_usaddress
import os
from requests.exceptions import RequestException

EXPECTED_MAP = {
    "county": "County",
    "auction sold": "Auction Sold",
    "case": "Case #",
    "parcel id": "Parcel ID",
    "property address": "Property Address",
    "City": "City",
    "State": "State",
    "Zip": "Zip",
    "final judgment amount": "Final Judgment Amount",
    "amount": "Amount",
    "sold_to": "Sold To",
    "auction type": "Auction Type",
    "auction time": "Auction Time",
    "upcoming date": "Upcoming Date",
}

def check_404_status():
    session = SESSION()
    url = 'https://www.alachua.realforeclose.com/'
    
    r = session.get(url)
    if r.status_code in (404, 403):
        return True
    return False

def norm(x: str):
    return x.lower().strip().replace(":", "").replace("#", "").replace("_", " ")

def build_rows(county, auctions):
    rows = []
    for a in auctions:
        only_address, City, State, Zip = extract_from_address(a.get("property_address"))
        rows.append({
            "County": county.upper(),
            "Auction Sold": a.get("auction_time"),
            "Case #": a.get("case_number"),
            "Parcel ID": a.get("parcel_id"),
            "Property Address": only_address,
            "City": City,
            "State": State,
            "Zip": Zip,
            "Final Judgment Amount": a.get("final_judgment"),
            "Amount": a.get("amount"),
            "Sold To": a.get("sold_to").upper(),
            "Auction Type": a.get("auction_type") or "FORECLOSURE",
        })

    return rows

def write_excel(all_rows, sheet2_rows, output_file):
    wb = Workbook()

    ws1 = wb.active
    ws1.title = "Sheet1"

    if all_rows:
        final_cols = list(EXPECTED_MAP.values())
        ws1.append(final_cols)

        for row in all_rows:
            normalized_row = {
                EXPECTED_MAP.get(norm(k), k): v
                for k, v in row.items()
            }
            ws1.append([normalized_row.get(col) for col in final_cols])

    ws2 = wb.create_sheet("Sheet2")
    headers2 = ["County", "Upcoming Date", "Auction Type"]
    ws2.append(headers2)

    for row in sheet2_rows:
        ws2.append([row.get(h) for h in headers2])

    wb.save(output_file)

def auto_width(output_file):
    wb = load_workbook(output_file)
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = max((len(str(c.value)) for c in col if c.value), default=0)
            ws.column_dimensions[get_column_letter(col[0].column)].width = max_len + 2
    wb.save(output_file)

DEFAULT_PATH = 'FL Forclosure Final Report'
DEFAULT_AUCTION_DATE = get_auction_date()
def main(output_path=DEFAULT_PATH, auction_date=DEFAULT_AUCTION_DATE):
    init_usaddress()

    if not auction_date:
        auction_date = get_auction_date()

    all_rows = []
    sheet2_rows = []

    if check_404_status():
        print('⚠️ Please reconnect or change VPN location.')
        print('Thanks for using...')
        return

    print("👋 Welcome to FL Foreclosure County Scraper...\n")
    print(f"=== Start Scraping {auction_date} ===\n")

    os.makedirs(output_path, exist_ok=True)
    output_file = os.path.join(output_path, f"Final_{auction_date.replace('/', '-')}.xlsx")

    if os.path.exists(output_file):
        print('⚠️ File already exists → overwriting...')

    for county, base_url in COUNTY_URLS.items():
        auctions = scrape_county(county, base_url, auction_date)

        if auctions:
            rows = build_rows(county, auctions)
            all_rows.extend(rows)
        else:
            print(f'⚠️ Skipping {county} (No Data)')

        upcoming = find_next_upcoming(base_url, auction_date)

        sheet2_rows.append({
            "County": county.upper(),
            "Upcoming Date": (upcoming or {}).get('next_date')
                or "No upcoming auction found in 12 months",
            "Auction Type": "FORECLOSURE"
        })

    if not all_rows:
        print("⚠️ No 3rd party bidder auction found. Writing upcoming only.")

    write_excel(all_rows, sheet2_rows, output_file)
    auto_width(output_file)

    print(f"\n✅ DONE Saved in {output_file}")
    print("Thanks for using...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted by User')
        sys.exit(32)
    except RequestException as e:
        print(f'Request failed {e}')
        sys.exit(1)