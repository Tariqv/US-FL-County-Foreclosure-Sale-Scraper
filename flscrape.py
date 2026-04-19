from re import sub
import sys
import make_excel
from config import get_config
from utils.utils import get_auction_date
from requests.exceptions import RequestException

def main():
    config = get_config()

    sub_days = 1
    if user_sub_days := config.get("subtraction_date"):
        try:
            sub_days = int(user_sub_days)
            print(f"SETTING SUBTRACTION DATE TO {user_sub_days}")
        except (ValueError, TypeError):
            print("Invalid subtraction_date, using default 1")
            sub_days = 1
    
    auction_date = get_auction_date(sub_days=sub_days)
    path = config.get('output_path', make_excel.DEFAULT_PATH)
    make_excel.main(path, auction_date)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted by User')
        sys.exit(32)
    except RequestException as e:
        print(f'Request failed {e}')
        sys.exit(1)