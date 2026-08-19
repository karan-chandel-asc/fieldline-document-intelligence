import textwrap

INVOICE_JSON = {
    "document_id": "doc_10482",
    "filename": "INV-10482.pdf",
    "schema": "InvoiceExtract",
    "status": "needs_review",
    "vendor": "Harbor Freight Lines",
    "invoice_no": "INV-10482",
    "invoice_date": "2026-08-18",
    "po_number": None,
    "currency": "USD",
    "subtotal": "4020.00",
    "tax": "260.00",
    "total": "4280.00",
    "line_items": [
        {"description": "Linehaul — Chicago to Dallas", "qty": "1", "amount": "3400.00"},
        {"description": "Fuel surcharge", "qty": "1", "amount": "620.00"},
        {"description": "Detention", "qty": "2 hrs", "amount": "260.00"},
    ],
    "validation": {"math_ok": True, "date_in_future": False},
}

RECEIPT_JSON = {
    "document_id": "doc_8831",
    "filename": "RCP-8831.pdf",
    "schema": "ReceiptExtract",
    "status": "needs_review",
    "merchant": "Meridian Supplies",
    "paid_at": "2027-03-14",
    "payment_method": "Visa ••4412",
    "subtotal": "41.20",
    "tax": "3.71",
    "total": "44.91",
    "validation": {"math_ok": True, "date_in_future": True},
}

BOL_JSON = {
    "document_id": "doc_2291",
    "filename": "BOL-2291.pdf",
    "schema": "BillOfLadingExtract",
    "status": "needs_review",
    "shipper": "Northline Logistics",
    "consignee": "Harbor Freight Lines — Dallas DC",
    "pro_number": "PRO-2291",
    "weight_lbs": "18420",
    "pickup_date": "2026-08-17",
    "validation": {"math_ok": True, "date_in_future": False},
}

SAMPLES = {
    "invoice": {
        "id": "invoice",
        "kind": "invoice",
        "filename": "INV-10482.pdf",
        "schema_name": "Invoice",
        "pages": "Page 1 of 2",
        "table": "invoice_extract",
        "payload": INVOICE_JSON,
        "pydantic": textwrap.dedent("""\
        class InvoiceExtract(BaseModel):
    vendor: str
    invoice_no: str
    invoice_date: date
    po_number: Optional[str] = None
    currency: Literal["USD", "EUR", "GBP"]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    line_items: list[LineItem]

    @model_validator(mode="after")
    def totals_must_balance(self):
        if self.subtotal + self.tax != self.total:
            raise ValueError("subtotal + tax must equal total")
        if self.invoice_date > date.today():
            raise ValueError("invoice_date cannot be in the future")
        return self
        """),
        "postgres": """CREATE TABLE invoice_extract (
  document_id  text PRIMARY KEY,
  vendor       text NOT NULL,
  invoice_no   text NOT NULL,
  invoice_date date NOT NULL,
  po_number    text,
  currency     char(3) NOT NULL,
  subtotal     numeric(12,2) NOT NULL,
  tax          numeric(12,2) NOT NULL,
  total        numeric(12,2) NOT NULL,
  CONSTRAINT invoice_math CHECK (subtotal + tax = total)
);""",
        "fields": [
            {"key": "vendor", "label": "Vendor", "value": "Harbor Freight Lines", "conf": 98, "bbox": [7, 5, 46, 8]},
            {"key": "invoice_no", "label": "Invoice number", "value": "INV-10482", "conf": 97, "bbox": [62, 6, 31, 8]},
            {"key": "invoice_date", "label": "Invoice date", "value": "2026-08-18", "conf": 94, "bbox": [7, 22, 38, 6], "tag": "ISO 8601"},
            {
                "key": "po_number",
                "label": "PO number",
                "value": "PO-??",
                "conf": 41,
                "low": True,
                "hint": "Check PO#",
                "bbox": [7, 78, 30, 10],
            },
            {"key": "currency", "label": "Currency", "value": "USD", "conf": 99, "bbox": [62, 70, 14, 6], "tag": "Normalized USD"},
            {"key": "total", "label": "Total", "value": "4280.00", "conf": 96, "bbox": [52, 70, 41, 9], "tag": "Sum verified"},
        ],
        "line_items": [
            ["Linehaul — Chicago to Dallas", "1", "3400.00"],
            ["Fuel surcharge", "1", "620.00"],
            ["Detention", "2 hrs", "260.00"],
        ],
        "validations": [
            {"ok": True, "title": "Line items sum match total ($4,280.00)", "detail": "$3,400 + $620 + $260 = $4,280.00"},
            {"ok": True, "title": "Date format standardized (ISO 8601)", "detail": "2026-08-18"},
            {"ok": True, "title": "Currency normalized (USD)", "detail": "All money fields in USD"},
        ],
    },
    "receipt": {
        "id": "receipt",
        "kind": "receipt",
        "filename": "RCP-8831.pdf",
        "schema_name": "Receipt",
        "pages": "Page 1 of 1",
        "table": "receipt_extract",
        "payload": RECEIPT_JSON,
        "pydantic": """class ReceiptExtract(BaseModel):
    merchant: str
    paid_at: date
    payment_method: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal

    @model_validator(mode="after")
    def totals_and_date(self):
        if self.subtotal + self.tax != self.total:
            raise ValueError("subtotal + tax must equal total")
        if self.paid_at > date.today():
            raise ValueError("paid_at cannot be in the future")
        return self""",
        "postgres": """CREATE TABLE receipt_extract (
  document_id text PRIMARY KEY,
  merchant    text NOT NULL,
  paid_at     date NOT NULL,
  subtotal    numeric(12,2) NOT NULL,
  tax         numeric(12,2) NOT NULL,
  total       numeric(12,2) NOT NULL,
  CONSTRAINT receipt_math CHECK (subtotal + tax = total)
);""",
        "fields": [
            {"key": "merchant", "label": "Merchant", "value": "Meridian Supplies", "conf": 91, "bbox": [18, 8, 64, 10]},
            {
                "key": "paid_at",
                "label": "Date paid",
                "value": "2027-03-14",
                "conf": 62,
                "low": True,
                "hint": "Date in the future",
                "bbox": [22, 20, 52, 8],
            },
            {"key": "payment_method", "label": "Payment", "value": "Visa ••4412", "conf": 88, "bbox": [20, 72, 56, 8]},
            {"key": "subtotal", "label": "Subtotal", "value": "41.20", "conf": 95, "bbox": [48, 48, 36, 7]},
            {"key": "tax", "label": "Tax", "value": "3.71", "conf": 93, "bbox": [48, 56, 36, 7]},
            {"key": "total", "label": "Total", "value": "44.91", "conf": 96, "bbox": [48, 64, 36, 8]},
        ],
        "line_items": [
            ["Copy paper 10-ream", "1", "28.40"],
            ["Binder clips", "2", "12.80"],
        ],
        "validations": [
            {"ok": True, "title": "Line items sum match total ($44.91)", "detail": "$41.20 + $3.71 = $44.91"},
            {"ok": True, "title": "Date format standardized (ISO 8601)", "detail": "2027-03-14"},
            {"ok": False, "title": "Date not in the future", "detail": "Model read 2027-03-14 — confirm on the scan"},
        ],
    },
    "bol": {
        "id": "bol",
        "kind": "bol",
        "filename": "BOL-2291.pdf",
        "schema_name": "Bill of lading",
        "pages": "Page 1 of 3 · skewed scan",
        "table": "bol_extract",
        "payload": BOL_JSON,
        "pydantic": """class BillOfLadingExtract(BaseModel):
    shipper: str
    consignee: str
    pro_number: str
    weight_lbs: int = Field(gt=0)
    pickup_date: date""",
        "postgres": """CREATE TABLE bol_extract (
  document_id text PRIMARY KEY,
  shipper     text NOT NULL,
  consignee   text NOT NULL,
  pro_number  text NOT NULL,
  weight_lbs  integer NOT NULL CHECK (weight_lbs > 0),
  pickup_date date NOT NULL
);""",
        "fields": [
            {"key": "shipper", "label": "Shipper", "value": "Northline Logistics", "conf": 96, "bbox": [8, 10, 50, 9]},
            {
                "key": "consignee",
                "label": "Consignee",
                "value": "Harbor Freight Lines — Dallas DC",
                "conf": 62,
                "low": True,
                "hint": "Check consignee",
                "bbox": [8, 24, 70, 10],
            },
            {"key": "pro_number", "label": "PRO number", "value": "PRO-2291", "conf": 94, "bbox": [58, 8, 34, 8]},
            {"key": "weight_lbs", "label": "Weight (lbs)", "value": "18420", "conf": 90, "bbox": [8, 68, 28, 8]},
            {"key": "pickup_date", "label": "Pickup date", "value": "2026-08-17", "conf": 92, "bbox": [8, 48, 36, 7]},
        ],
        "line_items": [],
        "validations": [
            {"ok": True, "title": "Weight parsed as integer", "detail": "18,420 lbs passed Pydantic Field(gt=0)"},
            {"ok": True, "title": "Date format standardized (ISO 8601)", "detail": "2026-08-17"},
            {"ok": True, "title": "PRO number normalized", "detail": "PRO-2291"},
        ],
    },
}


def build_sql(table, payload):
    skip = {"line_items", "validation", "schema", "status", "filename"}
    cols = []
    vals = []
    for key, value in payload.items():
        if key in skip or isinstance(value, (list, dict)):
            continue
        cols.append(key)
        if value is None:
            vals.append("NULL")
        else:
            vals.append("'" + str(value).replace("'", "''") + "'")
    return "INSERT INTO {table} (\n  {cols}\n) VALUES (\n  {vals}\n);".format(
        table=table,
        cols=",\n  ".join(cols),
        vals=",\n  ".join(vals),
    )
