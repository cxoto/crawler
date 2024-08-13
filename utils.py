import csv
import json
import os

import requests
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_links_to_csv(links, filename):
    # append
    with open(filename, 'a+', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for link in links:
            writer.writerow([link])


def read_from_csv(filename):
    # append
    csv_reader = csv.reader(open(filename))
    arr = []
    for row in csv_reader:
        arr.append(row[0])
    return arr


def exists(filename):
    return os.path.isfile(filename)


def download_image(image_url, save_path):
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as file:
                file.write(response.content)
            return image_url, True
        else:
            print(f"Failed to download {image_url}: Status code {response.status_code}")
            return image_url, False
    except requests.RequestException as e:
        print(f"Error downloading {image_url}: {e}")
        return image_url, False


def create_chrome_driver():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run Chrome in headless mode
    chrome_options.add_argument('--disable-images')  # Optional: Disable image loading
    chrome_options.set_capability('pageLoadStrategy', 'eager')  # Eager page load strategy
    service = Service('native/chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)  # Set page load timeout to 30 seconds
    return driver


def create_edge_driver():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run Chrome in headless mode
    # chrome_options.add_argument('--disable-images')  # Optional: Disable image loading
    # chrome_options.set_capability('pageLoadStrategy', 'eager')  # Eager page load strategy
    # service = Service('native/msedgedriver.exe')
    options = selenium.webdriver.edge.options.Options()
    options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    driver = webdriver.Edge(options=options)
    return driver
