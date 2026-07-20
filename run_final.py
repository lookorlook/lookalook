import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\zt26501\Documents\Codex\2026-07-17\pdf-pdf-pdf-pdf\project\app")
from parsers.attendance_parser import parse_attendance
from parsers.invoice_parser import parse_invoices
from reconciliation import reconcile

INPUTS = r"C:\Users\zt26501\Documents\Codex\2026-07-17\pdf-pdf-pdf-pdf\inputs"

for label, att_f, invs in [
    ("Period 1", "period1/0615-0621.xlsx", ["period1/61027976.pdf", "period1/61027977.pdf"]),
    ("Period 2", "period2/0622-0628.xlsx", ["period2/61029249.pdf", "period2/61029250.pdf"]),
]:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    
    att = parse_attendance(os.path.join(INPUTS, att_f))
    invs_dict = parse_invoices([os.path.join(INPUTS, p) for p in invs])
    
    print(f"  Attendance: {att.get_total_hours():.2f}h ({len(att.get_employees())} emps)")
    for inv in invs_dict.values():
        print(f"  Invoice {inv.num}: {inv.total_hours():.2f}h ({len(inv.emps)} emps)")
    
    report = reconcile(att, list(invs_dict.values()))
    print(report.get_summary())
