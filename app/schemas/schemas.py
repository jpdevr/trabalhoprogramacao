from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    legal_name: str = Field(min_length=2, max_length=200)
    cnpj: str = Field(min_length=14, max_length=18)
    email: str
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    legal_name: str | None = None
    cnpj: str | None = None
    email: str | None = None
    is_active: bool | None = None


class CustomerOut(CustomerBase):
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    sku: str
    name: str
    base_price: Decimal
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = None
    name: str | None = None
    base_price: Decimal | None = None
    is_active: bool | None = None


class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True


class PaymentConditionBase(BaseModel):
    name: str
    installments: int = Field(ge=1)
    interest_rate: Decimal = Decimal("0")


class PaymentConditionCreate(PaymentConditionBase):
    pass


class PaymentConditionUpdate(BaseModel):
    name: str | None = None
    installments: int | None = Field(default=None, ge=1)
    interest_rate: Decimal | None = None


class PaymentConditionOut(PaymentConditionBase):
    id: int

    class Config:
        from_attributes = True


class CustomerPriceBase(BaseModel):
    customer_id: int
    product_id: int
    price: Decimal


class CustomerPriceCreate(CustomerPriceBase):
    pass


class CustomerPriceUpdate(BaseModel):
    price: Decimal


class CustomerPriceOut(CustomerPriceBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class SaleItemInput(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class SaleCreate(BaseModel):
    customer_id: int
    payment_condition_id: int
    items: list[SaleItemInput]


class SaleItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: int
    customer_id: int
    payment_condition_id: int
    created_at: datetime
    items: list[SaleItemOut]

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    customer_id: int
    product_id: int
    old_price_paid: Decimal
    new_price: Decimal
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerSalesReportOut(BaseModel):
    customer_id: int
    legal_name: str
    cnpj: str
    sales_count: int
    total_amount: Decimal
    products: list[dict]
