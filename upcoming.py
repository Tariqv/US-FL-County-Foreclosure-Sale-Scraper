from utils import SESSION, parse_calendar
from datetime import datetime, timedelta

def find_next_upcoming(base_url, auction_date):
    session = SESSION()
    base_date = datetime.strptime(auction_date, "%m/%d/%Y")
    date_cursor = base_date

    for _ in range(12):
        month_start = date_cursor.replace(day=1)

        url = f"{base_url}/index.cfm?zaction=user&zmethod=calendar&selCalDate={month_start.strftime('%Y-%m-%d')}"
        res = session.get(url)
        cal_items = parse_calendar(res.text)
        for item in cal_items:
            date = item.get('date')
            if not date or not item.get('type'):
                continue

            day_date = datetime.strptime(date, "%m/%d/%Y")

            if day_date > base_date:
                return {
                    "found": True,
                    "next_date": date,
                }

        date_cursor = (month_start + timedelta(days=32)).replace(day=1)

    return {"found": False, "msg": "No auction found in next 12 months"}
