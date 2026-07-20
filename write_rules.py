import os

content = '''\"\"\"
TEMPOTEAM (Belgium) specific reconciliation rules.
\"\"\"
import re

def _get_invoice_item(inv_items, name_keyword):
    for item in inv_items:
        if name_keyword.lower() in item.name.lower():
            return item
    return None

def _count_attendance_days(att_records, name):
    return sum(1 for r in att_records
               if r.employee_name.lower().strip() == name.lower().strip()
               and r.status == \"present\")

def _count_qualifying_supplement_shifts(att_records, name):
    from parsers.attendance_parser import detect_shift_start, parse_french_time_slot
    qualifying_count = 0
    qualifying_hours = 0.0
    total_hours = 0.0
    for r in att_records:
        if r.employee_name.lower().strip() != name.lower().strip():
            continue
        if r.status != \"present\" or not r.raw_time_slot:
            continue
        start_h = detect_shift_start(r.raw_time_slot)
        total_hours += r.hours
        # Shifts starting at 6h (e.g. 6h-14h26) or 14h (e.g. 14h-22h06) qualify
        if start_h in (6, 14):
            qualifying_count += 1
            qualifying_hours += r.hours
    return qualifying_count, qualifying_hours, total_hours


def apply_tempoteam_rules(attendance_sheet, invoice_emps_dict):
    \"\"\"
    Apply TEMPOTEAM rules to generate per-employee validation results.
    Returns list of dicts.
    \"\"\"
    results = []
    for can_name, inv_data in invoice_emps_dict.items():
        att_name = inv_data[\"_att_name\"]
        att_records = attendance_sheet.get_records_by_employee(att_name)
        att_hours = sum(r.hours for r in att_records if r.status == \"present\")
        att_days = _count_attendance_days(attendance_sheet.records, att_name)
        inv_hours = inv_data.get(\"hours\", 0)
        inv_items = inv_data.get(\"items\", [])
        diff = inv_hours - att_hours

        # --- Supplement check ---
        supp_check = None
        supp_equipe_item = _get_invoice_item(inv_items, \"Supplement\") or _get_invoice_item(inv_items, \"Suppl\\u00e9ment\")
        qty_count, qty_hours, total_hours = _count_qualifying_supplement_shifts(
            attendance_sheet.records, att_name)
        
        if supp_equipe_item:
            if qty_count > 0:
                rate = supp_equipe_item.rate or 0
                expected_amt = round(qty_hours * rate * 7.5 / 100, 2) if rate else 0
                supp_check = {
                    \"status\": \"ok\" if abs(expected_amt - supp_equipe_item.amt) <= 0.05 else \"amount_mismatch\",
                    \"inv_qty\": supp_equipe_item.qty, \"inv_amt\": supp_equipe_item.amt,
                    \"inv_rate\": rate, \"qualifying_shifts\": qty_count,
                    \"qualifying_hours\": qty_hours, \"expected_amt\": expected_amt,
                }
            else:
                supp_check = {
                    \"status\": \"unexpected\", \"inv_qty\": supp_equipe_item.qty,
                    \"inv_amt\": supp_equipe_item.amt, \"qualifying_shifts\": 0, \"qualifying_hours\": 0,
                }
        elif qty_count > 0:
            supp_check = {\"status\": \"missing\", \"qualifying_shifts\": qty_count, \"qualifying_hours\": qty_hours}

        # --- Dimona check ---
        dimona_check = None
        dimona_item = _get_invoice_item(inv_items, \"Dimona\")
        if dimona_item:
            expected_dimona_qty = sum(i.qty for i in inv_items
                                       if i.name in [\"Prestations\", \"Hrs suppl\\u00e9m. pay\\u00e9es imm\\u00e9diatement\"])
            dimona_check = {
                \"status\": \"ok\" if abs(dimona_item.qty - expected_dimona_qty) <= 0.5 else \"qty_mismatch\",
                \"inv_qty\": dimona_item.qty, \"inv_rate\": dimona_item.rate,
                \"inv_amt\": dimona_item.amt, \"att_days\": att_days,
                \"expected_qty\": expected_dimona_qty,
            }

        # --- Verdict ---
        if abs(diff) <= 0.5:
            verdict = \"auto_approved\"
        elif att_hours > 0 and abs(diff) / att_hours * 100 < 1.0:
            verdict = \"match\"
        elif att_hours > 0 and abs(diff) / att_hours * 100 < 5.0:
            verdict = \"minor_diff\"
        else:
            verdict = \"mismatch\"

        results.append({
            \"name\": can_name, \"att_name\": att_name,
            \"att_hours\": att_hours, \"att_days\": att_days,
            \"inv_hours\": inv_hours, \"inv_amount\": inv_data.get(\"amount\", 0),
            \"diff_hours\": round(diff, 2), \"diff_percent\": round(abs(diff) / max(att_hours, 0.01) * 100, 1),
            \"verdict\": verdict,
            \"items_breakdown\": [\"%s: %.2fh x %.2f = %.2f\" % (i.name, i.qty, i.rate, i.amt) for i in inv_items],
            \"supplement_check\": supp_check, \"dimona_check\": dimona_check,
            \"unmatched\": inv_data.get(\"_unmatched\", False),
        })

    # Handle attendance-only employees (not matched to invoice)
    for r in attendance_sheet.records:
        n = r.employee_name.strip()
        found = False
        for inv_data in invoice_emps_dict.values():
            if inv_data[\"_att_name\"].lower() == n.lower():
                found = True
                break
        if not found:
            att_h = attendance_sheet.get_hours_by_employee(n)
            results.append({
                \"name\": n, \"att_name\": n, \"att_hours\": att_h,
                \"att_days\": _count_attendance_days(attendance_sheet.records, n),
                \"inv_hours\": 0, \"inv_amount\": 0, \"diff_hours\": -att_h,
                \"diff_percent\": 100.0, \"verdict\": \"manual_review\",
                \"items_breakdown\": [],
                \"supplement_check\": None, \"dimona_check\": None, \"unmatched\": True,
            })
            break

    return results
'''

path = r'project/app/rules/tempoteam_rules.py'
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Written:', path)
