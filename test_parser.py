# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'D:\\Documents\\New project\\repo_temp')
sys.path.insert(0, 'D:\\Documents\\New project\\repo_temp\\app')
sys.path.insert(0, 'D:\\Documents\\New project\\repo_temp\\app\\parsers')
from renotech_attendance_parser import parse_renotech_attendance
att = parse_renotech_attendance('D:\\Documents\\New project\\repo_temp\\test_data.xlsx')
print('Total employees:', len(att.get_employees()))
print('Total hours:', round(att.get_total_hours(), 2))
print('Total night hours:', round(att.get_total_night_hours(), 2))
for emp in att.get_employees()[:5]:
    h = att.get_hours_by_employee(emp)
    nh = att.get_night_hours_by_employee(emp)
    print(f'  {emp:30s}  {h:>6.2f}h  night:{nh:>5.2f}h')
