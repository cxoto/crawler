import json
import os
import os.path
from datetime import datetime, timedelta

from utils import save_arr_to_csv

json_folder_path = 'home_/'


def parse_sp_no():
    start_date = datetime(2016, 10, 15)
    end_date = datetime(2024, 8, 12)
    delta = timedelta(days=1)
    date = end_date
    sp_no = set()
    while date >= start_date:
        date_str = date.strftime('%Y%m%d')
        print("start: " + date_str)
        json_filename = os.path.join(json_folder_path, f'{date_str}.json')
        with open(json_filename, 'r') as json_file:
            try:
                json_data = json.load(json_file)
                for asset in json_data:
                    sp_no.add(asset["title"].split("-")[0])
            except Exception as e:
                print(f"{date} file can not load: {e}")
        date -= delta
    save_arr_to_csv(sp_no, "sp_no.csv")


if __name__ == "__main__":
    parse_sp_no()
