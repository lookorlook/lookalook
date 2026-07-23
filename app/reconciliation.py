"""Reconciliation Engine with fuzzy name matching and supplier-specific rules."""
import re
from typing import List, Dict, Optional
from pathlib import Path
from difflib import SequenceMatcher

def _clean(s):
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = re.sub(r"\*", "", s)
    s = re.sub(r"[,\-\+]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _normalize(s):
    """Normalize name: remove accents, lowercase."""
    s = s.lower()
    accents = {"\u00e9":"e","\u00e8":"e","\u00ea":"e","\u00e0":"a","\u00e2":"a",
               "\u00ee":"i","\u00ef":"i","\u00f4":"o","\u00f9":"u","\u00fc":"u","\u00e7":"c"}
    for a, b in accents.items():
        s = s.replace(a, b)
    return s

def _score_name(att_name, inv_name):
    """Hybrid name similarity: word overlap + character-level matching."""
    ca = _clean(_normalize(att_name))
    ci = _clean(_normalize(inv_name))
    if ca == ci: return 1.0
    wa = set(ca.split())
    wi = set(ci.split())
    word_overlap = len(wa & wi) / max(len(wa | wi), 1) if wa and wi else 0
    char_scores = []
    for aw in wa:
        best = max(SequenceMatcher(None, aw, iw).ratio() for iw in wi) if wi else 0
        char_scores.append(best)
    avg_char = sum(char_scores) / max(len(char_scores), 1) if char_scores else 0
    return max(word_overlap, avg_char * 0.8)

AUTO_MATCH_THRESHOLD = 0.35

class ReconReport:
    def __init__(self, period="", supplier="TEMPOTEAM"):
        self.period = period
        self.supplier = supplier
        self.results = []
        self.invoices = []
        self.attendance_file = ""
        self.unmatched_attendance = []
        self.unmatched_invoice = []

    def add_result(self, r): self.results.append(r)

    @property
    def total_attendance_hours(self):
        return sum(r["att_hours"] for r in self.results)

    @property
    def total_invoice_hours(self):
        return sum(r["inv_hours"] for r in self.results)

    @property
    def total_invoice_amount(self):
        return sum(r["inv_amount"] for r in self.results)

    def get_mismatches(self):
        return [r for r in self.results if r["verdict"] in ("minor_diff", "mismatch", "manual_review")]


def reconcile(attendance_sheet, invoices, supplier="TEMPOTEAM"):
    """Reconcile attendance vs invoices with supplier-specific rules."""
    period_label = "%s~%s" % (attendance_sheet.period_start, attendance_sheet.period_end)
    report = ReconReport(period=period_label)

    # Build attendance name set
    att_name_set = set()
    for rec in attendance_sheet.records:
        if rec.status == "present":
            att_name_set.add(rec.employee_name.strip())

    # Build invoice employee data
    invoice_raw_emps = {}
    for inv in invoices:
        for emp in inv.emps:
            name = emp.name.strip()
            if name not in invoice_raw_emps:
                invoice_raw_emps[name] = {"hours": 0, "amount": 0, "items": []}
            invoice_raw_emps[name]["hours"] += emp.hours()
            invoice_raw_emps[name]["amount"] += emp.subtotal or sum(i.amt for i in emp.items)
            invoice_raw_emps[name]["items"].extend(emp.items)

    # Score-sorted matching: attendance name -> invoice name
    att_to_inv = {}
    inv_used = set()
    pairs = []
    for att_name in att_name_set:
        for inv_name in invoice_raw_emps:
            s = _score_name(att_name, inv_name)
            if s >= AUTO_MATCH_THRESHOLD:
                pairs.append((s, att_name, inv_name))
    pairs.sort(key=lambda x: -x[0])
    for s, att_name, inv_name in pairs:
        if att_name in att_to_inv:
            continue
        if inv_name in inv_used:
            continue
        att_to_inv[att_name] = inv_name
        inv_used.add(inv_name)
    for att_name in att_name_set:
        if att_name not in att_to_inv:
            att_to_inv[att_name] = None

    # Build invoice_emps_dict with matched attendance names
    invoice_emps_dict = {}
    for inv_name, inv_data in invoice_raw_emps.items():
        matched_att = None
        for att_n, inv_n in att_to_inv.items():
            if inv_n == inv_name:
                matched_att = att_n
                break
        entry = {
            "hours": inv_data["hours"],
            "amount": inv_data["amount"],
            "items": inv_data["items"],
        }
        if matched_att:
            entry["_att_name"] = matched_att
            entry["_unmatched"] = False
        else:
            entry["_att_name"] = inv_name
            entry["_unmatched"] = True
            report.unmatched_invoice.append(inv_name)
        invoice_emps_dict[inv_name] = entry

    # Apply supplier-specific rules
    if supplier.upper() == "RENOTECH":
        from rules.renotech_rules import apply_renotech_rules
        raw_results = apply_renotech_rules(attendance_sheet, invoice_emps_dict)
    elif supplier.upper() in ("ALLIANCE", "RANDSTAD"):
        from rules.spain_rules import apply_spain_rules
        raw_results = apply_spain_rules(attendance_sheet, invoice_emps_dict, supplier=supplier)
    elif supplier.upper() == "PACEWORK":
        from rules.pvg_rules import apply_pvg_rules
        raw_results = apply_pvg_rules(attendance_sheet, invoice_emps_dict, supplier=supplier)
    elif supplier.upper() == "WORKSUPPLY":
        from rules.worksupply_rules import apply_worksupply_rules
        raw_results = apply_worksupply_rules(attendance_sheet, invoice_emps_dict, supplier=supplier)
    else:
        from rules.tempoteam_rules import apply_tempoteam_rules
        raw_results = apply_tempoteam_rules(attendance_sheet, invoice_emps_dict)

    # Build result lookup by attendance name
    result_by_att = {}
    for r in raw_results:
        result_by_att[r["att_name"]] = r

    # Pass 1: Merge attendance names that point to the SAME invoice person
    att_list = sorted(att_name_set)
    for n1 in att_list:
        inv1 = att_to_inv.get(n1)
        if inv1 is None or n1 not in result_by_att:
            continue
        for n2 in att_list:
            if n2 == n1 or n2 not in result_by_att:
                continue
            if att_to_inv.get(n2) != inv1:
                continue
            s = _score_name(n1, n2)
            if s >= 0.7:
                # Merge n2 into n1
                r1, r2 = result_by_att[n1], result_by_att[n2]
                r1["att_hours"] += r2["att_hours"]
                r1["att_days"] += r2.get("att_days", 0)
                r1["att_night_hours"] = round(r1.get("att_night_hours", 0) + r2.get("att_night_hours", 0), 2)
                r1["diff_hours"] = round(r1["inv_hours"] - r1["att_hours"], 2)
                r1["diff_percent"] = round(abs(r1["diff_hours"]) / max(r1["att_hours"], 0.01) * 100, 1)
                if abs(r1["diff_hours"]) <= 0.5:
                    r1["verdict"] = "auto_approved"
                elif r1["att_hours"] > 0 and abs(r1["diff_hours"]) / r1["att_hours"] * 100 < 1.0:
                    r1["verdict"] = "match"
                elif r1["att_hours"] > 0 and abs(r1["diff_hours"]) / r1["att_hours"] * 100 < 5.0:
                    r1["verdict"] = "minor_diff"
                else:
                    r1["verdict"] = "mismatch"
                result_by_att.pop(n2, None)

    # Add unmatched attendance names
    for att_name in sorted(att_name_set):
        if att_to_inv.get(att_name) is not None:
            continue
        if att_name not in result_by_att:
            att_h = attendance_sheet.get_hours_by_employee(att_name)
            raw_results.append({
                "name": att_name, "att_name": att_name,
                "att_hours": att_h, "att_days": 0,
                "inv_hours": 0, "inv_amount": 0,
                "diff_hours": -att_h, "diff_percent": 100.0,
                "verdict": "manual_review",
                "items_breakdown": [],
                "supplement_check": None, "dimona_check": None,
                "unmatched": True,
            })
            report.unmatched_attendance.append(att_name)

    # Pass 2: Merge unmatched attendance names into similar matched ones
    i = 0
    while i < len(raw_results):
        r = raw_results[i]
        if r.get("unmatched") and r["att_hours"] > 0 and r["inv_hours"] == 0:
            att_name = r.get("att_name", "")
            merged = False
            for j, other in enumerate(raw_results):
                if other.get("unmatched"):
                    continue
                s = _score_name(att_name, other.get("att_name", ""))
                if s >= 0.7:
                    other["att_hours"] += r["att_hours"]
                    other["att_days"] += r.get("att_days", 0)
                    other["att_night_hours"] = round(other.get("att_night_hours", 0) + r.get("att_night_hours", 0), 2)
                    other["diff_hours"] = round(other["inv_hours"] - other["att_hours"], 2)
                    other["diff_percent"] = round(abs(other["diff_hours"]) / max(other["att_hours"], 0.01) * 100, 1)
                    if abs(other["diff_hours"]) <= 0.5:
                        other["verdict"] = "auto_approved"
                    elif other["att_hours"] > 0 and abs(other["diff_hours"]) / other["att_hours"] * 100 < 1.0:
                        other["verdict"] = "match"
                    elif other["att_hours"] > 0 and abs(other["diff_hours"]) / other["att_hours"] * 100 < 5.0:
                        other["verdict"] = "minor_diff"
                    else:
                        other["verdict"] = "mismatch"
                    if att_name in report.unmatched_attendance:
                        report.unmatched_attendance.remove(att_name)
                    raw_results.pop(i)
                    merged = True
                    break
            if not merged:
                i += 1
        else:
            i += 1

    for r in raw_results:
        report.add_result(r)
    return report

def run_reconciliation(attendance_path, invoice_paths):
    from parsers.attendance_parser import parse_attendance
    from parsers.invoice_parser import parse_invoices
    attendance = parse_attendance(attendance_path)
    invoices_dict = parse_invoices(invoice_paths)
    invoices = list(invoices_dict.values())
    report = reconcile(attendance, invoices, supplier="TEMPOTEAM")
    report.attendance_file = Path(attendance_path).name
    for inv_path in invoice_paths:
        report.invoices.append({"file": Path(inv_path).name})
    return report
