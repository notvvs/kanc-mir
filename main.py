import asyncio

from src.scrapers.scraper import PageScraper

test = PageScraper()

print(asyncio.run(test.scrape_page('https://kanc-mir.ru/catalog/salfetki_vlazhnye_detskie/331482/#props')))