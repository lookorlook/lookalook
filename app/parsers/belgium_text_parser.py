"""Fallback Belgium Tempoteam Invoice Parser - uses text-based extraction."""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pdfplumber
from parsers.invoice_parser import InvItem, EmpDetail, Invoice, _pn, ITEM_NAMES


def parse_belgium_text(path):
    """Parse Belgium Tempoteam invoice using text extraction (more robust)."""
    inv = Invoice()

    with pdfplumber.open(path) as pdf:
        all_text = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text.append(text)

    p0 = all_text[0] if all_text else ""

    # Extract invoice metadata from first page
    m = re.search(r"Num[eé]ro de facture\s*(\d+)", p0)
    if m:
        inv.num = m.group(1)
    m = re.search(r"Date de facture\s*(\d{2}/\d{2}/\d{4})", p0)
    if m:
        inv.date = m.group(1)
    m = re.search(r"P[eé]riode\s*(\d{2}/\d{2}/\d{4})\s*[-]\s*(\d{2}/\d{2}/\d{4})", p0)
    if m:
        inv.p_start, inv.p_end = m.group(1), m.group(2)

    # Extract total amounts
    for text in all_text:
        m = re.search(r"Total excl\.\s*TVA\s*([\d\s.,]+)\s*EUR", text)
        if m:
            inv.excl = _pn(m.group(1))
        m = re.search(r"Total incl\.\s*TVA\s*([\d\s.,]+)\s*EUR", text)
        if m:
            inv.incl = _pn(m.group(1))

    # Detect format type
    has_structured_items = False
    for text in all_text:
        if re.search(r"Prestations|Suppl[eé]ment", text):
            has_structured_items = True
            break

    if not has_structured_items:
        return inv  # Empty invoice

    # Try structured parsing using text lines
    current_emp = None
    emp_section = False

    for text in all_text:
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for employee names (all caps, or proper names)
            # Tempoteam format: employee name followed by detail lines
            if _looks_like_emp_name(line):
                # Check if next line or data suggests new employee section
                current_emp = EmpDetail(name=line)
                inv.add(current_emp)
                emp_section = True
                continue

            if current_emp and emp_section:
                # Check for period row
                if re.match(r"\d{2}/\d{2}/\d{4}", line):
                    current_emp.period = line
                    continue

                # Check for Fonction:
                if "Fonction:" in line:
                    m2 = re.search(r"Fonction:\s*(.+)", line)
                    if m2:
                        current_emp.role = m2.group(1).strip()
                    continue

                # Check for item line: possibly ITEM_NAME qty rate amt
                for iname in ITEM_NAMES:
                    if iname in line:
                        # Extract numbers from the line
                        nums = re.findall(r"[\d.,]+", line.replace(iname, ""))
                        if len(nums) >= 2:
                            try:
                                qty = _pn(nums[0])
                                amt = _pn(nums[-1])
                                rate = _pn(nums[1]) if len(nums) >= 3 else 0
                                pct = _pn(nums[2]) if len(nums) >= 4 else 0
                                if pct > 100:
                                    pct = 0
                                if qty > 0:
                                    item = InvItem(name=iname, qty=qty, rate=rate, pct=pct, amt=amt)
                                    current_emp.add(item)
                            except:
                                pass
                        break

                # Check for Sous-total line
                if "Sous-total" in line:
                    m2 = re.search(r"([\d.,]+)\s*$", line)
                    if m2:
                        try:
                            current_emp.subtotal = _pn(m2.group(1))
                        except:
                            pass

                # Check for Total des Prestations line (end of employee section)
                if line.startswith("Total des") or "Sous-total Transfert" in line:
                    emp_section = False

    # Clean up: remove employees with no items
    inv.emps = [e for e in inv.emps if e.items]
    return inv


"""Fallback Belgium Tempoteam Invoice Parser - uses text-based extraction."""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pdfplumber
from parsers.invoice_parser import InvItem, EmpDetail, Invoice, _pn, ITEM_NAMES


def parse_belgium_text(path):
    """Parse Belgium Tempoteam invoice using text extraction (more robust)."""
    inv = Invoice()

    with pdfplumber.open(path) as pdf:
        all_text = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text.append(text)

    p0 = all_text[0] if all_text else ""

    # Extract invoice metadata from first page
    m = re.search(r"Num[eé]ro de facture\s*(\d+)", p0)
    if m:
        inv.num = m.group(1)
    m = re.search(r"Date de facture\s*(\d{2}/\d{2}/\d{4})", p0)
    if m:
        inv.date = m.group(1)
    m = re.search(r"P[eé]riode\s*(\d{2}/\d{2}/\d{4})\s*[-]\s*(\d{2}/\d{2}/\d{4})", p0)
    if m:
        inv.p_start, inv.p_end = m.group(1), m.group(2)

    # Extract total amounts
    for text in all_text:
        m = re.search(r"Total excl\.\s*TVA\s*([\d\s.,]+)\s*EUR", text)
        if m:
            inv.excl = _pn(m.group(1))
        m = re.search(r"Total incl\.\s*TVA\s*([\d\s.,]+)\s*EUR", text)
        if m:
            inv.incl = _pn(m.group(1))

    # Detect format type
    has_structured_items = False
    for text in all_text:
        if re.search(r"Prestations|Suppl[eé]ment", text):
            has_structured_items = True
            break

    if not has_structured_items:
        return inv  # Empty invoice

    # Try structured parsing using text lines
    current_emp = None
    emp_section = False

    for text in all_text:
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for employee names (all caps, or proper names)
            # Tempoteam format: employee name followed by detail lines
            if _looks_like_emp_name(line):
                # Check if next line or data suggests new employee section
                current_emp = EmpDetail(name=line)
                inv.add(current_emp)
                emp_section = True
                continue

            if current_emp and emp_section:
                # Check for period row
                if re.match(r"\d{2}/\d{2}/\d{4}", line):
                    current_emp.period = line
                    continue

                # Check for Fonction:
                if "Fonction:" in line:
                    m2 = re.search(r"Fonction:\s*(.+)", line)
                    if m2:
                        current_emp.role = m2.group(1).strip()
                    continue

                # Check for item line: possibly ITEM_NAME qty rate amt
                for iname in ITEM_NAMES:
                    if iname in line:
                        # Extract numbers from the line
                        nums = re.findall(r"[\d.,]+", line.replace(iname, ""))
                        if len(nums) >= 2:
                            try:
                                qty = _pn(nums[0])
                                amt = _pn(nums[-1])
                                rate = _pn(nums[1]) if len(nums) >= 3 else 0
                                pct = _pn(nums[2]) if len(nums) >= 4 else 0
                                if pct > 100:
                                    pct = 0
                                if qty > 0:
                                    item = InvItem(name=iname, qty=qty, rate=rate, pct=pct, amt=amt)
                                    current_emp.add(item)
                            except:
                                pass
                        break

                # Check for Sous-total line
                if "Sous-total" in line:
                    m2 = re.search(r"([\d.,]+)\s*$", line)
                    if m2:
                        try:
                            current_emp.subtotal = _pn(m2.group(1))
                        except:
                            pass

                # Check for Total des Prestations line (end of employee section)
                if line.startswith("Total des") or "Sous-total Transfert" in line:
                    emp_section = False

    # Clean up: remove employees with no items
    inv.emps = [e for e in inv.emps if e.items]
    return inv


"""Fallback Belgium Tempoteam Invoice Parser - uses text-based extraction."""
import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pdfplumber
from parsers.invoice_parser import InvItem, EmpDetail, Invoice, _pn, ITEM_NAMES


def parse_belgium_text(path):
    """Parse Belgium Tempoteam invoice using text extraction (more robust)."""
    inv = Invoice()

    with pdfplumber.open(path) as pdf:
        all_text = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text.append(text)

    p0 = all_text[0] if all_text else ""

    # Extract invoice metadata from first page
    m = re.search(r"Num[eé]ro de facture\s*(\d+)", p0)
    if m:
        inv.num = m.group(1)
    m = re.search(r"Date de facture\s*(\d{2}/\d{2}/\d{4})", p0)
    if m:
        inv.date = m.group(1)
    m = re.search(r"P[eé]riode\s*(\d{2}/\d{2}/\d{4})\s*[-]\s*(\d{2}/\d{2}/\d{4})", p0)
    if m:
        inv.p_start, inv.p_end = m.group(1), m.group(2)

    # Extract total amounts
    for text in all_text:
        m = re.search(r"Total excl\.\s*TVA\s*([\d\s.,]+)\s*EUR", text)
        if m:
            inv.excl = _pn(m.group(1))
        m = re.search(r"Total incl\.\s*TVA\s*([\d\s.,]+)\s*EUR", text)
        if m:
            inv.incl = _pn(m.group(1))

    # Detect format type
    has_structured_items = False
    for text in all_text:
        if re.search(r"Prestations|Suppl[eé]ment", text):
            has_structured_items = True
            break

    if not has_structured_items:
        return inv  # Empty invoice

    # Try structured parsing using text lines
    current_emp = None
    emp_section = False

    for text in all_text:
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for employee names (all caps, or proper names)
            # Tempoteam format: employee name followed by detail lines
            if _looks_like_emp_name(line):
                # Check if next line or data suggests new employee section
                current_emp = EmpDetail(name=line)
                inv.add(current_emp)
                emp_section = True
                continue

            if current_emp and emp_section:
                # Check for period row
                if re.match(r"\d{2}/\d{2}/\d{4}", line):
                    current_emp.period = line
                    continue

                # Check for Fonction:
                if "Fonction:" in line:
                    m2 = re.search(r"Fonction:\s*(.+)", line)
                    if m2:
                        current_emp.role = m2.group(1).strip()
                    continue

                # Check for item line: possibly ITEM_NAME qty rate amt
                for iname in ITEM_NAMES:
                    if iname in line:
                        # Extract numbers from the line
                        nums = re.findall(r"[\d.,]+", line.replace(iname, ""))
                        if len(nums) >= 2:
                            try:
                                qty = _pn(nums[0])
                                amt = _pn(nums[-1])
                                rate = _pn(nums[1]) if len(nums) >= 3 else 0
                                pct = _pn(nums[2]) if len(nums) >= 4 else 0
                                if pct > 100:
                                    pct = 0
                                if qty > 0:
                                    item = InvItem(name=iname, qty=qty, rate=rate, pct=pct, amt=amt)
                                    current_emp.add(item)
                            except:
                                pass
                        break

                # Check for Sous-total line
                if "Sous-total" in line:
                    m2 = re.search(r"([\d.,]+)\s*$", line)
                    if m2:
                        try:
                            current_emp.subtotal = _pn(m2.group(1))
                        except:
                            pass

                # Check for Total des Prestations line (end of employee section)
                if line.startswith("Total des") or "Sous-total Transfert" in line:
                    emp_section = False

    # Clean up: remove employees with no items
    inv.emps = [e for e in inv.emps if e.items]
    return inv


def _looks_like_emp_name(text):
    """Check if text looks like an employee name."""
    if not text:
        return False
    if text in ITEM_NAMES or text in ["Transfert"]:
        return False
    if "Sous-total" in text:
        return False
    if re.search(r"\d+,\d{2}", text):
        return False
    if re.search(r"Total des|Voir d\u00e9tails|Les conditions|Payable comptant", text):
        return False
    if "Fonction:" in text:
        return False
    # Exclude company registration info
    exclude_pats = ["RPM", "Bruxelles", "Agrement", "BUOSAP", "ONVA", "ONSS",
        "Caisse de vacances", "n\u00b0", "VG ", "W.INT", "B.00260",
        "Moniteur", "Belge", "SEPP:", "TVA:", "Tempo-Team", "Boechoutlaan", "Strombeek"]
    for pat in exclude_pats:
        if pat.lower() in text.lower():
            return False
    # Must have enough alphabetic chars
    letters = sum(1 for c in text if c.isalpha() or c in " '-")
    return len(text) >= 4 and letters >= len(text) * 0.4
