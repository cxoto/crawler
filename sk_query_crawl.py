from bs4 import BeautifulSoup
import os
import urllib

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

from utils import exists, download_image, save_json, create_chrome_driver, create_edge_driver

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


def main(sp_no_first, c_driver):
    data = []
    try:
        print("start query: " + sp_no_first)
        json_filename = os.path.join(json_folder_path, f'{sp_no_first}.json')
        if exists(json_filename):
            print(f"file: {json_filename} exists...")
            return
        url = os.getenv("URL")
        c_driver.get(f'{url}{sp_no_first}')

        click_downloadable_span(c_driver)

        soup = poll_click_(c_driver)
        fetch_mov_detail(data, soup)
        page_numbers = soup.find_all('li', class_='number')
        max_page_size = len(page_numbers)
        while True:
            for page in page_numbers:
                is_active_page = len(page.get('class')) == 2
                page_number = int(page.text.strip())
                if is_active_page and page_number == max_page_size:
                    break
                if is_active_page:
                    click_ = driver.find_elements(By.CLASS_NAME, "number")[page_number]
                    ActionChains(driver).click(click_).perform()
                    content = c_driver.page_source
                    soup = BeautifulSoup(content, 'html.parser')
                    fetch_mov_detail(data, soup)
        print(data)
        save_json(data, json_filename)
        # Print the output
        print("finish: " + sp_no_first)
    except Exception as e:
        print(f"failed to query: {sp_no_first}")


def poll_click_(c_driver):
    while True:
        content = c_driver.page_source
        soup = BeautifulSoup(content, 'html.parser')
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
            "image_url": image_url
        })


def click_downloadable_span(c_driver):
    switch_to_downloadable = driver.find_element(By.CLASS_NAME, "el-switch__label--right")
    ActionChains(c_driver).click(switch_to_downloadable).perform()


if __name__ == "__main__":
    no = ["START"]
    driver = create_chrome_driver()
    while len(no) > 0:
        main(no.pop(), driver)

    driver.quit()
