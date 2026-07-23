"""Spain Randstad Invoice Parser."""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pdfplumber
from parsers.invoice_parser import InvItem, EmpDetail, Invoice, _pn


def parse_ranstad_invoice_pdf(path):
    """Parse Randstad Spain invoice PDF."""
    inv = Invoice()
    inv.type = "RANDSTAD"

    with pdfplumber.open(path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]

    all_text = "\n".join(pages_text)

    # Invoice number
    m = re.search(r"N[u\u00fa]mero\s*(\d+)", all_text)
    if m: inv.num = m.group(1)

    # Date
    m = re.search(r"Fecha\s*(\d{2}/\d{2}/\d{4})", all_text)
    if m: inv.date = m.group(1)

    # Totals
    for text in pages_text:
        m = re.search(r"Base\s+Imponible\s*([\d.,]+)", text)
        if m: inv.excl = _pn(m.group(1))
        m = re.search(r"Total\s+Factura\s*\(Euros\)\s*([\d.,]+)", text)
        if m: inv.incl = _pn(m.group(1))

    # Skip patterns
    SKIP = ["Randstad Empleo", "Avda.", "FACTURA", "Dirigido a:", "Razon social",
             "YUNEXPRESS SPAIN", "C.I.F.", "28042 - Madrid", "Pag.",
             "Domicilio Social:", "Via de los Poblados", "Edificio",
             "Aut. Adtva.", "Version", "Concepto", "Unidades", "Tarifa", "Importe",
             "Fecha de vencimiento", "Forma de pago", "Transferencia:", "Cuenta:",
             "Base Imponible", "Base Exenta", "IVA", "Total Factura", "SWIFT:"]

    # Name regex: allow Spanish accented uppercase chars
    upper_acc = "\u00c1\u00c9\u00cd\u00d3\u00da\u00dc\u00d1"
    name_chars = "A-Za-z" + upper_acc + "\\s,.\\-\\u00c0-\\u00ff"
    name_pat = re.compile("^[" + upper_acc + "A-Z][" + name_chars + "]+$")

    # Item patterns: (regex, display_name)
    item_pats = [
        (re.compile(r"^(Horas normales)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)$"), "Prestations"),
        (re.compile(r"^(Exceso cotizaci[o\u00f3]n)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)$"), "Exceso cotizaci\u00f3n"),
        (re.compile(r"^(RDL32/2021\.Contra\.<30dias)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)$"), "RDL32 Cotizaci\u00f3n"),
        (re.compile(r"^(Horas extras)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)$"), "Horas Extras"),
        (re.compile(r"^(Plus nocturnidad)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)$"), "Plus nocturnidad"),
    ]

    current_emp = None
    for line in all_text.split("\n"):
        l = line.strip()
        if not l or l == ".": continue
        if any(l.startswith(p) for p in SKIP): continue
        if re.match(r"^\d+\s+de\s+\d+$", l): continue

        # Employee name: all caps with comma
        if name_pat.match(l) and "," in l and len(l) > 5 and not l.startswith("Subtotal:"):
            current_emp = EmpDetail(name=l.rstrip(","))
            inv.add(current_emp)
            continue

        if current_emp:
            matched = False
            for pat, pname in item_pats:
                m = pat.match(l)
                if m:
                    qty = _pn(m.group(2))
                    rate = _pn(m.group(3))
                    amt = _pn(m.group(4))
                    current_emp.add(InvItem(name=pname, qty=qty, rate=rate, pct=0, amt=amt))
                    matched = True
                    break
            if not matched and l.startswith("Subtotal:"):
                sm = re.search(r"([\d.,]+)$", l)
                if sm: current_emp.subtotal = _pn(sm.group(1))

    inv.emps = [e for e in inv.emps if e.items]

    # Merge duplicates
    i = 0
    while i < len(inv.emps) - 1:
        if inv.emps[i].name.lower().strip() == inv.emps[i+1].name.lower().strip():
            cur, nxt = inv.emps[i], inv.emps[i+1]
            for item in nxt.items: cur.add(item)
            if nxt.subtotal: cur.subtotal = (cur.subtotal or 0) + (nxt.subtotal or 0)
            inv.emps.pop(i + 1)
            continue
        i += 1

    return inv
