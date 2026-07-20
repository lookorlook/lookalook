import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import os

# Test main reconciliation without yaml dependency
sys.path.insert(0, r"C:\Users\zt26501\Documents\Codex\2026-07-17\pdf-pdf-pdf-pdf\project\app")

# Import parsers directly
from parsers.attendance_parser import parse_attendance
from parsers.invoice_parser import parse_invoices

INPUTS = r"C:\Users\zt26501\Documents\Codex\2026-07-17\pdf-pdf-pdf-pdf\inputs"

def test():
    p1 = os.path.join(INPUTS, "period1")
    att = parse_attendance(os.path.join(p1, "0615-0621.xlsx"))
    invs = parse_invoices([os.path.join(p1, f) for f in ["61027976.pdf", "61027977.pdf"]])
    
    print(f"\nAttendance: {len(att.get_employees())} employees, {att.get_total_hours():.2f}h")
    for inv in invs.values():
        print(f"Invoice {inv.num}: {inv.total_hours():.2f}h, {len(inv.emps)} employees")
    
    from reconciliation import reconcile
    report = reconcile(att, list(invs.values()))
    print(report.get_summary())

test()
