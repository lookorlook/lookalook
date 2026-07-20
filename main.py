"""
TEMPOTEAM 发票对账系统 - 主入口
支持: 上传考勤表 + 发票PDF → 自动对账 → 输出差异报告
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reconciliation import run_reconciliation

INPUTS = r"C:\Users\zt26501\Documents\Codex\2026-07-17\pdf-pdf-pdf-pdf\inputs"
RULES = r"C:\Users\zt26501\Documents\Codex\2026-07-17\pdf-pdf-pdf-pdf\project\rules\tempoteam_belgium.yaml"

def test_period(label, att_file, inv_files):
    print(f"\n{'='*60}")
    print(f"  测试: {label}")
    print(f"{'='*60}")
    try:
        report = run_reconciliation(att_file, inv_files, RULES)
        print(report.get_summary())
        
        # JSON output
        result = {
            "period": report.period,
            "total_attendance_hours": round(report.total_attendance_hours, 2),
            "total_invoice_hours": round(report.total_invoice_hours, 2),
            "total_invoice_amount": round(report.total_invoice_amount, 2),
            "employees_checked": len(report.results),
            "mismatches": [
                {
                    "name": r.name,
                    "attendance_hours": round(r.attendance_hours, 2),
                    "invoice_hours": round(r.invoice_hours, 2),
                    "diff_hours": round(r.diff_hours, 2),
                    "diff_percent": round(r.diff_percent, 1),
                    "verdict": r.verdict
                }
                for r in report.get_mismatches()
            ]
        }
        print(f"\n  JSON Summary: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return report
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"  ERROR: {e}")
        return None


if __name__ == "__main__":
    # Period 1
    p1 = os.path.join(INPUTS, "period1")
    r1 = test_period("Period 1 (15-21 Jun)",
        os.path.join(p1, "0615-0621.xlsx"),
        [os.path.join(p1, f) for f in ["61027976.pdf", "61027977.pdf"]])
    
    # Period 2
    p2 = os.path.join(INPUTS, "period2")
    r2 = test_period("Period 2 (22-28 Jun)",
        os.path.join(p2, "0622-0628.xlsx"),
        [os.path.join(p2, f) for f in ["61029249.pdf", "61029250.pdf"]])
    
    print(f"\n{'='*60}")
    print("  对账完成!")
    print(f"  Period 1: {r1.total_attendance_hours:.2f}h (考勤) vs {r1.total_invoice_hours:.2f}h (发票)" if r1 else "  Period 1: FAILED")
    print(f"  Period 2: {r2.total_attendance_hours:.2f}h (考勤) vs {r2.total_invoice_hours:.2f}h (发票)" if r2 else "  Period 2: FAILED")
