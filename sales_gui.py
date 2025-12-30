from __future__ import annotations

"""
واجهة رسومية (Tkinter) لنظام المبيعات والمخزون:
- فواتير بيع/شراء، جرد، أرباح، كاش، دفعات، كشوف حساب للموردين والعملاء
- بحث بالأسماء
- طباعة (تصدير HTML بحجم A4) للفواتير والجرد
- تسجيل دخول وصلاحيات للمستخدمين الثانويين
"""
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from datetime import datetime, date
from pathlib import Path
from typing import List

import pandas as pd

from sales_system import (
    CashEntry,
    Customer,
    LedgerEntry,
    LineItem,
    Payment,
    Product,
    SalesSystem,
    Supplier,
    User,
)


class LoginDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, system: SalesSystem) -> None:
        super().__init__(master)
        self.system = system
        self.result: User | None = None
        self.title("تسجيل الدخول")
        self.geometry("320x180")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(padx=15, pady=15, fill="both", expand=True)
        ttk.Label(frame, text="اسم المستخدم").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(frame, text="كلمة المرور").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.user_var = tk.StringVar(value="admin")
        self.pass_var = tk.StringVar(value="admin")
        ttk.Entry(frame, textvariable=self.user_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.pass_var, show="*").grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="دخول", command=self._login).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="افتراضي: admin / admin").grid(row=3, column=0, columnspan=2)

    def _login(self) -> None:
        user = self.system.authenticate(self.user_var.get().strip(), self.pass_var.get())
        if not user:
            messagebox.showerror("خطأ", "بيانات الدخول غير صحيحة")
            return
        self.result = user
        self.destroy()

    def _on_close(self) -> None:
        self.result = None
        self.destroy()


class SalesApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("نظام مبيعات ومخزون")
        self.geometry("1100x750")
        self.system = SalesSystem(Path("sales_data.json"))
        self.current_user: User | None = None
        self.items_rows: list[dict[str, tk.StringVar]] = []
        self.party_lookup: list[tuple[str, str, str, str]] = []  # (id, name, phone, address)
        self.report_headers: list[str] = []
        self.report_rows: list[tuple] = []
        self._login_first()
        if not self.current_user:
            self.destroy()
            return
        self._build_ui()

    # ------------------------------------------------------------------
    def _login_first(self) -> None:
        dlg = LoginDialog(self, self.system)
        self.wait_window(dlg)
        self.current_user = dlg.result

    def _build_ui(self) -> None:
        self._setup_clipboard_shortcuts()
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self.products_frame = ttk.Frame(notebook)
        self.customers_frame = ttk.Frame(notebook)
        self.suppliers_frame = ttk.Frame(notebook)
        self.invoice_frame = ttk.Frame(notebook)
        self.ledger_frame = ttk.Frame(notebook)
        self.report_frame = ttk.Frame(notebook)
        self.users_frame = ttk.Frame(notebook)

        notebook.add(self.products_frame, text="المنتجات")
        notebook.add(self.customers_frame, text="العملاء")
        notebook.add(self.suppliers_frame, text="الموردون")
        notebook.add(self.invoice_frame, text="الفواتير")
        notebook.add(self.ledger_frame, text="الدفعات/الحسابات")
        notebook.add(self.report_frame, text="التقارير والبحث")
        if self.current_user.username == "admin":
            notebook.add(self.users_frame, text="المستخدمون")

        self._build_products_tab()
        self._build_customers_tab()
        self._build_suppliers_tab()
        self._build_invoice_tab()
        self._build_ledger_tab()
        self._build_report_tab()
        if self.current_user.username == "admin":
            self._build_users_tab()

    # ------------------------------------------------------------------
    def _require_perm(self, perm: str) -> bool:
        if self.current_user and self.system.user_can(self.current_user, perm):
            return True
        messagebox.showwarning("تنبيه", "لا تملك صلاحية تنفيذ هذا الإجراء")
        return False

    def _setup_clipboard_shortcuts(self) -> None:
        menubar = tk.Menu(self)
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="نسخ", accelerator="Ctrl+C", command=self.global_copy)
        edit_menu.add_command(label="لصق", accelerator="Ctrl+V", command=self.global_paste)
        edit_menu.add_command(label="قص", accelerator="Ctrl+X", command=self.global_cut)
        edit_menu.add_command(label="تحديد الكل", accelerator="Ctrl+A", command=self.global_select_all)
        menubar.add_cascade(label="تحرير", menu=edit_menu)
        self.config(menu=menubar)
        self.bind_all("<Control-c>", lambda _: self.global_copy())
        self.bind_all("<Control-C>", lambda _: self.global_copy())
        self.bind_all("<Control-v>", lambda _: self.global_paste())
        self.bind_all("<Control-V>", lambda _: self.global_paste())
        self.bind_all("<Control-x>", lambda _: self.global_cut())
        self.bind_all("<Control-X>", lambda _: self.global_cut())
        self.bind_all("<Control-a>", lambda _: self.global_select_all())
        self.bind_all("<Control-A>", lambda _: self.global_select_all())

    # ------------------------------------------------------------------
    def _build_products_tab(self) -> None:
        form = ttk.LabelFrame(self.products_frame, text="إضافة/تعديل منتج")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="SKU").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.sku_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.sku_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="الاسم").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.pname_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.pname_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="السعر").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.price_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.price_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form, text="المخزون").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.stock_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.stock_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(form, text="الوحدة").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.unit_var = tk.StringVar(value="pcs")
        ttk.Entry(form, textvariable=self.unit_var).grid(row=4, column=1, padx=5, pady=5)

        ttk.Button(form, text="حفظ المنتج", command=self.add_product).grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(form, text="تحميل منتجات من إكسل", command=self.import_products_from_excel).grid(
            row=6, column=0, columnspan=2, pady=5
        )
        ttk.Button(form, text="حذف المنتج المحدد", command=self.delete_product).grid(row=7, column=0, columnspan=2, pady=5)

        self.products_tree = ttk.Treeview(self.products_frame, columns=("sku", "name", "price", "stock", "unit"), show="headings")
        for col, title in zip(self.products_tree["columns"], ["SKU", "الاسم", "السعر", "المخزون", "الوحدة"]):
            self.products_tree.heading(col, text=title)
        self.products_tree.pack(fill="both", expand=True, padx=10, pady=10)
        export_bar = ttk.Frame(self.products_frame)
        export_bar.pack(fill="x", padx=10, pady=5)
        ttk.Button(export_bar, text="تصدير المنتجات Excel", command=lambda: self.export_entities("products", "excel")).pack(
            side="left", padx=3
        )
        ttk.Button(export_bar, text="تصدير المنتجات PDF", command=lambda: self.export_entities("products", "pdf")).pack(
            side="left", padx=3
        )
        ttk.Button(export_bar, text="طباعة/HTML A4", command=lambda: self.export_entities("products", "html")).pack(
            side="left", padx=3
        )
        self.refresh_products()

        query_frame = ttk.LabelFrame(self.products_frame, text="استعلام منتج / بحث")
        query_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(query_frame, text="اسم/كود").grid(row=0, column=0, padx=5, pady=5)
        self.query_sku_var = tk.StringVar()
        ttk.Entry(query_frame, textvariable=self.query_sku_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(query_frame, text="عرض الكميات", command=self.query_product).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(query_frame, text="بحث", command=self.search_products).grid(row=0, column=3, padx=5, pady=5)
        self.query_result = tk.StringVar()
        ttk.Label(query_frame, textvariable=self.query_result).grid(row=1, column=0, columnspan=4, padx=5, pady=5)

    # ------------------------------------------------------------------
    def _build_customers_tab(self) -> None:
        form = ttk.LabelFrame(self.customers_frame, text="إضافة/تعديل عميل")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="ID العميل").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.cid_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.cid_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(form, text="توليد ID", command=self.fill_customer_id).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(form, text="الاسم").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.cname_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.cname_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="الهاتف").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.phone_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.phone_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form, text="العنوان").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.address_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.address_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(form, text="حفظ العميل", command=self.add_customer).grid(row=4, column=0, pady=10, padx=5, sticky="ew")
        ttk.Button(form, text="تحديث العميل", command=self.update_customer).grid(row=4, column=1, pady=10, padx=5, sticky="ew")
        ttk.Button(form, text="حذف العميل المحدد", command=self.delete_customer).grid(row=5, column=0, columnspan=2, pady=5)

        self.customers_tree = ttk.Treeview(self.customers_frame, columns=("id", "name", "phone", "address"), show="headings")
        for col, title in zip(self.customers_tree["columns"], ["ID", "الاسم", "الهاتف", "العنوان"]):
            self.customers_tree.heading(col, text=title)
        self.customers_tree.pack(fill="both", expand=True, padx=10, pady=10)
        export_bar = ttk.Frame(self.customers_frame)
        export_bar.pack(fill="x", padx=10, pady=5)
        ttk.Button(export_bar, text="تصدير العملاء Excel", command=lambda: self.export_entities("customers", "excel")).pack(
            side="left", padx=3
        )
        ttk.Button(export_bar, text="تصدير العملاء PDF", command=lambda: self.export_entities("customers", "pdf")).pack(
            side="left", padx=3
        )
        ttk.Button(export_bar, text="طباعة/HTML A4", command=lambda: self.export_entities("customers", "html")).pack(
            side="left", padx=3
        )
        self.customers_tree.bind("<<TreeviewSelect>>", self.on_customer_select)
        self.refresh_customers()

        search_frame = ttk.LabelFrame(self.customers_frame, text="بحث عن عميل")
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="اسم/معرف").grid(row=0, column=0, padx=5, pady=5)
        self.search_customer_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_customer_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="بحث", command=self.search_customers_by_name).grid(row=0, column=2, padx=5, pady=5)
        self.customer_search_result = tk.StringVar()
        ttk.Label(search_frame, textvariable=self.customer_search_result).grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    # ------------------------------------------------------------------
    def _build_suppliers_tab(self) -> None:
        form = ttk.LabelFrame(self.suppliers_frame, text="إضافة/تعديل مورد")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="ID المورد").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.sid_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.sid_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(form, text="توليد ID", command=self.fill_supplier_id).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(form, text="الاسم").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.sname_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.sname_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="الهاتف").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.sphone_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.sphone_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form, text="العنوان").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.saddress_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.saddress_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(form, text="حفظ المورد", command=self.add_supplier).grid(row=4, column=0, pady=10, padx=5, sticky="ew")
        ttk.Button(form, text="تحديث المورد", command=self.update_supplier).grid(row=4, column=1, pady=10, padx=5, sticky="ew")
        ttk.Button(form, text="حذف المورد المحدد", command=self.delete_supplier).grid(row=5, column=0, columnspan=2, pady=5)

        self.suppliers_tree = ttk.Treeview(self.suppliers_frame, columns=("id", "name", "phone", "address"), show="headings")
        for col, title in zip(self.suppliers_tree["columns"], ["ID", "الاسم", "الهاتف", "العنوان"]):
            self.suppliers_tree.heading(col, text=title)
        self.suppliers_tree.pack(fill="both", expand=True, padx=10, pady=10)
        export_bar = ttk.Frame(self.suppliers_frame)
        export_bar.pack(fill="x", padx=10, pady=5)
        ttk.Button(export_bar, text="تصدير الموردين Excel", command=lambda: self.export_entities("suppliers", "excel")).pack(
            side="left", padx=3
        )
        ttk.Button(export_bar, text="تصدير الموردين PDF", command=lambda: self.export_entities("suppliers", "pdf")).pack(
            side="left", padx=3
        )
        ttk.Button(export_bar, text="طباعة/HTML A4", command=lambda: self.export_entities("suppliers", "html")).pack(
            side="left", padx=3
        )
        self.suppliers_tree.bind("<<TreeviewSelect>>", self.on_supplier_select)
        self.refresh_suppliers()

        search_frame = ttk.LabelFrame(self.suppliers_frame, text="بحث وكشف حساب")
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="اسم/معرف").grid(row=0, column=0, padx=5, pady=5)
        self.search_supplier_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_supplier_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="بحث", command=self.search_suppliers_by_name).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(search_frame, text="عرض كشف الحساب", command=self.show_supplier_ledger).grid(row=0, column=3, padx=5, pady=5)
        self.supplier_search_result = tk.StringVar()
        ttk.Label(search_frame, textvariable=self.supplier_search_result).grid(row=1, column=0, columnspan=4, padx=5, pady=5)

    # ------------------------------------------------------------------
    def _build_invoice_tab(self) -> None:
        container = ttk.Frame(self.invoice_frame)
        container.pack(fill="both", expand=True, padx=5, pady=5)
        form = ttk.LabelFrame(container, text="إنشاء فاتورة بيع/شراء")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="رقم الفاتورة").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.inv_id_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.inv_id_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="الطرف").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.party_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.party_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(form, text="بحث بالاسم", command=self.fill_party_from_name).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(form, text="النوع").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.party_type_var = tk.StringVar(value="customer")
        party_type_combo = ttk.Combobox(
            form, textvariable=self.party_type_var, values=["customer", "supplier"], state="readonly", width=15
        )
        party_type_combo.grid(row=2, column=1, padx=5, pady=5)
        party_type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_party_lookup())
        self.party_search_var = tk.StringVar()
        self.party_search_combo = ttk.Combobox(form, textvariable=self.party_search_var, values=[], width=25)
        self.party_search_combo.grid(row=2, column=2, padx=5, pady=5)
        self.party_search_combo.bind("<<ComboboxSelected>>", lambda e: self.fill_party_from_name())
        self.party_details_var = tk.StringVar(value="تفاصيل الطرف ستظهر هنا")
        ttk.Label(form, textvariable=self.party_details_var).grid(row=3, column=0, columnspan=3, sticky="w", padx=5)

        items_box = ttk.LabelFrame(self.invoice_frame, text="العناصر والفاتورة")
        items_box.pack(fill="both", expand=True, padx=10, pady=5)
        items_box.columnconfigure(0, weight=1)
        header = ["SKU", "الكمية", "السعر", "خصم (0-1)"]
        for idx, title in enumerate(header):
            ttk.Label(items_box, text=title).grid(row=0, column=idx, padx=5, pady=5, sticky="w")
        self.items_rows_frame = ttk.Frame(items_box)
        self.items_rows_frame.grid(row=1, column=0, columnspan=4, sticky="ew")
        btns = ttk.Frame(items_box)
        btns.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        ttk.Button(btns, text="+ صف جديد", command=lambda: self.add_item_row()).pack(side="left", padx=2)
        ttk.Button(btns, text="حذف الصف الأخير", command=self.remove_last_item_row).pack(side="left", padx=2)
        self.add_item_row()

        ttk.Label(form, text="ضريبة (مثال 0.15)").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.tax_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.tax_var).grid(row=3, column=1, padx=5, pady=5)
        self.tax_var.trace_add("write", lambda *_: self._update_live_totals())

        ttk.Label(form, text="خصم عام (0-1)").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.discount_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.discount_var).grid(row=4, column=1, padx=5, pady=5)
        self.discount_var.trace_add("write", lambda *_: self._update_live_totals())

        ttk.Label(form, text="ملاحظات").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.notes_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.notes_var).grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(form, text="إنشاء الفاتورة", command=self.create_invoice).grid(row=6, column=0, columnspan=3, pady=10)

        display_frame = ttk.Frame(items_box)
        display_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)
        items_box.rowconfigure(3, weight=1)
        self.invoice_items_tree = ttk.Treeview(
            display_frame, columns=("sku", "name", "qty", "price", "disc", "total"), show="headings", height=8
        )
        for col, title, width in [
            ("sku", "SKU", 90),
            ("name", "الاسم", 140),
            ("qty", "الكمية", 70),
            ("price", "السعر", 90),
            ("disc", "خصم", 70),
            ("total", "الإجمالي", 90),
        ]:
            self.invoice_items_tree.heading(col, text=title)
            self.invoice_items_tree.column(col, width=width, anchor="center")
        self.invoice_items_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.invoice_text = tk.Text(display_frame, height=6)
        self.invoice_text.pack(fill="x", expand=False, padx=10, pady=5)

        self.total_var = tk.StringVar(value="المجموع الكلي: 0")
        ttk.Label(display_frame, textvariable=self.total_var, font=("Arial", 12, "bold")).pack(anchor="w", padx=12, pady=5)
        ttk.Button(display_frame, text="نسخ الفاتورة إلى الحافظة", command=self.copy_invoice_text).pack(anchor="e", padx=10, pady=5)

        pay_frame = ttk.LabelFrame(container, text="دفعة / كشف حساب")
        pay_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(pay_frame, text="رقم الفاتورة").grid(row=0, column=0, padx=5, pady=5)
        self.pay_inv_var = tk.StringVar()
        ttk.Entry(pay_frame, textvariable=self.pay_inv_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(pay_frame, text="المبلغ").grid(row=1, column=0, padx=5, pady=5)
        self.pay_amount_var = tk.StringVar()
        ttk.Entry(pay_frame, textvariable=self.pay_amount_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(pay_frame, text="الطريقة").grid(row=2, column=0, padx=5, pady=5)
        self.pay_method_var = tk.StringVar(value="cash")
        ttk.Entry(pay_frame, textvariable=self.pay_method_var).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(pay_frame, text="تسجيل الدفعة", command=self.add_payment).grid(row=3, column=0, columnspan=2, pady=5)
        export_row = ttk.Frame(pay_frame)
        export_row.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(export_row, text="تصدير A4 (HTML)", command=self.export_invoice_html).pack(side="left", padx=2)
        ttk.Button(export_row, text="تصدير PDF", command=self.export_invoice_pdf).pack(side="left", padx=2)
        ttk.Button(export_row, text="تصدير Excel", command=self.export_invoice_excel).pack(side="left", padx=2)
        ttk.Button(export_row, text="طباعة/عرض", command=self.print_invoice_html).pack(side="left", padx=2)

        self.refresh_party_lookup()

    # ------------------------------------------------------------------
    def _build_ledger_tab(self) -> None:
        frame = ttk.LabelFrame(self.ledger_frame, text="كشف حساب للموردين/العملاء")
        frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(frame, text="الطرف").grid(row=0, column=0, padx=5, pady=5)
        self.ledger_party_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ledger_party_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame, text="النوع").grid(row=0, column=2, padx=5, pady=5)
        self.ledger_type_var = tk.StringVar(value="customer")
        ttk.Combobox(frame, textvariable=self.ledger_type_var, values=["customer", "supplier"], state="readonly").grid(
            row=0, column=3, padx=5, pady=5
        )
        ttk.Button(frame, text="عرض كشف الحساب", command=self.show_ledger).grid(row=0, column=4, padx=5, pady=5)

        cash_frame = ttk.LabelFrame(self.ledger_frame, text="إيراد/مصروف إضافي")
        cash_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(cash_frame, text="معرف الحركة").grid(row=0, column=0, padx=5, pady=5)
        self.cash_id_var = tk.StringVar()
        ttk.Entry(cash_frame, textvariable=self.cash_id_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(cash_frame, text="التصنيف").grid(row=1, column=0, padx=5, pady=5)
        self.cash_cat_var = tk.StringVar()
        ttk.Entry(cash_frame, textvariable=self.cash_cat_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(cash_frame, text="المبلغ").grid(row=2, column=0, padx=5, pady=5)
        self.cash_amount_var = tk.StringVar()
        ttk.Entry(cash_frame, textvariable=self.cash_amount_var).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(cash_frame, text="النوع").grid(row=3, column=0, padx=5, pady=5)
        self.cash_kind_var = tk.StringVar(value="income")
        ttk.Combobox(cash_frame, textvariable=self.cash_kind_var, values=["income", "expense"], state="readonly").grid(
            row=3, column=1, padx=5, pady=5
        )
        ttk.Label(cash_frame, text="ملاحظة").grid(row=4, column=0, padx=5, pady=5)
        self.cash_note_var = tk.StringVar()
        ttk.Entry(cash_frame, textvariable=self.cash_note_var, width=50).grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(cash_frame, text="تسجيل", command=self.add_cash_entry).grid(row=5, column=0, columnspan=2, pady=10)

        profit_frame = ttk.LabelFrame(self.ledger_frame, text="حساب الأرباح")
        profit_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(profit_frame, text="من تاريخ YYYY-MM-DD").grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(profit_frame, text="إلى تاريخ YYYY-MM-DD").grid(row=1, column=0, padx=5, pady=5)
        self.profit_start_var = tk.StringVar(value=date.today().isoformat())
        self.profit_end_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(profit_frame, textvariable=self.profit_start_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Entry(profit_frame, textvariable=self.profit_end_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(profit_frame, text="حساب", command=self.show_profit).grid(row=0, column=2, rowspan=2, padx=5, pady=5)

        self.ledger_text = tk.Text(self.ledger_frame, height=18)
        self.ledger_text.pack(fill="both", expand=True, padx=10, pady=10)

    # ------------------------------------------------------------------
    def _build_report_tab(self) -> None:
        frame = ttk.LabelFrame(self.report_frame, text="تقارير وجرد")
        frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(frame, text="تاريخ التقرير YYYY-MM-DD").grid(row=0, column=0, padx=5, pady=5)
        self.report_date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(frame, textvariable=self.report_date_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="تقرير يومي", command=self.show_daily_report).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frame, text="جرد (daily/weekly/yearly)").grid(row=1, column=0, padx=5, pady=5)
        self.inventory_period_var = tk.StringVar(value="daily")
        ttk.Combobox(frame, textvariable=self.inventory_period_var, values=["daily", "weekly", "yearly"], state="readonly").grid(
            row=1, column=1, padx=5, pady=5
        )
        ttk.Button(frame, text="عرض الجرد", command=self.show_inventory_report).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(frame, text="طباعة الجرد A4", command=self.export_inventory_html).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(frame, text="تصدير الجرد PDF", command=self.export_inventory_pdf).grid(row=1, column=4, padx=5, pady=5)
        ttk.Button(frame, text="تصدير الجرد Excel", command=self.export_inventory_excel).grid(row=1, column=5, padx=5, pady=5)

        search_box = ttk.LabelFrame(self.report_frame, text="بحث عن عميل/مورد/مادة")
        search_box.pack(fill="x", padx=10, pady=10)
        ttk.Label(search_box, text="نص البحث").grid(row=0, column=0, padx=5, pady=5)
        self.generic_search_var = tk.StringVar()
        ttk.Entry(search_box, textvariable=self.generic_search_var, width=60).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(search_box, text="بحث", command=self.run_generic_search).grid(row=0, column=2, padx=5, pady=5)

        self.report_table = ttk.Treeview(self.report_frame, columns=("c1", "c2", "c3", "c4", "c5", "c6"), show="headings")
        self.report_table.pack(fill="both", expand=True, padx=10, pady=10)
        export_reports = ttk.Frame(self.report_frame)
        export_reports.pack(fill="x", padx=10, pady=5)
        ttk.Button(export_reports, text="تصدير الجدول Excel", command=self.export_report_excel).pack(side="left", padx=3)
        ttk.Button(export_reports, text="تصدير الجدول PDF", command=self.export_report_pdf).pack(side="left", padx=3)
        ttk.Button(export_reports, text="طباعة/HTML A4", command=self.export_report_html).pack(side="left", padx=3)

    # ------------------------------------------------------------------
    def _build_users_tab(self) -> None:
        form = ttk.LabelFrame(self.users_frame, text="إنشاء مستخدم ثانوي")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="اسم المستخدم").grid(row=0, column=0, padx=5, pady=5)
        self.new_user_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.new_user_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(form, text="كلمة المرور").grid(row=1, column=0, padx=5, pady=5)
        self.new_pass_var = tk.StringVar(value="admin")
        ttk.Entry(form, textvariable=self.new_pass_var, show="*").grid(row=1, column=1, padx=5, pady=5)

        self.perm_vars = {p: tk.BooleanVar() for p in ["products_edit", "customers_edit", "suppliers_edit", "invoices_edit", "reports_view", "ledger_view"]}
        for idx, (perm, var) in enumerate(self.perm_vars.items()):
            ttk.Checkbutton(form, text=perm, variable=var).grid(row=2 + idx // 3, column=idx % 3, padx=5, pady=5, sticky="w")
        ttk.Button(form, text="حفظ المستخدم", command=self.create_user).grid(row=4, column=0, columnspan=2, pady=10)

        self.users_tree = ttk.Treeview(self.users_frame, columns=("user", "role", "permissions"), show="headings")
        for col, title in zip(self.users_tree["columns"], ["المستخدم", "الدور", "الصلاحيات"]):
            self.users_tree.heading(col, text=title)
        self.users_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_users()

    # ============================= المنتجات =============================
    def add_product(self) -> None:
        if not self._require_perm("products_edit"):
            return
        try:
            product = Product(
                sku=self.sku_var.get().strip(),
                name=self.pname_var.get().strip(),
                unit_price=float(self.price_var.get()),
                stock=float(self.stock_var.get()),
                unit=self.unit_var.get().strip() or "pcs",
            )
            if not product.sku or not product.name:
                raise ValueError("يرجى إدخال SKU واسم المنتج")
            self.system.add_product(product)
            self.refresh_products()
            messagebox.showinfo("تم", "تم حفظ المنتج")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def refresh_products(self) -> None:
        for row in self.products_tree.get_children():
            self.products_tree.delete(row)
        for p in self.system.list_products():
            tags = ("low",) if p.stock <= 0 else ()
            self.products_tree.insert("", "end", values=(p.sku, p.name, p.unit_price, p.stock, p.unit), tags=tags)
        self.products_tree.tag_configure("low", background="#ffdddd")
        # تحديث خيارات التنبؤ لصفوف الفاتورة
        for row_vars in self.items_rows:
            combo = row_vars.get("sku_combo")
            if combo:
                combo["values"] = self.product_sku_choices()

    def delete_product(self) -> None:
        if not self._require_perm("products_edit"):
            return
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("تنبيه", "يرجى اختيار منتج للحذف")
            return
        sku = self.products_tree.item(selection[0], "values")[0]
        try:
            self.system.delete_product(sku)
            self.refresh_products()
            messagebox.showinfo("تم", "تم حذف المنتج")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_entities(self, entity: str, fmt: str) -> None:
        # يسمح بالتصدير حتى لمستخدم التقارير فقط
        if not self._require_perm("reports_view"):
            return
        if fmt == "excel":
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
            if not file_path:
                return
            try:
                path = self.system.export_entities_excel(entity, Path(file_path))
                messagebox.showinfo("تم", f"تم التصدير إلى {path}")
            except Exception as exc:  # pylint: disable=broad-except
                messagebox.showerror("خطأ", str(exc))
        elif fmt == "pdf":
            file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not file_path:
                return
            try:
                path = self.system.export_entities_pdf(entity, Path(file_path))
                messagebox.showinfo("تم", f"تم التصدير إلى {path}")
            except Exception as exc:  # pylint: disable=broad-except
                messagebox.showerror("خطأ", str(exc))
        elif fmt == "html":
            file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
            if not file_path:
                return
            try:
                path = self.system.export_entities_html(entity, Path(file_path))
                messagebox.showinfo("تم", f"تم التصدير إلى {path}")
            except Exception as exc:  # pylint: disable=broad-except
                messagebox.showerror("خطأ", str(exc))
        else:
            messagebox.showwarning("تنبيه", "صيغة غير مدعومة")

    def import_products_from_excel(self) -> None:
        if not self._require_perm("products_edit"):
            return
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
            required = {"sku", "name", "unit_price", "stock"}
            if not required.issubset({col.lower() for col in df.columns}):
                raise ValueError("يجب أن يتضمن الملف الأعمدة: sku, name, unit_price, stock (وحدة اختيارية)")
            success, failed = 0, 0
            for row in df.to_dict(orient="records"):
                data = {k.lower(): v for k, v in row.items()}
                sku = str(data.get("sku", "")).strip()
                name = str(data.get("name", "")).strip()
                unit_price = float(data.get("unit_price", 0) or 0)
                stock = float(data.get("stock", 0) or 0)
                unit = str(data.get("unit", "pcs") or "pcs").strip()
                if not sku or not name:
                    failed += 1
                    continue
                try:
                    self.system.add_product(Product(sku=sku, name=name, unit_price=unit_price, stock=stock, unit=unit))
                    success += 1
                except Exception:  # pylint: disable=broad-except
                    failed += 1
            self.refresh_products()
            messagebox.showinfo("انتهى التحميل", f"تم تحميل {success} منتج، أخفق {failed}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def query_product(self) -> None:
        sku = self.query_sku_var.get().strip()
        if not sku:
            messagebox.showwarning("تنبيه", "يرجى إدخال SKU للاستعلام")
            return
        try:
            summary = self.system.product_sales_summary(sku)
            self.query_result.set(
                f"المشتريات: {summary['purchased']} | المبيعات: {summary['sold']} | المرتجع: {summary['returned']} | المتاح: {summary['available']}"
            )
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def search_products(self) -> None:
        term = self.query_sku_var.get().strip()
        if not term:
            return
        products = self.system.search_products(term)
        self.query_result.set(" | ".join(f"{p.sku}:{p.name}" for p in products) or "لا توجد نتائج")

    # ============================= العملاء =============================
    def add_customer(self) -> None:
        if not self._require_perm("customers_edit"):
            return
        try:
            customer = Customer(
                customer_id=self.cid_var.get().strip(),
                name=self.cname_var.get().strip(),
                phone=self.phone_var.get().strip(),
                address=self.address_var.get().strip(),
            )
            if not customer.name:
                raise ValueError("يرجى إدخال اسم العميل")
            if not customer.customer_id:
                new_id = self.system.next_customer_id()
                self.cid_var.set(new_id)
                customer.customer_id = new_id
            self.system.add_customer(customer)
            self.refresh_customers()
            messagebox.showinfo("تم", "تم حفظ العميل")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def update_customer(self) -> None:
        if not self._require_perm("customers_edit"):
            return
        try:
            customer = Customer(
                customer_id=self.cid_var.get().strip(),
                name=self.cname_var.get().strip(),
                phone=self.phone_var.get().strip(),
                address=self.address_var.get().strip(),
            )
            if not customer.customer_id or not customer.name:
                raise ValueError("يرجى اختيار عميل وتعبئة البيانات")
            self.system.update_customer(customer)
            self.refresh_customers()
            messagebox.showinfo("تم", "تم تحديث العميل")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def refresh_customers(self) -> None:
        for row in self.customers_tree.get_children():
            self.customers_tree.delete(row)
        for c in self.system.customers.values():
            self.customers_tree.insert("", "end", values=(c.customer_id, c.name, c.phone, c.address))
        self.refresh_party_lookup()

    def delete_customer(self) -> None:
        if not self._require_perm("customers_edit"):
            return
        selection = self.customers_tree.selection()
        if not selection:
            messagebox.showwarning("تنبيه", "يرجى اختيار عميل للحذف")
            return
        cid = self.customers_tree.item(selection[0], "values")[0]
        try:
            self.system.delete_customer(cid)
            self.refresh_customers()
            messagebox.showinfo("تم", "تم حذف العميل")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def on_customer_select(self, event: tk.Event) -> None:  # type: ignore[override]
        selection = self.customers_tree.selection()
        if not selection:
            return
        values = self.customers_tree.item(selection[0], "values")
        if not values:
            return
        cid, name, phone, address = values
        self.cid_var.set(cid)
        self.cname_var.set(name)
        self.phone_var.set(phone)
        self.address_var.set(address)

    def search_customers_by_name(self) -> None:
        term = self.search_customer_var.get().strip()
        results = self.system.search_customers(term) if term else []
        self.customer_search_result.set(" | ".join(f"{c.customer_id}:{c.name}" for c in results) or "لا توجد نتائج")

    def fill_customer_id(self) -> None:
        new_id = self.system.next_customer_id()
        self.cid_var.set(new_id)

    # ============================= الموردون =============================
    def add_supplier(self) -> None:
        if not self._require_perm("suppliers_edit"):
            return
        try:
            supplier = Supplier(
                supplier_id=self.sid_var.get().strip(),
                name=self.sname_var.get().strip(),
                phone=self.sphone_var.get().strip(),
                address=self.saddress_var.get().strip(),
            )
            if not supplier.name:
                raise ValueError("يرجى إدخال اسم المورد")
            if not supplier.supplier_id:
                new_id = self.system.next_supplier_id()
                self.sid_var.set(new_id)
                supplier.supplier_id = new_id
            self.system.add_supplier(supplier)
            self.refresh_suppliers()
            messagebox.showinfo("تم", "تم حفظ المورد")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def update_supplier(self) -> None:
        if not self._require_perm("suppliers_edit"):
            return
        try:
            supplier = Supplier(
                supplier_id=self.sid_var.get().strip(),
                name=self.sname_var.get().strip(),
                phone=self.sphone_var.get().strip(),
                address=self.saddress_var.get().strip(),
            )
            if not supplier.supplier_id or not supplier.name:
                raise ValueError("يرجى اختيار مورد وتعبئة البيانات")
            self.system.update_supplier(supplier)
            self.refresh_suppliers()
            messagebox.showinfo("تم", "تم تحديث المورد")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def refresh_suppliers(self) -> None:
        for row in self.suppliers_tree.get_children():
            self.suppliers_tree.delete(row)
        for s in self.system.suppliers.values():
            self.suppliers_tree.insert("", "end", values=(s.supplier_id, s.name, s.phone, s.address))
        self.refresh_party_lookup()

    def delete_supplier(self) -> None:
        if not self._require_perm("suppliers_edit"):
            return
        selection = self.suppliers_tree.selection()
        if not selection:
            messagebox.showwarning("تنبيه", "يرجى اختيار مورد للحذف")
            return
        sid = self.suppliers_tree.item(selection[0], "values")[0]
        try:
            self.system.delete_supplier(sid)
            self.refresh_suppliers()
            messagebox.showinfo("تم", "تم حذف المورد")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def on_supplier_select(self, event: tk.Event) -> None:  # type: ignore[override]
        selection = self.suppliers_tree.selection()
        if not selection:
            return
        values = self.suppliers_tree.item(selection[0], "values")
        if not values:
            return
        sid, name, phone, address = values
        self.sid_var.set(sid)
        self.sname_var.set(name)
        self.sphone_var.set(phone)
        self.saddress_var.set(address)

    def search_suppliers_by_name(self) -> None:
        term = self.search_supplier_var.get().strip()
        results = self.system.search_suppliers(term) if term else []
        self.supplier_search_result.set(" | ".join(f"{s.supplier_id}:{s.name}" for s in results) or "لا توجد نتائج")

    def show_supplier_ledger(self) -> None:
        self.ledger_party_var.set(self.search_supplier_var.get().strip())
        self.ledger_type_var.set("supplier")
        self.show_ledger()

    def fill_supplier_id(self) -> None:
        new_id = self.system.next_supplier_id()
        self.sid_var.set(new_id)

    # ============================= الفواتير =============================
    def _parse_items(self) -> List[LineItem]:
        return self._collect_item_rows()

    def add_item_row(self) -> None:
        row = len(self.items_rows)
        vars_map = {
            "sku": tk.StringVar(),
            "qty": tk.StringVar(),
            "price": tk.StringVar(),
            "discount": tk.StringVar(value="0"),
        }
        row_frame = ttk.Frame(self.items_rows_frame)
        row_frame.grid(row=row, column=0, columnspan=4, sticky="ew")
        vars_map["sku_combo"] = ttk.Combobox(row_frame, textvariable=vars_map["sku"], width=18, values=self.product_sku_choices())
        vars_map["sku_combo"].grid(row=0, column=0, padx=5, pady=2)
        ttk.Entry(row_frame, textvariable=vars_map["qty"], width=10).grid(row=0, column=1, padx=5, pady=2)
        ttk.Entry(row_frame, textvariable=vars_map["price"], width=14).grid(row=0, column=2, padx=5, pady=2)
        ttk.Entry(row_frame, textvariable=vars_map["discount"], width=12).grid(row=0, column=3, padx=5, pady=2)
        vars_map["frame"] = row_frame
        self.items_rows.append(vars_map)
        self._bind_item_row_events(vars_map)
        self._update_live_totals()

    def remove_last_item_row(self) -> None:
        if not self.items_rows:
            return
        row_vars = self.items_rows.pop()
        frame = row_vars.get("frame")
        if frame:
            frame.destroy()
        self._update_live_totals()

    def _collect_item_rows(self) -> List[LineItem]:
        items: List[LineItem] = []
        for row_vars in self.items_rows:
            sku_text = row_vars["sku"].get().strip()
            sku = sku_text.split("-")[0].strip() if "-" in sku_text else sku_text
            qty = row_vars["qty"].get().strip()
            price = row_vars["price"].get().strip()
            if not sku or not qty or not price:
                continue
            discount = float(row_vars["discount"].get() or 0)
            items.append(LineItem(product_sku=sku, quantity=float(qty), unit_price=float(price), discount_rate=discount))
        if not items:
            raise ValueError("يرجى إدخال عنصر واحد على الأقل")
        return items

    def product_sku_choices(self) -> list[str]:
        return [f"{p.sku} - {p.name}" for p in self.system.products.values()]

    def _bind_item_row_events(self, vars_map: dict[str, tk.StringVar]) -> None:
        for key in ["sku", "qty", "price", "discount"]:
            vars_map[key].trace_add("write", lambda *_: self._update_live_totals())

    def _update_live_totals(self) -> None:
        subtotal = 0.0
        for row_vars in self.items_rows:
            qty = row_vars["qty"].get().strip()
            price = row_vars["price"].get().strip()
            if not qty or not price:
                continue
            try:
                q_val = float(qty)
                p_val = float(price)
                d_val = float(row_vars["discount"].get() or 0)
            except ValueError:
                continue
            line_total = q_val * p_val * (1 - d_val)
            subtotal += line_total
        try:
            discount_rate = float(self.discount_var.get() or 0) if hasattr(self, "discount_var") else 0.0
        except ValueError:
            discount_rate = 0.0
        try:
            tax_rate = float(self.tax_var.get() or 0) if hasattr(self, "tax_var") else 0.0
        except ValueError:
            tax_rate = 0.0
        discount_amount = subtotal * discount_rate
        taxable = subtotal - discount_amount
        tax_amount = taxable * tax_rate
        total = round(taxable + tax_amount, 2)
        if hasattr(self, "total_var"):
            self.total_var.set(f"المجموع الكلي: {total}")

    def refresh_party_lookup(self) -> None:
        if not hasattr(self, "party_type_var") or not hasattr(self, "party_search_combo"):
            return
        party_type = self.party_type_var.get()
        if party_type == "supplier":
            data = self.system.suppliers.values()
            self.party_lookup = [(s.supplier_id, s.name, s.phone, s.address) for s in data]
        else:
            data = self.system.customers.values()
            self.party_lookup = [(c.customer_id, c.name, c.phone, c.address) for c in data]
        names = [f"{pid} | {name}" for pid, name, _, _ in self.party_lookup]
        self.party_search_combo["values"] = names
        self.party_search_var.set("")
        self.party_details_var.set("تفاصيل الطرف ستظهر هنا")

    def fill_party_from_name(self) -> None:
        if not hasattr(self, "party_search_var"):
            return
        selection = self.party_search_var.get()
        if not selection:
            return
        pid = selection.split("|")[0].strip()
        for candidate in self.party_lookup:
            if candidate[0] == pid:
                self.party_var.set(candidate[0])
                self.party_details_var.set(f"{candidate[1]} | هاتف: {candidate[2]} | عنوان: {candidate[3]}")
                if not self.inv_id_var.get().strip():
                    self.inv_id_var.set(self.system.next_invoice_id())
                return
        self.party_details_var.set("لم يتم العثور على الطرف")

    def create_invoice(self) -> None:
        if not self._require_perm("invoices_edit"):
            return
        try:
            items = self._parse_items()
            invoice = self.system.create_invoice(
                invoice_id=self.inv_id_var.get().strip(),
                party_id=self.party_var.get().strip(),
                items=items,
                tax_rate=float(self.tax_var.get()),
                overall_discount_rate=float(self.discount_var.get()),
                notes=self.notes_var.get().strip(),
                party_type=self.party_type_var.get(),
            )
            self.invoice_text.delete("1.0", tk.END)
            self.invoice_text.insert(tk.END, self.system.invoice_summary(invoice.invoice_id))
            self.refresh_products()
            self.total_var.set(f"المجموع الكلي: {invoice.total_due()}")
            self.pay_inv_var.set(invoice.invoice_id)
            self._populate_invoice_table(invoice)
            messagebox.showinfo("تم", "تم إنشاء الفاتورة")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def add_payment(self) -> None:
        if not self._require_perm("invoices_edit"):
            return
        try:
            entry = self.system.add_payment(
                self.pay_inv_var.get().strip(),
                Payment(self.pay_method_var.get().strip(), float(self.pay_amount_var.get())),
            )
            self.invoice_text.delete("1.0", tk.END)
            self.invoice_text.insert(tk.END, self.system.invoice_summary(self.pay_inv_var.get().strip()))
            self.refresh_products()
            messagebox.showinfo("تم", f"تم تسجيل الدفعة\nقيد دفتر: {entry.entry_id}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_invoice_html(self) -> None:
        inv_id = self.pay_inv_var.get().strip() or self.inv_id_var.get().strip()
        if not inv_id:
            messagebox.showwarning("تنبيه", "يرجى إدخال رقم الفاتورة")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if not file_path:
            return
        try:
            path = self.system.export_invoice_html(inv_id, Path(file_path))
            messagebox.showinfo("تم", f"تم التصدير إلى {path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_invoice_pdf(self) -> None:
        inv_id = self.pay_inv_var.get().strip() or self.inv_id_var.get().strip()
        if not inv_id:
            messagebox.showwarning("تنبيه", "يرجى إدخال رقم الفاتورة")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not file_path:
            return
        try:
            path = self.system.export_invoice_pdf(inv_id, Path(file_path))
            messagebox.showinfo("تم", f"تم التصدير إلى {path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_invoice_excel(self) -> None:
        inv_id = self.pay_inv_var.get().strip() or self.inv_id_var.get().strip()
        if not inv_id:
            messagebox.showwarning("تنبيه", "يرجى إدخال رقم الفاتورة")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not file_path:
            return
        try:
            path = self.system.export_invoice_excel(inv_id, Path(file_path))
            messagebox.showinfo("تم", f"تم التصدير إلى {path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def print_invoice_html(self) -> None:
        inv_id = self.pay_inv_var.get().strip() or self.inv_id_var.get().strip()
        if not inv_id:
            messagebox.showwarning("تنبيه", "يرجى إدخال رقم الفاتورة")
            return
        try:
            path = self.system.export_invoice_html(inv_id, Path("invoice_print.html"))
            import webbrowser

            webbrowser.open(path.absolute().as_uri())
            messagebox.showinfo("تنبيه", "تم فتح الفاتورة للطباعة. استخدم طباعة المتصفح على A4 أو PDF.")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def copy_invoice_text(self) -> None:
        text = self.invoice_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("تنبيه", "لا يوجد نص لنسخه")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("تم", "تم نسخ الفاتورة إلى الحافظة")

    def _populate_invoice_table(self, invoice: Invoice) -> None:
        for row in self.invoice_items_tree.get_children():
            self.invoice_items_tree.delete(row)
        for item in invoice.items:
            name = self.system.products.get(item.product_sku, Product("", "", 0)).name
            self.invoice_items_tree.insert(
                "",
                "end",
                values=(
                    item.product_sku,
                    name,
                    item.quantity,
                    item.unit_price,
                    f"{int(item.discount_rate*100)}%",
                    item.total(),
                ),
            )

    # ============================= كشف حساب/كاش =============================
    def show_ledger(self) -> None:
        if not self._require_perm("ledger_view"):
            return
        party_id = self.ledger_party_var.get().strip()
        party_type = self.ledger_type_var.get()
        if not party_id:
            messagebox.showwarning("تنبيه", "يرجى إدخال معرف الطرف")
            return
        entries: List[LedgerEntry] = self.system.ledger_for_party(party_type, party_id)
        lines = [f"كشف حساب لـ {party_type} - {party_id}"]
        balance = 0.0
        for e in entries:
            sign = 1 if e.direction == "in" else -1
            balance += sign * e.amount
            lines.append(f"{e.timestamp} | {e.reference} | {e.direction} | {e.amount} | {e.note}")
        lines.append(f"الرصيد (in - out): {round(balance,2)}")
        self.ledger_text.delete("1.0", tk.END)
        self.ledger_text.insert(tk.END, "\n".join(lines))

    def add_cash_entry(self) -> None:
        if not self._require_perm("ledger_view"):
            return
        try:
            self.system.add_cash_entry(
                self.cash_id_var.get().strip(),
                self.cash_cat_var.get().strip(),
                float(self.cash_amount_var.get()),
                self.cash_kind_var.get(),
                self.cash_note_var.get().strip(),
            )
            messagebox.showinfo("تم", "تم تسجيل الحركة")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def show_profit(self) -> None:
        if not self._require_perm("ledger_view"):
            return
        try:
            start = datetime.strptime(self.profit_start_var.get(), "%Y-%m-%d").date()
            end = datetime.strptime(self.profit_end_var.get(), "%Y-%m-%d").date()
            report = self.system.period_report(start, end)
            lines = [
                f"الفترة: {report['start']} -> {report['end']}",
                f"المبيعات: {report['sales_total']}",
                f"المشتريات: {report['purchases_total']}",
                f"إيرادات أخرى: {report['income_extra']}",
                f"مصروفات: {report['expenses_extra']}",
                f"الربح التقديري: {report['profit_estimated']}",
            ]
            self.ledger_text.delete("1.0", tk.END)
            self.ledger_text.insert(tk.END, "\n".join(lines))
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    # ============================= تقارير وبحث =============================
    def show_daily_report(self) -> None:
        if not self._require_perm("reports_view"):
            return
        try:
            target = datetime.strptime(self.report_date_var.get(), "%Y-%m-%d").date()
            report = self.system.daily_report(target)
            self._fill_report_table(
                ["التاريخ", "عدد الفواتير", "المبيعات", "المشتريات", "المحصل", "المدفوع", "الربح"],
                [
                    (
                        report.get("start", target.isoformat()),
                        report["invoices"],
                        report["sales_total"],
                        report["purchases_total"],
                        report["collected"],
                        report["paid_out"],
                        report["profit_estimated"],
                    )
                ],
            )
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def show_inventory_report(self) -> None:
        if not self._require_perm("reports_view"):
            return
        try:
            period = self.inventory_period_var.get()
            report = self.system.inventory_report(period)
            rows = []
            for sku, info in report.items():
                rows.append((sku, info["name"], info["purchased"], info["sold"], info["returned"], info["available"]))
            self._fill_report_table(["SKU", "الاسم", "مشتريات", "مبيعات", "مرتجع", "متاح"], rows)
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_inventory_html(self) -> None:
        if not self._require_perm("reports_view"):
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if not file_path:
            return
        try:
            path = self.system.export_inventory_html(self.inventory_period_var.get(), Path(file_path))
            messagebox.showinfo("تم", f"تم التصدير إلى {path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_inventory_pdf(self) -> None:
        if not self._require_perm("reports_view"):
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not file_path:
            return
        try:
            path = self.system.export_inventory_pdf(self.inventory_period_var.get(), Path(file_path))
            messagebox.showinfo("تم", f"تم التصدير إلى {path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_inventory_excel(self) -> None:
        if not self._require_perm("reports_view"):
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not file_path:
            return
        try:
            path = self.system.export_inventory_excel(self.inventory_period_var.get(), Path(file_path))
            messagebox.showinfo("تم", f"تم التصدير إلى {path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def run_generic_search(self) -> None:
        if not self._require_perm("reports_view"):
            return
        term = self.generic_search_var.get().strip()
        if not term:
            return
        products = self.system.search_products(term)
        customers = self.system.search_customers(term)
        suppliers = self.system.search_suppliers(term)
        rows = []
        for p in products:
            rows.append(("منتج", p.sku, p.name, "", "", ""))
        for c in customers:
            rows.append(("عميل", c.customer_id, c.name, c.phone, c.address, ""))
        for s in suppliers:
            rows.append(("مورد", s.supplier_id, s.name, s.phone, s.address, ""))
        self._fill_report_table(["النوع", "المعرف", "الاسم", "الهاتف", "العنوان", ""], rows)

    def export_report_excel(self) -> None:
        if not self._require_perm("reports_view"):
            return
        if not self.report_headers or not self.report_rows:
            messagebox.showwarning("تنبيه", "لا يوجد بيانات لعرضها في الجدول")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not file_path:
            return
        try:
            df = pd.DataFrame(self.report_rows, columns=self.report_headers)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("تم", f"تم التصدير إلى {file_path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_report_pdf(self) -> None:
        if not self._require_perm("reports_view"):
            return
        if not self.report_headers or not self.report_rows:
            messagebox.showwarning("تنبيه", "لا يوجد بيانات لعرضها في الجدول")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not file_path:
            return
        try:
            from fpdf import FPDF  # type: ignore

            pdf = FPDF(orientation="L", unit="mm", format="A4")
            pdf.add_page()
            pdf.set_font("Arial", size=11)
            col_count = len(self.report_headers)
            width = 280 / max(col_count, 1)
            for header in self.report_headers:
                pdf.cell(width, 8, txt=str(header), border=1, align="C")
            pdf.ln()
            for row in self.report_rows:
                for cell in row:
                    pdf.cell(width, 8, txt=str(cell), border=1, align="C")
                pdf.ln()
            pdf.output(file_path)
            messagebox.showinfo("تم", f"تم التصدير إلى {file_path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def export_report_html(self) -> None:
        if not self._require_perm("reports_view"):
            return
        if not self.report_headers or not self.report_rows:
            messagebox.showwarning("تنبيه", "لا يوجد بيانات لعرضها في الجدول")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML", "*.html")])
        if not file_path:
            return
        try:
            header_cells = "".join(f"<th>{h}</th>" for h in self.report_headers)
            rows = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in self.report_rows)
            html = f"""
            <html><head><meta charset="utf-8">
            <style>
            @media print {{ @page {{ size: A4 landscape; margin: 10mm; }} }}
            body{{font-family:'Arial';margin:20px;}}
            table{{width:100%;border-collapse:collapse;}}
            th,td{{border:1px solid #999;padding:6px;text-align:center;}}
            </style></head><body>
            <table><tr>{header_cells}</tr>{rows}</table>
            </body></html>
            """
            Path(file_path).write_text(html, encoding="utf-8")
            messagebox.showinfo("تم", f"تم التصدير إلى {file_path}")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def _fill_report_table(self, headers: list[str], rows: list[tuple]) -> None:
        self.report_headers = headers
        self.report_rows = rows
        self.report_table["columns"] = [f"c{i}" for i in range(len(headers))]
        self.report_table.delete(*self.report_table.get_children())
        for idx, title in enumerate(headers):
            col_id = f"c{idx}"
            self.report_table.heading(col_id, text=title)
            self.report_table.column(col_id, anchor="center")
        for row in rows:
            self.report_table.insert("", "end", values=row)

    # ============================= اختصارات النسخ/اللصق =============================
    def _focus_widget(self):
        try:
            return self.focus_get()
        except Exception:
            return None

    def global_copy(self) -> None:
        widget = self._focus_widget()
        if not widget:
            return
        text = ""
        try:
            if isinstance(widget, tk.Text):
                text = widget.get("sel.first", "sel.last")
            elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
                text = widget.selection_get()
            elif isinstance(widget, ttk.Treeview):
                selection = widget.selection()
                if selection:
                    lines = []
                    for iid in selection:
                        values = widget.item(iid, "values")
                        lines.append("\t".join(str(v) for v in values))
                    text = "\n".join(lines)
            else:
                text = widget.selection_get()
        except Exception:
            try:
                widget.event_generate("<<Copy>>")
            except Exception:
                return
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

    def global_paste(self) -> None:
        widget = self._focus_widget()
        if not widget:
            return
        try:
            widget.event_generate("<<Paste>>")
        except Exception:
            pass

    def global_cut(self) -> None:
        widget = self._focus_widget()
        if not widget:
            return
        try:
            widget.event_generate("<<Cut>>")
        except Exception:
            # fallback for Text
            try:
                if isinstance(widget, tk.Text):
                    text = widget.get("sel.first", "sel.last")
                    self.clipboard_clear()
                    self.clipboard_append(text)
                    widget.delete("sel.first", "sel.last")
            except Exception:
                pass

    def global_select_all(self) -> None:
        widget = self._focus_widget()
        if not widget:
            return
        try:
            if isinstance(widget, tk.Text):
                widget.tag_add("sel", "1.0", "end")
            elif isinstance(widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
                widget.selection_range(0, tk.END)
            elif isinstance(widget, ttk.Treeview):
                widget.selection_set(widget.get_children())
            else:
                widget.event_generate("<<SelectAll>>")
        except Exception:
            pass

    # ============================= المستخدمون =============================
    def create_user(self) -> None:
        if self.current_user.username != "admin":
            messagebox.showwarning("تنبيه", "فقط حساب admin يمكنه إضافة مستخدمين")
            return
        admin_pass = simpledialog.askstring("تأكيد", "أدخل كلمة مرور admin", show="*")
        admin_user = self.system.users.get("admin")
        if not admin_user or not admin_pass or not admin_user.check_password(admin_pass):
            messagebox.showerror("خطأ", "كلمة مرور admin غير صحيحة")
            return
        username = self.new_user_var.get().strip()
        password = self.new_pass_var.get()
        if not username or not password:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المستخدم وكلمة المرور")
            return
        if username == "admin":
            messagebox.showwarning("تنبيه", "لا يمكن إنشاء مستخدم بنفس اسم وحساب admin")
            return
        perms = [perm for perm, var in self.perm_vars.items() if var.get()]
        try:
            self.system.add_user(username, password, role="user", permissions=perms)
            self.refresh_users()
            messagebox.showinfo("تم", "تم إنشاء المستخدم")
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("خطأ", str(exc))

    def refresh_users(self) -> None:
        for row in self.users_tree.get_children():
            self.users_tree.delete(row)
        for u in self.system.users.values():
            self.users_tree.insert("", "end", values=(u.username, u.role, ",".join(u.permissions)))


def main() -> None:
    app = SalesApp()
    app.mainloop()


if __name__ == "__main__":
    main()
