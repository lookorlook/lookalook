"""PVG (Pacework/Worksupply) reconciliation rules.
Simple total-hours comparison since invoices are aggregated (no per-employee detail).
"""
def calc_night_hours_from_time_slot(time_str):
    """Calculate night shift hours (18:00-06:00) from a time slot."""
    import re
    if not time_str or not isinstance(time_str, str):
        return 0.0
    m = re.match(r"(\d+):(\d+)\s*-\s*(\d+):(\d+)", time_str.strip())
    if not m:
        return 0.0
    start_h = int(m.group(1)) + int(m.group(2)) / 60
    end_h = int(m.group(3)) + int(m.group(4)) / 60
    if end_h < start_h:
        end_h += 24
    NIGHT_START = 18
    NIGHT_END = 30
    overlap_start = max(start_h, NIGHT_START)
    overlap_end = min(end_h, NIGHT_END)
    return round(max(0, overlap_end - overlap_start), 2)

def apply_pvg_rules(attendance_sheet, invoice_emps_dict, supplier=None):
    """PVG reconciliation: compare total attendance hours vs total invoice hours."""
    results = []
    
    total_att_hours = attendance_sheet.get_total_hours()
    total_inv_hours = sum(inv_data.get("hours", 0) for inv_data in invoice_emps_dict.values())
    total_inv_amount = sum(inv_data.get("amount", 0) for inv_data in invoice_emps_dict.values())
    
    # Group by Team Leader vs Regular workers
    team_leader_records = [r for r in attendance_sheet.records if r.role == "Team Leader" and r.status == "present"]
    worker_records = [r for r in attendance_sheet.records if r.role != "Team Leader" and r.status == "present"]
    
    tl_hours = sum(r.hours for r in team_leader_records)
    tl_night = sum(r.night_hours for r in team_leader_records)
    worker_hours = sum(r.hours for r in worker_records)
    worker_night = sum(r.night_hours for r in worker_records)
    
    # Try to find Team Leader and Warehouse invoices
    tl_inv_hours = 0.0
    wh_inv_hours = 0.0
    tl_inv_amount = 0.0
    wh_inv_amount = 0.0
    tl_inv_items = []
    wh_inv_items = []
    
    for inv_name, inv_data in invoice_emps_dict.items():
        items = inv_data.get("items", [])
        h = inv_data.get("hours", 0)
        amt = inv_data.get("amount", 0)
        # Match by invoice employee name
        if "Team Leader" in inv_name or "Leader" in inv_name:
            tl_inv_hours += h
            tl_inv_amount += amt
            tl_inv_items.extend(items)
        elif "Magazijn" in inv_name or "Workers" in inv_name or "Worker" in inv_name or "Warehouse" in inv_name:
            wh_inv_hours += h
            wh_inv_amount += amt
            wh_inv_items.extend(items)
        else:
            # Fallback: use hours threshold
            if h < 50:
                tl_inv_hours += h
                tl_inv_amount += amt
                tl_inv_items.extend(items)
            else:
                wh_inv_hours += h
                wh_inv_amount += amt
                wh_inv_items.extend(items)
    
    # Team Leader result
    tl_diff = tl_inv_hours - tl_hours
    if tl_hours > 0 or tl_inv_hours > 0:
        tl_diff_pct = round(abs(tl_diff) / max(tl_hours, 0.01) * 100, 1) if tl_hours > 0 else 100.0
        if abs(tl_diff) <= 0.5:
            tl_verdict = "auto_approved"
        elif tl_hours > 0 and tl_diff_pct < 1.0:
            tl_verdict = "match"
        elif tl_hours > 0 and tl_diff_pct < 5.0:
            tl_verdict = "minor_diff"
        else:
            tl_verdict = "mismatch"
        
        results.append({
            "name": "Team Leader", "att_name": "Team Leader",
            "att_hours": round(tl_hours, 2),
            "att_days": len(team_leader_records),
            "att_night_hours": round(tl_night, 2),
            "att_subsidy_hours": round(sum(r.subsidy_hours for r in team_leader_records if r.status == "present"), 2),
            "att_subsidy_hours": round(attendance_sheet.get_total_subsidy_hours(), 2) if False else 0,
            "inv_hours": round(tl_inv_hours, 2),
            "inv_amount": round(tl_inv_amount, 2),
            "diff_hours": round(tl_diff, 2),
            "diff_percent": tl_diff_pct,
            "verdict": tl_verdict,
            "overtime_hours": 0.0,
            "items_breakdown": ["%s: %.2fh x %.2f = %.2f" % (i.name, i.qty, i.rate, i.amt) for i in tl_inv_items],
            "supplement_check": None, "dimona_check": None,
            "unmatched": False,
        })
    
    # Warehouse workers result
    wh_diff = wh_inv_hours - worker_hours
    if worker_hours > 0 or wh_inv_hours > 0:
        wh_diff_pct = round(abs(wh_diff) / max(worker_hours, 0.01) * 100, 1) if worker_hours > 0 else 100.0
        if abs(wh_diff) <= 0.5:
            wh_verdict = "auto_approved"
        elif worker_hours > 0 and wh_diff_pct < 1.0:
            wh_verdict = "match"
        elif worker_hours > 0 and wh_diff_pct < 5.0:
            wh_verdict = "minor_diff"
        else:
            wh_verdict = "mismatch"
        
        results.append({
            "name": "Magazijnmedewerkers", "att_name": "Magazijnmedewerkers",
            "att_hours": round(worker_hours, 2),
            "att_days": len(worker_records),
            "att_night_hours": round(worker_night, 2),
            "att_subsidy_hours": round(sum(r.subsidy_hours for r in worker_records if r.status == "present"), 2),
            "inv_hours": round(wh_inv_hours, 2),
            "inv_amount": round(wh_inv_amount, 2),
            "diff_hours": round(wh_diff, 2),
            "diff_percent": wh_diff_pct,
            "verdict": wh_verdict,
            "overtime_hours": 0.0,
            "items_breakdown": ["%s: %.2fh x %.2f = %.2f" % (i.name, i.qty, i.rate, i.amt) for i in wh_inv_items],
            "supplement_check": None, "dimona_check": None,
            "unmatched": False,
        })
    
    # Add individual employee attendance detail entries
    for emp_name in sorted(attendance_sheet.get_employees()):
        emp_hours = attendance_sheet.get_hours_by_employee(emp_name)
        emp_night = attendance_sheet.get_night_hours_by_employee(emp_name)
        emp_days = attendance_sheet.get_attendance_days(emp_name)
        role = ""
        for r in attendance_sheet.get_records_by_employee(emp_name):
            if r.role:
                role = r.role
                break
        results.append({
            "name": emp_name, "att_name": emp_name,
            "att_hours": round(emp_hours, 2),
            "att_days": emp_days,
            "att_night_hours": round(emp_night, 2),
            "att_subsidy_hours": round(attendance_sheet.get_subsidy_hours_by_employee(emp_name), 2),
            "inv_hours": 0, "inv_amount": 0,
            "diff_hours": 0, "diff_percent": 0,
            "verdict": "info",
            "overtime_hours": 0.0,
            "items_breakdown": [],
            "supplement_check": None, "dimona_check": None,
            "unmatched": True,
        })
    
    return results
