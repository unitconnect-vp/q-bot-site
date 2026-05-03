#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q렌즈 동네 카드 — 페치 v4 (전국 17개 시도)
KOSIS 응답에서 모든 시군구를 동적 발견 + LAWD_CD를 slug로 사용.
"""

import os
import sys
import json
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

SIDO_BY_PREFIX = {
    "11": {"code": "seoul",     "name": "서울특별시",     "airkorea": "서울", "hira_cds": ["110000"],            "neis": "B10"},
    "26": {"code": "busan",     "name": "부산광역시",     "airkorea": "부산", "hira_cds": ["210000", "260000"],  "neis": "C10"},
    "27": {"code": "daegu",     "name": "대구광역시",     "airkorea": "대구", "hira_cds": ["220000", "270000"],  "neis": "D10"},
    "28": {"code": "incheon",   "name": "인천광역시",     "airkorea": "인천", "hira_cds": ["230000", "280000"],  "neis": "E10"},
    "29": {"code": "gwangju",   "name": "광주광역시",     "airkorea": "광주", "hira_cds": ["240000", "290000"],  "neis": "F10"},
    "30": {"code": "daejeon",   "name": "대전광역시",     "airkorea": "대전", "hira_cds": ["250000", "300000"],  "neis": "G10"},
    "31": {"code": "ulsan",     "name": "울산광역시",     "airkorea": "울산", "hira_cds": ["260000", "310000"],  "neis": "H10"},
    "36": {"code": "sejong",    "name": "세종특별자치시", "airkorea": "세종", "hira_cds": ["290000", "360000"],  "neis": "I10"},
    "41": {"code": "gyeonggi",  "name": "경기도",         "airkorea": "경기", "hira_cds": ["310000", "410000"],  "neis": "J10"},
    "43": {"code": "chungbuk",  "name": "충청북도",       "airkorea": "충북", "hira_cds": ["330000", "430000"],  "neis": "M10"},
    "44": {"code": "chungnam",  "name": "충청남도",       "airkorea": "충남", "hira_cds": ["340000", "440000"],  "neis": "N10"},
    "46": {"code": "jeonnam",   "name": "전라남도",       "airkorea": "전남", "hira_cds": ["360000", "460000"],  "neis": "Q10"},
    "47": {"code": "gyeongbuk", "name": "경상북도",       "airkorea": "경북", "hira_cds": ["370000", "470000"],  "neis": "R10"},
    "48": {"code": "gyeongnam", "name": "경상남도",       "airkorea": "경남", "hira_cds": ["380000", "480000"],  "neis": "S10"},
    "50": {"code": "jeju",      "name": "제주특별자치도", "airkorea": "제주", "hira_cds": ["390000", "500000"],  "neis": "T10"},
    "51": {"code": "gangwon",   "name": "강원특별자치도", "airkorea": "강원", "hira_cds": ["320000", "420000", "510000"], "neis": "K10"},
    "52": {"code": "jeonbuk",   "name": "전북특별자치도", "airkorea": "전북", "hira_cds": ["350000", "450000", "520000"], "neis": "P10"},
}

SIDO_NAMES_SET = {v["name"] for v in SIDO_BY_PREFIX.values()} | {"강원도", "전라북도", "세종시"}

OUTPUT_INTEGRATED = Path("town/data/seoul.json")
TIMEOUT = 30


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


def fetch_kosis_population(key):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList", "apiKey": key, "itmId": "T20", "objL1": "ALL",
        "format": "json", "jsonVD": "Y", "prdSe": "M", "newEstPrdCnt": "1",
        "orgId": "101", "tblId": "DT_1B040A3",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    j = r.json()
    if not isinstance(j, list):
        return [], {}, {}, None

    period = None
    sido_totals = {}
    discovered = []
    pop_per_lawd = {}

    for row in j:
        c1 = (row.get("C1", "") or "").strip()
        c1_nm = (row.get("C1_NM", "") or "").strip()
        if not period:
            period = row.get("PRD_DE")

        if c1_nm in SIDO_NAMES_SET:
            normalized = c1_nm.replace("강원도", "강원특별자치도").replace("전라북도", "전북특별자치도")
            if normalized == "세종시":
                normalized = "세종특별자치시"
            sido_totals[normalized] = to_int_or_none(row.get("DT"))

        if len(c1) == 5 and c1.isdigit():
            prefix = c1[:2]
            if prefix in SIDO_BY_PREFIX:
                discovered.append((c1, c1_nm, prefix))
                pop_per_lawd[c1] = {
                    "total": to_int_or_none(row.get("DT")),
                    "name": c1_nm,
                    "period": row.get("PRD_DE"),
                }

    return discovered, pop_per_lawd, sido_totals, period


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


def fetch_environment(key, sido_airkorea, sigun_lawds):
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {"serviceKey": key, "returnType": "json", "numOfRows": "300", "pageNo": "1", "sidoName": sido_airkorea, "ver": "1.0"}
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
    for lawd_cd, c1_nm in sigun_lawds:
        keyword = c1_nm.replace("구", "").replace("군", "").replace("시", "").strip()
        if not keyword or len(keyword) < 2:
            continue
        for it in items:
            station = it.get("stationName", "") or ""
            if keyword in station:
                per_lawd[lawd_cd] = {
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


def fetch_medical(key, hira_cds, sigun_lawds):
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    final_hosp = []

    for sido_cd in hira_cds:
        all_hosp = []
        for page in range(1, 16):
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
            break

    per_lawd = {}
    for lawd_cd, c1_nm in sigun_lawds:
        gu_hosps = [h for h in final_hosp if c1_nm in (h.get("addr", "") or "")]
        type_counts = {}
        for h in gu_hosps:
            t = h.get("clCdNm", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_lawd[lawd_cd] = {"sgg_count": len(gu_hosps), "by_type": type_counts}

    return {"_total": len(final_hosp), "_per_lawd": per_lawd}


def fetch_education(key, atpt_code, sigun_lawds):
    url = "https://open.neis.go.kr/hub/schoolInfo"
    all_schools = []
    for page in range(1, 10):
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
    for lawd_cd, c1_nm in sigun_lawds:
        gu_schools = [s for s in all_schools if c1_nm in (s.get("ORG_RDNMA", "") or "")]
        type_counts = {}
        for s in gu_schools:
            t = s.get("SCHUL_KND_SC_NM", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_lawd[lawd_cd] = {"sgg_count": len(gu_schools), "by_type": type_counts}

    return {"_total": len(all_schools), "_per_lawd": per_lawd}


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

    print("[STEP 1] KOSIS 시군구 발견 + 인구")
    discovered, pop_per_lawd, sido_totals, period = fetch_kosis_population(keys["KOSIS_KEY"])
    print(f"  발견: {len(discovered)}개 시군구, {len(sido_totals)}개 시도")

    by_prefix = {}
    for lawd_cd, c1_nm, prefix in discovered:
        by_prefix.setdefault(prefix, []).append((lawd_cd, c1_nm))
    print(f"  시도 prefix: {sorted(by_prefix.keys())}")

    all_records = []
    sido_meta_used = []

    for prefix in sorted(by_prefix.keys()):
        sido_meta = SIDO_BY_PREFIX[prefix]
        sido_name = sido_meta["name"]
        sigun_lawds = by_prefix[prefix]
        sido_total_pop = sido_totals.get(sido_name)

        print(f"\n=== {sido_name} ({prefix}, {len(sigun_lawds)}개) ===")
        env, _ = safe("environment", fetch_environment, keys["AIRKOREA_KEY"], sido_meta["airkorea"], sigun_lawds,
                      default={"_avg": None, "_per_lawd": {}, "_measured_at": None})
        med, _ = safe("medical",     fetch_medical,     keys["HIRA_KEY"],     sido_meta["hira_cds"],   sigun_lawds,
                      default={"_total": 0, "_per_lawd": {}})
        edu, _ = safe("education",   fetch_education,   keys["NEIS_KEY"],     sido_meta["neis"],       sigun_lawds,
                      default={"_total": 0, "_per_lawd": {}})

        sido_meta_used.append({
            "code": sido_meta["code"],
            "name": sido_name,
            "prefix": prefix,
            "count": len(sigun_lawds),
        })

        for i, (lawd_cd, c1_nm) in enumerate(sigun_lawds, 1):
            print(f"  [{i:2d}/{len(sigun_lawds)}] {c1_nm} ({lawd_cd})", flush=True)
            trade, _ = safe("    trade", fetch_real_estate_trade, keys["MOLIT_TRADE_KEY"], lawd_cd, default={})
            rent,  _ = safe("    rent",  fetch_real_estate_rent,  keys["MOLIT_RENT_KEY"],  lawd_cd, default={})

            sgg_pop = (pop_per_lawd.get(lawd_cd) or {}).get("total")
            share = round(sgg_pop / sido_total_pop * 100, 2) if sgg_pop and sido_total_pop else None

            record = {
                "slug": lawd_cd,
                "lawd_cd": lawd_cd,
                "name": c1_nm,
                "name_full": f"{sido_name} {c1_nm}",
                "sido_code": sido_meta["code"],
                "sido_name": sido_name,
                "sido_prefix": prefix,
                "level": "sigungu",
                "fetched_at": fetched_at,
                "sections": {
                    "real_estate_trade": trade,
                    "real_estate_rent": rent,
                    "environment": {
                        "sido_avg": env.get("_avg"),
                        "gu_station": env.get("_per_lawd", {}).get(lawd_cd),
                        "measured_at": env.get("_measured_at"),
                    },
                    "medical": med.get("_per_lawd", {}).get(lawd_cd, {"sgg_count": 0, "by_type": {}}),
                    "education": edu.get("_per_lawd", {}).get(lawd_cd, {"sgg_count": 0, "by_type": {}}),
                    "population": {
                        "table_id": "DT_1B040A3",
                        "table_name": "행정구역(시군구)별/성별 인구수",
                        "period": (pop_per_lawd.get(lawd_cd) or {}).get("period") or period,
                        "sgg_total": sgg_pop,
                        "sido_total": sido_total_pop,
                        "share_of_sido_pct": share,
                    },
                },
                "errors": [],
            }
            all_records.append(record)

    OUTPUT_INTEGRATED.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": fetched_at,
        "sido_list": sido_meta_used,
        "total_count": len(all_records),
        "records": all_records,
    }
    OUTPUT_INTEGRATED.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 저장: {OUTPUT_INTEGRATED} ({len(all_records)}개)")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 페치 결과 (전국)\n\n- 총 시군구: {len(all_records)}\n- 시도: {len(sido_meta_used)}\n\n")
            f.write("| 시도 | 시군구 | 인구 |\n|---|---|---|\n")
            for sido in sido_meta_used:
                total = sido_totals.get(sido["name"])
                total_str = f"{total:,}명" if total else "—"
                f.write(f"| {sido['name']} | {sido['count']} | {total_str} |\n")


if __name__ == "__main__":
    main()
