"""PVG Worksupply Invoice Parser - Count Normal, Saturday, Sunday, OT hours (exclude Night)."""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pdfplumber
from parsers.invoice_parser import InvItem, EmpDetail, Invoice, _pn

# Which types count as work hours (Night Hours 125% excluded)
COUNT_TYPES = {
    "Normal Hours 100%": True,
    "Saturday Hours 125%": True,
    "Sunday Hours 150%": True,
    "OT Hours (Above 40 hrs)": True,
    "Night Hours 125%": False,
}


def parse_worksupply_invoice_pdf(path):
    inv = Invoice()
    inv.type = "WORKSUPPLY"
    
    with pdfplumber.open(path) as pdf:
        all_lines = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "Duplicado" in text:
                break
            for line in text.split("\n"):
                l = line.strip()
                if l:
                    all_lines.append(l)
    
    all_text = "\n".join(all_lines)
    
    m = re.search(r"FT\s+(\d+/\d+)", all_text)
    if m: inv.num = "FT " + m.group(1)
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+EUR", all_text)
    if m: inv.date = m.group(1)
    inv.p_start = "Week 27"
    inv.p_end = "Week 27"
    
    for line in reversed(all_lines):
        m = re.search(r"Total\s+\(Valor sem iva / Net amount\)\s*([\d.,]+)", line)
        if m:
            inv.excl = _pn(m.group(1))
            inv.incl = _pn(m.group(1))
            break
    
    SUBSIDY_TYPES = {"Saturday Hours 125%", "Sunday Hours 150%", "OT Hours (Above 40 hrs)"}
    emp_data = {}
    current_qty = None
    current_type = None
    current_emp = None
    
    for line in all_lines:
        dl = line.lstrip('"').strip()
        m_prov = re.match(r"Provision of Temporary Staffing\s+([\d.]+)\s*horas?\s+", dl)
        if m_prov:
            current_qty = float(m_prov.group(1))
            current_type = None
            current_emp = None
            continue
        
        if current_qty is not None and current_type is None:
            if line in ("Normal Hours 100%", "Saturday Hours 125%", "Sunday Hours 150%", "OT Hours (Above 40 hrs)", "Night Hours 125%"):
                current_type = line
                continue
            if line == "Services (*)":
                continue
            if "Provision of" in line:
                continue
        
        if current_qty is not None and current_type is not None and current_emp is None:
            skip_words = ["Services", "IVA", "(*)","Total","Transporte","Pagina","Codigo","Week","Brought","Carried","(Valor"]
            is_skip = any(line.startswith(w) or line.startswith(w.lower()) for w in skip_words)
            if not is_skip and "IVA" not in line and "(*) " not in line:
                current_emp = line.strip()
                continue
        
        if current_qty is not None and current_type is not None and current_emp is not None:
            if "Week" in line:
                cn = current_emp
                if cn not in emp_data:
                    emp_data[cn] = {"total": 0.0, "subsidy": 0.0, "night": 0.0, "items": []}
                if current_type == "Night Hours 125%" and "Night" in current_type:
                    emp_data[cn]["night"] += current_qty
                else:
                    emp_data[cn]["total"] += current_qty
                    if current_type in SUBSIDY_TYPES:
                        emp_data[cn]["subsidy"] += current_qty
                    emp_data[cn]["items"].append((current_type, current_qty))
                current_qty = None
                current_type = None
                current_emp = None
    
    for emp_name, ed in emp_data.items():
        emp = EmpDetail(name=emp_name, period="", role="")
        emp.add(InvItem(name="Prestations", qty=round(ed["total"], 2), rate=0, pct=0, amt=0))
        if ed["subsidy"] > 0:
            emp.add(InvItem(name="Subsidy Hours", qty=round(ed["subsidy"], 2), rate=0, pct=0, amt=0))
        if ed["night"] > 0:
            emp.add(InvItem(name="Night Hours", qty=round(ed["night"], 2), rate=0, pct=0, amt=0))
        for item_name, qty in ed["items"]:
            emp.add(InvItem(name=item_name, qty=round(qty, 2), rate=0, pct=0, amt=0))
        emp.subtotal = 0
        inv.add(emp)
    
    return inv

