import json
import os
import os.path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from selenium.common import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from utils import save_json, exists, create_chrome_driver, save_arr_to_csv, read_from_csv

json_folder_path = 'home_/'
json_details_path = 'home_/asset'


def parse_meta(html_elements):
    """Parse meta information from HTML elements."""
    parsed_data = {}
    for item in html_elements:
        label_elem = item.find('label', class_='el-form-item__label')
        if not label_elem:
            continue

        label = label_elem.text.strip()
        content = ''

        content_div = item.find('div', class_='el-form-item__content')
        if content_div:
            button = content_div.find('button')
            if button:
                content = button.get('data-clipboard-text', '').strip()
            else:
                spans = content_div.find_all('span')
                content = ' '.join(span.text.strip().replace(' ', '') for span in spans)

        parsed_data[label] = content.strip()
    return parsed_data


def get_magnet_links(soup):
    """Extract magnet links from the page."""
    magnets = []
    download_info_rows = soup.find_all("tr")

    for row in download_info_rows:
        info_div = row.find("div")
        magnet_td = row.find("td", class_="btn")

        if info_div and magnet_td:
            info = info_div.text.strip()
            magnet = {info: magnet_td.get('data-clipboard-text', '').strip()}
            magnets.append(magnet)

    return magnets


def fetch(asset_id, chrome_driver):
    try:
        file_name = os.path.join(json_details_path, f'{asset_id.split("/")[2]}.json')
        if exists(file_name):
            print("file exists...")
            return
        # Load the webpage
        url = os.getenv("URL")
        chrome_driver.get(f'{url}{asset_id}')

        # Click the tab to load content
        tab_down = chrome_driver.find_element(By.ID, "tab-down")
        ActionChains(chrome_driver).click(tab_down).perform()

        # Get the page source and parse it
        content = chrome_driver.page_source
        soup = BeautifulSoup(content, 'html.parser')

        # Extract title and meta data
        title = soup.title.string.strip() if soup.title else "No Title"
        meta_divs = soup.find_all("div", class_="el-form-item")
        meta_data = parse_meta(meta_divs)
        meta_data['title'] = title

        # Extract magnet links
        magnet_links = get_magnet_links(soup)
        meta_data['magnet'] = magnet_links

        save_json(meta_data, file_name)
        print(f"finish to save: {asset_id}")
    except NoSuchElementException as e:
        print(f"can not found download info, {asset_id}")


def fetch_mov_details(chrome_driver):
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 8, 12)
    delta = timedelta(days=1)
    date = end_date
    while date >= start_date:
        date_str = date.strftime('%Y%m%d')
        print("start: " + date_str)
        json_filename = os.path.join(json_folder_path, f'{date_str}.json')
        with open(json_filename, 'r') as json_file:
            json_data = json.load(json_file)
            for asset in json_data:
                asset_id = asset['link']
                print(f"assetId: {asset_id}")
                try:
                    fetch(asset["link"], chrome_driver)
                except Exception:
                    print(f"asset_id: {asset_id}, fetch error")
        date -= delta


def fetch_mov_details_for_date(date_str):
    json_filename = os.path.join(json_folder_path, f'{date_str}.json')
    with open(json_filename, 'r') as json_file:
        json_data = json.load(json_file)
        driver = create_chrome_driver()
        error_links = []
        for asset in json_data:
            asset_id = asset['link']
            try:
                fetch(asset_id, driver)
            except Exception:
                print(f"asset_id: {asset_id}, fetch error")
                error_links.append(asset_id)
        if len(error_links) != 0:
            save_arr_to_csv(error_links, "mov_fetch_error.csv")
        driver.quit()


def main():
    start_date = datetime(2016, 10, 15)
    end_date = datetime(2024, 8, 14)
    delta = timedelta(days=1)

    date_list = []
    date = start_date
    while date <= end_date:
        date_list.append(date.strftime('%Y%m%d'))
        date += delta

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.map(fetch_mov_details_for_date, date_list)


if __name__ == "__main__":
    main()
