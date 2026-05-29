from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    cnpj: Mapped[str] = mapped_column(String(18), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prices: Mapped[list["CustomerPrice"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    sales: Mapped[list["Sale"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    notifications: Mapped[list["PriceDropNotification"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class PaymentCondition(Base):
    __tablename__ = "payment_conditions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    installments: Mapped[int] = mapped_column(nullable=False, default=1)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=0)

    sales: Mapped[list["Sale"]] = relationship(back_populates="payment_condition")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prices: Mapped[list["CustomerPrice"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    sale_items: Mapped[list["SaleItem"]] = relationship(back_populates="product")
    notifications: Mapped[list["PriceDropNotification"]] = relationship(back_populates="product")


class CustomerPrice(Base):
    __tablename__ = "customer_prices"
    __table_args__ = (UniqueConstraint("customer_id", "product_id", name="uq_customer_product"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    customer: Mapped[Customer] = relationship(back_populates="prices")
    product: Mapped[Product] = relationship(back_populates="prices")


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    payment_condition_id: Mapped[int] = mapped_column(ForeignKey("payment_conditions.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    customer: Mapped[Customer] = relationship(back_populates="sales")
    payment_condition: Mapped[PaymentCondition] = relationship(back_populates="sales")
    items: Mapped[list["SaleItem"]] = relationship(back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sale: Mapped[Sale] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="sale_items")


class PriceDropNotification(Base):
    __tablename__ = "price_drop_notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    old_price_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    customer: Mapped[Customer] = relationship(back_populates="notifications")
    product: Mapped[Product] = relationship(back_populates="notifications")
