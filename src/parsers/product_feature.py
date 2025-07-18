import re
from typing import List, Optional
from bs4 import BeautifulSoup

from src.core.settings import settings
from src.scrapers.scraper import PageScraper
from src.schemas.product import Product, Supplier, SupplierOffer, PriceInfo, Attribute


class ProductFeatureParser:
    """Парсер для извлечения детальной информации о товаре"""

    def __init__(self):
        self.scraper = PageScraper()

    async def parse_product(self, url: str) -> Optional[Product]:
        """Парсит страницу товара и возвращает объект Product"""
        html = await self.scraper.scrape_page(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Извлекаем основную информацию о товаре
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        article = self._extract_article(soup)
        brand = self._extract_brand(soup)
        country_of_origin = self._extract_country(soup)
        category = self._extract_category(soup)

        # Извлекаем атрибуты
        attributes = self._extract_attributes(soup)

        # Извлекаем информацию о поставщике
        suppliers = self._extract_supplier_info(soup, url)

        return Product(
            title=title,
            description=description,
            article=article,
            brand=brand,
            country_of_origin=country_of_origin,
            category=category,
            attributes=attributes,
            suppliers=suppliers
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлекает название товара"""
        # Ищем в meta тегах
        meta_title = soup.find('meta', {'itemprop': 'name'})
        if meta_title and meta_title.get('content'):
            return meta_title.get('content')

        # Альтернативный поиск в h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)

        # Поиск в title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)

        return 'Нет данных'

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлекает описание товара"""
        # Ищем в табе описания (может быть активным или неактивным)
        descr_tab = soup.find('div', {'id': 'descr'})
        if descr_tab:
            # Ищем в descr-outer-wrapper
            descr_wrapper = descr_tab.find('div', class_='descr-outer-wrapper')
            if descr_wrapper:
                text = descr_wrapper.get_text(strip=True)
                if text:
                    return text

            # Ищем любой текст в табе описания
            text = descr_tab.get_text(strip=True)
            # Убираем заголовок "Описание"
            text = text.replace('Описание', '').strip()
            if text:
                return text

        # Ищем в основном блоке описания (если есть)
        desc_block = soup.find('div', class_='detail_text')
        if desc_block:
            text = desc_block.get_text(strip=True)
            if text:
                return text

        # Альтернативный поиск в meta описании
        meta_desc = soup.find('meta', {'itemprop': 'description'})
        if meta_desc and meta_desc.get('content'):
            content = meta_desc.get('content')
            # Проверяем, что описание не дублирует название
            title = self._extract_title(soup)
            if content and content != title:
                return content

        return 'Нет данных'

    def _extract_article(self, soup: BeautifulSoup) -> str:
        """Извлекает артикул товара"""
        # Сначала ищем в таблице характеристик (приоритет)
        props_table = soup.find('table', class_='props_list')
        if props_table:
            rows = props_table.find_all('tr')
            for row in rows:
                name_cell = row.find('td', class_='char_name')
                value_cell = row.find('td', class_='char_value')
                if name_cell and value_cell:
                    name = name_cell.get_text(strip=True)
                    if name == 'Артикул':
                        article = value_cell.get_text(strip=True)
                        if article:
                            return article

        # Если не найден в таблице, ищем в meta теге sku
        meta_sku = soup.find('meta', {'itemprop': 'sku'})
        if meta_sku and meta_sku.get('content'):
            return meta_sku.get('content')

        # Ищем ШтрихКод как альтернативу
        if props_table:
            rows = props_table.find_all('tr')
            for row in rows:
                name_cell = row.find('td', class_='char_name')
                value_cell = row.find('td', class_='char_value')
                if name_cell and value_cell:
                    name = name_cell.get_text(strip=True)
                    if name == 'ШтрихКод':
                        return value_cell.get_text(strip=True)

        return 'Нет данных'

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Извлекает бренд товара"""
        # Ищем в таблице характеристик
        props_table = soup.find('table', class_='props_list')
        if props_table:
            rows = props_table.find_all('tr')
            for row in rows:
                name_cell = row.find('td', class_='char_name')
                value_cell = row.find('td', class_='char_value')
                if name_cell and value_cell:
                    name = name_cell.get_text(strip=True)
                    if name == 'Бренд':
                        # Извлекаем текст, игнорируя ссылки
                        brand_link = value_cell.find('a')
                        if brand_link:
                            return brand_link.get_text(strip=True)
                        return value_cell.get_text(strip=True)

        return 'Нет данных'

    def _extract_country(self, soup: BeautifulSoup) -> str:
        """Извлекает страну производителя"""
        props_table = soup.find('table', class_='props_list')
        if props_table:
            rows = props_table.find_all('tr')
            for row in rows:
                name_cell = row.find('td', class_='char_name')
                value_cell = row.find('td', class_='char_value')
                if name_cell and value_cell:
                    name = name_cell.get_text(strip=True)
                    if name == 'Производитель':
                        return value_cell.get_text(strip=True)

        return 'Нет данных'

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Извлекает последнюю категорию товара из цепочки"""
        # Ищем в meta теге
        meta_category = soup.find('meta', {'itemprop': 'category'})
        if meta_category and meta_category.get('content'):
            category_chain = meta_category.get('content')
            # Разделяем по слэшу и берем последнее значение
            parts = category_chain.split('/')
            last_category = parts[-1].strip()
            if last_category:
                return last_category

        # Ищем в таблице характеристик
        props_table = soup.find('table', class_='props_list')
        if props_table:
            rows = props_table.find_all('tr')
            for row in rows:
                name_cell = row.find('td', class_='char_name')
                value_cell = row.find('td', class_='char_value')
                if name_cell and value_cell:
                    name = name_cell.get_text(strip=True)
                    if name == 'Категория товара':
                        category_link = value_cell.find('a')
                        if category_link:
                            category_text = category_link.get_text(strip=True)
                        else:
                            category_text = value_cell.get_text(strip=True)

                        # Разделяем по слэшу и берем последнее значение
                        parts = category_text.split('/')
                        last_category = parts[-1].strip()
                        if last_category:
                            return last_category

        return 'Нет данных'

    def _extract_attributes(self, soup: BeautifulSoup) -> List[Attribute]:
        """Извлекает атрибуты товара без дублирования"""
        attributes = []
        seen_attributes = set()

        # Характеристики, которые уже извлекаются как отдельные поля
        excluded_attributes = {
            'бренд', 'артикул', 'штрихкод', 'производитель', 'категория товара',
            'код', 'название', 'описание', 'цена', 'стоимость'
        }

        # Ищем таблицы характеристик: в основном блоке и в табе #props
        tables_to_check = []

        # 1. Основная таблица в верхней части товара
        main_char_blocks = soup.find_all('div', class_='char_block')
        for block in main_char_blocks:
            table = block.find('table', class_='props_list')
            if table:
                tables_to_check.append(table)

        # 2. Таблица в табе #props (может быть неактивным)
        props_tab = soup.find('div', {'id': 'props'})
        if props_tab:
            char_block = props_tab.find('div', class_='char_block')
            if char_block:
                tab_table = char_block.find('table', class_='props_list')
                if tab_table and tab_table not in tables_to_check:
                    tables_to_check.append(tab_table)

        # Обрабатываем все найденные таблицы
        for props_table in tables_to_check:
            rows = props_table.find_all('tr')
            for row in rows:
                name_cell = row.find('td', class_='char_name')
                value_cell = row.find('td', class_='char_value')

                if name_cell and value_cell:
                    # Извлекаем название из span с itemprop="name"
                    name_span = name_cell.find('span', {'itemprop': 'name'})
                    if name_span:
                        name = name_span.get_text(strip=True)
                    else:
                        name = name_cell.get_text(strip=True)

                    # Извлекаем значение из span с itemprop="value" или любого содержимого
                    value_span = value_cell.find('span', {'itemprop': 'value'})
                    if value_span:
                        # Проверяем есть ли ссылка внутри
                        value_link = value_span.find('a')
                        if value_link:
                            value = value_link.get_text(strip=True)
                        else:
                            value = value_span.get_text(strip=True)
                    else:
                        # Если нет span с itemprop, берем весь текст ячейки
                        value_link = value_cell.find('a')
                        if value_link:
                            value = value_link.get_text(strip=True)
                        else:
                            value = value_cell.get_text(strip=True)

                    if name and value:
                        name_lower = name.lower().strip()

                        # Пропускаем исключенные характеристики
                        if name_lower in excluded_attributes:
                            continue

                        # Пропускаем дубликаты
                        if name_lower in seen_attributes:
                            continue

                        attributes.append(Attribute(attr_name=name, attr_value=value))
                        seen_attributes.add(name_lower)

        return attributes

    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Извлекает цену товара"""
        # Ищем цену в блоке цен с атрибутом data-value
        price_block = soup.find('div', class_='price')
        if price_block:
            # Сначала пробуем data-value атрибут
            data_value = price_block.get('data-value')
            if data_value:
                try:
                    return float(data_value)
                except ValueError:
                    pass

            # Если нет data-value, ищем в span с классом price_value
            price_value = price_block.find('span', class_='price_value')
            if price_value:
                price_text = price_value.get_text(strip=True)
                # Извлекаем число из строки
                price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
                if price_match:
                    return float(price_match.group(1))

        # Ищем в meta теге
        meta_price = soup.find('meta', {'itemprop': 'price'})
        if meta_price and meta_price.get('content'):
            try:
                return float(meta_price.get('content'))
            except ValueError:
                pass

        return 0.0

    def _extract_stock(self, soup: BeautifulSoup) -> str:
        """Извлекает информацию о наличии"""
        # Ищем в div с классом item-stock
        stock_block = soup.find('div', class_='item-stock')
        if stock_block:
            return stock_block.get_text(strip=True)

        # Альтернативный поиск
        stock_blocks = soup.find_all('div', string=re.compile(r'В наличии|Нет в наличии|Под заказ'))
        if stock_blocks:
            return stock_blocks[0].get_text(strip=True)

        return 'Нет данных'

    def _extract_delivery_info(self, soup: BeautifulSoup) -> str:
        """Извлекает информацию о доставке"""
        delivery_block = soup.find('div', class_='my_delivery')
        if delivery_block:
            return delivery_block.get_text(strip=True)

        return 'Нет данных'

    def _extract_package_info(self, soup: BeautifulSoup) -> str:
        """Извлекает информацию об упаковке"""
        # Ищем количество в упаковке в характеристиках
        props_table = soup.find('table', class_='props_list')
        if props_table:
            rows = props_table.find_all('tr')
            for row in rows:
                name_cell = row.find('td', class_='char_name')
                value_cell = row.find('td', class_='char_value')
                if name_cell and value_cell:
                    name = name_cell.get_text(strip=True)
                    if name == 'Кол-во в упаковке':
                        count = value_cell.get_text(strip=True)
                        return f"{count} шт в упаковке"

        return 'Нет данных'

    def _extract_supplier_info(self, soup: BeautifulSoup, page_url: str) -> List[Supplier]:
        """Извлекает информацию о поставщике"""
        # Извлекаем данные
        price = self._extract_price(soup)
        stock = self._extract_stock(soup)
        delivery_info = self._extract_delivery_info(soup)
        package_info = self._extract_package_info(soup)

        # Создаем объект цены
        price_info = PriceInfo(qnt=1, discount=0, price=price)

        # Создаем предложение поставщика
        supplier_offer = SupplierOffer(
            price=[price_info],
            stock=stock,
            delivery_time=delivery_info,
            package_info=package_info,
            purchase_url=page_url
        )

        # Создаем поставщика
        supplier = Supplier(
            supplier_name='КанцМир',
            supplier_tel='+7 (499) 199-59-60',
            supplier_description='Интернет-магазин канцелярских товаров',
            supplier_offers=[supplier_offer]
        )

        return [supplier]