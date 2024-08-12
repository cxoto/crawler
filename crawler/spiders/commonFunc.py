# _*_ coding:utf-8 _*_
import os

import execjs
from bs4 import BeautifulSoup
import requests
import pandas as pd
from numpy import random
from pandas import json_normalize


def extract_content(s, start='{', end='}'):
    count = 0
    start_idx = None
    for i, c in enumerate(s):
        if c == start:
            if count == 0:
                start_idx = i
            count += 1
        elif c == end:
            count -= 1
            if count == 0 and start_idx is not None:
                return s[start_idx:i + 1]

    return None


class CommonFunc:

    @classmethod
    def parse_meta(cls, html_data):
        parsed_data = {}
        for item in html_data:
            soup = BeautifulSoup(item.replace('\n', ''), 'html.parser')
            label = soup.find('label', class_='el-form-item__label').text.strip()
            content = ''
            if label == '番号':
                content = soup.find('button').attrs.get('data-clipboard-text').strip()
            else:
                for span in soup.find('div', class_='el-form-item__content').findAll('span'):
                    content += ' ' + span.text.strip().replace(' ', '')
            parsed_data[label] = content.replace(' ', '', 1)
        return parsed_data

    @classmethod
    def get_next_page(cls, page, offset):

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/json;charset=UTF-8",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin"
        }
        data = {
            "class": "mov",
            "para": "search",
            "j": {
                "data": {
                    "query": {
                        "bool": {
                            "must": [{"match_phrase": {"cn_name": "VR"}}, {"match": {"hasDown": True}}]
                        }
                    },
                    "size": 20,
                    "from": offset,
                    "sort": {"movDate": {"order": "desc"}}
                },
                "page": page
            }
        }
        response = requests.post(f'{os.getenv("URL")}/a', headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            # 提取 JSON 响应
            json_response = response.json()
            print(json_response['list'])
            df = json_normalize(json_response, record_path=['list'])
            return {'total': json_response['total'], 'asset_ids': df['_id'].tolist()}
        else:
            return {'total': 0, 'asset_ids': []}

    @classmethod
    def find_all_bracket_content(cls, s):
        stack = []
        contents = []
        for i, c in enumerate(s):
            if c == '{':
                stack.append(i)
            elif c == '}':
                if stack:
                    start_idx = stack.pop()
                    content = extract_content(s[start_idx:], '{', '}')
                    if content:
                        contents.append(content)
                else:
                    return None
        one_jav = []
        for content in contents:
            if 0 < content.find('oneJav') < 40:
                one_jav.append(content)

        return one_jav

    @classmethod
    def get_js_context(cls):
        variable_ = """
                    a='a'; b='b'; c='c'; d='d'; e='e'; f='f'; g='g'; h='h'; i='i'; j='j'; k='k'; l='l'; m='m'; n='n'; o='o'; p='p'; q='q'; r='r'; s='s'; t='t'; u='u'; v='v'; w='w'; x='x'; y='y'; z='z'; A='a'; B='b'; C='c'; D='d'; E='e'; F='f'; G='g'; H='h'; I='i'; J='j'; K='k'; L='l'; M='m'; N='n'; O='o'; P='p'; Q='q'; R='r'; S='s'; T='t'; U='u'; V='v'; W='w'; X='x'; Y='y'; Z='z'; 
                    """
        return execjs.compile(variable_)
