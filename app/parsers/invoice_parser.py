import sys, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import pdfplumber

class InvItem:
    def __init__(self, name="", qty=0, rate=0, pct=0, amt=0, vat="A"):
        self.name = name; self.qty = qty; self.rate = rate
        self.pct = pct; self.amt = amt; self.vat = vat
    def __repr__(self): return "{}({}x{}={})".format(self.name, self.qty, self.rate, self.amt)

class EmpDetail:
    def __init__(self, name="", period="", role=""):
        self.name = name; self.period = period; self.role = role
        self.items = []; self.subtotal = 0.0
    def add(self, item): self.items.append(item)
    def hours(self):
        pn = ["Prestations", "Hrs supplém. payées immédiatement", "Heures supplémentaires à récupérer"]
        return sum(i.qty for i in self.items if i.name in pn)

class Invoice:
    def __init__(self):
        self.num = ""; self.date = ""; self.p_start = ""; self.p_end = ""
        self.excl = 0.0; self.incl = 0.0; self.type = ""
        self.emps = []
    def add(self, e): self.emps.append(e)
    def total_hours(self): return sum(e.hours() for e in self.emps)

FOOTER_PREFIX_PAT = re.compile(r"^(?:3|10|14|0|\.2|V|2)(?=[A-Z\d/])")

def _pn(s):
    if not s: return 0.0
    s = s.strip().replace(" ", "")
    if not s: return 0.0
    s = re.sub(r"[^\d,.\-]+$", "", s)
    if not s: return 0.0
    if "," in s:
        s = s.replace(".", "")
        s = s.replace(",", ".")
    else:
        s = s.replace(".", "")
    try: return float(s)
    except: return 0.0

ITEM_NAMES = [
    "Prestations", "Supplément équipe", "Hrs supplém. payées immédiatement",
    "Supplément hrs supp.", "Supplément weekend/jour férié",
    "Heures supplémentaires à récupérer",
    "Prime de pension", "Frais domicile-travail", "Chèques repas",
    "Eco-chèques", "Dimona", "Surcharge frais admin. étudiant",
    "Frais de gestion étudiant",
]

FOOTER_FRAGMENTS = {"3", "2", "0", "1", "4", "V", ".", ":", "", " ", "10", "14"}

def _strip_footer_prefix(n):
    if not n: return n
    n = FOOTER_PREFIX_PAT.sub("", n)
    return n.strip()

def _clean_n(n):
    if not n: return ""
    n = _strip_footer_prefix(n)
    n = n.strip()
    if n in ["fourche", "à", "élévateur"]: return ""
    if "Fonction:" in n:
        parts = n.split("Fonction:", 1)
        n = parts[0].strip()
    n = re.sub(r"\s*-\s*Fonction.*", "", n)
    return n.strip()

def parse_page(page):
    raw = {}
    for c in page.chars:
        rk = round(c["top"] / 7) * 7
        raw.setdefault(rk, []).append((c["x0"], c["text"]))
    cols_list = []
    for top in sorted(raw.keys()):
        items = sorted(raw[top], key=lambda x: x[0])
        cols = {"_top": top}
        for x0, text in items:
            if x0 < 250: cols["n"] = cols.get("n", "") + text
            elif x0 < 380: cols["q"] = cols.get("q", "") + text
            elif x0 < 430: cols["r"] = cols.get("r", "") + text
            elif x0 < 480: cols["p"] = cols.get("p", "") + text
            elif x0 < 530: cols["v"] = cols.get("v", "") + text
            else: cols["a"] = cols.get("a", "") + text
        cols["t"] = "".join(t[1] for t in items)
        t = cols["t"].strip()
        q = cols.get("q", "").strip()
        if t in FOOTER_FRAGMENTS: continue
        if re.match(r"^\d{1,2}$", t) and not q: continue
        if t in (".", ".2", "V") and not q: continue
        cols["_n"] = _clean_n(cols.get("n", ""))
        cols_list.append(cols)
    return cols_list

HEADER_KEYWORDS = ["ANNEXE", "Numéro de facture", "Numéro de client",
    "Tempo-Team sa", "TVA:", "SEPP:", "RPM", "YUNEXPRESS",
    "Sous-total Transfert", "Sous-total Dimona", "Sous-total -",
    "Total des Prestations", "Voir détails", "Les conditions générales",
    "Payable comptant", "Adresse postale", "Adresse de société", "Frais de démarrage",
    "Unit2163", "Unit 2163", "heure/nombre", "Changiweg"]

def _is_emp_name(text):
    if not text: return False
    if text in ITEM_NAMES or text in ["Transfert"]: return False
    if "Sous-total" in text: return False
    if re.search(r"\d+,\d{2}", text): return False
    if re.search(r"\d{2}/\d{2}/\d{4}", text): return False
    if "Fonction:" in text: return False
    # Exclude company registration / legal info lines
    exclude_pats = ["RPM", "Bruxelles", "Agrement", "BUOSAP", "ONVA", "ONSS",
        "Caisse de vacances", "n\u00b0", "VG ", "W.INT", "B.00260",
        "Moniteur", "Belge", "SEPP:", "TVA:", "Tempo-Team", "Boechoutlaan", "Strombeek"]
    for pat in exclude_pats:
        if pat.lower() in text.lower():
            return False
    letters = sum(1 for c in text if c.isalpha() or c in " '-")
    return len(text) >= 4 and letters >= len(text) * 0.5
def _is_item_name(text):
    if not text: return None
    if text.startswith("Total des") or text.startswith("Sous-total"):
        return None
    for iname in ITEM_NAMES:
        if iname in text: return iname
    return None

def _is_period_row(text):
    if not text: return False
    return bool(re.match(r"\d{2}/\d{2}/\d{4}", text.strip()))

def _add_item_no_dup(emp, name, qty, rate, pct, amt, vat):
    for ex in emp.items:
        if ex.name == name and abs(ex.qty - qty) < 0.01 and abs(ex.rate - rate) < 0.01:
            ex.amt += amt
            return
    emp.add(InvItem(name=name, qty=qty, rate=rate, pct=pct, amt=amt, vat=vat))

def _parse_detail(inv, cols_list):
    blocks = []
    data_buffer = []
    orphan_names = {}
    last_emp = None

    for c in cols_list:
        n = c["_n"]; q = c.get("q","").strip(); t = c["t"].strip()
        if any(h in t for h in HEADER_KEYWORDS):
            continue
        if t.startswith("Page") or t.startswith("Bijkantoor") or t.startswith("Siège"):
            continue
        if _is_emp_name(n):
            if last_emp:
                for buf in list(data_buffer):
                    if buf.get("item"):
                        _add_item_no_dup(last_emp, buf["item"], buf["qty"], buf["rate"], buf["pct"], buf["amt"], "A")
                        data_buffer.remove(buf)
            emp = {"name": n, "rows": []}
            blocks.append(emp)
            last_emp = emp
            if _is_item_name(n):
                orphan_names[c["_top"]] = n
        elif last_emp:
            last_emp["rows"].append(c)

    for c in cols_list:
        n = c["_n"]; q = c.get("q","").strip()
        rv = c.get("r","").strip(); p = c.get("p","").strip()
        a_str = c.get("a","").strip()
        im = _is_item_name(n)
        if im and not q:
            orphan_names[c["_top"]] = im
            continue
        if q and last_emp:
            qty = _pn(q); rate = _pn(rv); pct = _pn(p)
            amt_src = (c.get("v","") + " " + a_str).strip()
            amt_src = re.sub(r"[A-Z]", "", amt_src).strip()
            amt = _pn(amt_src) if amt_src else (qty * rate if rate else 0)
            if pct > 100: pct = 0
            if qty > 0 and amt > 0:
                item_name = _is_item_name(n) or ""
                if not item_name:
                    for otop, oname in sorted(orphan_names.items(), reverse=True):
                        if abs(c["_top"] - otop) < 25: item_name = oname; break
                if item_name:
                    _add_item_no_dup(last_emp, item_name, qty, rate, pct, amt, "A")

    data_buffer = []
    for block in blocks:
        emp = EmpDetail(name=block["name"])
        for c in block["rows"]:
            n = c["_n"]; q = c.get("q","").strip(); rv = c.get("r","").strip()
            p = c.get("p","").strip(); a_str = c.get("a","").strip(); t = c["t"].strip()
            if _is_period_row(t) or _is_period_row(n):
                emp.period = n if _is_period_row(n) else t; continue
            rm = re.search(r"Fonction:(.+)", n or t)
            if rm: emp.role = rm.group(1).strip(); continue
            if "Sous-total" in (n or t):
                m = re.search(r"([\d\s.,]+)$", t)
                if m:
                    try: emp.subtotal = _pn(m.group(1))
                    except: pass
                continue
            im = _is_item_name(n)
            if im and not q:
                for buf in reversed(data_buffer):
                    if abs(c["_top"] - buf["top"]) < 30 and buf["item"] is None:
                        buf["item"] = im; break
                continue
            if q:
                qty = _pn(q); rate = _pn(rv); pct = _pn(p)
                amt_src = (c.get("v","") + " " + a_str).strip()
                amt_src = re.sub(r"[A-Z]", "", amt_src).strip()
                amt = _pn(amt_src) if amt_src else (qty * rate if rate else 0)
                if pct > 100: pct = 0
                if qty > 0 and amt > 0:
                    item_name = _is_item_name(n) or ""
                    if not item_name:
                        for buf in reversed(data_buffer):
                            if abs(c["_top"] - buf["top"]) < 25 and buf.get("item"):
                                item_name = buf["item"]; break
                    if item_name:
                        _add_item_no_dup(emp, item_name, qty, rate, pct, amt, "A")
                    else:
                        data_buffer.append({"top": c["_top"], "qty": qty, "rate": rate, "pct": pct, "amt": amt, "item": None})
        for buf in list(data_buffer):
            if buf.get("item"):
                _add_item_no_dup(emp, buf["item"], buf["qty"], buf["rate"], buf["pct"], buf["amt"], "A")
                data_buffer.remove(buf)
        if emp.items:
            inv.add(emp)
        elif emp.name:
            inv.add(emp)


def _parse_pdf_chars(path):
    inv = Invoice()
    with pdfplumber.open(path) as pdf:
        # Check if Spain ALLIANCE
        try:
            p0_text = pdf.pages[0].extract_text() or ""
            if re.search(r'ALLIANCE\s+WORK\s+ETT', p0_text, re.IGNORECASE):
                from parsers.spain_invoice_parser import parse_spain_invoice_pdf
                return parse_spain_invoice_pdf(path)
            if re.search(r'Randstad\s+Empleo', p0_text, re.IGNORECASE):
                from parsers.ranstad_invoice_parser import parse_ranstad_invoice_pdf
                return parse_ranstad_invoice_pdf(path)
                from parsers.spain_invoice_parser import parse_spain_invoice_pdf
                return parse_spain_invoice_pdf(path)
        except Exception:
            pass
        
        # Check for PVG/Pacework
        try:
            p0_text = pdf.pages[0].extract_text() or ""
            if 'Pacework B.V.' in p0_text or 'Pacework B' in p0_text:
                from parsers.pvg_invoice_parser import parse_pacework_invoice_pdf
                return parse_pacework_invoice_pdf(path)
        except Exception:
            pass
        
        # Check for PVG/Worksupply
        try:
            p0_text = pdf.pages[0].extract_text() or ""
            if "WORK SUPPLY" in p0_text or "Work Supply" in p0_text:
                from parsers.pvg_worksupply_invoice_parser import parse_worksupply_invoice_pdf
                return parse_worksupply_invoice_pdf(path)
        except Exception:
            pass
        
        # Belgium/Default parser
        all_pages = [parse_page(p) for p in pdf.pages]
    if all_pages:
        p0 = " ".join(c["t"] for c in all_pages[0])
        m = re.search(r"(?:Numéro de facture|de la proposition)\D*(\d+)", p0, re.IGNORECASE)
        if m: inv.num = m.group(1)
        m = re.search(r"(?:Date de facture|Date de la proposition)\s*(\d{2}/\d{2}/\d{4})", p0, re.IGNORECASE)
        if m: inv.date = m.group(1)
        m = re.search(r"Période\s*(\d{2}/\d{2}/\d{4})\s*[-]\s*(\d{2}/\d{2}/\d{4})", p0)
        if m: inv.p_start, inv.p_end = m.group(1), m.group(2)
        if "Transfert" in p0: inv.type = "Transfert"
        m = re.search(r"Total excl\.\s*TVA\s*([\d\s.,]+)\s*EUR", p0)
        if m: inv.excl = _pn(m.group(1))
        m = re.search(r"Total incl\.\s*TVA\s*([\d\s.,]+)\s*EUR", p0)
        if m: inv.incl = _pn(m.group(1))
    for pi, cols_list in enumerate(all_pages):
        if pi == 0: continue
        pt = " ".join(c["t"] for c in cols_list)
        if any(m in pt for m in ["Conditions générales", "Article 1.", "Toute modalité"]): continue
        if not any(re.search(r"\d+,\d{2}", c.get("q","")+c.get("a","")) for c in cols_list): continue
        _parse_detail(inv, cols_list)
    inv.emps = [e for e in inv.emps if e.items]
    i = 0
    while i < len(inv.emps) - 1:
        if inv.emps[i].name.lower().strip() == inv.emps[i+1].name.lower().strip():
            cur, nxt = inv.emps[i], inv.emps[i+1]
            if not cur.period and nxt.period: cur.period = nxt.period
            if not cur.role and nxt.role: cur.role = nxt.role
            for item in nxt.items: _add_item_no_dup(cur, item.name, item.qty, item.rate, item.pct, item.amt, item.vat)
            if nxt.subtotal: cur.subtotal = nxt.subtotal
            inv.emps.pop(i + 1)
            continue
        i += 1
    return inv




def parse_pdf_fallback(path):
    """Try char-based parser first, fall back to text-based parser."""
    from parsers.belgium_text_parser import parse_belgium_text
    try:
        inv = _parse_pdf_chars(path)
        if inv and inv.num and inv.emps:
            return inv
        # Fallback
        inv2 = parse_belgium_text(path)
        if inv2 and inv2.num:
            return inv2
        return inv
    except Exception:
        import traceback; traceback.print_exc()
        try:
            return parse_belgium_text(path)
        except Exception:
            return Invoice()


def parse_invoices(filepaths):
    results = {}
    for fp in filepaths:
        try:
            inv = parse_pdf_fallback(fp)
            if inv.num: results[inv.num] = inv
        except Exception as e:
            import traceback; traceback.print_exc()
    return results
