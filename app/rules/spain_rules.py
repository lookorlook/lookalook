"""Spain (Alliance / Randstad) reconciliation rules."""
from datetime import date, timedelta

def calc_legal_workdays(year, month):
    """Calculate legal working days (Mon-Fri) in a given month."""
    import calendar
    count = 0
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        d = date(year, month, day)
        if d.weekday() < 5:  # Mon=0, Fri=4
            count += 1
    return count

def calc_overtime_alliance(attendance_sheet, emp_name):
    """
    Calculate overtime for ALLIANCE employees.
    Returns (overtime_hours, type) where type is "monthly", "daily", or None.
    """
    records = attendance_sheet.get_records_by_employee(emp_name)
    records = [r for r in records if r.status == "present"]
    if not records:
        return (0.0, None)
    
    # Get year/month from records
    dates = []
    daily_hours = {}
    for r in records:
        try:
            parts = r.date.split("-")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            dates.append((y, m, d))
            key = f"{y}-{m:02d}-{d:02d}"
            daily_hours[key] = daily_hours.get(key, 0) + r.hours
        except:
            continue
    
    if not dates:
        return (0.0, None)
    
    year, month = dates[0][0], dates[0][1]
    total_hours = sum(r.hours for r in records)
    
    # Type 2: Monthly overtime
    legal_days = calc_legal_workdays(year, month)
    threshold = legal_days * 8
    monthly_ot = total_hours - threshold
    
    if monthly_ot > 0:
        return (round(monthly_ot, 2), "monthly")
    
    # Type 1: Daily overtime (each day over 8h)
    daily_ot = 0.0
    for day_key, day_hrs in daily_hours.items():
        if day_hrs > 8:
            daily_ot += day_hrs - 8
    
    if daily_ot > 0:
        return (round(daily_ot, 2), "daily")
    
    return (0.0, None)

def apply_spain_rules(attendance_sheet, invoice_emps_dict, supplier=None):
    """
    Spain reconciliation rules.
    supplier: "ALLIANCE" or "RANDSTAD" (optional, for overtime logic).
    """
    results = []
    for can_name, inv_data in invoice_emps_dict.items():
        att_name = inv_data["_att_name"]
        att_records = attendance_sheet.get_records_by_employee(att_name)
        att_hours = sum(r.hours for r in att_records if r.status == "present")
        att_night = sum(r.night_hours for r in att_records if r.status == "present")
        inv_hours = inv_data.get("hours", 0)
        inv_items = inv_data.get("items", [])
        diff = inv_hours - att_hours
        
        # Overtime calculation for ALLIANCE
        overtime_hours = 0.0
        overtime_type = None
        if supplier and supplier.upper() == "ALLIANCE":
            overtime_hours, overtime_type = calc_overtime_alliance(attendance_sheet, att_name)

        if abs(diff) <= 0.5:
            verdict = "auto_approved"
        elif att_hours > 0 and abs(diff) / att_hours * 100 < 1.0:
            verdict = "match"
        elif att_hours > 0 and abs(diff) / att_hours * 100 < 5.0:
            verdict = "minor_diff"
        else:
            verdict = "mismatch"

        results.append({
            "name": can_name, "att_name": att_name,
            "att_hours": att_hours, "att_days": len(att_records),
            "att_night_hours": round(att_night, 2),
            "inv_hours": inv_hours, "inv_amount": inv_data.get("amount", 0),
            "diff_hours": round(diff, 2),
            "diff_percent": round(abs(diff) / max(att_hours, 0.01) * 100, 1),
            "verdict": verdict,
            "overtime_hours": round(overtime_hours, 2),
            "overtime_type": overtime_type,
            "items_breakdown": ["%s: %.2fh x %.2f = %.2f" % (i.name, i.qty, i.rate, i.amt) for i in inv_items],
            "supplement_check": None, "dimona_check": None,
            "unmatched": inv_data.get("_unmatched", False),
        })
    return results
