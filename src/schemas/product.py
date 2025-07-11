from typing import List
from pydantic import BaseModel, Field
from datetime import datetime


class PriceInfo(BaseModel):
    qnt: int = 1
    discount: float = 0
    price: float


class SupplierOffer(BaseModel):
    price: List[PriceInfo]
    stock: str = 'Нет данных'
    delivery_time: str = 'Нет данных'
    package_info: str = 'Нет данных'
    purchase_url: str


class Supplier(BaseModel):
    dealer_id: str = 'Нет данных'
    supplier_name: str = 'КанцМир'
    supplier_tel: str = '+7 (499) 199-59-60'
    supplier_address: str = '123154, г. Москва, ул. Генерала Глаголева, 6 корпус 1'
    supplier_description: str = 'Описание отсутствует'
    supplier_offers: List[SupplierOffer] = Field(default_factory=list)


class Attribute(BaseModel):
    attr_name: str
    attr_value: str


class Product(BaseModel):
    title: str
    description: str
    article: str
    brand: str
    country_of_origin: str = 'Нет данных'
    warranty_months: str = 'Нет данных'
    category: str = 'Нет данных'
    created_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%d.%m.%Y %H:%M")
    )
    attributes: List[Attribute] = Field(default_factory=list)
    suppliers: List[Supplier] = Field(default_factory=list)