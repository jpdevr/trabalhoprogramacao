import threading
from dataclasses import dataclass
from decimal import Decimal
from queue import Empty, Queue

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import PriceDropNotification, SaleItem


@dataclass
class PriceChangedEvent:
    product_id: int
    new_price: Decimal


class PriceEventBus:
    def __init__(self):
        self._queue: Queue[PriceChangedEvent] = Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, session_factory):
        if self._thread and self._thread.is_alive():
            return

        def worker():
            while not self._stop.is_set():
                try:
                    event = self._queue.get(timeout=0.3)
                except Empty:
                    continue
                db: Session = session_factory()
                try:
                    stmt = select(SaleItem).where(
                        SaleItem.product_id == event.product_id,
                        SaleItem.unit_price > event.new_price,
                    )
                    items = db.execute(stmt).scalars().all()
                    for item in items:
                        msg = (
                            f"Produto {item.product_id} com novo preco {event.new_price} menor que "
                            f"preco pago {item.unit_price} na venda {item.sale_id}."
                        )
                        notification = PriceDropNotification(
                            customer_id=item.sale.customer_id,
                            product_id=item.product_id,
                            old_price_paid=item.unit_price,
                            new_price=event.new_price,
                            message=msg,
                        )
                        db.add(notification)
                    db.commit()
                finally:
                    db.close()
                    self._queue.task_done()

        self._stop.clear()
        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def publish(self, event: PriceChangedEvent):
        self._queue.put(event)


price_event_bus = PriceEventBus()
