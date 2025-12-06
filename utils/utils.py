from bs4 import BeautifulSoup
import re, os
from curl_cffi import requests
from datetime import datetime, timedelta
import usaddress

REPLACEMENTS = {
    "@A": '<div class="',
    "@B": "</div>",
    "@C": 'class="',
    "@D": "<div>",
    "@E": "AUCTION",
    "@F": "</td><td",
    "@G": "</td></tr>",
    "@H": "<tr><td ",
    "@I": "table",
    "@J": 'p_back="NextCheck=',
    "@K": 'style="Display:none"',
    "@L": '/index.cfm?zaction=auction&zmethod=details&AID=',
}

def SESSION():
    SESSION = requests.Session(impersonate='chrome')
    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",

        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',

        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",

        "upgrade-insecure-requests": "1",

        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }
    SESSION.headers.update(HEADERS)
    return SESSION

def decode_html(raw):
    html = raw
    for token, val in REPLACEMENTS.items():
        html = html.replace(token, val)
    return html

def parse_realforeclose(county, html):
    soup = BeautifulSoup(html, "html.parser")
    auctions = []

    items = soup.select(".AUCTION_ITEM")
    for item in items:
        data = {
            "aid": item.get("aid"),
            "County": county,
            "auction_type": None,
            "case_number": None,
            "case_number_url": None,
            "final_judgment": None,
            "parcel_id": None,
            "parcel_url": None,
            "property_address": None,
            "plaintiff_max_bid": None
        }

        pairs = []

        for tr in item.select("table tr"):
            tds = tr.find_all("td")
            if len(tds) >= 2:
                pairs.append((tds[0].get_text(strip=True), tds[1]))

        divs = item.select(".ad_tab > div")
        if divs:
            for i in range(0, len(divs), 2):
                label = divs[i].get_text(strip=True)
                if i + 1 < len(divs):
                    pairs.append((label, divs[i+1]))

        def is_label(text, key):
            t = text.lower()
            return key in t or t.startswith(key)
        
        for label, val_el in pairs:
            txt = val_el.get_text(strip=True)
            link = val_el.find("a")

            if is_label(label, "auction type"):
                data["auction_type"] = txt

            elif is_label(label, "case"):
                data["case_number"] = link.get_text(strip=True) if link else txt
                data["case_number_url"] = link["href"] if link else None

            elif is_label(label, "final judgment"):
                data["final_judgment"] = txt

            elif is_label(label, "parcel"):
                data["parcel_id"] = link.get_text(strip=True) if link else txt
                data["parcel_url"] = link["href"] if link else None

            elif is_label(label, "property address"):
                line1 = txt
                next_div = val_el.find_next_sibling("div", class_="AD_DTA")
                if next_div:
                    line2 = next_div.get_text(strip=True)
                    data["property_address"] = f"{line1}, {line2}"
                elif val_el.find_all_next("td", limit=2) and len(tds) == 2:
                    tds = val_el.find_all_next("td", limit=2)
                    line2 = tds[0].get_text(strip=True)
                    line3 = tds[1].get_text(strip=True)
                    data["property_address"] = f"{line1}, {line2} {line3}"
                else:
                    data["property_address"] = line1

            elif label == "":
                data["city_zip"] = txt

            elif is_label(label, "plaintiff max"):
                data["plaintiff_max_bid"] = txt

        auctions.append(data)

    return auctions

def parse_calendar(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for row in soup.select(".CALDAYBOX"):
        for box in row.select(".CALBOX"):
            
            dayid = box.get("dayid")
            
            calnum = box.select_one(".CALNUM")
            day = int(calnum.text.strip()) if calnum else None

            caltext = box.select_one(".CALTEXT")
            if caltext:
                type_name = caltext.contents[0].strip()
                active = int(caltext.select_one(".CALACT").text.strip())
                scheduled = int(caltext.select_one(".CALSCH").text.strip())
                time = caltext.select_one(".CALTIME").text.strip()
            else:
                type_name = None
                active = 0
                scheduled = 0
                time = None

            results.append({
                "date": dayid,
                "day": day,
                "type": type_name,
                "active": active,
                "scheduled": scheduled,
                "time": time
            })

    return results or None

def get_auction_date():
    real_date = datetime.now()
    yesterday = real_date - timedelta(days=1)
    AUCTION_DATE = yesterday.strftime("%m/%d/%Y")
    return AUCTION_DATE

def extract_from_address(address: str):
    address = (address or "").strip()
    if not address:
        return "", "", "FL", ""

    try:
        parsed, _ = usaddress.tag(address)
    except usaddress.RepeatedLabelError:
        parsed = {}
    zipcode = (parsed.get("ZipCode") or "").strip()
    city    = (parsed.get("PlaceName") or "").strip().upper()

    if not zipcode:
        m = re.search(r"\b(\d{5})(?:-\d{4})?\b", address)
        if m:
            zipcode = m.group(1)

    if not city:
        if "StreetNamePostDirectional" in parsed:
            maybe_city = parsed["StreetNamePostDirectional"].strip().upper()

            # If this directional word appears RIGHT BEFORE ZIP → it's a CITY
            if zipcode and maybe_city and f"{maybe_city}," in address.upper():
                city = maybe_city
                parsed.pop("StreetNamePostDirectional", None)

    if not city:
        m = re.search(r",\s*([A-Za-z\s]+)\s*,?\s*\d{5}", address)
        if m:
            city = m.group(1).strip().upper()
        else:
            if zipcode and zipcode in address:
                before_zip = address.split(zipcode)[0]
                parts = before_zip.replace(",", " ").split()
                if len(parts) >= 1:
                    city = parts[-1].strip().upper()

    street_parts = []
    for key in ["AddressNumber", "StreetNamePreDirectional",
                "StreetName", "StreetNamePostType"]:
        if key in parsed:
            street_parts.append(parsed[key])

    street = " ".join(street_parts).strip()

    if not street:
        if city and city in address:
            street = address.split(city)[0]
        elif zipcode:
            street = address.split(zipcode)[0]
        street = street.replace(",", " ").strip()

    return street, city, "FL", zipcode

def init_usaddress():
    model_path = os.path.join(os.path.dirname(__file__), "usaddress", "data", "usaddr.crfsuite")
    usaddress.TAGGER.open(model_path)