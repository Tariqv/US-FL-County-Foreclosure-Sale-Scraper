from utils import SESSION, parse_calendar
from datetime import datetime, timedelta

def find_next_upcoming(county, base_url, auction_date):
    session = SESSION()
    date_obj = datetime.strptime(auction_date, "%m/%d/%Y")

    for i in range(0, 5):  # search next 5 months
        month_start = date_obj.replace(day=1)
        month_param = month_start.strftime("%Y-%m-%d")
        url = f"{base_url}/index.cfm?zaction=user&zmethod=calendar&selCalDate={month_param}"
        res = session.get(url)
        cal_items = parse_calendar(res.text)
        for item in cal_items:
            if not item["date"]:
                continue
            if not item["type"]:
                continue
            day_date = datetime.strptime(item["date"], "%m/%d/%Y")
            if day_date > date_obj:
                return {
                    "found": True,
                    "next_date": item["date"],
                }
        date_obj = (month_start + timedelta(days=32)).replace(day=1)

    return {"found": False, "msg": "No auction found in next 5 months"}
