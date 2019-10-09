import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def main():
    async with aiohttp.ClientSession() as session:
        html_doc = await fetch(session, 'https://www.sparknotes.com/lit/')
        soup = BeautifulSoup(html_doc, 'html.parser')
        res = soup.find_all(name="h3", attrs={"class": "letter-list__filter-title"})
        for ele in res:
            print(ele.find('a').attrs['href'])

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
