import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

from parsers.attendance_parser import parse_attendance
from parsers.invoice_parser import parse_invoices
from reconciliation import reconcile

INPUTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'inputs')

def test(label, att_file, inv_files):
    print()
    print('=' * 65)
    print('  ' + label)
    print('=' * 65)
    att = parse_attendance(att_file)
    invs = parse_invoices(inv_files)
    print('  Attendance  : %d emps, %.2fh' % (len(att.get_employees()), att.get_total_hours()))
    for num, inv in invs.items():
        print('  Invoice %s : %d emps, %.2fh' % (num, len(inv.emps), inv.total_hours()))
    report = reconcile(att, list(invs.values()))
    print(report.get_summary())

p1 = os.path.join(INPUTS, 'period1')
test('Period 1 (15-21 Jun)', os.path.join(p1, '0615-0621.xlsx'),
     [os.path.join(p1, f) for f in ['61027976.pdf', '61027977.pdf']])

p2 = os.path.join(INPUTS, 'period2')
test('Period 2 (22-28 Jun)', os.path.join(p2, '0622-0628.xlsx'),
     [os.path.join(p2, f) for f in ['61029249.pdf', '61029250.pdf']])
