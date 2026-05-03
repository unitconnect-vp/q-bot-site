"""
build_persona_page.py
- /town/data/all.json 로드 → 슬림 변환 → /town/persona/index.html 빌드
- fetch-town-data.yml 워크플로우에서 build_town_page.py 다음에 실행
- 매주 페치 시 자동으로 거주지 의사결정 도구 데이터 갱신
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PATH = ROOT / "town" / "data" / "all.json"
TEMPLATE_PATH = Path(__file__).parent / "town_persona_template.html"
OUTPUT = ROOT / "town" / "persona" / "index.html"


def slim_records(records):
    """페르소나 점수 산출에 필요한 필드만 추출."""
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
                "medical": {"sgg_count": (s.get("medical") or {}).get("sgg_count", 0)},
                "education": {"sgg_count": (s.get("education") or {}).get("sgg_count", 0)},
                "population": {"sgg_total": (s.get("population") or {}).get("sgg_total", 0)},
                "population_age": s.get("population_age", {}) or {},  # 5세별 (있으면)
            },
        })
    return out


def main():
    if not DATA_PATH.exists():
        print(f"❌ 데이터 파일 없음: {DATA_PATH}", file=sys.stderr)
        sys.exit(1)
    if not TEMPLATE_PATH.exists():
        print(f"❌ 템플릿 파일 없음: {TEMPLATE_PATH}", file=sys.stderr)
        sys.exit(1)
    
    raw = DATA_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    records = data.get("records", [])
    print(f"  로드: {len(records)}개 시군구")
    
    slim = {"records": slim_records(records)}
    data_json = json.dumps(slim, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace("__DATA_JSON__", data_json)
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"  ✓ {OUTPUT} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
