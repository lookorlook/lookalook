"""PVG Worksupply Attendance Parser.
Format similar to Pacework but with different column layout.
  Row 2: "Team Leader" header
  Row 3-4: Team Leaders (Stefin Saji, Jaspreet Singh)
  Row 5+: Regular employees (with possible header rows in between)
  Columns: A=name, B-D=Mon(Time,Hours,Total), E-G=Tue, H-J=Wed, K-M=Thu, N-P=Fri, Q-S=Sat, T-V=Sun
"""
import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import openpyxl

from parsers.pvg_attendance_parser import AttendanceRecord, AttendanceSheet, parse_time_to_hours, calc_subsidy_hours

def calc_night_hours_ws(time_str, date_str=None):
    """Calculate night shift hours (19:00-06:00) for Worksupply.
    Only counts night hours on weekdays (Mon-Fri)."""
    if not time_str or not isinstance(time_str, str):
        return 0.0
    if date_str:
        try:
            parts = date_str.split("-")
            d = __import__("datetime").date(int(parts[0]), int(parts[1]), int(parts[2]))
            if d.weekday() >= 5:
                return 0.0
        except:
            pass
    m = re.match(r"(\d+)[:;](\d+)\s*-(\d+)[:;](\d+)", time_str.strip())
    if not m:
        return 0.0
    start_h = int(m.group(1)) + int(m.group(2)) / 60
    end_h = int(m.group(3)) + int(m.group(4)) / 60
    if end_h < start_h:
        end_h += 24
    NIGHT_START = 19
    NIGHT_END = 30  # 06:00 next day
    overlap_start = max(start_h, NIGHT_START)
    overlap_end = min(end_h, NIGHT_END)
    return round(max(0, overlap_end - overlap_start), 2)

DAY_COLS_WS = [
    (2, 3, 4),   # Monday: B, C, D
    (5, 6, 7),   # Tuesday: E, F, G
    (8, 9, 10),  # Wednesday: H, I, J
    (11, 12, 13),# Thursday: K, L, M
    (14, 15, 16),# Friday: N, O, P
    (17, 18, 19),# Saturday: Q, S, R
    (20, 21, 22),# Sunday: T, U, V
]

def _is_header_name(name):
    """Check if a cell value is a header/section marker."""
    if not name or not name.strip():
        return True
    n = name.strip().lower()
    return n in ("", "work supply", "employee name", "team leader")

def parse_worksupply_attendance(filepath, supplier=None):
    """Parse Worksupply weekly attendance Excel.
    Handles both formats:
      - With separator rows (week 27): rows 3-4 TL, rows 5-7 separator/headers, rows 8+ employees
      - Without separator (week 21): rows 3-4 TL, rows 5+ employees (no blank rows between)
    """
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb.active

    sheet = AttendanceSheet(period_start="", period_end="")

    # Extract dates from header row 1
    day_dates = []
    for c in [2, 5, 8, 11, 14, 17, 20]:
        hdr = str(ws.cell(1, c).value or "")
        m = re.search(r"(\d+)\.(\d+)\.(\d+)", hdr)
        if m:
            d, mon, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000
            if y < 2026:
                y = 2026
            day_dates.append(f"{y}-{mon:02d}-{d:02d}")
        else:
            day_dates.append("")

    # Team Leaders are consistently at rows 3-4 in all known files
    TL_ROWS = {3, 4}

    for r in range(3, ws.max_row + 1):
        name = ws.cell(r, 1).value
        if not name or not str(name).strip():
            continue
        name = str(name).strip()
        if _is_header_name(name):
            continue

        is_leader = (r in TL_ROWS)

        for day_idx in range(7):
            time_col, hours_col, total_col = DAY_COLS_WS[day_idx]
            date_str = day_dates[day_idx] if day_idx < len(day_dates) else ""
            if not date_str:
                continue

            time_val = ws.cell(r, time_col).value
            time_str = str(time_val or "").strip() if time_val else ""

            # Skip OFF/SICK days
            time_upper = time_str.upper()
            if time_upper in ("OFF", "SICK", "") or time_upper.startswith("OFF") or time_upper.startswith("SICK"):
                continue

            total_val = ws.cell(r, total_col).value
            hours = parse_time_to_hours(total_val) if total_val else 0.0

            if hours > 0:
                night_h = calc_night_hours_ws(time_str, date_str)
                sheet.add_record(AttendanceRecord(
                    employee_name=name,
                    date=date_str,
                    hours=hours,
                    night_hours=night_h,
                    status="present",
                    raw_time_slot=time_str,
                    role="Team Leader" if is_leader else ""
                ))

    calc_subsidy_hours(sheet)
    return sheet

def parse_attendance(filepath, country="pvg", supplier="WORKSUPPLY", config=None):
    return parse_worksupply_attendance(filepath, supplier)