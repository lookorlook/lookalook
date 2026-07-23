"""Spain ALLIANCE Invoice Parser."""
import sys, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pdfplumber
from parsers.invoice_parser import InvItem, EmpDetail, Invoice, _pn


def parse_spain_invoice_pdf(path):
    """Parse Spain ALLIANCE invoice PDF (text-based Empleado format)."""
    inv = Invoice()
    inv.type = "SPAIN_ALLIANCE"

    with pdfplumber.open(path) as pdf:
        page_texts = [page.extract_text() or "" for page in pdf.pages]

    p0 = page_texts[0]

    # Invoice number: Factura n\u00famero: 001/2026/000273
    m = re.search(r"Factura\s+n[uú]mero:\s*([\d/]+)", p0)
    if m:
        inv.num = m.group(1).strip()

    # Date: Fecha operaci\u00f3n: 30/06/2026
    m = re.search(r"Fecha\s+operaci[o\u00f3]n:\s*(\d{2}/\d{2}/\d{4})", p0)
    if m:
        inv.date = m.group(1)

    # Totals from last page
    last_text = page_texts[-1]
    m = re.search(r"Base\s+Imponible:\s*([\d\.\,]+)", last_text)
    if m:
        inv.excl = _pn(m.group(1))
    m = re.search(r"Total\s+Factura:\s*([\d\.\,]+)", last_text)
    if m:
        inv.incl = _pn(m.group(1))

    # Clean lines: remove header/footer noise
    clean_lines = []
    skip_patterns = [
        r"^ALLIANCE\s+WORK\s+ETT",
        r"^PS\s+DE\s+LAS\s+DELICIAS",
        r"^28045\s+MADRID",
        r"^CIF:.*Tlf:",
        r"^Factura\s+n[u\u00fa]mero:",
        r"^Fecha\s+operaci[o\u00f3]n:",
        r"^Concepto\s+Unidades\s+Precio",
        r"^Inscrita\s+en\s+el\s+Registro",
        r"^Datos\s+bancarios:",
        r"^IBAN",
        r"^Forma\s+de\s+pago:",
        r"^Vencimientos:",
        r"^\d+,\d+\s+%\s+IVA",
    ]
    for text in page_texts:
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            skip = False
            for pat in skip_patterns:
                if re.match(pat, line, re.IGNORECASE):
                    skip = True
                    break
            if not skip:
                clean_lines.append(line)

    # Parse employees
    current_emp = None

    for line in clean_lines:
        # Empleado: NAME
        m = re.match(r"Empleado:\s*(.*)", line)
        if m:
            emp_name = m.group(1).strip().rstrip(",")
            current_emp = EmpDetail(name=emp_name)
            inv.add(current_emp)
            continue

        # Contrato del START al END
        m = re.match(r"Contrato\s+del\s+(\d{2}/\d{2}/\d{4})\s+al\s+(\d{2}/\d{2}/\d{4})", line)
        if m:
            continue

        # Item line: CODE DESC QTY RATE AMT (no discount column in Spain format)
        tokens = line.split()
        if len(tokens) >= 4 and re.match(r"^\d{5}$", tokens[0]):
            code = tokens[0]
            amt_str = tokens[-1]
            rate_str = tokens[-2]
            qty_str = tokens[-3]
            desc = " ".join(tokens[1:-3]).strip()
            pct = 0

            qty = _pn(qty_str)
            rate = _pn(rate_str)
            amt = _pn(amt_str)

            name_map = {
                "HORAS NORMALES": "Prestations",
                "HORAS EXTRAS 2": "Horas Extras",
                "HORAS EX NORMAL": "Horas Ex Normal",
            }
            item_name = name_map.get(desc, desc)

            item = InvItem(name=item_name, qty=qty, rate=rate, pct=pct, amt=amt)
            if current_emp:
                current_emp.add(item)
            continue

        # Skip total lines
        if line.startswith("Total por periodo") or line.startswith("Total por empleado"):
            continue

    inv.emps = [e for e in inv.emps if e.items]
    return inv
