"""PVG Pacework Invoice Parser.
Format: Aggregated PDF invoice with line items by day and hour type.
No per-employee breakdown. Total hours from attendance vs total hours from invoice.
"""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pdfplumber
from parsers.invoice_parser import InvItem, EmpDetail, Invoice, _pn

def parse_pacework_invoice_pdf(path):
    """Parse Pacework invoice PDF. Returns an Invoice with an artificial employee entry for the total."""
    inv = Invoice()
    inv.type = "PACEWORK"
    
    with pdfplumber.open(path) as pdf:
        page_texts = []
        for page in pdf.pages:
            t = page.extract_text() or ""
            if "Duplicado" in t:
                break
            page_texts.append(t)
    
    all_text = "\n".join(page_texts)
    
    # Invoice number
    m = re.search(r'Factuur\s+(\S+)', all_text)
    if m:
        inv.num = m.group(1).strip()
    
    # Invoice date
    m = re.search(r'Factuurdatum:\s*(\d{2}-\d{2}-\d{4})', all_text)
    if m:
        inv.date = m.group(1)
    
    # Period from Kenmerk
    m = re.search(r'Kenmerk:\s*Week\s+(\d+)\s*-\s*(.*?)(?:\s+Vervaldatum)', all_text)
    if m:
        week = m.group(1)
        inv_type = m.group(2).strip()
        inv.p_start = f"Week {week}"
        inv.p_end = f"Week {week}"
    
    # Type: Teamleider or Magazijnmedewerkers
    if "Teamleider" in all_text:
        inv.type = "PACEWORK_TEAM_LEADER"
    elif "Magazijnmedewerkers" in all_text:
        inv.type = "PACEWORK_WAREHOUSE"
    
    # Parse line items
    # Format: "2 Maandag: Ochtenduren en Avond normale uren € 29,42 € 58,84 21%"
    total_regular_hours = 0.0
    total_surcharge_hours = 0.0
    total_night_hours = 0.0
    
    # Pattern for line items
    item_pattern = re.compile(
        r'^([\d.]+)\s+'
        r'(Maandag|Dinsdag|Woensdag|Donderdag|Vrijdag|Zaterdag|Zondag):\s+'
        r'(.*?)\s+'
        r'[€]\s*([\d.,]+)\s+'
        r'[€]\s*([\d.,]+)\s+'
        r'(\d+)%'
    )
    
    day_names_nl = {
        "Maandag": "Monday", "Dinsdag": "Tuesday", "Woensdag": "Wednesday",
        "Donderdag": "Thursday", "Vrijdag": "Friday", "Zaterdag": "Saturday", "Zondag": "Sunday"
    }
    SUBSIDY_DAYS = {"Zaterdag", "Zondag"}
    
    for line in all_text.split("\n"):
        line = line.strip()
        m = item_pattern.match(line)
        if m:
            qty = float(m.group(1))
            day_nl = m.group(2)
            desc = m.group(3).strip()
            rate_str = m.group(4)
            total_str = m.group(5)
            
            if "normale uren" in desc:
                total_regular_hours += qty
            elif "Nachturen" in desc:
                total_night_hours += qty
            elif "Toeslaguren" in desc or "Volledige dag" in desc:
                total_surcharge_hours += qty
    
    # Totals
    m = re.search(r'Subtotaal\s*[€]\s*([\d.,]+)', all_text)
    if m:
        inv.excl = _pn(m.group(1))
    m = re.search(r'Totaal\s*[€]\s*([\d.,]+)', all_text)
    if m:
        inv.incl = _pn(m.group(1))
    
    # Create a single "employee" representing the total
    total_hours = total_regular_hours + total_surcharge_hours + total_night_hours
    
    # Use different emp names to keep Team Leader and Warehouse invoices separate
    inv_type_label = "Team Leader" if inv.type == "PACEWORK_TEAM_LEADER" else "Magazijnmedewerkers"
    # Calculate subsidy: Saturday + Sunday surcharge hours (these are the extra hours on weekends)
    subsidy_hours = 0.0
    for line in all_text.split("\n"):
        line = line.strip()
        m = item_pattern.match(line)
        if m:
            day_nl = m.group(2)
            desc = m.group(3).strip()
            if day_nl in SUBSIDY_DAYS and ("Toeslaguren" in desc or "Volledige dag" in desc):
                qty = float(m.group(1))
                subsidy_hours += qty
    
    emp = EmpDetail(name=inv_type_label, period=inv.p_start, role="")
    emp.add(InvItem(name="Prestations", qty=total_hours, rate=0, pct=0, amt=0))
    if subsidy_hours > 0:
        emp.add(InvItem(name="Subsidy Hours", qty=round(subsidy_hours, 2), rate=0, pct=0, amt=0))
    if total_regular_hours > 0:
        emp.add(InvItem(name="Regular Hours", qty=total_regular_hours, rate=0, pct=0, amt=0))
    if total_surcharge_hours > 0:
        emp.add(InvItem(name="Surcharge Hours", qty=total_surcharge_hours, rate=0, pct=0, amt=0))
    if total_night_hours > 0:
        emp.add(InvItem(name="Night Hours", qty=total_night_hours, rate=0, pct=0, amt=0))
    emp.subtotal = inv.excl
    inv.add(emp)
    
    return inv
