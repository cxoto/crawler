import os

import scrapy
import execjs
import re
from bs4 import BeautifulSoup

from crawler.spiders.commonFunc import CommonFunc
from crawler.spiders.selenium_script import fetch_page_source

common_func = CommonFunc()
js_context = common_func.get_js_context()


def parse_subpage(response):
    # for src in response.css('img::attr(src)').getall():
    #     image_url = self.base_url + src
    #     image_name = src.split('/')[-1] + '.png'
    #     yield {image_url: image_url, image_name: image_name}

    title = response.css('h1.title::text').get()
    div_all = response.css('.el-tabs__content').css('.el-form-item').getall()
    output = common_func.parse_meta(div_all)
    output['title'] = title
    magnet = ''
    for script_str in response.css('script').getall():
        if script_str.find('window.__NUXT__') != -1:
            for content in common_func.find_all_bracket_content(script_str):
                print("\n execjs.eval: " + content)
                parsed_data = js_context.eval(content)
                for meg in parsed_data['oneJav']['list']:
                    magnet += '|' + meg['magnet']
    output['magnet'] = magnet
    yield output


class PrivateSpider(scrapy.Spider):
    name = "private"
    base_url = os.getenv("URL")
    start_urls = [f"{base_url}/q/cn_name=VR"]

    def parse(self, response):
        for href in response.css('a::attr(href)').getall():
            if href.find('mov') != -1:
                url_href = self.base_url + href
                print(url_href)
                yield scrapy.Request(url=url_href, callback=parse_subpage)

        total = 60
        page = 1
        while total > (page - 1) * 20:
            result = common_func.get_next_page(page, (page - 1) * 20)
            for asset_id in result['asset_ids']:
                url_href = self.base_url + '/mov/' + asset_id
                print('get_next_page: ' + url_href)
                yield scrapy.Request(url=url_href, callback=parse_subpage)
            # total = result['total']
            page = page + 1
            print('total:' + str(total))
            print('page:' + str(page))
