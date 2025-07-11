import asyncio
import logging

from src.parsers.start_page import StartPageParser
from src.parsers.category import CategoryPageParser
from src.parsers.product_feature import ProductFeatureParser
from src.repository.mongo_client import mongo_client
from src.repository.repository import ProductRepository

logger = logging.getLogger(__name__)


class ParserService:
    """Сервис для парсинга товаров с сайта КанцМир"""

    def __init__(self):
        self.start_parser = StartPageParser()
        self.category_parser = CategoryPageParser()
        self.product_parser = ProductFeatureParser()
        self.repository = ProductRepository()

        # Задержки между запросами
        self.delay_between_requests = 0.5
        self.delay_between_categories = 2.0

    async def start_parsing(self, base_url: str = "https://kanc-mir.ru/"):
        """Запускает полный парсинг сайта"""
        try:
            logger.info("Запуск парсинга КанцМир")

            # Подключаемся к MongoDB
            await mongo_client.connect()

            # Получаем список категорий
            logger.info("Получение списка категорий")
            categories = await self.start_parser.get_categories(base_url)
            logger.info(f"Найдено категорий: {len(categories)}")

            # Обрабатываем каждую категорию
            for i, category_url in enumerate(categories, 1):
                logger.info(f"Обработка категории {i}/{len(categories)}: {category_url}")
                await self._process_category(category_url)

                # Задержка между категориями
                if i < len(categories):
                    await asyncio.sleep(self.delay_between_categories)

            logger.info("Парсинг завершен")

        except Exception as e:
            logger.error(f"Критическая ошибка в парсинге: {e}")
        finally:
            await mongo_client.disconnect()

    async def parse_single_category(self, category_url: str):
        """Парсит одну категорию"""
        try:
            logger.info(f"Парсинг категории: {category_url}")

            # Подключаемся к MongoDB
            await mongo_client.connect()

            # Обрабатываем категорию
            await self._process_category(category_url)

            logger.info("Парсинг категории завершен")

        except Exception as e:
            logger.error(f"Ошибка при парсинге категории: {e}")
        finally:
            await mongo_client.disconnect()

    async def _process_category(self, category_url: str):
        """Обрабатывает одну категорию"""
        try:
            # Получаем все страницы категории
            page_links = await self.category_parser.create_page_links(category_url)
            logger.info(f"Найдено страниц: {len(page_links)}")

            # Обрабатываем каждую страницу
            for page_num, page_url in enumerate(page_links, 1):
                logger.info(f"Обработка страницы {page_num}/{len(page_links)}")

                # Получаем товары со страницы
                product_links = await self.category_parser.get_product_links(page_url)
                logger.info(f"Найдено товаров на странице: {len(product_links)}")

                # Парсим товары со страницы
                for product_url in product_links:
                    await self._process_product(product_url)
                    await asyncio.sleep(self.delay_between_requests)

            logger.info("Категория обработана")

        except Exception as e:
            logger.error(f"Ошибка при обработке категории {category_url}: {e}")

    async def _process_product(self, product_url: str):
        """Обрабатывает один товар"""
        try:
            # Парсим товар
            product = await self.product_parser.parse_product(product_url)

            if product:
                # Сохраняем в базу данных
                await self.repository.save_product(product)
                logger.info(f"Сохранен товар: {product.article}")
            else:
                logger.warning(f"Не удалось спарсить товар: {product_url}")

        except Exception as e:
            logger.error(f"Ошибка при обработке товара {product_url}: {e}")