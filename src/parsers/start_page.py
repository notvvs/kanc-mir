from typing import List

from bs4 import BeautifulSoup

from src.core.settings import settings
from src.scrapers.scraper import PageScraper

class StartPageParser:

    def __init__(self):
        self.scraper = PageScraper()

    async def get_categories(self, url: str) -> List[str]:
        html = await self.scraper.scrape_page(url)
        soup = BeautifulSoup(html, 'html.parser')

        name_items = soup.find_all('li', class_='name')

        categories = []
        for item in name_items:
            link = item.find('a', class_='dark_link')
            if link:
                categories.append(
                    settings.base_url + link.get('href'),
                )

        return categories
