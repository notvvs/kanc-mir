import logging
from src.core.settings import settings
from src.repository.mongo_client import mongo_client
from src.schemas.product import Product

logger = logging.getLogger(__name__)


class ProductRepository:
    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = mongo_client.get_collection(settings.collection_name)
        return self._collection

    async def save_product(self, product: Product):
        try:
            product_dict = product.model_dump()

            # Проверяем по артикулу
            existing = await self.collection.find_one({"article": product.article})

            if existing:
                await self.collection.update_one(
                    {"article": product.article},
                    {"$set": product_dict}
                )
                logger.info(f"Обновлен: {product.article}")
            else:
                await self.collection.insert_one(product_dict)
                logger.info(f"Сохранен: {product.article}")

        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")