"""PVG Worksupply reconciliation - per-employee comparison."""
from reconciliation import _score_name

AUTO_MATCH = 0.35

def apply_worksupply_rules(attendance_sheet, invoice_emps_dict, supplier=None):
    results = []
    
    total_att_hours = attendance_sheet.get_total_hours()
    total_inv_hours = sum(inv_data.get("hours", 0) for inv_data in invoice_emps_dict.values())
    total_inv_amount = sum(inv_data.get("amount", 0) for inv_data in invoice_emps_dict.values())
    
    # Per-employee matching
    att_names = set(attendance_sheet.get_employees())
    inv_names_used = set()
    
    # Build match pairs
    pairs = []
    for att_name in att_names:
        for inv_name, inv_data in invoice_emps_dict.items():
            s = _score_name(att_name, inv_name)
            if s >= AUTO_MATCH:
                pairs.append((s, att_name, inv_name))
    pairs.sort(key=lambda x: -x[0])
    
    att_to_inv = {}
    for s, att_n, inv_n in pairs:
        if att_n in att_to_inv or inv_n in inv_names_used:
            continue
        att_to_inv[att_n] = inv_n
        inv_names_used.add(inv_n)
    
    # Build matching results
    for emp_name in sorted(att_names):
        emp_hours = attendance_sheet.get_hours_by_employee(emp_name)
        emp_night = attendance_sheet.get_night_hours_by_employee(emp_name)
        emp_days = attendance_sheet.get_attendance_days(emp_name)
        emp_subsidy = attendance_sheet.get_subsidy_hours_by_employee(emp_name)
        
        matched_inv = att_to_inv.get(emp_name)
        if matched_inv:
            inv_data = invoice_emps_dict[matched_inv]
            inv_h = inv_data["hours"]
            inv_amt = inv_data["amount"]
            inv_items = inv_data.get("items", [])
            # Extract subsidy and night hours from invoice items
            inv_subsidy = 0.0
            inv_night = 0.0
            for it in inv_items:
                if 'Subsidy' in it.name or 'subsidy' in it.name.lower():
                    inv_subsidy += it.qty
                if 'Night' in it.name or 'night' in it.name.lower():
                    inv_night += it.qty
            diff_h = inv_h - emp_hours
            diff_pct = round(abs(diff_h) / max(emp_hours, 0.01) * 100, 1) if emp_hours > 0 else 100.0
            if abs(diff_h) <= 0.5:
                v = "auto_approved"
            elif emp_hours > 0 and abs(diff_h) / emp_hours * 100 < 1.0:
                v = "match"
            elif emp_hours > 0 and abs(diff_h) / emp_hours * 100 < 5.0:
                v = "minor_diff"
            else:
                v = "mismatch"
            results.append({
                "name": emp_name, "att_name": emp_name,
                "att_hours": round(emp_hours, 2), "att_days": emp_days,
                "att_night_hours": round(emp_night, 2),
                "inv_night_hours": round(inv_night, 2),
                "att_subsidy_hours": round(emp_subsidy, 2),
                "inv_subsidy_hours": round(inv_subsidy, 2),
                "inv_hours": round(inv_h, 2), "inv_amount": round(inv_amt, 2),
                "diff_hours": round(diff_h, 2), "diff_percent": diff_pct,
                "verdict": v,
                "overtime_hours": 0.0,
                "items_breakdown": ["%s: %.2fh" % (i.name, i.qty) for i in inv_items],
                "supplement_check": {"status": "ok", "att_hours": round(emp_subsidy, 2), "inv_hours": round(inv_subsidy, 2)},
                "dimona_check": None,
                "unmatched": False,
            })
        else:
            results.append({
                "name": emp_name, "att_name": emp_name,
                "att_hours": round(emp_hours, 2), "att_days": emp_days,
                "att_night_hours": round(emp_night, 2),
                "att_subsidy_hours": round(emp_subsidy, 2),
                "inv_hours": 0, "inv_amount": 0,
                "diff_hours": 0, "diff_percent": 0,
                "verdict": "info",
                "overtime_hours": 0.0,
                "items_breakdown": [],
                "supplement_check": None, "dimona_check": None,
                "unmatched": True,
            })
    
    # Unmatched invoice employees
    used_inv_names = set(att_to_inv.values())
    for inv_name, inv_data in invoice_emps_dict.items():
        if inv_name not in used_inv_names:
            results.append({
                "name": inv_name, "att_name": inv_name,
                "att_hours": 0, "att_days": 0,
                "att_night_hours": 0, "att_subsidy_hours": 0,
                "inv_hours": round(inv_data["hours"], 2),
                "inv_amount": round(inv_data["amount"], 2),
                "diff_hours": 0, "diff_percent": 0,
                "verdict": "info",
                "overtime_hours": 0.0,
                "items_breakdown": ["%s: %.2fh" % (i.name, i.qty) for i in inv_data.get("items", [])],
                "supplement_check": None, "dimona_check": None,
                "unmatched": True,
            })
    
    return results
