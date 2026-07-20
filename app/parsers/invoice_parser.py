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
    # Remove trailing non-numeric chars (EUR codes, etc.)
    s = re.sub(r"[^\d,.\-]+$", "", s)
    if not s: return 0.0
    # European format: comma is decimal separator, dots are thousands separators
    if "," in s:
        s = s.replace(".", "")      # Remove thousands separators
        s = s.replace(",", ".")     # Convert decimal comma to dot
    else:
        s = s.replace(".", "")      # No comma: dots are thousands separators
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
    letters = sum(1 for c in text if c.isalpha() or c in " '-")
    return len(text) >= 4 and letters >= len(text) * 0.5

def _is_item_name(text):
    if not text: return None
    # Exclude section headers that may contain item name substrings
    if text.startswith("Total des") or text.startswith("Sous-total"):
        return None
    for iname in ITEM_NAMES:
        if iname in text: return iname
    return None

def _is_period_row(text):
    return bool(re.search(r"\d{2}/\d{2}/\d{4}\s*-", text or ""))

def _add_item_no_dup(emp, item_name, qty, rate, pct, amt, vat="A"):
    for existing in emp.items:
        if existing.name == item_name and abs(existing.qty - qty) < 0.01 and abs(existing.rate - rate) < 0.01:
            return
    emp.add(InvItem(item_name, qty, rate, pct, amt, vat))

def _repair_split_rows(cols_list):
    """Merge rows where item names and their qty/rate/amt split across
    different y-positions due to long role descriptions overflowing x0 boundaries."""
    for c in cols_list:
        c["_skip"] = False
    for i, c in enumerate(cols_list):
        if c["_skip"]: continue
        n = c.get("_n", "")
        if not n: continue
        # Only repair actual item rows, not subtotals or section labels
        if not _is_item_name(n): continue
        if "Sous-total" in n: continue
        raw_q = c.get("q", "").strip()
        if raw_q and _pn(raw_q) > 0: continue
        for j, cj in enumerate(cols_list):
            if i == j or cj["_skip"]: continue
            if cj.get("_n", ""): continue
            if cj.get("_skip"): continue
            qj = cj.get("q", "").strip()
            if not qj or _pn(qj) == 0: continue
            if abs(cj["_top"] - c["_top"]) > 20: continue
            c["q"] = qj
            for col in ("r", "p", "v", "a"):
                if cj.get(col): c[col] = cj[col]
            cj["_skip"] = True
            c["_repaired"] = True
            break
        if not c.get("_repaired") and raw_q:
            extracted = _pn(raw_q)
            if extracted > 0:
                c["q"] = str(extracted).replace(".", ",")
                c["_repaired"] = True
    return cols_list

def _parse_detail(inv, cols_list):
    """Parse invoice detail rows into employee blocks and populate items."""
    cols_list = _repair_split_rows(cols_list)
    # Annotate columns
    for c in cols_list:
        n = c["_n"]
        t = c["t"].strip()
        c["_is_header"] = any(h in t for h in HEADER_KEYWORDS) or t == ""
        c["_is_emp"] = _is_emp_name(n) and not c["_is_header"]
        c["_is_item"] = bool(_is_item_name(n))
        c["_has_qty"] = bool(c.get("q","").strip()) and not c.get("_skip")

    # Build employee blocks
    blocks = []
    cur_emp = None
    orphan_rows = []

    for i, c in enumerate(cols_list):
        if c.get("_skip"): continue
        n = c["_n"]
        is_emp = c["_is_emp"]
        # Skip footer-contaminated names that have no real data following
        n_raw = c.get("n", "")
        if is_emp and _strip_footer_prefix(n_raw) != n_raw.strip():
            has_follow = False
            for j in range(i + 1, min(i + 6, len(cols_list))):
                rc = cols_list[j]
                rn = rc["_n"]; rt = rc["t"].strip()
                if _is_period_row(rt) or _is_period_row(rn): has_follow = True; break
                if "Fonction:" in (rn or rt): has_follow = True; break
            if not has_follow:
                is_emp = False

        if is_emp and not c["_is_item"]:
            cur_emp = {"type": "emp", "name": n, "rows": []}
            blocks.append(cur_emp)

        if cur_emp is None:
            if c["_has_qty"]:
                orphan_rows.append(c)
            continue

        cur_emp["rows"].append(c)

    # Process orphan rows FIRST (belong to employee from previous page)
    if orphan_rows and inv.emps:
        last_emp = inv.emps[-1]
        orphan_names = {}
        for c in orphan_rows:
            n = c["_n"]; q = c.get("q","").strip(); a_str = c.get("a","").strip()
            # Skip subtotal/section rows that happen to match item names (e.g. "Sous-total Dimona")
            t = c.get("t", "").strip()
            if "Sous-total" in (n or t): continue
            im = _is_item_name(n)
            if im and not q:
                orphan_names[c["_top"]] = im
                continue
            if q:
                qty = _pn(q); rate = _pn(c.get("r","").strip()); pct = _pn(c.get("p","").strip())
                amt_src = (c.get("v","") + " " + a_str).strip()
                amt_src = re.sub(r"[A-Z]", "", amt_src).strip()
                amt = _pn(amt_src) if amt_src else (qty * rate if rate else 0)
                if qty > 0 and amt > 0:
                    item_name = _is_item_name(n) or ""
                    if not item_name:
                        for otop, oname in sorted(orphan_names.items(), reverse=True):
                            if abs(c["_top"] - otop) < 25: item_name = oname; break
                    if item_name:
                        _add_item_no_dup(last_emp, item_name, qty, rate, pct, amt, "A")

    # Process employee blocks
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


def parse_pdf(path):
    inv = Invoice()
    with pdfplumber.open(path) as pdf:
        all_pages = [parse_page(p) for p in pdf.pages]
    if all_pages:
        p0 = " ".join(c["t"] for c in all_pages[0])
        m = re.search(r"Numéro de facture\s*(\d+)", p0)
        if m: inv.num = m.group(1)
        m = re.search(r"Date de facture\s*(\d{2}/\d{2}/\d{4})", p0)
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

    # CLEANUP
    inv.emps = [e for e in inv.emps if e.items]
    # Merge employees with same name (case-insensitive)
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


def parse_invoices(filepaths):
    results = {}
    for fp in filepaths:
        try:
            inv = parse_pdf(fp)
            if inv.num: results[inv.num] = inv
        except Exception as e:
            import traceback; traceback.print_exc()
    return results
