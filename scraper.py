from utils import SESSION, parse_realforeclose, decode_html

def scrape_page(session, base_url, area="C", page_dir=0, county=None):
    load_url = (
        f"{base_url}/index.cfm?zaction=AUCTION"
        f"&Zmethod=UPDATE&FNC=LOAD&AREA={area}&bypassPage={page_dir}")
    res = session.get(load_url)
    try:
        load_json = res.json()
    except Exception:
        return []
    if not load_json or "retHTML" not in load_json:
        return []
    html_raw = decode_html(load_json["retHTML"])
    html_items = parse_realforeclose(county, html_raw)
    update_url = f"{base_url}/index.cfm?zaction=AUCTION&ZMETHOD=UPDATE&FNC=UPDATE"
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
        return []
    try:
        upd = session.get(f"{base_url}/index.cfm?zaction=AUCTION&ZMETHOD=UPDATE&FNC=UPDATE").json()
        max_pages = int(upd.get("CM", 1))
        print(f"📄 Total Pages: {max_pages}")
    except Exception:
        max_pages = 1
        print("✅ Defaulting to 1 page.")

    for p in range(2, max_pages + 1):
        print(f"🔄 Navigating to page {p}...")
        page_result = scrape_page(session, base_url, "C", p, county_name)
        all_auctions.extend(page_result)
    
    def make_key(ac):
        return (
            ac.get("case_number")
            or ac.get("aid")
            or ac.get("final_judgment")
            or ac.get("property_address")
            or ac.get("parcel_id")
        )

    def dedupe_auctions(data):
        if not data or []:
            return []
        seen = set()
        out = []

        for ac in data:
            key = make_key(ac)

            if not key or key in seen:
                continue

            seen.add(key)
            out.append(ac)
        return out

    for auction in dedupe_auctions(all_auctions):
        parcel = str(auction.get("parcel_id", "PARCEL_ID")).upper()
        is_timeshare = (
            "TS" in parcel or
            "TIMESHARE" in parcel
        )
        if not auction.get('sold_to'):
            continue
        if 'taxdeed' in (auction.get('auction_type') or '').lower():
            print('⚠️ Found taxdeed skipping auction.')
            continue
        if '3rd Party' in auction.get('sold_to') and not is_timeshare:
            final_auctions.append(auction)
            auction.pop("aid", None)            
        elif is_timeshare:
            print('⚠️ Found timeshare skipping this auction.')
            continue

    if final_auctions:
        print(f"✅ Finished {county_name} Scraping: ({len(final_auctions)}) 3rd party Found.")
    return final_auctions