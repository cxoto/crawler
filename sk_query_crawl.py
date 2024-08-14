from time import sleep

from bs4 import BeautifulSoup
import os
import urllib

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

from utils import exists, download_image, save_json, create_chrome_driver, create_edge_driver, read_from_csv, \
    save_arr_to_csv
from wait_page_load import wait_page_load

# 基础路径配置
base_image_path = 'home_/img/'
base_csv_path = 'home_/mov/'
json_folder_path = 'home_/no/'

# 最大线程数
MAX_THREADS = 10


# 生成图片保存路径
def get_save_path(image_url, base_path):
    # 解析 URL
    parsed_url = urllib.parse.urlparse(image_url)
    path = parsed_url.path  # 获取路径部分
    # 提取文件名
    image_name = os.path.basename(path)
    # 生成保存路径
    # 去掉 URL 路径前的 / 并生成完整的保存路径
    save_path = os.path.join(base_path, path.lstrip('/'))
    # 返回完整的保存路径
    return save_path


# 下载图片和 .pl.jpg 后缀图片的函数
def download_images(image_urls):
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_url = {executor.submit(download_image, url, get_save_path(url, base_image_path)): url for url in
                         image_urls}
        results = {}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                image_url, success = future.result()
                results[image_url] = success
                if success:
                    print(f"Successfully downloaded {image_url}")
                else:
                    print(f"Failed to download {image_url}")
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results[url] = False
        return results


def main(sp_no_first):
    c_driver = create_chrome_driver()
    data = []
    try:
        print("start query: " + sp_no_first)
        json_filename = os.path.join(json_folder_path, f'{sp_no_first}.json')
        if exists(json_filename):
            print(f"file: {json_filename} exists...")
            return
        url = os.getenv("URL")
        c_driver.get(f'{url}{sp_no_first}')

        # click_downloadable_span(c_driver)

        soup = BeautifulSoup(c_driver.page_source, 'html.parser')  # poll_click_(c_driver)
        fetch_mov_detail(data, soup)
        page_numbers = soup.find_all('li', class_='number')
        active_page = int(soup.find('li', class_='number active').text)
        max_page_size = len(page_numbers)
        while active_page < max_page_size:
            soup = click_to_next_page(active_page, c_driver)
            while not (active_page + 1 == int(
                    soup.find('li', class_='number active').text)) and active_page < max_page_size:
                soup = click_to_next_page(active_page, c_driver)
            active_page += 1
            sleep(3)
            soup = BeautifulSoup(c_driver.page_source, 'html.parser')
            fetch_mov_detail(data, soup)
        if len(data) < 5:
            save_arr_to_csv(data, "temp.json")
        else:
            save_json(data, json_filename)
        print("finish: " + sp_no_first)
    except Exception as e:
        print(f"failed to query: {sp_no_first}, error: {e}")
    c_driver.quit()


def click_to_next_page(active_page, c_driver):
    click_ = c_driver.find_elements(By.CLASS_NAME, "number")[active_page]
    ActionChains(c_driver).click(click_).perform()
    soup = BeautifulSoup(c_driver.page_source, 'html.parser')
    return soup


def poll_click_(c_driver):
    while True:
        soup = BeautifulSoup(c_driver.page_source, 'html.parser')
        find = soup.find('span', class_='el-switch__label--right')
        if len(find.get("class")) == 3:
            break
        click_downloadable_span(c_driver)
    return soup


def fetch_mov_detail(data, soup):
    assets = soup.find_all("div", class_="el-card__body")
    for asset in assets:
        image_url = asset.find('img').get('src')
        sp_id = asset.find('a', class_='a_name').get('href')
        sp_no = asset.find('span', class_='sp_no').text.strip()
        sp_name = asset.find('span', class_='sp_name').text.strip()
        sp_time = asset.find('span', class_='sp_time').text.strip()
        # 保存数据
        data.append({
            "sp_id": sp_id,
            "sp_no": sp_no,
            "sp_name": sp_name,
            "sp_time": sp_time,
            "image_url": image_url,
            "downloadable": asset.find('i', class_='fa fa-download') is not None
        })


def click_downloadable_span(c_driver):
    switch_to_downloadable = c_driver.find_element(By.CLASS_NAME, "el-switch__label--right")
    ActionChains(c_driver).click(switch_to_downloadable).perform()


if __name__ == "__main__":
    sp_no_arr = read_from_csv('sp_no.csv')
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.map(main, sp_no_arr)
