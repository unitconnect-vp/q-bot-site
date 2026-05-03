#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q렌즈 동네 카드 — 페치 스크립트 v2 (서울 25개 자치구)
모든 자치구 데이터를 한 번에 페치 → town/data/seoul.json (통합) + 개별 JSON 백업
"""

import os
import sys
import json
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ─────────────────────────────────────────────────
# 서울 25개 자치구 매핑
# ─────────────────────────────────────────────────
SEOUL_GU = [
    ("11110", "종로구",     "jongno"),
    ("11140", "중구",       "junggu"),
    ("11170", "용산구",     "yongsan"),
    ("11200", "성동구",     "seongdong"),
    ("11215", "광진구",     "gwangjin"),
    ("11230", "동대문구",   "dongdaemun"),
    ("11260", "중랑구",     "jungnang"),
    ("11290", "성북구",     "seongbuk"),
    ("11305", "강북구",     "gangbuk"),
    ("11320", "도봉구",     "dobong"),
    ("11350", "노원구",     "nowon"),
    ("11380", "은평구",     "eunpyeong"),
    ("11410", "서대문구",   "seodaemun"),
    ("11440", "마포구",     "mapo"),
    ("11470", "양천구",     "yangcheon"),
    ("11500", "강서구",     "gangseo"),
    ("11530", "구로구",     "guro"),
    ("11545", "금천구",     "geumcheon"),
    ("11560", "영등포구",   "yeongdeungpo"),
    ("11590", "동작구",     "dongjak"),
    ("11620", "관악구",     "gwanak"),
    ("11650", "서초구",     "seocho"),
    ("11680", "강남구",     "gangnam"),
    ("11710", "송파구",     "songpa"),
    ("11740", "강동구",     "gangdong"),
]

SIDO_HIRA = "110000"
ATPT_NEIS = "B10"
OUTPUT_INTEGRATED = Path("town/data/seoul.json")
OUTPUT_INDIVIDUAL_DIR = Path("town/data/seoul")
TIMEOUT = 30


# ─────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────

def parse_amount_man(s):
    if not s:
        return 0
    try:
        return int(str(s).replace(",", "").strip())
    except ValueError:
        return 0


def m2_to_pyeong(m2):
    return float(m2) / 3.3058


def get_recent_yyyymm(months_back=0):
    today = datetime.now()
    for _ in range(months_back):
        today = today.replace(day=1) - timedelta(days=1)
    return today.strftime("%Y%m")


def to_int_or_none(s):
    if s is None:
        return None
    s = str(s).strip()
    if not s or s == "-":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


# ─────────────────────────────────────────────────
# 자치구별 페치
# ─────────────────────────────────────────────────

def fetch_real_estate_trade(key, lawd_cd):
    """매매 — 자치구 단위, 최근 3개월."""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    all_items = []
    months_used = []
    for m in range(3):
        ym = get_recent_yyyymm(m)
        params = {"serviceKey": key, "LAWD_CD": lawd_cd, "DEAL_YMD": ym, "numOfRows": "1000", "pageNo": "1"}
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.text)
        except (requests.RequestException, ET.ParseError):
            continue
        items = root.findall(".//item")
        if items:
            months_used.append(ym)
        for item in items:
            d = {child.tag: (child.text or "").strip() for child in item}
            all_items.append(d)

    if not all_items:
        return {"status": "no_data", "count": 0, "period_months": months_used}

    pyeong_prices, deal_prices = [], []
    for it in all_items:
        amt = parse_amount_man(it.get("dealAmount", "0"))
        try:
            area = float(it.get("excluUseAr", 0))
        except (ValueError, TypeError):
            continue
        if area > 0 and amt > 0:
            pyeong_prices.append(amt / m2_to_pyeong(area))
            deal_prices.append(amt)

    return {
        "count": len(all_items),
        "median_price_per_pyeong_man": int(statistics.median(pyeong_prices)) if pyeong_prices else None,
        "mean_price_per_pyeong_man": int(statistics.mean(pyeong_prices)) if pyeong_prices else None,
        "median_deal_amount_man": int(statistics.median(deal_prices)) if deal_prices else None,
        "period_months": months_used,
        "monthly_count_avg": round(len(all_items) / max(len(months_used), 1), 1),
    }


def fetch_real_estate_rent(key, lawd_cd):
    """전월세 — 자치구 단위, 최근 3개월."""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
    all_items = []
    months_used = []
    for m in range(3):
        ym = get_recent_yyyymm(m)
        params = {"serviceKey": key, "LAWD_CD": lawd_cd, "DEAL_YMD": ym, "numOfRows": "1000", "pageNo": "1"}
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.text)
        except (requests.RequestException, ET.ParseError):
            continue
        items = root.findall(".//item")
        if items:
            months_used.append(ym)
        for item in items:
            d = {child.tag: (child.text or "").strip() for child in item}
            all_items.append(d)

    if not all_items:
        return {"status": "no_data", "count": 0, "period_months": months_used}

    jeonse, monthly = [], []
    for it in all_items:
        deposit = parse_amount_man(it.get("deposit", "0"))
        monthly_rent = parse_amount_man(it.get("monthlyRent", "0"))
        if monthly_rent == 0 and deposit > 0:
            jeonse.append(deposit)
        elif monthly_rent > 0:
            monthly.append({"deposit": deposit, "rent": monthly_rent})

    return {
        "total_count": len(all_items),
        "jeonse_count": len(jeonse),
        "monthly_count": len(monthly),
        "median_jeonse_man": int(statistics.median(jeonse)) if jeonse else None,
        "mean_jeonse_man": int(statistics.mean(jeonse)) if jeonse else None,
        "period_months": months_used,
    }


# ─────────────────────────────────────────────────
# 공통 페치 (한 번 호출 → 자치구별 분리)
# ─────────────────────────────────────────────────

def fetch_environment_all(key):
    """에어코리아 서울 전체 측정소 → 자치구별 분리."""
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {"serviceKey": key, "returnType": "json", "numOfRows": "100", "pageNo": "1", "sidoName": "서울", "ver": "1.0"}
    r = requests.get(url, params=params, timeout=TIMEOUT)
    j = r.json()
    items = j.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return {"_seoul_avg": None, "_per_gu": {}}

    pm10s = [v for v in (to_int_or_none(it.get("pm10Value")) for it in items) if v is not None]
    pm25s = [v for v in (to_int_or_none(it.get("pm25Value")) for it in items) if v is not None]
    seoul_avg = {
        "pm10": int(statistics.mean(pm10s)) if pm10s else None,
        "pm25": int(statistics.mean(pm25s)) if pm25s else None,
        "station_count": len(items),
    }

    # 자치구별 측정소 매핑 (이름에 자치구명이 들어가는 측정소 찾기)
    per_gu = {}
    for _, name, _ in SEOUL_GU:
        gu_short = name.replace("구", "")  # "강남구" → "강남"
        for it in items:
            station = it.get("stationName", "") or ""
            if gu_short in station or name in station:
                per_gu[name] = {
                    "station": station,
                    "pm10": to_int_or_none(it.get("pm10Value")),
                    "pm25": to_int_or_none(it.get("pm25Value")),
                }
                break

    return {
        "_seoul_avg": seoul_avg,
        "_measured_at": items[0].get("dataTime") if items else None,
        "_per_gu": per_gu,
    }


def fetch_medical_all(key):
    """심평원 서울 전체 → 주소 기준 자치구별 분리."""
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    all_hosp = []
    for page in range(1, 11):
        params = {"ServiceKey": key, "_type": "json", "numOfRows": "1000", "pageNo": str(page), "sidoCd": SIDO_HIRA}
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            j = r.json()
        except (requests.RequestException, json.JSONDecodeError):
            break
        body = j.get("response", {}).get("body", {})
        items_wrap = body.get("items", {}) or {}
        items = items_wrap.get("item", []) if isinstance(items_wrap, dict) else []
        if isinstance(items, dict):
            items = [items]
        if not items:
            break
        all_hosp.extend(items)
        total = int(body.get("totalCount", 0) or 0)
        if total and len(all_hosp) >= total:
            break

    per_gu = {}
    for _, name, _ in SEOUL_GU:
        gu_hosps = [h for h in all_hosp if name in (h.get("addr", "") or "")]
        type_counts = {}
        for h in gu_hosps:
            t = h.get("clCdNm", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_gu[name] = {
            "sgg_count": len(gu_hosps),
            "by_type": type_counts,
        }

    return {"_total_seoul": len(all_hosp), "_per_gu": per_gu}


def fetch_education_all(key):
    """NEIS 서울 전체 → 주소 기준 자치구별 분리."""
    url = "https://open.neis.go.kr/hub/schoolInfo"
    all_schools = []
    for page in range(1, 6):
        params = {"KEY": key, "Type": "json", "pIndex": str(page), "pSize": "1000", "ATPT_OFCDC_SC_CODE": ATPT_NEIS}
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            j = r.json()
        except (requests.RequestException, json.JSONDecodeError):
            break
        if "schoolInfo" not in j:
            break
        info = j["schoolInfo"]
        if not isinstance(info, list) or len(info) < 2:
            break
        rows = info[1].get("row", []) if isinstance(info[1], dict) else []
        if not rows:
            break
        all_schools.extend(rows)
        if len(rows) < 1000:
            break

    per_gu = {}
    for _, name, _ in SEOUL_GU:
        gu_schools = [s for s in all_schools if name in (s.get("ORG_RDNMA", "") or "")]
        type_counts = {}
        for s in gu_schools:
            t = s.get("SCHUL_KND_SC_NM", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_gu[name] = {
            "sgg_count": len(gu_schools),
            "by_type": type_counts,
        }

    return {"_total_seoul": len(all_schools), "_per_gu": per_gu}


def fetch_population_all(key):
    """KOSIS DT_1B040A3 — 한 번 호출로 모든 시군구 인구."""
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList", "apiKey": key, "itmId": "T20", "objL1": "ALL",
        "format": "json", "jsonVD": "Y", "prdSe": "M", "newEstPrdCnt": "1",
        "orgId": "101", "tblId": "DT_1B040A3",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    try:
        j = r.json()
    except json.JSONDecodeError:
        return {"_per_gu": {}, "_seoul_total": None, "_period": None}

    if not isinstance(j, list):
        return {"_per_gu": {}, "_seoul_total": None, "_period": None}

    seoul_total = None
    period = None
    per_gu = {}
    for row in j:
        c1_nm = row.get("C1_NM", "") or ""
        c2_nm = row.get("C2_NM", "") or ""
        if not period:
            period = row.get("PRD_DE")
        if c1_nm == "서울특별시" and not c2_nm:
            seoul_total = to_int_or_none(row.get("DT"))
        # 자치구 매칭
        for _, name, _ in SEOUL_GU:
            if name in c1_nm or name in c2_nm:
                per_gu[name] = {
                    "total": to_int_or_none(row.get("DT")),
                    "period": row.get("PRD_DE"),
                }
                break

    return {
        "_per_gu": per_gu,
        "_seoul_total": seoul_total,
        "_period": period,
    }


# ─────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────

def safe(name, fn, *args, default=None):
    try:
        result = fn(*args)
        print(f"  ✓ {name}", flush=True)
        return result, None
    except Exception as e:
        msg = f"{type(e).__name__}: {str(e)[:200]}"
        print(f"  ✗ {name}: {msg}", file=sys.stderr, flush=True)
        return default, msg


def main():
    keys = {
        "MOLIT_TRADE_KEY": os.environ.get("MOLIT_TRADE_KEY", "").strip(),
        "MOLIT_RENT_KEY":  os.environ.get("MOLIT_RENT_KEY", "").strip(),
        "AIRKOREA_KEY":    os.environ.get("AIRKOREA_KEY", "").strip(),
        "HIRA_KEY":        os.environ.get("HIRA_KEY", "").strip(),
        "KOSIS_KEY":       os.environ.get("KOSIS_KEY", "").strip(),
        "NEIS_KEY":        os.environ.get("NEIS_KEY", "").strip(),
    }
    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(f"❌ Missing env keys: {missing}", file=sys.stderr)
        sys.exit(1)

    fetched_at = datetime.now(timezone.utc).isoformat()

    print("[STEP 1/2] 공통 데이터 (서울 전체 → 자치구 분리)")
    env_all, _    = safe("environment_all", fetch_environment_all, keys["AIRKOREA_KEY"], default={"_seoul_avg": None, "_per_gu": {}, "_measured_at": None})
    med_all, _    = safe("medical_all",     fetch_medical_all,     keys["HIRA_KEY"],     default={"_total_seoul": 0, "_per_gu": {}})
    edu_all, _    = safe("education_all",   fetch_education_all,   keys["NEIS_KEY"],     default={"_total_seoul": 0, "_per_gu": {}})
    pop_all, _    = safe("population_all",  fetch_population_all,  keys["KOSIS_KEY"],    default={"_per_gu": {}, "_seoul_total": None, "_period": None})

    print(f"\n[STEP 2/2] 자치구별 부동산 페치 ({len(SEOUL_GU)}개)")
    all_records = []
    for i, (lawd_cd, name, slug) in enumerate(SEOUL_GU, 1):
        print(f"  [{i:2d}/{len(SEOUL_GU)}] {name} ({lawd_cd})", flush=True)
        trade, _ = safe(f"  trade",  fetch_real_estate_trade, keys["MOLIT_TRADE_KEY"], lawd_cd, default={})
        rent,  _ = safe(f"  rent",   fetch_real_estate_rent,  keys["MOLIT_RENT_KEY"],  lawd_cd, default={})

        record = {
            "slug": f"seoul/{slug}",
            "name": name,
            "name_full": f"서울특별시 {name}",
            "level": "gu",
            "lawd_cd": lawd_cd,
            "fetched_at": fetched_at,
            "sections": {
                "real_estate_trade": trade,
                "real_estate_rent": rent,
                "environment": {
                    "seoul_avg": env_all.get("_seoul_avg"),
                    "gangnam_station": env_all.get("_per_gu", {}).get(name),  # key 이름은 호환성 위해 유지
                    "gu_station": env_all.get("_per_gu", {}).get(name),       # 새 일반화 키
                    "measured_at": env_all.get("_measured_at"),
                },
                "medical": med_all.get("_per_gu", {}).get(name, {"sgg_count": 0, "by_type": {}}),
                "education": edu_all.get("_per_gu", {}).get(name, {"sgg_count": 0, "by_type": {}}),
                "population": {
                    "table_id": "DT_1B040A3",
                    "table_name": "행정구역(시군구)별/성별 인구수",
                    "period": pop_all.get("_period"),
                    "sgg_total": (pop_all.get("_per_gu", {}).get(name) or {}).get("total"),
                    "gangnam_total": (pop_all.get("_per_gu", {}).get(name) or {}).get("total"),  # 호환성
                    "seoul_total": pop_all.get("_seoul_total"),
                    "share_of_seoul_pct": round(
                        ((pop_all.get("_per_gu", {}).get(name) or {}).get("total") or 0)
                        / (pop_all.get("_seoul_total") or 1) * 100, 2
                    ) if pop_all.get("_seoul_total") else None,
                },
            },
            "errors": [],
        }
        all_records.append(record)

    # 통합 JSON 저장
    OUTPUT_INTEGRATED.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_INTEGRATED.write_text(
        json.dumps({
            "fetched_at": fetched_at,
            "city": "seoul",
            "city_name": "서울특별시",
            "count": len(all_records),
            "records": all_records,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✓ 통합 저장: {OUTPUT_INTEGRATED} ({len(all_records)}개 자치구)")

    # 개별 JSON도 저장 (호환성)
    OUTPUT_INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)
    for record in all_records:
        slug_short = record["slug"].split("/")[-1]
        path = OUTPUT_INDIVIDUAL_DIR / f"{slug_short}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  + 개별 JSON {len(all_records)}개 저장")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 페치 결과 (서울 25개 자치구)\n\n")
            f.write(f"- 페치 시각: {fetched_at}\n")
            f.write(f"- 자치구 수: {len(all_records)}\n")
            f.write(f"- 통합 파일: `{OUTPUT_INTEGRATED}`\n\n")
            f.write("| 자치구 | 매매 | 전세 | 의료 | 학교 | 인구 |\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in all_records:
                t = r["sections"]["real_estate_trade"]
                rt = r["sections"]["real_estate_rent"]
                m = r["sections"]["medical"]
                e = r["sections"]["education"]
                p = r["sections"]["population"]
                f.write(
                    f"| {r['name']} | {t.get('count', '—')}건 "
                    f"| {rt.get('jeonse_count', '—')}건 "
                    f"| {m.get('sgg_count', '—')} "
                    f"| {e.get('sgg_count', '—')} "
                    f"| {p.get('sgg_total') or '—'} |\n"
                )


if __name__ == "__main__":
    main()
