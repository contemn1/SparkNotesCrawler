import os
from typing import List

from io_util import output_iterator, read_file
import json
import aiohttp
import asyncio
from bs4 import BeautifulSoup


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    await asyncio.sleep(1)
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


def parse_url_page(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    res = soup.find(name='li',
                    attrs={'class': "category"}).parent
    url_class_name = 'section-list__link indented titlepage_content1'
    res_list = res.find_all(name='li',
                            attrs={'class': url_class_name})
    res_list = [ele.find('a') for ele in res_list]
    res_list = [{'name': res.contents[0], 'url': res.attrs['href']}
                for res in res_list]
    return res_list


async def main(url_dict_list):
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15"}
    async with aiohttp.ClientSession(headers=headers) as session:
        done, pending = await asyncio.wait([fetch(session, ele['url']) for ele in url_dict_list])
        return done

if __name__ == '__main__':
    input_path = "/Users/zxj/Google 云端硬盘/SparkNotes/urls_test.txt"
    root_url = "https://www.sparknotes.com"
    input_list = list(read_file(input_path, preprocess=lambda x: json.loads(x.strip())))
    for ele in input_list:
        ele['url'] = root_url + ele['url']

    loop = asyncio.get_event_loop()
    result_list = loop.run_until_complete(main(input_list))
    for ele in result_list:
        print(ele.result())