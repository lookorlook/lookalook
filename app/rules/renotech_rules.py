\"\"\"RENOTECH (Denmark) specific reconciliation rules.\"\"\"

def apply_renotech_rules(attendance_sheet, invoice_emps_dict):
    \"\"\"Apply Renotech rules with night shift calculation.\"\"\"
    results = []
    for can_name, inv_data in invoice_emps_dict.items():
        att_name = inv_data["_att_name"]
        att_records = attendance_sheet.get_records_by_employee(att_name)
        att_hours = sum(r.hours for r in att_records if r.status == "present")
        att_night = sum(r.night_hours for r in att_records if r.status == "present")
        inv_hours = inv_data.get("hours", 0)
        inv_items = inv_data.get("items", [])
        diff = inv_hours - att_hours

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
            "items_breakdown": ["%s: %.2fh x %.2f = %.2f" % (i.name, i.qty, i.rate, i.amt) for i in inv_items],
            "supplement_check": None, "dimona_check": None,
            "unmatched": inv_data.get("_unmatched", False),
        })
    return results
