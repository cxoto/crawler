import os
import re
import json
import urllib

import requests
import csv
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from firecrawl import FirecrawlApp

from utils import save_json, download_image, save_links_to_csv

# 基础路径配置
base_image_path = 'home/img/'
base_csv_path = 'home/mov/'
json_folder_path = 'home/'

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


# 获取当前日期，并计算一年的日期
start_date = datetime(2024, 1, 6)
end_date = datetime(2024, 2, 1)
delta = timedelta(days=1)

date = start_date
all_links = []

while date <= end_date:
    # 生成 URL
    print("开始：", date)
    date_str = date.strftime('%Y%m%d')
    url = f'{os.getenv("URL")}/day/{date_str}'

    response = FirecrawlApp(api_key='fc-b6b1099b21bf4d79b3cd0fb604f4afaa').scrape_url(url=url)
    markdown_data = response.get("content", "")

    # 正则表达式匹配
    pattern = re.compile(r'!\[\]\((.*?)\)\\\n\\\n### (.*?)\]\((.*?)\)')
    matches = pattern.findall(markdown_data)

    # 收集图片 URLs 和数据
    image_urls = []
    data = []
    for image_url, title, link in matches:
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
        all_links.append(link)

    # 处理图片
    download_results = download_images(image_urls)

    # 更新数据中图片下载失败的标记
    for entry in data:
        if download_results.get(entry["image_url"], True) == False:
            entry["download_failed"] = True

    # 保存 JSON 文件
    json_filename = os.path.join(json_folder_path, f'{date_str}.json')
    save_json(data, json_filename)

    print("结束：", date)
    # 递增日期
    date += delta

    # 等待2分钟
    print(f"Waiting for 2 minutes before the next run...")
    time.sleep(120)

# 保存所有链接到 CSV 文件
csv_filename = os.path.join(base_csv_path, 'list.csv')
save_links_to_csv(all_links, csv_filename)

print("数据抓取和文件保存完成。")
