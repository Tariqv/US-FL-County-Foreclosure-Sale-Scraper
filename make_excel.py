import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from scraper import scrape_county
from upcoming import find_next_upcoming
from db.base_url import COUNTY_URLS
from utils import get_auction_date, extract_from_address, SESSION
import os

date = get_auction_date()

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
    if r.status_code == 404:
        return True
    return False

def norm(x: str):
    return x.lower().strip().replace(":", "").replace("#", "").replace("_", " ")

def build_rows(county, auctions):
    rows = []
    for a in auctions:
        City, State, Zip = extract_from_address(a.get("property_address"))
        rows.append({
            "County": county.upper(),
            "Auction Sold": a.get("auction_time"),
            "Case #": a.get("case_number"),
            "Parcel ID": a.get("parcel_id"),
            "Property Address": a.get("property_address"),
            "City": City,
            "State": State,
            "Zip": Zip,
            "Final Judgment Amount": a.get("final_judgment"),
            "Amount": a.get("amount"),
            "Sold To": a.get("sold_to").upper(),
            "Auction Type": a.get("auction_type") or "FORECLOSURE",
        })

    return rows


def main():
    all_rows = []
    sheet2_rows = []

    if check_404_status():
        print('Please Reconnect or Change loaction from Vpn.')
        print('Thanks For Using...')
        return

    for county, base_url in COUNTY_URLS.items():
        auctions = scrape_county(county, base_url, date)
        if auctions:
            rows = build_rows(county, auctions)
            all_rows.extend(rows)
        else:
            print(f'⚠️ Skipping {county} No Data Found.')
        upcoming = find_next_upcoming(county, base_url, date)
        sheet2_rows.append({
            "County": county.upper(),
            "Upcoming Date": upcoming.get('next_date') or "",
            "Auction Type": "FORECLOSURE"
        })
    df = pd.DataFrame(all_rows)
    normalized = {
        col: EXPECTED_MAP[norm(col)]
        for col in df.columns
        if norm(col) in EXPECTED_MAP
    }
    output_folder = "FL Forclosure Final Report"
    os.makedirs(output_folder, exist_ok=True)
    df = df.rename(columns=normalized)
    final_cols = list(EXPECTED_MAP.values())
    df = df[[c for c in final_cols if c in df.columns]]
    output_file =  os.path.join(output_folder, f"Final_{date.replace('/', '-')}.xlsx")
    df.to_excel(output_file, index=False)
    wb = load_workbook(output_file)
    ws = wb.active
    for col in ws.columns:
        width = max((len(str(c.value)) for c in col if c.value), default=0) + 2
        ws.column_dimensions[get_column_letter(col[0].column)].width = width
    wb.save(output_file)
    df2 = pd.DataFrame(sheet2_rows)

    with pd.ExcelWriter(output_file, engine="openpyxl", mode="a") as writer:
        df2.to_excel(writer, sheet_name="Sheet2", index=False)

    print("\n✅ DONE Saved in ", output_file)
    print('Thanks For Using...')