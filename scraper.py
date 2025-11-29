from utils import SESSION, parse_realforeclose, decode_html
from pprint import pprint

def scrape_page(session, base_url, area="C", page_dir=0, county=None):
    load_url = (
        f"{base_url}/index.cfm?zaction=AUCTION"
        f"&Zmethod=UPDATE&FNC=LOAD&AREA={area}&PageDir={page_dir}"
    )
    res = session.get(load_url)
    try:
        load_json = res.json()
    except Exception:
        return []
    if not load_json or "retHTML" not in load_json:
        return []
    html_raw = decode_html(load_json["retHTML"])
    html_items = parse_realforeclose(county, html_raw)
    update_url = (
        f"{base_url}/index.cfm?zaction=AUCTION&ZMETHOD=UPDATE&FNC=UPDATE"
    )
    try:
        update_json = session.get(update_url).json()
        update_dict = parse_update_dict(update_json)
    except Exception:
        update_dict = {}
    for item in html_items:
        aid = item.get("aid")
        if aid in update_dict:
            item.update(update_dict[aid])

    return html_items


def parse_update_dict(update_json):
    items = update_json.get("ADATA", {}).get("AITEM", [])
    out = {}
    for it in items:
        aid = it.get("AID")
        if not aid:
            continue
        out[aid] = {
            "auction_time": it.get("B") or None,
            "sold_to": it.get('ST'),
            "amount": it.get('D'),
        }
    return out

def scrape_county(county_name, base_url, auction_date):
    print(f"\n=== Scraping {county_name} ===")
    final_auctions = []

    session = SESSION()
    print(f"🔄 Start Scraping {county_name} 🕸️...")
    preview = f"{base_url}/index.cfm?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE={auction_date}"
    session.get(preview)
    all_auctions = []
    print("🔄 Scraping page 1 🕸️...")
    page0 = scrape_page(session, base_url, "C", 0, county_name)
    all_auctions.extend(page0)
    if not all_auctions:
        return None
    try:
        upd = session.get(f"{base_url}/index.cfm?zaction=AUCTION&ZMETHOD=UPDATE&FNC=UPDATE").json()
        max_pages = int(upd.get("CM", 1))
        print(f"📄 Total Pages: {max_pages}")
    except:
        max_pages = 1
        print("✅ Defaulting to 1 page.")

    for p in range(1, max_pages):
        print(f"🔄 Navigating to page {p}...")
        page_result = scrape_page(session, base_url, "C", p, county_name)
        all_auctions.extend(page_result)
    for auction in all_auctions:
        parcel = str(auction.get("parcel_id", "")).upper()

        is_timeshare = (
            "TS" in parcel or
            "WK" in parcel or
            "TIMESHARE" in parcel
        )
        if auction.get('sold_to') == '3rd Party Bidder' and not is_timeshare:
            final_auctions.append(auction)
            auction.pop("aid", None)
    if final_auctions:
        print(f"✅ Finished {county_name} Scraping: ({len(final_auctions)}) 3rd party Found.")
    return final_auctions