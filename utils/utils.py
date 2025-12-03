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

def extract_auctions(decoded_html):
    blocks = re.findall(
        r'<div id="AITEM_[0-9]+".*?</div>@A@E_ITEM_SPACER',
        decoded_html,
        flags=re.DOTALL,
    )

    auctions = []
    for block in blocks:
        auctions.append(parse_block(block))

    return auctions

def parse_block(block):
    soup = BeautifulSoup(block, "html.parser")
    text = [t.strip() for t in soup.stripped_strings]

    data = {}

    for i, t in enumerate(text):
        if t == "Auction Type:":
            data["auction_type"] = text[i+1]

        elif t == "Case #:":
            data["case_number"] = text[i+1]

        elif t == "Final Judgment Amount:":
            data["final_judgment"] = text[i+1]

        elif t == "Parcel ID:":
            data["parcel_id"] = text[i+1]

        elif t == "Property Address:":
            data["property_address"] = text[i+1] + " " + text[i+2]

        elif t == "Plaintiff Max Bid:":
            data["plaintiff_max_bid"] = text[i+1]

    return data

def retHTML_to_json(retHTML):
    decoded = decode_html(retHTML)
    return extract_auctions(decoded)

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

        # TABLE FORMAT
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
                if val_el.find_next("td"):
                    line2 = val_el.find_next("td").get_text(strip=True)
                    line3 = val_el.find_next("td").find_next("td").get_text(strip=True)
                    data["property_address"] = f"{line1} {line2} {line3}"
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
    address = str(address).strip()
    if not address:
        return "", "FL", "", ""
    try:
        parsed, _ = usaddress.tag(address)
    except:
        parsed = {}
    city = parsed.get("PlaceName", "").strip().upper()
    state = parsed.get("StateName", "").replace("-", "").strip().upper()
    zipcode = parsed.get("ZipCode", "").strip()
    address_parts = []
    for key, value in parsed.items():
        if key in ("PlaceName", "StateName", "ZipCode"):
            continue
        address_parts.append(value)
    street_address = " ".join(address_parts).strip()
    return street_address, city, state, zipcode


def init_usaddress():
    model_path = os.path.join(os.path.dirname(__file__), "usaddress", "data", "usaddr.crfsuite")
    usaddress.TAGGER.open(model_path)