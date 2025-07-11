import re
from typing import List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.core.settings import settings
from src.scrapers.scraper import PageScraper


class CategoryPageParser:

    def __init__(self):
        self.scraper = PageScraper()

    async def get_page_count(self, url: str) -> int:
        html = await self.scraper.scrape_page(url)
        pattern = r'PAGEN_1=(\d+)'
        matches = re.findall(pattern, html)

        if matches:
            # Возвращаем максимальный номер страницы
            return max(int(match) for match in matches)
        else:
            return 1


    async def create_page_links(self, url: str) -> List[str]:
        pages = []
        page_count = await self.get_page_count(url)

        for page_number in range(1, page_count + 1):
            pages.append(f'{url}?PAGEN_1={page_number}')

        return pages

    async def get_product_links(self, url: str) -> List[str]:
        html = await self.scraper.scrape_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        product_links = set()  # Используем set для избежания дубликатов

        # Находим все блоки товаров
        item_blocks = soup.find_all('div', class_='item_block')

        for block in item_blocks:
            # Ищем ссылки в заголовках товаров
            title_links = block.find_all('a', class_='dark_link')
            for link in title_links:
                href = link.get('href')
                if href and href.startswith('/catalog/') and href.count('/') >= 3:
                    full_url = urljoin(settings.base_url, href)
                    product_links.add(full_url)

        return sorted(list(product_links))

