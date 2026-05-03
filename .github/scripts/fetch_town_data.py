#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q렌즈 동네 카드 — 페치 v4 (전국 17개 시도, KOSIS 동적 SIDO_LIST)"""

import os
import re
import sys
import json
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ─────────────────────────────────────────────────
# 시도 메타 (LAWD_CD 앞 2자리 prefix → 시도 정보)
# ─────────────────────────────────────────────────
SIDO_META = {
    "11": {"code": "seoul",     "name": "서울특별시",       "airkorea": "서울", "hira_cds": ["110000"],            "neis_atpt": "B10"},
    "26": {"code": "busan",     "name": "부산광역시",       "airkorea": "부산", "hira_cds": ["210000", "260000"],  "neis_atpt": "C10"},
    "27": {"code": "daegu",     "name": "대구광역시",       "airkorea": "대구", "hira_cds": ["230000", "270000"],  "neis_atpt": "D10"},
    "28": {"code": "incheon",   "name": "인천광역시",       "airkorea": "인천", "hira_cds": ["220000", "280000"],  "neis_atpt": "E10"},
    "29": {"code": "gwangju",   "name": "광주광역시",       "airkorea": "광주", "hira_cds": ["240000", "290000"],  "neis_atpt": "F10"},
    "30": {"code": "daejeon",   "name": "대전광역시",       "airkorea": "대전", "hira_cds": ["250000", "300000"],  "neis_atpt": "G10"},
    "31": {"code": "ulsan",     "name": "울산광역시",       "airkorea": "울산", "hira_cds": ["260000", "310000"],  "neis_atpt": "H10"},
    "36": {"code": "sejong",    "name": "세종특별자치시",   "airkorea": "세종", "hira_cds": ["290000", "360000"],  "neis_atpt": "I10"},
    "41": {"code": "gyeonggi",  "name": "경기도",           "airkorea": "경기", "hira_cds": ["410000", "310000"],  "neis_atpt": "J10"},
    "42": {"code": "gangwon",   "name": "강원특별자치도",   "airkorea": "강원", "hira_cds": ["320000", "420000", "510000"],  "neis_atpt": "K10"},
    "51": {"code": "gangwon",   "name": "강원특별자치도",   "airkorea": "강원", "hira_cds": ["320000", "420000", "510000"],  "neis_atpt": "K10"},
    "43": {"code": "chungbuk",  "name": "충청북도",         "airkorea": "충북", "hira_cds": ["330000", "430000"],  "neis_atpt": "M10"},
    "44": {"code": "chungnam",  "name": "충청남도",         "airkorea": "충남", "hira_cds": ["340000", "440000"],  "neis_atpt": "N10"},
    "45": {"code": "jeonbuk",   "name": "전북특별자치도",   "airkorea": "전북", "hira_cds": ["350000", "450000", "520000"],  "neis_atpt": "P10"},
    "52": {"code": "jeonbuk",   "name": "전북특별자치도",   "airkorea": "전북", "hira_cds": ["350000", "450000", "520000"],  "neis_atpt": "P10"},
    "46": {"code": "jeonnam",   "name": "전라남도",         "airkorea": "전남", "hira_cds": ["360000", "460000"],  "neis_atpt": "Q10"},
    "47": {"code": "gyeongbuk", "name": "경상북도",         "airkorea": "경북", "hira_cds": ["370000", "470000"],  "neis_atpt": "R10"},
    "48": {"code": "gyeongnam", "name": "경상남도",         "airkorea": "경남", "hira_cds": ["380000", "480000"],  "neis_atpt": "S10"},
    "50": {"code": "jeju",      "name": "제주특별자치도",   "airkorea": "제주", "hira_cds": ["390000", "500000"],  "neis_atpt": "T10"},
}

OUTPUT_INTEGRATED = Path("town/data/seoul.json")  # 경로 호환성 유지
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


def slugify(eng_name):
    """KOSIS C1_NM_ENG → URL slug. 'Gangnam-gu' -> 'gangnam', 'Bucheon-si' -> 'bucheon'."""
    if not eng_name:
        return ""
    s = eng_name.lower()
    # 행정구역 접미어 제거
    for suffix in ["-gu", "-si", "-gun", "-do", "-myeon", "-eup", "-dong"]:
        if s.endswith(suffix):
            s = s[:-len(suffix)]
            break
    # 특수문자 → 하이픈
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


# ─────────────────────────────────────────────────
# KOSIS — SIDO_LIST 동적 생성 + 인구 데이터
# ─────────────────────────────────────────────────

def fetch_kosis_and_build_sido(kosis_key):
    """KOSIS DT_1B040A3 한 번 호출 → SIDO_LIST + 인구 매핑 동시 생성."""
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList", "apiKey": kosis_key, "itmId": "T20", "objL1": "ALL",
        "format": "json", "jsonVD": "Y", "prdSe": "M", "newEstPrdCnt": "1",
        "orgId": "101", "tblId": "DT_1B040A3",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    j = r.json()

    if not isinstance(j, list):
        raise RuntimeError(f"KOSIS 응답 형식 오류: {str(j)[:200]}")

    period = None
    sido_totals = {}      # sido_code → 인구
    population_by_lawd = {}  # LAWD_CD → 인구
    sigun_pool = {}       # sido_code → list of (lawd_cd, name_kr, name_eng)
    used_slugs = set()    # 시도-slug 충돌 방지

    for row in j:
        c1 = row.get("C1", "") or ""
        c1_nm = row.get("C1_NM", "") or ""
        c1_eng = row.get("C1_NM_ENG", "") or ""
        if not period:
            period = row.get("PRD_DE")

        # 출장소·전국 등 특수 row 제외
        if not c1 or not c1_nm or "출장소" in c1_nm or c1 == "00":
            continue

        # 시도 합계 (코드가 짧거나 끝이 "00000" 등 특수)
        # KOSIS는 시도를 c1_nm으로 직접 매칭 가능
        if c1_nm.endswith(("특별시", "광역시", "도", "특별자치시", "특별자치도")):
            # 시도 row
            for prefix, meta in SIDO_META.items():
                if meta["name"] == c1_nm:
                    sido_totals[meta["code"]] = to_int_or_none(row.get("DT"))
                    break
            continue

        # 시군구 row — LAWD_CD 5자리
        if len(c1) != 5:
            continue
        prefix = c1[:2]
        if prefix not in SIDO_META:
            continue

        sido_meta = SIDO_META[prefix]
        sido_code = sido_meta["code"]
        sigun_pool.setdefault(sido_code, [])

        # 중복 LAWD_CD 방지
        if any(s[0] == c1 for s in sigun_pool[sido_code]):
            continue

        sigun_pool[sido_code].append((c1, c1_nm, c1_eng))
        population_by_lawd[c1] = {
            "total": to_int_or_none(row.get("DT")),
            "period": row.get("PRD_DE"),
        }

    # SIDO_LIST 빌드 (코드 정렬 유지)
    sido_list = []
    sido_codes_seen = set()
    sido_meta_by_code = {}
    for prefix, meta in SIDO_META.items():
        if meta["code"] in sido_codes_seen:
            continue  # 중복 코드 (강원: 42, 51 둘 다 있음) 제거
        sido_codes_seen.add(meta["code"])
        sido_meta_by_code[meta["code"]] = meta

    # 시도 순서: SIDO_META 기준
    seen_codes = []
    for prefix, meta in SIDO_META.items():
        if meta["code"] in seen_codes:
            continue
        seen_codes.append(meta["code"])

    for sido_code in seen_codes:
        meta = sido_meta_by_code[sido_code]
        sigun_raw = sigun_pool.get(sido_code, [])
        if not sigun_raw:
            continue

        # 시군구 리스트 빌드 (slug 생성)
        sigun_list = []
        local_used = set()
        for lawd_cd, kr, eng in sigun_raw:
            slug_short = slugify(eng) or lawd_cd
            # 충돌 시 lawd_cd 일부 추가
            if slug_short in local_used:
                slug_short = f"{slug_short}-{lawd_cd[2:]}"
            local_used.add(slug_short)
            full_slug = f"{sido_code}/{slug_short}"
            sigun_list.append({
                "lawd_cd": lawd_cd,
                "full_name": kr,         # "강남구"
                "short_label": kr,        # 셀렉터 칩 표시용
                "slug": full_slug,
                "eng_name": eng,
            })

        sido_list.append({
            "code": sido_code,
            "name": meta["name"],
            "airkorea": meta["airkorea"],
            "hira_cds": meta["hira_cds"],
            "neis_atpt": meta["neis_atpt"],
            "sigun_list": sigun_list,
        })

    return {
        "sido_list": sido_list,
        "sido_totals": sido_totals,
        "population_by_lawd": population_by_lawd,
        "period": period,
    }


# ─────────────────────────────────────────────────
# 부동산 (시군구별)
# ─────────────────────────────────────────────────

def fetch_real_estate_trade(key, lawd_cd):
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
# 시도별 공통 페치
# ─────────────────────────────────────────────────

def fetch_environment(key, sido_name, sigun_list):
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {"serviceKey": key, "returnType": "json", "numOfRows": "300", "pageNo": "1", "sidoName": sido_name, "ver": "1.0"}
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        j = r.json()
    except (requests.RequestException, json.JSONDecodeError):
        return {"_avg": None, "_per_lawd": {}, "_measured_at": None}

    items = j.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return {"_avg": None, "_per_lawd": {}, "_measured_at": None}

    pm10s = [v for v in (to_int_or_none(it.get("pm10Value")) for it in items) if v is not None]
    pm25s = [v for v in (to_int_or_none(it.get("pm25Value")) for it in items) if v is not None]
    avg = {
        "pm10": int(statistics.mean(pm10s)) if pm10s else None,
        "pm25": int(statistics.mean(pm25s)) if pm25s else None,
        "station_count": len(items),
    }

    per_lawd = {}
    for sigun in sigun_list:
        kr = sigun["full_name"]
        kw = kr.replace("시", "").replace("구", "").replace("군", "").strip()
        if len(kw) < 2:
            continue
        for it in items:
            station = it.get("stationName", "") or ""
            if kw and kw in station:
                per_lawd[sigun["lawd_cd"]] = {
                    "station": station,
                    "pm10": to_int_or_none(it.get("pm10Value")),
                    "pm25": to_int_or_none(it.get("pm25Value")),
                }
                break

    return {
        "_avg": avg,
        "_measured_at": items[0].get("dataTime") if items else None,
        "_per_lawd": per_lawd,
    }


def fetch_medical(key, sido_cds, sigun_list):
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    final_hosp = []
    used_cd = None

    for sido_cd in sido_cds:
        all_hosp = []
        for page in range(1, 21):  # 최대 20000개
            params = {"ServiceKey": key, "_type": "json", "numOfRows": "1000", "pageNo": str(page), "sidoCd": sido_cd}
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
        if all_hosp:
            print(f"    medical sidoCd={sido_cd}: {len(all_hosp)}개", flush=True)
            final_hosp = all_hosp
            used_cd = sido_cd
            break

    per_lawd = {}
    for sigun in sigun_list:
        kr = sigun["full_name"]
        gu_hosps = [h for h in final_hosp if kr in (h.get("addr", "") or "")]
        type_counts = {}
        for h in gu_hosps:
            t = h.get("clCdNm", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_lawd[sigun["lawd_cd"]] = {
            "sgg_count": len(gu_hosps),
            "by_type": type_counts,
        }

    return {"_total": len(final_hosp), "_used_cd": used_cd, "_per_lawd": per_lawd}


def fetch_education(key, atpt_code, sigun_list):
    url = "https://open.neis.go.kr/hub/schoolInfo"
    all_schools = []
    for page in range(1, 11):
        params = {"KEY": key, "Type": "json", "pIndex": str(page), "pSize": "1000", "ATPT_OFCDC_SC_CODE": atpt_code}
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

    per_lawd = {}
    for sigun in sigun_list:
        kr = sigun["full_name"]
        gu_schools = [s for s in all_schools if kr in (s.get("ORG_RDNMA", "") or "")]
        type_counts = {}
        for s in gu_schools:
            t = s.get("SCHUL_KND_SC_NM", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_lawd[sigun["lawd_cd"]] = {
            "sgg_count": len(gu_schools),
            "by_type": type_counts,
        }

    return {"_total": len(all_schools), "_per_lawd": per_lawd}


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

    print("[STEP 1] KOSIS — SIDO_LIST 동적 생성 + 전국 인구")
    kosis_data = fetch_kosis_and_build_sido(keys["KOSIS_KEY"])
    sido_list = kosis_data["sido_list"]
    sido_totals = kosis_data["sido_totals"]
    pop_by_lawd = kosis_data["population_by_lawd"]
    period = kosis_data["period"]

    total_sigun = sum(len(s["sigun_list"]) for s in sido_list)
    print(f"  → 시도 {len(sido_list)}개, 시군구 {total_sigun}개, 기준일 {period}")
    for s in sido_list:
        tot = sido_totals.get(s["code"])
        tot_str = f"{tot:,}명" if tot else "N/A"
        print(f"    {s['name']}: {len(s['sigun_list'])}개 (전체 {tot_str})")

    all_records = []

    for sido in sido_list:
        sido_name = sido["name"]
        sido_code = sido["code"]
        sigun_count = len(sido["sigun_list"])
        sido_total = sido_totals.get(sido_code)

        print(f"\n=== {sido_name} ({sigun_count}개) ===")
        env, _ = safe("environment", fetch_environment, keys["AIRKOREA_KEY"], sido["airkorea"], sido["sigun_list"],
                      default={"_avg": None, "_per_lawd": {}, "_measured_at": None})
        med, _ = safe("medical",     fetch_medical,     keys["HIRA_KEY"],     sido["hira_cds"], sido["sigun_list"],
                      default={"_total": 0, "_per_lawd": {}})
        edu, _ = safe("education",   fetch_education,   keys["NEIS_KEY"],     sido["neis_atpt"], sido["sigun_list"],
                      default={"_total": 0, "_per_lawd": {}})

        for i, sigun in enumerate(sido["sigun_list"], 1):
            lawd_cd = sigun["lawd_cd"]
            print(f"  [{i:2d}/{sigun_count}] {sigun['full_name']} ({lawd_cd})", flush=True)
            trade, _ = safe("    trade", fetch_real_estate_trade, keys["MOLIT_TRADE_KEY"], lawd_cd, default={})
            rent,  _ = safe("    rent",  fetch_real_estate_rent,  keys["MOLIT_RENT_KEY"],  lawd_cd, default={})

            pop_record = pop_by_lawd.get(lawd_cd, {})
            sgg_pop = pop_record.get("total")
            share = round(sgg_pop / sido_total * 100, 2) if sgg_pop and sido_total else None

            record = {
                "slug": sigun["slug"],
                "name": sigun["short_label"],
                "name_full": f"{sido_name} {sigun['full_name']}",
                "sido_code": sido_code,
                "sido_name": sido_name,
                "level": "sigungu",
                "lawd_cd": lawd_cd,
                "fetched_at": fetched_at,
                "sections": {
                    "real_estate_trade": trade,
                    "real_estate_rent": rent,
                    "environment": {
                        "sido_avg": env.get("_avg"),
                        "seoul_avg": env.get("_avg") if sido_code == "seoul" else None,
                        "gu_station": env.get("_per_lawd", {}).get(lawd_cd),
                        "gangnam_station": env.get("_per_lawd", {}).get(lawd_cd),
                        "measured_at": env.get("_measured_at"),
                    },
                    "medical": med.get("_per_lawd", {}).get(lawd_cd, {"sgg_count": 0, "by_type": {}}),
                    "education": edu.get("_per_lawd", {}).get(lawd_cd, {"sgg_count": 0, "by_type": {}}),
                    "population": {
                        "table_id": "DT_1B040A3",
                        "table_name": "행정구역(시군구)별/성별 인구수",
                        "period": pop_record.get("period") or period,
                        "sgg_total": sgg_pop,
                        "gangnam_total": sgg_pop,
                        "sido_total": sido_total,
                        "seoul_total": sido_total if sido_code == "seoul" else None,
                        "share_of_sido_pct": share,
                        "share_of_seoul_pct": share if sido_code == "seoul" else None,
                    },
                },
                "errors": [],
            }
            all_records.append(record)

    OUTPUT_INTEGRATED.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": fetched_at,
        "sido_list": [{"code": s["code"], "name": s["name"], "count": len(s["sigun_list"])} for s in sido_list],
        "total_count": len(all_records),
        "records": all_records,
    }
    OUTPUT_INTEGRATED.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 통합 저장: {OUTPUT_INTEGRATED} ({len(all_records)}개 시군구)")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 페치 결과\n\n- 총 시도: {len(sido_list)}\n- 총 시군구: {len(all_records)}\n\n")
            for sido in sido_list:
                count = sum(1 for r in all_records if r["sido_code"] == sido["code"])
                pop = sido_totals.get(sido["code"])
                pop_str = f"{pop:,}명" if pop else "—"
                f.write(f"- **{sido['name']}**: {count}개 시군구, 인구 {pop_str}\n")


if __name__ == "__main__":
    main()
