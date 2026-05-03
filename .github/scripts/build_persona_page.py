"""
build_persona_page.py
- /town/data/all.json 로드 → 슬림 변환 → 3개 페이지 빌드:
  · /town/persona/index.html (단일 분석)
  · /town/persona/compare/index.html (A vs B 비교)
  · /town/persona/checklist/index.html (이사 전 확인할 12가지)
- fetch-town-data.yml 워크플로우에서 build_town_page.py 다음에 실행
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = ROOT / "town" / "data" / "all.json"
SCRIPT_DIR = Path(__file__).parent

PAGES = [
    ("town_persona_template.html",           "town/persona/index.html"),
    ("town_persona_compare_template.html",   "town/persona/compare/index.html"),
    ("town_persona_checklist_template.html", "town/persona/checklist/index.html"),
]


def slim_records(records):
    out = []
    for r in records:
        s = r.get("sections", {}) or {}
        out.append({
            "slug": r["slug"],
            "name": r["name"],
            "name_full": r["name_full"],
            "sido_code": r["sido_code"],
            "sido_name": r["sido_name"],
            "sections": {
                "real_estate_trade": {
                    "median_price_per_pyeong_man": (s.get("real_estate_trade") or {}).get("median_price_per_pyeong_man"),
                    "count": (s.get("real_estate_trade") or {}).get("count"),
                },
                "real_estate_rent": {
                    "median_jeonse_man": (s.get("real_estate_rent") or {}).get("median_jeonse_man"),
                },
                "environment": s.get("environment", {}) or {},
                "medical": {
                    "sgg_count": (s.get("medical") or {}).get("sgg_count", 0),
                    "by_type": (s.get("medical") or {}).get("by_type", {}),
                },
                "education": {"sgg_count": (s.get("education") or {}).get("sgg_count", 0)},
                "population": {"sgg_total": (s.get("population") or {}).get("sgg_total", 0)},
                "population_age": s.get("population_age", {}) or {},
            },
        })
    return out


def main():
    if not DATA_PATH.exists():
        print(f"❌ 데이터 없음: {DATA_PATH}", file=sys.stderr)
        sys.exit(1)
    
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    records = data.get("records", [])
    print(f"  로드: {len(records)}개 시군구")
    
    slim = {"records": slim_records(records)}
    data_json = json.dumps(slim, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    
    failed = []
    for tmpl_name, output_rel in PAGES:
        tmpl_path = SCRIPT_DIR / tmpl_name
        out_path = ROOT / output_rel
        if not tmpl_path.exists():
            print(f"  ❌ 템플릿 없음: {tmpl_path}", file=sys.stderr)
            failed.append(output_rel)
            continue
        template = tmpl_path.read_text(encoding="utf-8")
        html = template.replace("__DATA_JSON__", data_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"  ✓ {out_path} ({len(html):,} bytes)")
    
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
