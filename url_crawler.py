import asyncio
import json
from typing import Dict
from typing import List

import aiohttp
from bs4 import BeautifulSoup

from io_util import read_file, output_iterator

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15"}


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    await asyncio.sleep(4)
    async with session.get(url) as response:
        return await response.text()


def parse_home_page(html_doc) -> List[str]:
    soup = BeautifulSoup(html_doc, 'html.parser')
    res = soup.find_all(name='h3',
                        attrs={'class': "letter-list__filter-title"})
    result_list: List[str] = list()
    for ele in res:
        title_url = ele.find('a')

        url = title_url.attrs.get('href', '')
        title_list = title_url.contents

        if not url or not title_list or 'short-stories' in url:
            continue
        title = title_list[0].strip()
        result_list.append(json.dumps({"url": url, "title": title}))
    return result_list


async def get_url_link(session: aiohttp.ClientSession, json_dict: Dict[str, str]):
    html_doc = await fetch(session, json_dict['url'])
    result_list = parse_url_page(html_doc)
    json_dict['chapters_url'] = result_list


def parse_url_page(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    res = soup.find(name='li',
                    attrs={'class': "category"})
    if not res or not res.parent:
        return ''

    res = res.parent
    url_class_name = 'section-list__link indented titlepage_content1'
    res_list = res.find_all(name='li',
                            attrs={'class': url_class_nammissing_urls_new.txte})
    res_list = [ele.find('a') for ele in res_list]
    res_list = [{'name': res.contents[0], 'url': res.attrs['href']}
                for res in res_list]
    return res_list


async def get_url_link_list(url_dict_list, get_link=get_url_link):
    async with aiohttp.ClientSession(headers=headers) as session:
        return await asyncio.wait([get_link(session, ele) for ele in url_dict_list])


def parse_plot_overview(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    overview_div = soup.find("div", attrs={"id": "plotoverview"})
    res = (ele.string.strip() for ele in overview_div.children)
    return "\n".join([text for text in res if text])


async def get_summary(session, json_dict):
    url_string = json_dict.pop('url', '')
    if url_string:
        html_doc = await fetch(session, url_string)
        json_dict['summary'] = parse_plot_overview(html_doc)


def main():
    input_path = "/home/zxj/Data/SparkNotes/url_parts/url_part_{0}.txt"
    root_url = "https://www.sparknotes.com"
    output_path = "/home/zxj/Data/SparkNotes/chapters_url_parts/chapters_url_part_{0}.txt"
    loop = asyncio.get_event_loop()
    input_list = list(
        read_file("/home/zxj/Data/SparkNotes/missing_urls.txt", preprocess=lambda x: json.loads(x.strip())))
    for ele in input_list:
        print(ele)
    loop.run_until_complete(get_url_link_list(input_list))

    output_iterator("/home/zxj/Data/SparkNotes/missing_urls_new.txt", input_list, process=lambda x: json.dumps(x))


if __name__ == '__main__':
    input_path = "/home/zxj/Data/SparkNotes/chapter_urls.txt"
    input_list = read_file(input_path, preprocess=lambda x: json.loads(x.strip()))
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(get_url_link_list(input_list, get_link=get_summary))
    output_iterator("/home/zxj/Data/SparkNotes/book_summaries", input_list, process=lambda x: json.dumps(x))
