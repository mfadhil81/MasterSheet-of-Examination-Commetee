"""
نظام مبيعات ومخزون متكامل يدعم:
- فواتير المبيعات والمشتريات (إدخال/إخراج مخزني)
- إدارة العملاء والموردين
- دفعات مع كشف حساب للطرفين
- الإيرادات والمصروفات واحتساب الأرباح
- جرد المخزون (يومي/أسبوعي/سنوي)
- بحث بالأسماء وملفات طباعة A4 (HTML) للفواتير/التقارير
- نظام دخول بمستخدم رئيسي (admin) ومستخدمين ثانويين بصلاحيات محددة
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


DATE_FMT = "%Y-%m-%d %H:%M:%S"


def now_str() -> str:
    return datetime.now().strftime(DATE_FMT)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@dataclass
class Product:
    sku: str
    name: str
    unit_price: float
    stock: float = 0.0
    unit: str = "pcs"


@dataclass
class Customer:
    customer_id: str
    name: str
    phone: str = ""
    address: str = ""


@dataclass
class Supplier:
    supplier_id: str
    name: str
    phone: str = ""
    address: str = ""


@dataclass
class LineItem:
    product_sku: str
    quantity: float
    unit_price: float
    discount_rate: float = 0.0  # نسبة خصم على السطر (0 إلى 1)

    def total(self) -> float:
        gross = self.quantity * self.unit_price
        discount = gross * self.discount_rate
        return round(gross - discount, 2)


@dataclass
class Payment:
    method: str
    amount: float
    timestamp: str = field(default_factory=now_str)


@dataclass
class Invoice:
    invoice_id: str
    party_id: str  # customer_id أو supplier_id حسب النوع
    party_type: str = "customer"  # customer | supplier
    items: List[LineItem] = field(default_factory=list)
    tax_rate: float = 0.0
    overall_discount_rate: float = 0.0
    notes: str = ""
    created_at: str = field(default_factory=now_str)
    status: str = "open"  # open, paid, refunded
    payments: List[Payment] = field(default_factory=list)

    def subtotal(self) -> float:
        return round(sum(item.total() for item in self.items), 2)

    def discount_amount(self) -> float:
        return round(self.subtotal() * self.overall_discount_rate, 2)

    def tax_amount(self) -> float:
        taxable = self.subtotal() - self.discount_amount()
        return round(taxable * self.tax_rate, 2)

    def total_due(self) -> float:
        return round(self.subtotal() - self.discount_amount() + self.tax_amount(), 2)

    def paid_amount(self) -> float:
        return round(sum(p.amount for p in self.payments), 2)

    def remaining(self) -> float:
        return round(self.total_due() - self.paid_amount(), 2)

    @property
    def invoice_type(self) -> str:
        return "sale" if self.party_type == "customer" else "purchase"


@dataclass
class ReturnRecord:
    invoice_id: str
    product_sku: str
    quantity: float
    refund_amount: float
    timestamp: str = field(default_factory=now_str)
    reason: str = ""


@dataclass
class LedgerEntry:
    entry_id: str
    party_type: str  # customer | supplier
    party_id: str
    direction: str  # in (استلام) | out (دفع)
    amount: float
    reference: str = ""
    note: str = ""
    timestamp: str = field(default_factory=now_str)


@dataclass
class CashEntry:
    entry_id: str
    category: str
    amount: float
    kind: str  # income | expense
    note: str = ""
    timestamp: str = field(default_factory=now_str)


@dataclass
class User:
    username: str
    password_hash: str
    role: str = "user"  # admin | user
    permissions: List[str] = field(default_factory=list)

    def check_password(self, password: str) -> bool:
        return self.password_hash == hash_password(password)


class SalesSystem:
    """نظام مبيعات مبسط لإدارة عمليات البيع، المشتريات، المرتجعات والمخزون."""

    def __init__(self, data_path: Path = Path("sales_data.json")) -> None:
        self.data_path = data_path
        self.products: Dict[str, Product] = {}
        self.customers: Dict[str, Customer] = {}
        self.suppliers: Dict[str, Supplier] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.returns: List[ReturnRecord] = []
        self.ledger: List[LedgerEntry] = []
        self.cashbook: List[CashEntry] = []
        self.users: Dict[str, User] = {}
        self.load()
        self._ensure_admin()

    # ----------------------------- التخزين -----------------------------
    def load(self) -> None:
        if not self.data_path.exists():
            return
        data = json.loads(self.data_path.read_text(encoding="utf-8"))
        self.products = {p["sku"]: Product(**p) for p in data.get("products", [])}
        self.customers = {c["customer_id"]: Customer(**c) for c in data.get("customers", [])}
        self.suppliers = {s["supplier_id"]: Supplier(**s) for s in data.get("suppliers", [])}
        self.invoices = {}
        for inv in data.get("invoices", []):
            items = [LineItem(**item) for item in inv.get("items", [])]
            payments = [Payment(**p) for p in inv.get("payments", [])]
            invoice = Invoice(
                invoice_id=inv["invoice_id"],
                party_id=inv.get("party_id") or inv.get("customer_id") or inv.get("supplier_id") or "",
                party_type=inv.get("party_type", "customer"),
                items=items,
                tax_rate=inv.get("tax_rate", 0.0),
                overall_discount_rate=inv.get("overall_discount_rate", 0.0),
                notes=inv.get("notes", ""),
                created_at=inv.get("created_at", now_str()),
                status=inv.get("status", "open"),
                payments=payments,
            )
            self.invoices[invoice.invoice_id] = invoice
        self.returns = [ReturnRecord(**r) for r in data.get("returns", [])]
        self.ledger = [LedgerEntry(**e) for e in data.get("ledger", [])]
        self.cashbook = [CashEntry(**c) for c in data.get("cashbook", [])]
        self.users = {u["username"]: User(**u) for u in data.get("users", [])}

    def save(self) -> None:
        payload = {
            "products": [asdict(p) for p in self.products.values()],
            "customers": [asdict(c) for c in self.customers.values()],
            "suppliers": [asdict(s) for s in self.suppliers.values()],
            "invoices": [
                {
                    **asdict(inv),
                    "items": [asdict(item) for item in inv.items],
                    "payments": [asdict(p) for p in inv.payments],
                }
                for inv in self.invoices.values()
            ],
            "returns": [asdict(r) for r in self.returns],
            "ledger": [asdict(e) for e in self.ledger],
            "cashbook": [asdict(c) for c in self.cashbook],
            "users": [asdict(u) for u in self.users.values()],
        }
        self.data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ensure_admin(self) -> None:
        if "admin" not in self.users:
            admin = User(username="admin", password_hash=hash_password("admin"), role="admin", permissions=["*"])
            self.users[admin.username] = admin
            self.save()

    # ----------------------------- الدخول والصلاحيات -----------------------------
    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.users.get(username)
        if user and user.check_password(password):
            return user
        return None

    def add_user(self, username: str, password: str, role: str = "user", permissions: Optional[List[str]] = None) -> None:
        if username in self.users:
            raise ValueError("اسم المستخدم موجود بالفعل")
        perms = permissions or []
        self.users[username] = User(username=username, password_hash=hash_password(password), role=role, permissions=perms)
        self.save()

    def update_user_permissions(self, username: str, permissions: List[str]) -> None:
        if username not in self.users:
            raise KeyError("المستخدم غير موجود")
        self.users[username].permissions = permissions
        self.save()

    def user_can(self, user: User, permission: str) -> bool:
        return "*" in user.permissions or permission in user.permissions or user.role == "admin"

    # ----------------------------- إدارة المنتجات -----------------------------
    def add_product(self, product: Product) -> None:
        existing_by_name = next((p for p in self.products.values() if p.name.lower() == product.name.lower()), None)
        if existing_by_name:
            existing_by_name.stock = round(existing_by_name.stock + product.stock, 2)
            existing_by_name.unit_price = product.unit_price
            existing_by_name.unit = product.unit or existing_by_name.unit
        elif product.sku in self.products:
            raise ValueError("المنتج موجود مسبقاً")
        else:
            self.products[product.sku] = product
        self.save()

    def delete_product(self, sku: str) -> None:
        if sku not in self.products:
            raise KeyError("المنتج غير موجود")
        del self.products[sku]
        self.save()

    def update_stock(self, sku: str, delta: float) -> None:
        if sku not in self.products:
            raise KeyError("المنتج غير موجود")
        self.products[sku].stock = round(self.products[sku].stock + delta, 2)
        self.save()

    def list_products(self) -> List[Product]:
        return list(self.products.values())

    def search_products(self, query: str) -> List[Product]:
        q = query.lower()
        return [p for p in self.products.values() if q in p.name.lower() or q in p.sku.lower()]

    # ----------------------------- العملاء والموردون -----------------------------
    def add_customer(self, customer: Customer) -> None:
        cid = customer.customer_id or self.next_customer_id()
        if cid in self.customers:
            raise ValueError("العميل موجود مسبقاً")
        self.customers[cid] = Customer(customer_id=cid, name=customer.name, phone=customer.phone, address=customer.address)
        self.save()

    def update_customer(self, customer: Customer) -> None:
        if customer.customer_id not in self.customers:
            raise KeyError("العميل غير موجود")
        self.customers[customer.customer_id] = customer
        self.save()

    def delete_customer(self, customer_id: str) -> None:
        if customer_id not in self.customers:
            raise KeyError("العميل غير موجود")
        del self.customers[customer_id]
        self.save()

    def add_supplier(self, supplier: Supplier) -> None:
        sid = supplier.supplier_id or self.next_supplier_id()
        if sid in self.suppliers:
            raise ValueError("المورد موجود مسبقاً")
        self.suppliers[sid] = Supplier(supplier_id=sid, name=supplier.name, phone=supplier.phone, address=supplier.address)
        self.save()

    def update_supplier(self, supplier: Supplier) -> None:
        if supplier.supplier_id not in self.suppliers:
            raise KeyError("المورد غير موجود")
        self.suppliers[supplier.supplier_id] = supplier
        self.save()

    def delete_supplier(self, supplier_id: str) -> None:
        if supplier_id not in self.suppliers:
            raise KeyError("المورد غير موجود")
        del self.suppliers[supplier_id]
        self.save()

    def _generate_id(self, prefix: str, existing: List[str]) -> str:
        used = {e for e in existing}
        i = 1
        while True:
            candidate = f"{prefix}-{i:04d}"
            if candidate not in used:
                return candidate
            i += 1

    def next_customer_id(self) -> str:
        return self._generate_id("C", list(self.customers.keys()))

    def next_supplier_id(self) -> str:
        return self._generate_id("S", list(self.suppliers.keys()))

    def search_customers(self, query: str) -> List[Customer]:
        q = query.lower()
        return [c for c in self.customers.values() if q in c.name.lower() or q in c.customer_id.lower()]

    def search_suppliers(self, query: str) -> List[Supplier]:
        q = query.lower()
        return [s for s in self.suppliers.values() if q in s.name.lower() or q in s.supplier_id.lower()]

    # ----------------------------- إدارة الفواتير -----------------------------
    def create_invoice(
        self,
        invoice_id: str,
        party_id: str,
        items: List[LineItem],
        tax_rate: float = 0.0,
        overall_discount_rate: float = 0.0,
        notes: str = "",
        party_type: str = "customer",
    ) -> Invoice:
        if invoice_id in self.invoices:
            raise ValueError("رقم الفاتورة مستخدم مسبقاً")
        if party_type == "customer" and party_id not in self.customers:
            raise KeyError("العميل غير موجود")
        if party_type == "supplier" and party_id not in self.suppliers:
            raise KeyError("المورد غير موجود")
        for item in items:
            if item.product_sku not in self.products:
                raise KeyError(f"المنتج {item.product_sku} غير موجود")
            if party_type == "customer" and self.products[item.product_sku].stock < item.quantity:
                raise ValueError(f"كمية المنتج {item.product_sku} غير كافية في المخزون")
        for item in items:
            delta = -item.quantity if party_type == "customer" else item.quantity
            self.products[item.product_sku].stock += delta
        invoice = Invoice(
            invoice_id=invoice_id,
            party_id=party_id,
            party_type=party_type,
            items=items,
            tax_rate=tax_rate,
            overall_discount_rate=overall_discount_rate,
            notes=notes,
        )
        self.invoices[invoice_id] = invoice
        self.save()
        return invoice

    def next_invoice_id(self) -> str:
        seq = len(self.invoices) + 1
        return f"INV-{datetime.now().strftime('%Y%m%d')}-{seq:04d}"

    def add_payment(self, invoice_id: str, payment: Payment) -> LedgerEntry:
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            raise KeyError("الفاتورة غير موجودة")
        invoice.payments.append(payment)
        if invoice.remaining() <= 0:
            invoice.status = "paid"
        direction = "in" if invoice.party_type == "customer" else "out"
        ledger_entry = LedgerEntry(
            entry_id=f"LED-{len(self.ledger)+1}",
            party_type=invoice.party_type,
            party_id=invoice.party_id,
            direction=direction,
            amount=payment.amount,
            reference=invoice.invoice_id,
            note=f"دفعة ({payment.method})",
            timestamp=payment.timestamp,
        )
        self.ledger.append(ledger_entry)
        self.save()
        return ledger_entry

    def issue_return(self, invoice_id: str, product_sku: str, quantity: float, reason: str = "") -> ReturnRecord:
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            raise KeyError("الفاتورة غير موجودة")
        matching = [item for item in invoice.items if item.product_sku == product_sku]
        if not matching:
            raise KeyError("المنتج غير موجود في الفاتورة")
        line = matching[0]
        if quantity > line.quantity:
            raise ValueError("لا يمكن إرجاع كمية أكبر من المباعة/المشتراة")
        unit_net = line.total() / line.quantity
        refund_amount = round(unit_net * quantity, 2)
        record = ReturnRecord(
            invoice_id=invoice_id,
            product_sku=product_sku,
            quantity=quantity,
            refund_amount=refund_amount,
            reason=reason,
        )
        self.returns.append(record)
        delta = quantity if invoice.party_type == "customer" else -quantity
        self.products[product_sku].stock += delta
        invoice.status = "refunded" if quantity == line.quantity else invoice.status
        self.save()
        return record

    def invoice_summary(self, invoice_id: str) -> str:
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            raise KeyError("الفاتورة غير موجودة")
        party = self.customers.get(invoice.party_id) if invoice.party_type == "customer" else self.suppliers.get(invoice.party_id)
        party_name = party.name if party else "غير معروف"
        party_label = "عميل" if invoice.party_type == "customer" else "مورد"
        lines = [
            f"فاتورة رقم: {invoice.invoice_id}",
            f"نوع: {'بيع' if invoice.party_type=='customer' else 'شراء'}",
            f"{party_label}: {party_name} ({invoice.party_id})",
            f"التاريخ: {invoice.created_at}",
        ]
        lines.append("الاصناف:")
        for item in invoice.items:
            name = self.products.get(item.product_sku).name if item.product_sku in self.products else ""
            lines.append(
                f"- {item.product_sku} ({name}): كمية {item.quantity} * {item.unit_price}"
                f" (خصم {int(item.discount_rate * 100)}%) = {item.total()}"
            )
        lines.append(f"الإجمالي الفرعي: {invoice.subtotal()}")
        lines.append(f"خصم عام: {int(invoice.overall_discount_rate * 100)}% => {invoice.discount_amount()}")
        lines.append(f"ضريبة: {int(invoice.tax_rate * 100)}% => {invoice.tax_amount()}")
        lines.append(f"الإجمالي: {invoice.total_due()}")
        lines.append(f"مدفوع: {invoice.paid_amount()} | متبقي: {invoice.remaining()}")
        lines.append(f"الحالة: {invoice.status}")
        if invoice.notes:
            lines.append(f"ملاحظات: {invoice.notes}")
        return "\n".join(lines)

    # ----------------------------- التقارير -----------------------------
    def daily_report(self, target_date: date) -> Dict[str, float]:
        return self.period_report(target_date, target_date)

    def period_report(self, start_date: date, end_date: date) -> Dict[str, float]:
        total_sales = 0.0
        total_purchases = 0.0
        invoices_count = 0
        collected = 0.0
        paid_out = 0.0
        for inv in self.invoices.values():
            inv_date = datetime.strptime(inv.created_at, DATE_FMT).date()
            if start_date <= inv_date <= end_date:
                invoices_count += 1
                if inv.party_type == "customer":
                    total_sales += inv.total_due()
                    collected += inv.paid_amount()
                else:
                    total_purchases += inv.total_due()
                    paid_out += inv.paid_amount()
        income_extra = sum(c.amount for c in self.cashbook if c.kind == "income")
        expenses_extra = sum(c.amount for c in self.cashbook if c.kind == "expense")
        profit = total_sales + income_extra - (total_purchases + expenses_extra)
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "invoices": invoices_count,
            "sales_total": round(total_sales, 2),
            "purchases_total": round(total_purchases, 2),
            "collected": round(collected, 2),
            "paid_out": round(paid_out, 2),
            "income_extra": round(income_extra, 2),
            "expenses_extra": round(expenses_extra, 2),
            "profit_estimated": round(profit, 2),
        }

    def export_sales_report(self, file_path: Path) -> Path:
        rows = []
        for inv in self.invoices.values():
            rows.append(
                {
                    "invoice_id": inv.invoice_id,
                    "party_type": inv.party_type,
                    "party_id": inv.party_id,
                    "created_at": inv.created_at,
                    "subtotal": inv.subtotal(),
                    "discount": inv.discount_amount(),
                    "tax": inv.tax_amount(),
                    "total_due": inv.total_due(),
                    "paid": inv.paid_amount(),
                    "remaining": inv.remaining(),
                    "status": inv.status,
                }
            )
        df = pd.DataFrame(rows)
        if not file_path.suffix:
            file_path = file_path.with_suffix(".xlsx")
        df.to_excel(file_path, index=False)
        return file_path

    def inventory_report(self, period: str, reference: Optional[date] = None) -> Dict[str, Dict[str, float]]:
        reference = reference or date.today()
        if period == "daily":
            start = reference
        elif period == "weekly":
            start = reference - timedelta(days=6)
        elif period == "yearly":
            start = reference.replace(month=1, day=1)
        else:
            raise ValueError("الفترة يجب أن تكون daily أو weekly أو yearly")
        end = reference
        report: Dict[str, Dict[str, float]] = {}
        for sku, product in self.products.items():
            purchased = 0.0
            sold = 0.0
            for inv in self.invoices.values():
                inv_date = datetime.strptime(inv.created_at, DATE_FMT).date()
                if not (start <= inv_date <= end):
                    continue
                for item in inv.items:
                    if item.product_sku != sku:
                        continue
                    if inv.party_type == "customer":
                        sold += item.quantity
                    else:
                        purchased += item.quantity
            returned = sum(r.quantity for r in self.returns if r.product_sku == sku)
            report[sku] = {
                "name": product.name,
                "purchased": round(purchased, 2),
                "sold": round(sold, 2),
                "returned": round(returned, 2),
                "available": product.stock,
            }
        return report

    def product_sales_summary(self, sku: str) -> Dict[str, float]:
        if sku not in self.products:
            raise KeyError("المنتج غير موجود")
        sold_qty = 0.0
        purchased_qty = 0.0
        for inv in self.invoices.values():
            for item in inv.items:
                if item.product_sku == sku:
                    if inv.party_type == "customer":
                        sold_qty += item.quantity
                    else:
                        purchased_qty += item.quantity
        returned_qty = 0.0
        for ret in self.returns:
            if ret.product_sku == sku:
                returned_qty += ret.quantity
        net_sold = round(sold_qty - returned_qty, 2)
        available = self.products[sku].stock
        return {"sku": sku, "purchased": purchased_qty, "sold": net_sold, "returned": returned_qty, "available": available}

    # ----------------------------- الدفعات/الكاش -----------------------------
    def add_cash_entry(self, entry_id: str, category: str, amount: float, kind: str, note: str = "") -> None:
        if kind not in {"income", "expense"}:
            raise ValueError("النوع يجب أن يكون income أو expense")
        self.cashbook.append(CashEntry(entry_id=entry_id, category=category, amount=amount, kind=kind, note=note))
        self.save()

    def ledger_for_party(self, party_type: str, party_id: str) -> List[LedgerEntry]:
        return [e for e in self.ledger if e.party_type == party_type and e.party_id == party_id]

    # ----------------------------- طباعة/تصدير -----------------------------
    def export_invoice_html(self, invoice_id: str, file_path: Path) -> Path:
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            raise KeyError("الفاتورة غير موجودة")
        party_label = "عميل" if invoice.party_type == "customer" else "مورد"
        party = self.customers.get(invoice.party_id) if invoice.party_type == "customer" else self.suppliers.get(invoice.party_id)
        party_name = party.name if party else "غير معروف"
        lines = "".join(
            f"<tr><td>{item.product_sku}</td><td>{self.products.get(item.product_sku, Product('', '', 0)).name}</td>"
            f"<td>{item.quantity}</td><td>{item.unit_price}</td>"
            f"<td>{int(item.discount_rate*100)}%</td><td>{item.total()}</td></tr>"
            for item in invoice.items
        )
        section = f"""
        <div style='width:48%;border:1px dashed #999;padding:8px;box-sizing:border-box;margin:4px;'>
          <h2 style="text-align:center;">فاتورة {'بيع' if invoice.party_type=='customer' else 'شراء'}</h2>
          <p>{party_label}: {party_name} ({invoice.party_id})</p>
          <p>التاريخ: {invoice.created_at}</p>
          <table style="width:100%;border-collapse:collapse;">
            <tr><th>SKU</th><th>الاسم</th><th>الكمية</th><th>السعر</th><th>خصم</th><th>الإجمالي</th></tr>
            {lines}
          </table>
          <p>الإجمالي الفرعي: {invoice.subtotal()}</p>
          <p>خصم عام: {invoice.discount_amount()}</p>
          <p>ضريبة: {invoice.tax_amount()}</p>
          <h3>الإجمالي: {invoice.total_due()} | مدفوع: {invoice.paid_amount()} | متبقي: {invoice.remaining()}</h3>
          <p>ملاحظات: {invoice.notes}</p>
        </div>
        """
        html = f"""
        <html><head><meta charset="utf-8">
        <style>
        @media print {{
            @page {{ size: A4 landscape; margin: 10mm; }}
        }}
        body{{font-family:'Arial';margin:10px;}}
        table{{border-collapse:collapse;}}
        th,td{{border:1px solid #999;padding:4px;text-align:center;}}
        .row{{display:flex;flex-direction:row;justify-content:space-between;}}
        </style></head><body>
        <div class='row'>
          {section}
          {section}
        </div>
        </body></html>
        """
        if not file_path.suffix:
            file_path = file_path.with_suffix(".html")
        file_path.write_text(html, encoding="utf-8")
        return file_path

    def export_inventory_html(self, period: str, file_path: Path, reference: Optional[date] = None) -> Path:
        report = self.inventory_report(period, reference)
        rows = "".join(
            f"<tr><td>{sku}</td><td>{info['name']}</td><td>{info['purchased']}</td><td>{info['sold']}</td>"
            f"<td>{info['returned']}</td><td>{info['available']}</td></tr>"
            for sku, info in report.items()
        )
        html = f"""
        <html><head><meta charset="utf-8"><style>
        body{{font-family:'Arial';margin:20px;}}
        table{{width:100%;border-collapse:collapse;}}
        th,td{{border:1px solid #999;padding:6px;text-align:center;}}
        </style></head><body>
        <h2 style="text-align:center;">جرد مخزني ({period})</h2>
        <table>
        <tr><th>SKU</th><th>الاسم</th><th>المشتريات</th><th>المبيعات</th><th>المرتجع</th><th>المتوفر</th></tr>
        {rows}
        </table>
        </body></html>
        """
        if not file_path.suffix:
            file_path = file_path.with_suffix(".html")
        file_path.write_text(html, encoding="utf-8")
        return file_path

    def export_inventory_excel(self, period: str, file_path: Path, reference: Optional[date] = None) -> Path:
        report = self.inventory_report(period, reference)
        df = pd.DataFrame(
            [
                {
                    "SKU": sku,
                    "Name": info["name"],
                    "Purchased": info["purchased"],
                    "Sold": info["sold"],
                    "Returned": info["returned"],
                    "Available": info["available"],
                }
                for sku, info in report.items()
            ]
        )
        if not file_path.suffix:
            file_path = file_path.with_suffix(".xlsx")
        df.to_excel(file_path, index=False)
        return file_path

    def export_inventory_pdf(self, period: str, file_path: Path, reference: Optional[date] = None) -> Path:
        report = self.inventory_report(period, reference)
        try:
            from fpdf import FPDF  # type: ignore
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError("مطلوب حزمة fpdf لتوليد PDF") from exc
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 10, txt=f"جرد مخزني ({period})", ln=True, align="C")
        headers = ["SKU", "الاسم", "مشتريات", "مبيعات", "مرتجع", "متاح"]
        col_widths = [35, 60, 30, 30, 30, 30]
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 8, txt=h, border=1, align="C")
        pdf.ln()
        for sku, info in report.items():
            values = [sku, info["name"], info["purchased"], info["sold"], info["returned"], info["available"]]
            for w, val in zip(col_widths, values):
                pdf.cell(w, 8, txt=str(val), border=1, align="C")
            pdf.ln()
        if not file_path.suffix:
            file_path = file_path.with_suffix(".pdf")
        pdf.output(str(file_path))
        return file_path

    def export_entities_excel(self, entity: str, file_path: Path) -> Path:
        if entity == "products":
            rows = [
                {"SKU": p.sku, "Name": p.name, "Unit Price": p.unit_price, "Stock": p.stock, "Unit": p.unit}
                for p in self.products.values()
            ]
        elif entity == "customers":
            rows = [{"ID": c.customer_id, "Name": c.name, "Phone": c.phone, "Address": c.address} for c in self.customers.values()]
        elif entity == "suppliers":
            rows = [{"ID": s.supplier_id, "Name": s.name, "Phone": s.phone, "Address": s.address} for s in self.suppliers.values()]
        else:
            raise ValueError("النوع يجب أن يكون products أو customers أو suppliers")
        df = pd.DataFrame(rows)
        if not file_path.suffix:
            file_path = file_path.with_suffix(".xlsx")
        df.to_excel(file_path, index=False)
        return file_path

    def export_entities_html(self, entity: str, file_path: Path) -> Path:
        if entity == "products":
            title = "قائمة المنتجات"
            rows = "".join(
                f"<tr><td>{p.sku}</td><td>{p.name}</td><td>{p.unit_price}</td><td>{p.stock}</td><td>{p.unit}</td></tr>"
                for p in self.products.values()
            )
            headers = "<tr><th>SKU</th><th>الاسم</th><th>السعر</th><th>المخزون</th><th>الوحدة</th></tr>"
        elif entity == "customers":
            title = "قائمة العملاء"
            rows = "".join(
                f"<tr><td>{c.customer_id}</td><td>{c.name}</td><td>{c.phone}</td><td>{c.address}</td></tr>"
                for c in self.customers.values()
            )
            headers = "<tr><th>ID</th><th>الاسم</th><th>الهاتف</th><th>العنوان</th></tr>"
        elif entity == "suppliers":
            title = "قائمة الموردين"
            rows = "".join(
                f"<tr><td>{s.supplier_id}</td><td>{s.name}</td><td>{s.phone}</td><td>{s.address}</td></tr>"
                for s in self.suppliers.values()
            )
            headers = "<tr><th>ID</th><th>الاسم</th><th>الهاتف</th><th>العنوان</th></tr>"
        else:
            raise ValueError("النوع يجب أن يكون products أو customers أو suppliers")
        html = f"""
        <html><head><meta charset="utf-8"><style>
        @media print {{ @page {{ size: A4 portrait; margin: 10mm; }} }}
        body{{font-family:'Arial';margin:20px;}}
        table{{width:100%;border-collapse:collapse;}}
        th,td{{border:1px solid #999;padding:6px;text-align:center;}}
        </style></head><body>
        <h2 style="text-align:center;">{title}</h2>
        <table>{headers}{rows}</table>
        </body></html>
        """
        if not file_path.suffix:
            file_path = file_path.with_suffix(".html")
        file_path.write_text(html, encoding="utf-8")
        return file_path

    def export_entities_pdf(self, entity: str, file_path: Path) -> Path:
        try:
            from fpdf import FPDF  # type: ignore
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError("مطلوب حزمة fpdf لتوليد PDF") from exc
        if entity == "products":
            title = "قائمة المنتجات"
            headers = ["SKU", "الاسم", "السعر", "المخزون", "الوحدة"]
            rows = [[p.sku, p.name, p.unit_price, p.stock, p.unit] for p in self.products.values()]
            widths = [30, 60, 25, 25, 25]
        elif entity == "customers":
            title = "قائمة العملاء"
            headers = ["ID", "الاسم", "الهاتف", "العنوان"]
            rows = [[c.customer_id, c.name, c.phone, c.address] for c in self.customers.values()]
            widths = [30, 60, 40, 60]
        elif entity == "suppliers":
            title = "قائمة الموردين"
            headers = ["ID", "الاسم", "الهاتف", "العنوان"]
            rows = [[s.supplier_id, s.name, s.phone, s.address] for s in self.suppliers.values()]
            widths = [30, 60, 40, 60]
        else:
            raise ValueError("النوع يجب أن يكون products أو customers أو suppliers")
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 10, txt=title, ln=True, align="C")
        for w, h in zip(widths, headers):
            pdf.cell(w, 8, txt=h, border=1, align="C")
        pdf.ln()
        for row in rows:
            for w, val in zip(widths, row):
                pdf.cell(w, 8, txt=str(val), border=1, align="C")
            pdf.ln()
        if not file_path.suffix:
            file_path = file_path.with_suffix(".pdf")
        pdf.output(str(file_path))
        return file_path

    def export_invoice_excel(self, invoice_id: str, file_path: Path) -> Path:
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            raise KeyError("الفاتورة غير موجودة")
        party = self.customers.get(invoice.party_id) if invoice.party_type == "customer" else self.suppliers.get(invoice.party_id)
        party_name = party.name if party else "غير معروف"
        rows = [
            {
                "SKU": item.product_sku,
                "Quantity": item.quantity,
                "Unit Price": item.unit_price,
                "Discount": item.discount_rate,
                "Line Total": item.total(),
            }
            for item in invoice.items
        ]
        df = pd.DataFrame(rows)
        summary = pd.DataFrame(
            {
                "Field": ["Party Type", "Party Name", "Party ID", "Subtotal", "Discount", "Tax", "Total Due", "Paid", "Remaining"],
                "Value": [
                    "Customer" if invoice.party_type == "customer" else "Supplier",
                    party_name,
                    invoice.party_id,
                    invoice.subtotal(),
                    invoice.discount_amount(),
                    invoice.tax_amount(),
                    invoice.total_due(),
                    invoice.paid_amount(),
                    invoice.remaining(),
                ],
            }
        )
        with pd.ExcelWriter(file_path.with_suffix(".xlsx")) as writer:
            df.to_excel(writer, sheet_name="Items", index=False)
            summary.to_excel(writer, sheet_name="Summary", index=False)
        return file_path.with_suffix(".xlsx")

    def export_invoice_pdf(self, invoice_id: str, file_path: Path) -> Path:
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            raise KeyError("الفاتورة غير موجودة")
        try:
            from fpdf import FPDF  # type: ignore
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError("مطلوب حزمة fpdf للتصدير إلى PDF") from exc
        party = self.customers.get(invoice.party_id) if invoice.party_type == "customer" else self.suppliers.get(invoice.party_id)
        party_name = party.name if party else "غير معروف"
        pdf = FPDF(orientation="L", unit="mm", format="A4")
        for _ in range(1):  # صفحة واحدة تحوي نسختين أفقياً
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for copy_idx in range(2):
                x_offset = 10 + copy_idx * 145  # قسمين في صفحة أفقية
                pdf.set_xy(x_offset, 10)
                pdf.cell(0, 8, txt=f"فاتورة {'بيع' if invoice.party_type=='customer' else 'شراء'} رقم {invoice.invoice_id}", ln=False, align="C")
                pdf.set_xy(x_offset, 18)
                pdf.cell(0, 8, txt=f"الطرف: {party_name} ({invoice.party_id})", ln=False)
                pdf.set_xy(x_offset, 26)
                pdf.cell(0, 8, txt=f"التاريخ: {invoice.created_at}", ln=False)
                pdf.set_xy(x_offset, 35)
                headers = ["SKU", "الاسم", "الكمية", "السعر", "خصم", "الإجمالي"]
                col_widths = [25, 45, 20, 25, 20, 30]
                for w, h in zip(col_widths, headers):
                    pdf.cell(w, 8, txt=h, border=1, align="C")
                pdf.ln()
                for item in invoice.items:
                    name = self.products.get(item.product_sku, Product("", "", 0)).name
                    values = [
                        item.product_sku,
                        name[:20],
                        str(item.quantity),
                        str(item.unit_price),
                        f"{int(item.discount_rate*100)}%",
                        str(item.total()),
                    ]
                    pdf.set_x(x_offset)
                    for w, val in zip(col_widths, values):
                        pdf.cell(w, 8, txt=val, border=1, align="C")
                    pdf.ln()
                pdf.set_x(x_offset)
                pdf.cell(0, 8, txt=f"الإجمالي الفرعي: {invoice.subtotal()}", ln=True)
                pdf.set_x(x_offset)
                pdf.cell(0, 8, txt=f"خصم عام: {invoice.discount_amount()}", ln=True)
                pdf.set_x(x_offset)
                pdf.cell(0, 8, txt=f"ضريبة: {invoice.tax_amount()}", ln=True)
                pdf.set_x(x_offset)
                pdf.cell(0, 8, txt=f"الإجمالي: {invoice.total_due()}", ln=True)
                pdf.set_x(x_offset)
                pdf.cell(0, 8, txt=f"مدفوع: {invoice.paid_amount()} | متبقي: {invoice.remaining()}", ln=True)
        pdf.output(file_path.with_suffix(".pdf"))
        return file_path.with_suffix(".pdf")


# ----------------------------- CLI بسيطة -----------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="نظام مبيعات ومشتريات مبسط")
    sub = parser.add_subparsers(dest="command")

    add_product = sub.add_parser("add-product", help="إضافة منتج")
    add_product.add_argument("sku")
    add_product.add_argument("name")
    add_product.add_argument("unit_price", type=float)
    add_product.add_argument("stock", type=float)
    add_product.add_argument("--unit", default="pcs")

    add_customer = sub.add_parser("add-customer", help="إضافة عميل")
    add_customer.add_argument("customer_id")
    add_customer.add_argument("name")
    add_customer.add_argument("--phone", default="")
    add_customer.add_argument("--address", default="")

    add_supplier = sub.add_parser("add-supplier", help="إضافة مورد")
    add_supplier.add_argument("supplier_id")
    add_supplier.add_argument("name")
    add_supplier.add_argument("--phone", default="")
    add_supplier.add_argument("--address", default="")

    create_inv = sub.add_parser("create-invoice", help="إنشاء فاتورة بيع/شراء")
    create_inv.add_argument("invoice_id")
    create_inv.add_argument("party_id")
    create_inv.add_argument("items", help="صيغة: sku:qty:price[:discount_rate];...")
    create_inv.add_argument("--type", default="customer", choices=["customer", "supplier"])
    create_inv.add_argument("--tax", type=float, default=0.0)
    create_inv.add_argument("--discount", type=float, default=0.0)
    create_inv.add_argument("--notes", default="")

    pay = sub.add_parser("pay", help="تسجيل دفعة")
    pay.add_argument("invoice_id")
    pay.add_argument("amount", type=float)
    pay.add_argument("--method", default="cash")

    ret = sub.add_parser("return", help="إرجاع صنف")
    ret.add_argument("invoice_id")
    ret.add_argument("product_sku")
    ret.add_argument("quantity", type=float)
    ret.add_argument("--reason", default="")

    sub.add_parser("list-invoices", help="عرض ملخصات الفواتير")
    sub.add_parser("list-products", help="عرض المنتجات والمخزون")

    report = sub.add_parser("daily-report", help="تقرير يومي")
    report.add_argument("date", help="صيغة YYYY-MM-DD")

    export = sub.add_parser("export", help="تصدير تقرير المبيعات إلى إكسل")
    export.add_argument("file_path", type=Path)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        raise SystemExit(1)
    return args


def parse_items(arg: str) -> List[LineItem]:
    items: List[LineItem] = []
    for part in arg.split(";"):
        if not part:
            continue
        pieces = part.split(":")
        if len(pieces) < 3:
            raise ValueError("صيغة العناصر غير صحيحة")
        sku, qty, price, *rest = pieces
        discount_rate = float(rest[0]) if rest else 0.0
        items.append(LineItem(product_sku=sku, quantity=float(qty), unit_price=float(price), discount_rate=discount_rate))
    return items


def main() -> None:
    args = parse_args()
    system = SalesSystem()

    if args.command == "add-product":
        system.add_product(Product(args.sku, args.name, args.unit_price, args.stock, args.unit))
        print("تمت إضافة المنتج")
    elif args.command == "add-customer":
        system.add_customer(Customer(args.customer_id, args.name, args.phone, args.address))
        print("تمت إضافة العميل")
    elif args.command == "add-supplier":
        system.add_supplier(Supplier(args.supplier_id, args.name, args.phone, args.address))
        print("تمت إضافة المورد")
    elif args.command == "create-invoice":
        items = parse_items(args.items)
        invoice = system.create_invoice(
            args.invoice_id,
            args.party_id,
            items,
            tax_rate=args.tax,
            overall_discount_rate=args.discount,
            notes=args.notes,
            party_type=args.type,
        )
        print(system.invoice_summary(invoice.invoice_id))
    elif args.command == "pay":
        system.add_payment(args.invoice_id, Payment(args.method, args.amount))
        print(system.invoice_summary(args.invoice_id))
    elif args.command == "return":
        record = system.issue_return(args.invoice_id, args.product_sku, args.quantity, args.reason)
        print(f"تم تسجيل الإرجاع: {record}")
    elif args.command == "list-invoices":
        for inv_id in system.invoices:
            print(system.invoice_summary(inv_id))
            print("-" * 40)
    elif args.command == "list-products":
        for p in system.list_products():
            print(f"{p.sku} | {p.name} | السعر {p.unit_price} | المخزون {p.stock} {p.unit}")
    elif args.command == "daily-report":
        target = datetime.strptime(args.date, "%Y-%m-%d").date()
        print(system.daily_report(target))
    elif args.command == "export":
        path = system.export_sales_report(args.file_path)
        print(f"تم الحفظ في {path}")


if __name__ == "__main__":
    main()
