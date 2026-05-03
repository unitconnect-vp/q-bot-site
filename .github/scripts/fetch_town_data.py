#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q렌즈 동네 카드 — 페치 스크립트 v1
강남구(법정동코드 11680) 데이터를 6개 API에서 수집해 JSON 한 파일로 저장.

산출: town/data/seoul/gangnam.json
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
# 강남구 상수
# ─────────────────────────────────────────────────
LAWD_CD = "11680"             # 법정동 코드 (5자리)
SGG_NAME = "강남구"
SGG_NAME_FULL = "서울특별시 강남구"
SIDO_HIRA = "110000"          # HIRA 시도코드 (서울)
ATPT_NEIS = "B10"             # NEIS 서울교육청

OUTPUT_PATH = Path("town/data/seoul/gangnam.json")
TIMEOUT = 30


# ─────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────

def parse_amount_man(s):
    """'13,500' → 13500 (만원)."""
    if not s:
        return 0
    try:
        return int(str(s).replace(",", "").strip())
    except ValueError:
        return 0


def m2_to_pyeong(m2):
    return float(m2) / 3.3058


def get_recent_yyyymm(months_back=0):
    """현재 시점에서 N개월 전 YYYYMM 문자열."""
    today = datetime.now()
    for _ in range(months_back):
        today = today.replace(day=1) - timedelta(days=1)
    return today.strftime("%Y%m")


def to_int_or_none(s):
    """숫자 문자열을 int로. '-' 또는 빈 문자열은 None."""
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
# 1. 부동산 매매 (MOLIT_TRADE)
# ─────────────────────────────────────────────────

def fetch_real_estate_trade(key):
    """국토교통부 아파트 매매 실거래가 — 최근 3개월."""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"

    all_items = []
    months_used = []
    for m in range(3):
        ym = get_recent_yyyymm(m)
        params = {
            "serviceKey": key,
            "LAWD_CD": LAWD_CD,
            "DEAL_YMD": ym,
            "numOfRows": "1000",
            "pageNo": "1",
        }
        r = requests.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            continue
        try:
            root = ET.fromstring(r.text)
        except ET.ParseError:
            continue
        items = root.findall(".//item")
        if items:
            months_used.append(ym)
        for item in items:
            d = {child.tag: (child.text or "").strip() for child in item}
            all_items.append(d)

    if not all_items:
        return {"status": "no_data", "count": 0, "period_months": months_used}

    pyeong_prices = []
    deal_prices = []
    for it in all_items:
        amt = parse_amount_man(it.get("dealAmount", "0"))
        try:
            area = float(it.get("excluUseAr", 0))
        except (ValueError, TypeError):
            continue
        if area > 0 and amt > 0:
            ppp = amt / m2_to_pyeong(area)
            pyeong_prices.append(ppp)
            deal_prices.append(amt)

    return {
        "count": len(all_items),
        "median_price_per_pyeong_man": int(statistics.median(pyeong_prices)) if pyeong_prices else None,
        "mean_price_per_pyeong_man": int(statistics.mean(pyeong_prices)) if pyeong_prices else None,
        "median_deal_amount_man": int(statistics.median(deal_prices)) if deal_prices else None,
        "period_months": months_used,
        "monthly_count_avg": round(len(all_items) / max(len(months_used), 1), 1),
    }


# ─────────────────────────────────────────────────
# 2. 부동산 전월세 (MOLIT_RENT)
# ─────────────────────────────────────────────────

def fetch_real_estate_rent(key):
    """국토교통부 아파트 전월세 실거래가 — 최근 3개월, 전세 따로 집계."""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"

    all_items = []
    months_used = []
    for m in range(3):
        ym = get_recent_yyyymm(m)
        params = {
            "serviceKey": key,
            "LAWD_CD": LAWD_CD,
            "DEAL_YMD": ym,
            "numOfRows": "1000",
            "pageNo": "1",
        }
        r = requests.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            continue
        try:
            root = ET.fromstring(r.text)
        except ET.ParseError:
            continue
        items = root.findall(".//item")
        if items:
            months_used.append(ym)
        for item in items:
            d = {child.tag: (child.text or "").strip() for child in item}
            all_items.append(d)

    if not all_items:
        return {"status": "no_data", "count": 0, "period_months": months_used}

    jeonse = []
    monthly = []
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
# 3. 환경 (AIRKOREA)
# ─────────────────────────────────────────────────

def fetch_environment(key):
    """에어코리아 시도별 실시간 측정 — 서울 평균 + 강남구 측정소 별도."""
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {
        "serviceKey": key,
        "returnType": "json",
        "numOfRows": "100",
        "pageNo": "1",
        "sidoName": "서울",
        "ver": "1.0",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    j = r.json()
    items = j.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return {"status": "no_data"}

    # 강남구 측정소 찾기 (이름에 "강남")
    gangnam_station = None
    for it in items:
        name = it.get("stationName", "") or ""
        if "강남" in name:
            gangnam_station = it
            break

    # 서울 전체 평균
    pm10_vals = [v for v in (to_int_or_none(it.get("pm10Value")) for it in items) if v is not None]
    pm25_vals = [v for v in (to_int_or_none(it.get("pm25Value")) for it in items) if v is not None]

    result = {
        "seoul_avg": {
            "pm10": int(statistics.mean(pm10_vals)) if pm10_vals else None,
            "pm25": int(statistics.mean(pm25_vals)) if pm25_vals else None,
            "station_count": len(items),
        },
        "measured_at": items[0].get("dataTime") if items else None,
    }

    if gangnam_station:
        result["gangnam_station"] = {
            "name": gangnam_station.get("stationName"),
            "pm10": to_int_or_none(gangnam_station.get("pm10Value")),
            "pm25": to_int_or_none(gangnam_station.get("pm25Value")),
        }

    return result


# ─────────────────────────────────────────────────
# 4. 의료 (HIRA)
# ─────────────────────────────────────────────────

def fetch_medical(key):
    """심평원 병원기본목록 — 서울 받아서 주소에서 강남구 필터."""
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"

    all_hosp = []
    for page in range(1, 11):  # 최대 10페이지 안전장치
        params = {
            "ServiceKey": key,
            "_type": "json",
            "numOfRows": "1000",
            "pageNo": str(page),
            "sidoCd": SIDO_HIRA,
        }
        r = requests.get(url, params=params, timeout=TIMEOUT)
        try:
            j = r.json()
        except json.JSONDecodeError:
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

    gangnam = [h for h in all_hosp if "강남구" in (h.get("addr", "") or "")]
    type_counts = {}
    for h in gangnam:
        t = h.get("clCdNm", "기타")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_seoul": len(all_hosp),
        "gangnam_count": len(gangnam),
        "by_type": type_counts,
    }


# ─────────────────────────────────────────────────
# 5. 인구 — KOSIS (1단계 placeholder)
# ─────────────────────────────────────────────────

def fetch_population(key):
    """KOSIS — 통계표 ID 미확정, 1단계는 카테고리 목록 호출만."""
    url = "https://kosis.kr/openapi/statisticsList.do"
    params = {
        "method": "getList",
        "apiKey": key,
        "vwCd": "MT_ZTITLE",
        "parentListId": "A",
        "format": "json",
        "jsonVD": "Y",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    try:
        j = r.json()
    except json.JSONDecodeError:
        return {"status": "error", "note": "응답 파싱 실패"}

    return {
        "status": "pending",
        "note": "1단계 placeholder — KOSIS 통계표 ID 확정 후 2단계에서 인구·연령·소득 수집",
        "available_categories": len(j) if isinstance(j, list) else None,
    }


# ─────────────────────────────────────────────────
# 6. 교육 (NEIS)
# ─────────────────────────────────────────────────

def fetch_education(key):
    """NEIS 학교기본정보 — 서울교육청(B10) 받아서 주소에서 강남구 필터."""
    url = "https://open.neis.go.kr/hub/schoolInfo"

    all_schools = []
    for page in range(1, 6):  # 최대 5페이지 안전장치
        params = {
            "KEY": key,
            "Type": "json",
            "pIndex": str(page),
            "pSize": "1000",
            "ATPT_OFCDC_SC_CODE": ATPT_NEIS,
        }
        r = requests.get(url, params=params, timeout=TIMEOUT)
        try:
            j = r.json()
        except json.JSONDecodeError:
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

    gangnam = [s for s in all_schools if "강남구" in (s.get("ORG_RDNMA", "") or "")]
    type_counts = {}
    for s in gangnam:
        t = s.get("SCHUL_KND_SC_NM", "기타")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_seoul": len(all_schools),
        "gangnam_count": len(gangnam),
        "by_type": type_counts,
    }


# ─────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────

def safe_call(name, fn, *args):
    """페치 독립 실행 — 한 섹션 실패가 다른 섹션에 영향 없도록."""
    try:
        result = fn(*args)
        print(f"  ✓ {name}")
        return result, None
    except Exception as e:
        msg = f"{type(e).__name__}: {str(e)[:200]}"
        print(f"  ✗ {name}: {msg}", file=sys.stderr)
        return None, msg


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

    result = {
        "slug": "seoul/gangnam",
        "name": SGG_NAME,
        "name_full": SGG_NAME_FULL,
        "level": "gu",
        "lawd_cd": LAWD_CD,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sections": {},
        "errors": [],
    }

    print("[페치 시작 — 강남구]")
    sections = [
        ("real_estate_trade", fetch_real_estate_trade, keys["MOLIT_TRADE_KEY"]),
        ("real_estate_rent",  fetch_real_estate_rent,  keys["MOLIT_RENT_KEY"]),
        ("environment",       fetch_environment,       keys["AIRKOREA_KEY"]),
        ("medical",           fetch_medical,           keys["HIRA_KEY"]),
        ("population",        fetch_population,        keys["KOSIS_KEY"]),
        ("education",         fetch_education,         keys["NEIS_KEY"]),
    ]
    for name, fn, key in sections:
        data, err = safe_call(name, fn, key)
        if data is not None:
            result["sections"][name] = data
        if err is not None:
            result["errors"].append({"section": name, "error": err})

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✓ 저장: {OUTPUT_PATH}")
    print(f"  성공: {len(result['sections'])}/6")
    print(f"  에러: {len(result['errors'])}/6")

    # GitHub Actions Step Summary
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 강남구 페치 결과\n\n")
            f.write(f"- 성공: **{len(result['sections'])}/6** 섹션\n")
            f.write(f"- 에러: **{len(result['errors'])}/6** 섹션\n\n")
            if result["errors"]:
                f.write("## 에러 상세\n\n")
                for e in result["errors"]:
                    f.write(f"- `{e['section']}`: {e['error']}\n")


if __name__ == "__main__":
    main()
