import csv
import json
import os

import requests


def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_links_to_csv(links, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['link'])  # 写入表头
        for link in links:
            writer.writerow([link])


def exists(filename):
    return os.path.isfile(filename)


def download_image(image_url, save_path):
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as file:
                file.write(response.content)
            return (image_url, True)
        else:
            print(f"Failed to download {image_url}: Status code {response.status_code}")
            return (image_url, False)
    except requests.RequestException as e:
        print(f"Error downloading {image_url}: {e}")
        return (image_url, False)
