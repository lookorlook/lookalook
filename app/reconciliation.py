"""
Reconciliation Engine with fuzzy name matching and TEMPOTEAM rules.
"""
from typing import List, Dict, Optional
from pathlib import Path
import re

def _clean(s):
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = re.sub(r"\*", "", s)
    s = re.sub(r"[,\-\+]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

from difflib import SequenceMatcher

def _normalize(s):
    """Normalize name: remove accents, lowercase, remove special chars."""
    s = s.lower().replace('\u00e9', 'e').replace('\u00e8', 'e').replace('\u00ea', 'e')
    s = s.replace('\u00e0', 'a').replace('\u00e2', 'a')
    s = s.replace('\u00ee', 'i').replace('\u00ef', 'i')
    s = s.replace('\u00f4', 'o').replace('\u00f9', 'u').replace('\u00fc', 'u')
    s = s.replace('\u00e7', 'c')
    return s

def _score_name(att_name, inv_name):
    """Hybrid name similarity: word overlap + character-level matching."""
    ca = _clean(_normalize(att_name))
    ci = _clean(_normalize(inv_name))
    if ca == ci: return 1.0
    
    # Word overlap score
    wa = set(ca.split())
    wi = set(ci.split())
    word_overlap = len(wa & wi) / max(len(wa | wi), 1) if wa and wi else 0
    
    # Character-level similarity for individual words
    char_scores = []
    for aw in wa:
        best = max(SequenceMatcher(None, aw, iw).ratio() for iw in wi) if wi else 0
        char_scores.append(best)
    avg_char = sum(char_scores) / max(len(char_scores), 1) if char_scores else 0
    
    # Combined score (word overlap matters more)
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
    def total_attendance_hours(self): return sum(r["att_hours"] for r in self.results)
    @property
    def total_invoice_hours(self): return sum(r["inv_hours"] for r in self.results)
    @property
    def total_invoice_amount(self): return sum(r["inv_amount"] for r in self.results)

    def get_mismatches(self):
        return [r for r in self.results if r["verdict"] in ("minor_diff", "mismatch", "manual_review")]

    def get_summary(self):
        lines = []
        lines.append("=" * 65)
        lines.append("  Reconciliation: %s | %s" % (self.supplier, self.period))
        lines.append("=" * 65)
        lines.append("  Attendance   : %s (%.2fh)" % (self.attendance_file, self.total_attendance_hours))
        lines.append("  Invoices     : %d" % len(self.invoices))
        for inv in self.invoices:
            lines.append("    %s" % inv.get("file", ""))
        lines.append("  Employees    : %d" % len(self.results))
        ok = [r for r in self.results if r["verdict"] == "match"]
        auto = [r for r in self.results if r["verdict"] == "auto_approved"]
        minor = [r for r in self.results if r["verdict"] == "minor_diff"]
        bad = [r for r in self.results if r["verdict"] == "mismatch"]
        review = [r for r in self.results if r["verdict"] == "manual_review"]
        lines.append("  Results: %d OK | %d auto(0.5h) | %d minor | %d mismatch | %d review" % (
            len(ok), len(auto), len(minor), len(bad), len(review)))
        if bad:
            lines.append("")
            lines.append("  --- Mismatches ---")
            for r in bad:
                lines.append("    [%s] att=%.2fh inv=%.2fh diff=%+.2fh" % (r["att_name"], r["att_hours"], r["inv_hours"], r["diff_hours"]))
                sc = r.get("supplement_check")
                if sc and sc["status"] != "ok":
                    lines.append("      Supplement: %s" % sc["status"])
                dc = r.get("dimona_check")
                if dc and dc["status"] != "ok":
                    lines.append("      Dimona: %s" % dc["status"])
        if review:
            lines.append("")
            lines.append("  --- Unmatched (manual review) ---")
            for r in review:
                lines.append("    [%s] att=%.2fh (not on invoice)" % (r["att_name"], r["att_hours"]))
        if minor:
            lines.append("")
            lines.append("  --- Minor ---")
            for r in minor:
                lines.append("    %s: %.2fh vs %.2fh" % (r["name"], r["att_hours"], r["inv_hours"]))
        return "\n".join(lines)


def reconcile(attendance_sheet, invoices):
    period_label = "%s~%s" % (attendance_sheet.period_start, attendance_sheet.period_end)
    report = ReconReport(period=period_label)
    att_name_set = set()
    for rec in attendance_sheet.records:
        att_name_set.add(rec.employee_name.strip())

    invoice_raw_emps = {}
    for inv in invoices:
        for emp in inv.emps:
            name = emp.name.strip()
            if name not in invoice_raw_emps:
                invoice_raw_emps[name] = {"hours": 0, "amount": 0, "items": []}
            invoice_raw_emps[name]["hours"] += emp.hours()
            invoice_raw_emps[name]["amount"] += emp.subtotal or sum(i.amt for i in emp.items)
            invoice_raw_emps[name]["items"].extend(emp.items)

    # Score-sorted matching: compute ALL pairs, match highest scores first
    att_to_inv = {}  # att_name -> inv_name
    inv_used = set()  # invoice names already matched
    pairs = []
    for att_name in att_name_set:
        for inv_name in invoice_raw_emps:
            s = _score_name(att_name, inv_name)
            if s >= AUTO_MATCH_THRESHOLD:
                pairs.append((s, att_name, inv_name))
    pairs.sort(key=lambda x: -x[0])  # highest score first
    for s, att_name, inv_name in pairs:
        if att_name in att_to_inv: continue  # already matched
        if inv_name in inv_used: continue  # already claimed
        att_to_inv[att_name] = inv_name
        inv_used.add(inv_name)
    # Unmatched attendance names
    for att_name in att_name_set:
        if att_name not in att_to_inv:
            att_to_inv[att_name] = None

    invoice_emps_dict = {}
    for inv_name, inv_data in invoice_raw_emps.items():
        matched_att = None
        for att_n, inv_n in att_to_inv.items():
            if inv_n == inv_name:
                matched_att = att_n
                break
        if matched_att:
            invoice_emps_dict[inv_name] = {
                "hours": inv_data["hours"], "amount": inv_data["amount"],
                "items": inv_data["items"], "_att_name": matched_att, "_unmatched": False,
            }
        else:
            invoice_emps_dict[inv_name] = {
                "hours": inv_data["hours"], "amount": inv_data["amount"],
                "items": inv_data["items"], "_att_name": inv_name, "_unmatched": True,
            }
            report.unmatched_invoice.append(inv_name)

    from rules.tempoteam_rules import apply_tempoteam_rules
    raw_results = apply_tempoteam_rules(attendance_sheet, invoice_emps_dict)

    for att_name in sorted(att_name_set):
        if att_to_inv.get(att_name) is None:
            already = any(r["att_name"] == att_name and r.get("unmatched") for r in raw_results)
            if not already:
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

    for r in raw_results:
        report.add_result(r)
    return report


def run_reconciliation(attendance_path, invoice_paths):
    from parsers.attendance_parser import parse_attendance
    from parsers.invoice_parser import parse_invoices
    attendance = parse_attendance(attendance_path)
    invoices_dict = parse_invoices(invoice_paths)
    invoices = list(invoices_dict.values())
    report = reconcile(attendance, invoices)
    report.attendance_file = Path(attendance_path).name
    for inv_path in invoice_paths:
        report.invoices.append({"file": Path(inv_path).name})
    return report
