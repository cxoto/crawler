import json
import os
import os.path
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from utils import save_json, exists

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

        if label == '番号':
            button = item.find('button')
            if button:
                content = button.get('data-clipboard-text', '').strip()
        else:
            content_div = item.find('div', class_='el-form-item__content')
            if content_div:
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

    except NoSuchElementException as e:

        print(f"can not found download info, {asset_id}")
    finally:
        print(f"finish to save: {asset_id}")


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


if __name__ == "__main__":
    # Initialize the WebDriver
    service = Service('native/chromedriver.exe')
    driver = webdriver.Chrome(service=service)
    fetch_mov_details(driver)
    driver.quit()
