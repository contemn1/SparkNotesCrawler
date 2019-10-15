import asyncio
import json
from typing import Dict
from typing import List

import aiohttp
from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

from io_util import read_file, output_iterator
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15"}
password = "kvKzfDamqkhGQNhYSYs6s44Hf"
proxy_url = f"http://auto:{password}@proxy.apify.com:8000"


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    await asyncio.sleep(1e-2)
    async with session.get(url, proxy=proxy_url) as response:
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


async def get_url_link(session: aiohttp.ClientSession,
                       json_dict: Dict[str, str]):
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
                            attrs={'class': url_class_name})
    res_list = [ele.find('a') for ele in res_list]
    res_list = [{'name': res.contents[0], 'url': res.attrs['href']}
                for res in res_list]
    return res_list


async def get_url_link_list(url_dict_list, get_link=get_url_link):
    async with aiohttp.ClientSession(headers=headers) as session:
        return await asyncio.wait(
            [get_link(session, ele) for ele in url_dict_list])


def parse_plot_overview(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    overview_div = soup.find("div", attrs={"id": "plotoverview"})
    res = (ele.text for ele in overview_div.children if isinstance(ele, Tag))
    return "\n".join([text for text in res if text])


async def get_summary(session, json_dict):
    url_string = json_dict.get('url', '')
    if url_string and 'summary' not in json_dict:
        html_doc = await fetch(session, url_string + 'summary')
        json_dict['summary'] = parse_plot_overview(html_doc)


def main():
    input_path = "/home/zxj/Data/SparkNotes/url_parts/url_part_{0}.txt"
    root_url = "https://www.sparknotes.com"
    output_path = "/home/zxj/Data/SparkNotes/chapters_url_parts/chapters_url_part_{0}.txt"
    loop = asyncio.get_event_loop()
    input_list = list(
        read_file("/home/zxj/Data/SparkNotes/missing_urls.txt",
                  preprocess=lambda x: json.loads(x.strip())))
    for ele in input_list:
        print(ele)
    loop.run_until_complete(get_url_link_list(input_list))

    output_iterator("/home/zxj/Data/SparkNotes/missing_urls_new.txt",
                    input_list, process=lambda x: json.dumps(x))


def summary_scrapping():
    input_path = "/Users/zxj/Google 云端硬盘/SparkNotes/book_summaries_unfinished.txt"
    input_list = list(
        read_file(input_path, preprocess=lambda x: json.loads(x.strip())))
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(get_url_link_list(input_list,
                                                        get_link=get_summary))
    finished_path = "/Users/zxj/Google 云端硬盘/SparkNotes/book_summaries_finished_new.txt"
    unfinished_path = "/Users/zxj/Google 云端硬盘/SparkNotes/book_summaries_unfinished_new.txt"

    finished = [ele for ele in input_list if 'summary' in ele]
    unfinished = [ele for ele in input_list if not 'summary' in ele]
    output_iterator(finished_path, finished, process=lambda x: json.dumps(x))
    output_iterator(unfinished_path, unfinished,
                    process=lambda x: json.dumps(x))


def parse_chapter_summary_one_page(soup):
    section_attrs_dict = {"id": "section",
                          "class": "studyGuideText hack-to-hide-first-h2"}
    section = soup.find("div", attrs=section_attrs_dict)
    if not section or not section.contents:
        return []

    return [ele.text for ele in section.contents if isinstance(ele, Tag)]


async def get_chapter_summary(session, json_dict):
    url_string = json_dict.get("url", "")
    if url_string:
        url_string = "https://www.sparknotes.com" + url_string
        url_template = url_string + "page/{0}"
        html_doc = await fetch(session, url_string)
        soup = BeautifulSoup(html_doc, "html.parser")
        result = parse_chapter_summary_one_page(soup)
        page_attrs_dict = {
            "class": "interior-sticky-nav__navigation__list--short"}
        page_container = soup.find("div", attrs=page_attrs_dict)
        if page_container and len(page_container.contents) >= 2:
            for idx in range(2, len(page_container.contents) + 1):
                page_doc = await fetch(session, url_template.format(idx))
                page_soup = BeautifulSoup(page_doc, "html.parser")
                page_result = parse_chapter_summary_one_page(page_soup)
                result = result + page_result

        if result:
            json_dict['summary'] = result


async def get_chapter_summary_test(input_path):
    async with aiohttp.ClientSession(headers=headers) as session:
        coroutine_list = [asyncio.gather(*[get_chapter_summary(session, ele)
                                           for ele in summary["chapters_url"]])
                          for summary in input_list if
                          "chapters_url" in summary]
        coroutines = asyncio.wait(coroutine_list)

        return await coroutines

if __name__ == '__main__':
    input_path = "/Users/zxj/Google 云端硬盘/SparkNotes/book_summaries.txt"
    input_list = list(
        read_file(input_path, preprocess=lambda x: json.loads(x.strip())))[150: ]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_chapter_summary_test(input_list))
    output_path = "/Users/zxj/Google 云端硬盘/SparkNotes/book_chapter_summaries_5.txt"
    output_iterator(output_path, input_list, process=lambda x: json.dumps(x))
