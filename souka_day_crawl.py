
from bs4 import BeautifulSoup
import os
import urllib

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import exists, download_image, save_json, create_chrome_driver

# 基础路径配置
base_image_path = 'home_/img/'
base_csv_path = 'home_/mov/'
json_folder_path = 'home_/'

# 最大线程数
MAX_THREADS = 5


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


def main(date_, driver):
    # Initialize the WebDriver

    data = []
    date_str = date_.strftime('%Y%m%d')
    try:
        print("start: " + date_str)
        json_filename = os.path.join(json_folder_path, f'{date_str}.json')
        if exists(json_filename):
            print(f"file: {json_filename} exists...")
            return
        url = os.getenv("URL")
        driver.get(f'{url}/day/{date_str}')

        # Get the page source and parse it
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')

        image_urls = []
        # Extract title and meta data
        assets = soup.find_all("div", class_="d_mov")
        for asset in assets:
            title = asset.find('h3').text.strip()
            image_url = asset.find('img').get('src')
            link = asset.find('a').get('href')
            if image_url:
                # 收集图片 URL
                if 'ps.jpg' in image_url:
                    pl_image_url = image_url.replace('ps.jpg', 'pl.jpg')
                    image_urls.extend([image_url, pl_image_url])
                else:
                    image_urls.append(image_url)

            # 保存数据
            data.append({
                "title": title,
                "image_url": image_url,
                "link": link,
                "download_failed": False  # 默认图片下载成功
            })

        # 处理图片
        download_results = download_images(image_urls)
        # 更新数据中图片下载失败的标记
        for entry in data:
            if not download_results.get(entry["image_url"], True):
                entry["download_failed"] = True

        # 保存 JSON 文件
        save_json(data, json_filename)
        # Print the output
        print("finish: " + date_str)
    except Exception as e:
        print(f"failed to fetch: {date_str}")


if __name__ == "__main__":
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    delta = timedelta(days=1)
    date = start_date
    driver = create_chrome_driver()
    while date <= end_date:
        main(date, driver)
        date += delta
    driver.quit()
