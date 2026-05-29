from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import (
    Customer,
    CustomerPrice,
    PaymentCondition,
    PriceDropNotification,
    Product,
    Sale,
    SaleItem,
)
from app.schemas.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerPriceCreate,
    CustomerPriceOut,
    CustomerPriceUpdate,
    CustomerSalesReportOut,
    CustomerUpdate,
    NotificationOut,
    PaymentConditionCreate,
    PaymentConditionOut,
    PaymentConditionUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    SaleCreate,
    SaleOut,
)
from app.services.price_events import PriceChangedEvent, price_event_bus

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: int, label: str):
    obj = db.get(model, obj_id)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{label} nao encontrado")
    return obj


@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(**payload.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.execute(select(Customer).order_by(Customer.id)).scalars().all()


@router.get("/customers/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Customer, customer_id, "Cliente")


@router.put("/customers/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    customer = _get_or_404(db, Customer, customer_id, "Cliente")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = _get_or_404(db, Customer, customer_id, "Cliente")
    db.delete(customer)
    db.commit()


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.execute(select(Product).order_by(Product.id)).scalars().all()


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Product, product_id, "Produto")


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = _get_or_404(db, Product, product_id, "Produto")
    previous_price = product.base_price
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)

    if payload.base_price is not None and Decimal(payload.base_price) < Decimal(previous_price):
        price_event_bus.publish(PriceChangedEvent(product_id=product.id, new_price=Decimal(payload.base_price)))

    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_or_404(db, Product, product_id, "Produto")
    db.delete(product)
    db.commit()


@router.post("/payment-conditions", response_model=PaymentConditionOut, status_code=status.HTTP_201_CREATED)
def create_payment_condition(payload: PaymentConditionCreate, db: Session = Depends(get_db)):
    condition = PaymentCondition(**payload.model_dump())
    db.add(condition)
    db.commit()
    db.refresh(condition)
    return condition


@router.get("/payment-conditions", response_model=list[PaymentConditionOut])
def list_payment_conditions(db: Session = Depends(get_db)):
    return db.execute(select(PaymentCondition).order_by(PaymentCondition.id)).scalars().all()


@router.put("/payment-conditions/{condition_id}", response_model=PaymentConditionOut)
def update_payment_condition(condition_id: int, payload: PaymentConditionUpdate, db: Session = Depends(get_db)):
    condition = _get_or_404(db, PaymentCondition, condition_id, "Condicao de pagamento")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(condition, key, value)
    db.commit()
    db.refresh(condition)
    return condition


@router.delete("/payment-conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_condition(condition_id: int, db: Session = Depends(get_db)):
    condition = _get_or_404(db, PaymentCondition, condition_id, "Condicao de pagamento")
    db.delete(condition)
    db.commit()


@router.post("/customer-prices", response_model=CustomerPriceOut, status_code=status.HTTP_201_CREATED)
def create_customer_price(payload: CustomerPriceCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Customer, payload.customer_id, "Cliente")
    _get_or_404(db, Product, payload.product_id, "Produto")
    price = CustomerPrice(**payload.model_dump())
    db.add(price)
    db.commit()
    db.refresh(price)
    return price


@router.get("/customer-prices", response_model=list[CustomerPriceOut])
def list_customer_prices(db: Session = Depends(get_db)):
    return db.execute(select(CustomerPrice).order_by(CustomerPrice.id)).scalars().all()


@router.put("/customer-prices/{price_id}", response_model=CustomerPriceOut)
def update_customer_price(price_id: int, payload: CustomerPriceUpdate, db: Session = Depends(get_db)):
    cp = _get_or_404(db, CustomerPrice, price_id, "Preco de cliente")
    cp.price = payload.price
    db.commit()
    db.refresh(cp)
    return cp


@router.delete("/customer-prices/{price_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer_price(price_id: int, db: Session = Depends(get_db)):
    cp = _get_or_404(db, CustomerPrice, price_id, "Preco de cliente")
    db.delete(cp)
    db.commit()


@router.post("/sales", response_model=SaleOut, status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    _get_or_404(db, Customer, payload.customer_id, "Cliente")
    _get_or_404(db, PaymentCondition, payload.payment_condition_id, "Condicao de pagamento")

    sale = Sale(customer_id=payload.customer_id, payment_condition_id=payload.payment_condition_id)
    db.add(sale)
    db.flush()

    for item in payload.items:
        _get_or_404(db, Product, item.product_id, "Produto")
        customer_price = db.execute(
            select(CustomerPrice).where(
                CustomerPrice.customer_id == payload.customer_id,
                CustomerPrice.product_id == item.product_id,
            )
        ).scalar_one_or_none()

        if customer_price:
            unit_price = customer_price.price
        else:
            unit_price = db.get(Product, item.product_id).base_price

        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=unit_price,
        )
        db.add(sale_item)

    db.commit()
    db.refresh(sale)
    return sale


@router.get("/sales", response_model=list[SaleOut])
def list_sales(db: Session = Depends(get_db)):
    return db.execute(select(Sale).order_by(Sale.id)).scalars().all()


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db)):
    return db.execute(select(PriceDropNotification).order_by(PriceDropNotification.id.desc())).scalars().all()


@router.get("/reports/customer-sales", response_model=CustomerSalesReportOut)
def customer_sales_report(
    cnpj: str | None = Query(default=None),
    legal_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not cnpj and not legal_name:
        raise HTTPException(status_code=400, detail="Informe cnpj ou legal_name")

    customer_query = select(Customer)
    if cnpj:
        customer_query = customer_query.where(Customer.cnpj == cnpj)
    if legal_name:
        customer_query = customer_query.where(func.lower(Customer.legal_name).like(f"%{legal_name.lower()}%"))

    customer = db.execute(customer_query).scalars().first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")

    sales = db.execute(select(Sale).where(Sale.customer_id == customer.id)).scalars().all()
    products_map: dict[int, dict] = defaultdict(lambda: {"quantity": 0, "total": Decimal("0.00")})
    total_amount = Decimal("0.00")

    for sale in sales:
        for item in sale.items:
            subtotal = Decimal(item.unit_price) * item.quantity
            total_amount += subtotal
            products_map[item.product_id]["quantity"] += item.quantity
            products_map[item.product_id]["total"] += subtotal

    products = []
    for product_id, data in products_map.items():
        product = db.get(Product, product_id)
        products.append(
            {
                "product_id": product_id,
                "product_name": product.name if product else "N/A",
                "quantity": data["quantity"],
                "total": data["total"],
            }
        )

    return CustomerSalesReportOut(
        customer_id=customer.id,
        legal_name=customer.legal_name,
        cnpj=customer.cnpj,
        sales_count=len(sales),
        total_amount=total_amount,
        products=products,
    )
