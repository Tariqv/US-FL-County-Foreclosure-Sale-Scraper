import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from db import COUNTY_URLS
from scraper import scrape_county
from upcoming import find_next_upcoming
from curl_cffi import requests
TEST_DATE = '11/18/2025'

def is_us_ip():
    try:
        r = requests.get("http://ip-api.com/json", timeout=5).json()
        return r.get("country") == "United States"
    except Exception:
        return False

@pytest.mark.real
@pytest.mark.skipif(not is_us_ip(), reason="Requires US VPN")
def test_scrape_all_counties():
    failures = []

    for county, base_url in COUNTY_URLS.items():
        print(f"\n=== Testing {county} ===")

        try:
            items = scrape_county(county, base_url, TEST_DATE)
            assert items is None or isinstance(items, list)
            if items:
                assert isinstance(items[0], dict)
        except Exception as e:
            failures.append((county, f"scrape_county failed: {e}"))
    if failures:
        print("\n❌ FAILURES:")
        for c, err in failures:
            print(f"  - {c}: {err}")
        assert False, f"{len(failures)} counties failed. See above."
    else:
        print("\n✅ All counties passed scrape_county")


@pytest.mark.real
@pytest.mark.skipif(not is_us_ip(), reason="Requires US VPN")
def test_find_upcoming_all_counties():
    failures = []

    for county, base_url in COUNTY_URLS.items():
        print(f"\n=== Testing Upcoming for {county} ===")

        try:
            result = find_next_upcoming(county, base_url, TEST_DATE)
            assert isinstance(result, dict)
            assert "found" in result

        except Exception as e:
            failures.append((county, f"find_next_upcoming failed: {e}"))

    if failures:
        print("\n❌ FAILURES:")
        for c, err in failures:
            print(f"  - {c}: {err}")
        assert False, f"{len(failures)} counties failed."
    else:
        print("\n✅ All counties passed upcoming checking")
