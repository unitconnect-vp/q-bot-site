#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q렌즈 동네 카드 — 페치 v4 (전국 17개 시도 자동화)"""

import os
import sys
import re
import json
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# 시도 메타: prefix(2자리) → (full_name, sido_slug, airkorea_sido, hira_sido_cds, neis_atpt)
SIDO_META = {
    "11": ("서울특별시", "seoul",     "서울", ["110000"], "B10"),
    "26": ("부산광역시", "busan",     "부산", ["210000", "260000"], "C10"),
    "27": ("대구광역시", "daegu",     "대구", ["220000", "270000"], "D10"),
    "28": ("인천광역시", "incheon",   "인천", ["230000", "280000"], "E10"),
    "29": ("광주광역시", "gwangju",   "광주", ["240000", "290000"], "F10"),
    "30": ("대전광역시", "daejeon",   "대전", ["250000", "300000"], "G10"),
    "31": ("울산광역시", "ulsan",     "울산", ["310000"], "H10"),
    "36": ("세종특별자치시", "sejong","세종", ["360000", "410000"], "I10"),
    "41": ("경기도", "gyeonggi",      "경기", ["310000", "410000"], "J10"),
    "43": ("충청북도", "chungbuk",    "충북", ["330000", "430000"], "M10"),
    "44": ("충청남도", "chungnam",    "충남", ["340000", "440000"], "N10"),
    "46": ("전라남도", "jeonnam",     "전남", ["360000", "460000"], "Q10"),
    "47": ("경상북도", "gyeongbuk",   "경북", ["370000", "470000"], "R10"),
    "48": ("경상남도", "gyeongnam",   "경남", ["380000", "480000"], "S10"),
    "50": ("제주특별자치도", "jeju",  "제주", ["390000", "500000"], "T10"),
    "51": ("강원특별자치도", "gangwon","강원", ["420000", "510000"], "K10"),
    "52": ("전북특별자치도", "jeonbuk","전북", ["350000", "450000"], "P10"),
}

OUTPUT_INTEGRATED = Path("town/data/all.json")
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


def make_slug_from_eng(c1_eng, lawd_cd):
    """
    KOSIS c1_eng → 슬러그 변환.
    - 일반: "Gangnam-gu" → "gangnam"
    - 분구(부모 시 결합형): "Hwaseong-si Manse-gu" → "manse"
      (KOSIS가 신규 분구를 부모-자식 결합 영문으로 반환하는 경우 대응)
    """
    s = (c1_eng or "").lower().strip()
    # 부모-자식 결합형: 공백으로 토큰 분리하면 마지막 토큰이 분구 자체 명칭
    # ex) "hwaseong-si manse-gu" → ["hwaseong-si", "manse-gu"] → "manse-gu"
    if " " in s:
        s = s.split()[-1]
    for suffix in ["-gu", "-si", "-gun", "-do", "_si"]:
        if s.endswith(suffix):
            s = s[:-len(suffix)]
            break
    s = re.sub(r"[^a-z0-9\-]", "", s)
    if not s:
        s = lawd_cd
    return s


def make_display_label(c1_nm, parent_si_name=None):
    if parent_si_name:
        si_short = parent_si_name.rstrip("시")
        gu_short = c1_nm.rstrip("구")
        return f"{si_short} {gu_short}"
    return c1_nm


def fetch_kosis_and_build_sigun_list(key):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList", "apiKey": key, "itmId": "T20", "objL1": "ALL",
        "format": "json", "jsonVD": "Y", "prdSe": "M", "newEstPrdCnt": "1",
        "orgId": "101", "tblId": "DT_1B040A3",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    j = r.json()

    if not isinstance(j, list):
        raise RuntimeError(f"KOSIS unexpected response: {str(j)[:200]}")

    sido_endings = ("도", "특별시", "광역시", "특별자치도", "특별자치시")
    sido_totals = {}
    period = None
    raw_sigun_rows = []

    for row in j:
        c1 = (row.get("C1") or "").strip()
        c1_nm = (row.get("C1_NM") or "").strip()
        c1_eng = (row.get("C1_NM_ENG") or "").strip()
        dt = to_int_or_none(row.get("DT"))
        if not period:
            period = row.get("PRD_DE")

        if c1_nm.endswith(sido_endings) and len(c1) <= 2:
            sido_totals[c1] = {"name": c1_nm, "total": dt}
            continue
        if c1_nm == "전국" or "출장소" in c1_nm:
            continue
        if len(c1) == 5:
            raw_sigun_rows.append({
                "lawd_cd": c1, "c1_nm": c1_nm, "c1_eng": c1_eng,
                "total": dt, "period": row.get("PRD_DE"), "sido_prefix": c1[:2],
            })

    # 분구 우선: 4자리 prefix 그룹화 → 통합시(끝0+"시") 제외
    groups = {}
    for r in raw_sigun_rows:
        groups.setdefault(r["lawd_cd"][:4], []).append(r)

    parent_si_for_group = {}
    for g_key, rows in groups.items():
        if len(rows) > 1:
            si_row = next((x for x in rows if x["lawd_cd"][-1] == "0" and x["c1_nm"].endswith("시")), None)
            if si_row:
                parent_si_for_group[g_key] = si_row["c1_nm"]

    filtered = []
    for g_key, rows in groups.items():
        if len(rows) > 1 and g_key in parent_si_for_group:
            filtered.extend([r for r in rows if not (r["lawd_cd"][-1] == "0" and r["c1_nm"].endswith("시"))])
        else:
            filtered.extend(rows)

    sigun_list = []
    per_lawd = {}
    for r in filtered:
        prefix = r["sido_prefix"]
        if prefix not in SIDO_META:
            continue
        meta = SIDO_META[prefix]
        sido_name = meta[0]
        sido_slug = meta[1]

        g_key = r["lawd_cd"][:4]
        parent_si = parent_si_for_group.get(g_key)
        display = make_display_label(r["c1_nm"], parent_si)

        if parent_si:
            full_name = f"{sido_name} {parent_si} {r['c1_nm']}"
        else:
            full_name = f"{sido_name} {r['c1_nm']}"

        slug_short = make_slug_from_eng(r["c1_eng"], r["lawd_cd"])
        slug = f"{sido_slug}/{slug_short}"

        sigun_list.append((r["lawd_cd"], full_name, display, slug, prefix))
        per_lawd[r["lawd_cd"]] = {"total": r["total"], "period": r["period"], "sido_name": sido_name}

    return sigun_list, {"_per_lawd": per_lawd, "_sido_totals": sido_totals, "_period": period}



def fetch_population_age_5y(key, lawd_cds):
    """
    KOSIS DT_1B04005N — 행정구역(시군구)별/5세별 인구.
    - 페르소나 매칭(20대·30대·40대·...·은퇴 비율) 인풋
    - 가중치 v1의 "인구 활력" 지표
    
    Returns:
      {lawd_cd: {"total": int, "by_age_band": {"20s": int, "30s": int, ...},
                 "shares": {"20s": float, ...}, "median_age_band": "30s"}}
    """
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList", "apiKey": key, "itmId": "T20",
        "objL1": "ALL", "format": "json", "jsonVD": "Y",
        "prdSe": "Y", "newEstPrdCnt": "1",
        "orgId": "101", "tblId": "DT_1B04005N",
    }
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        j = r.json()
    except Exception as e:
        return {}
    
    if not isinstance(j, list):
        return {}
    
    # 5세 단위를 10세 단위 밴드로 묶기 — 페르소나 매칭에 적합
    # KOSIS C2 코드: 0~4세=0, 5~9=1, ..., 80+=16
    band_map = {
        "0": "under10", "1": "under10",
        "2": "10s", "3": "10s",
        "4": "20s", "5": "20s",
        "6": "30s", "7": "30s",
        "8": "40s", "9": "40s",
        "10": "50s", "11": "50s",
        "12": "60s", "13": "60s",
        "14": "70s", "15": "70s",
        "16": "80plus",
    }
    
    target_lawd = set(lawd_cds)
    result = {}  # lawd_cd → {total, by_age_band, shares}
    
    for row in j:
        c1 = (row.get("C1") or "").strip()
        c2 = (row.get("C2") or "").strip()
        if c1 not in target_lawd or c2 not in band_map:
            continue
        dt = to_int_or_none(row.get("DT"))
        if dt is None:
            continue
        band = band_map[c2]
        result.setdefault(c1, {"by_age_band": {}, "total": 0})
        result[c1]["by_age_band"][band] = result[c1]["by_age_band"].get(band, 0) + dt
        result[c1]["total"] += dt
    
    # 비율 산출
    for cd, r in result.items():
        total = r["total"] or 1
        r["shares"] = {b: round(v / total * 100, 2) for b, v in r["by_age_band"].items()}
    
    return result


def fetch_pm25_yearly(key):
    """
    KOSIS DT_106N_03_0200145 — 미세먼지(PM2.5) 월별 도시별 대기오염도
    최근 12개월 페치 → 지역별 1년 평균 산출
    """
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList", "apiKey": key,
        "itmId": "ALL",
        "objL1": "ALL", "format": "json", "jsonVD": "Y",
        "prdSe": "M", "newEstPrdCnt": "12",
        "orgId": "106", "tblId": "DT_106N_03_0200145",
    }
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        j = r.json()
    except Exception as e:
        print(f"  [PM2.5 yearly] 페치 실패: {e}")
        return {}
    if not isinstance(j, list) or not j:
        print(f"  [PM2.5 yearly] 응답 형식 예상 외")
        return {}
    print(f"  [PM2.5 yearly] 샘플 row: {dict(list(j[0].items())[:8])}")
    by_region = {}
    for row in j:
        region = (row.get("C1_NM") or row.get("C2_NM") or row.get("C3_NM") or "").strip()
        if not region:
            continue
        dt_raw = row.get("DT")
        if not dt_raw or dt_raw in ("-", "..", ""):
            continue
        try:
            val = float(dt_raw)
        except (ValueError, TypeError):
            continue
        prd = (row.get("PRD_DE") or "").strip()
        if region not in by_region:
            by_region[region] = {"sum": 0.0, "count": 0, "periods": []}
        by_region[region]["sum"] += val
        by_region[region]["count"] += 1
        by_region[region]["periods"].append(prd)
    result = {}
    for name, info in by_region.items():
        if info["count"] == 0:
            continue
        periods = sorted(info["periods"])
        result[name] = {
            "pm25_yearly": round(info["sum"] / info["count"], 1),
            "period": f"{periods[0]}~{periods[-1]}",
            "month_count": info["count"],
        }
    print(f"  [PM2.5 yearly] 지역 {len(result)}개 매칭")
    return result


def fetch_real_estate_trade(key, lawd_cd):
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    all_items = []
    months_used = []
    monthly_breakdown = []  # 시계열 추세용
    for m in range(12):  # 3 → 12개월
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
        month_items = []
        for item in items:
            d = {child.tag: (child.text or "").strip() for child in item}
            month_items.append(d)
            all_items.append(d)
        if month_items:
            months_used.append(ym)
            # 월별 통계 계산
            mp, md = [], []
            for it in month_items:
                amt = parse_amount_man(it.get("dealAmount", "0"))
                try:
                    area = float(it.get("excluUseAr", 0))
                except (ValueError, TypeError):
                    continue
                if area > 0 and amt > 0:
                    mp.append(amt / m2_to_pyeong(area))
                    md.append(amt)
            monthly_breakdown.append({
                "ym": ym,
                "count": len(month_items),
                "median_price_per_pyeong_man": int(statistics.median(mp)) if mp else None,
                "median_deal_amount_man": int(statistics.median(md)) if md else None,
            })

    if not all_items:
        return {"status": "no_data", "count": 0, "period_months": months_used, "monthly_breakdown": []}

    # 직전 3개월 합산 통계 (기존 호환)
    recent_3 = [m for m in monthly_breakdown[:3]]
    recent_items = [it for it in all_items if any(m["ym"] == it.get("dealYear", "") + str(int(it.get("dealMonth", "1"))).zfill(2) or m["ym"] == get_recent_yyyymm(0) for m in recent_3)]
    # 단순화: 전체 12개월 통계 사용 (overall)
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

    # 정렬: 오래된 → 최근 (차트 왼→오 시간순)
    monthly_breakdown.sort(key=lambda x: x["ym"])

    # 직전 3개월 중앙값을 카드의 대표 통계로 (기존 동작 유지)
    last3_prices = [p for m in monthly_breakdown[-3:] for p in [m["median_price_per_pyeong_man"]] if p]
    last3_deals = [p for m in monthly_breakdown[-3:] for p in [m["median_deal_amount_man"]] if p]

    return {
        "count": len(all_items),
        "median_price_per_pyeong_man": int(statistics.median(last3_prices)) if last3_prices else (int(statistics.median(pyeong_prices)) if pyeong_prices else None),
        "mean_price_per_pyeong_man": int(statistics.mean(pyeong_prices)) if pyeong_prices else None,
        "median_deal_amount_man": int(statistics.median(last3_deals)) if last3_deals else (int(statistics.median(deal_prices)) if deal_prices else None),
        "period_months": months_used,
        "monthly_count_avg": round(len(all_items) / max(len(months_used), 1), 1),
        "monthly_breakdown": monthly_breakdown,  # 신규: 시계열 추세
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


def fetch_environment(key, sido_name_for_air):
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {"serviceKey": key, "returnType": "json", "numOfRows": "200", "pageNo": "1", "sidoName": sido_name_for_air, "ver": "1.0"}
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        j = r.json()
    except (requests.RequestException, json.JSONDecodeError):
        return {"_avg": None, "_measured_at": None}

    items = j.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return {"_avg": None, "_measured_at": None}

    pm10s = [v for v in (to_int_or_none(it.get("pm10Value")) for it in items) if v is not None]
    pm25s = [v for v in (to_int_or_none(it.get("pm25Value")) for it in items) if v is not None]
    avg = {
        "pm10": int(statistics.mean(pm10s)) if pm10s else None,
        "pm25": int(statistics.mean(pm25s)) if pm25s else None,
        "station_count": len(items),
    }
    return {"_avg": avg, "_measured_at": items[0].get("dataTime") if items else None}


def fetch_medical(key, sido_cds, sigun_lawd_list, sigun_full_names):
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    final_hosp = []
    for sido_cd in sido_cds:
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
    for lawd_cd in sigun_lawd_list:
        full_name = sigun_full_names.get(lawd_cd, "")
        last_token = full_name.split()[-1] if full_name else ""
        gu_hosps = [h for h in final_hosp if last_token and last_token in (h.get("addr", "") or "")]
        type_counts = {}
        for h in gu_hosps:
            t = h.get("clCdNm", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_lawd[lawd_cd] = {"sgg_count": len(gu_hosps), "by_type": type_counts}

    return {"_total": len(final_hosp), "_per_lawd": per_lawd}


def fetch_education(key, atpt_code, sigun_lawd_list, sigun_full_names):
    url = "https://open.neis.go.kr/hub/schoolInfo"
    all_schools = []
    for page in range(1, 8):
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
    for lawd_cd in sigun_lawd_list:
        full_name = sigun_full_names.get(lawd_cd, "")
        last_token = full_name.split()[-1] if full_name else ""
        gu_schools = [s for s in all_schools if last_token and last_token in (s.get("ORG_RDNMA", "") or "")]
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

    print("[KOSIS] 전국 시군구 자동 추출")
    sigun_list, pop_data = fetch_kosis_and_build_sigun_list(keys["KOSIS_KEY"])
    print(f"  추출: {len(sigun_list)}개")

    print("[KOSIS] 5세별 연령 분포 페치")
    all_lawd_cds = [item[0] for item in sigun_list]
    pop_age_data = fetch_population_age_5y(keys["KOSIS_KEY"], all_lawd_cds)
    print(f"  매칭: {len(pop_age_data)}개 시군구")

    print("[KOSIS] PM2.5 1년 평균 페치 (DT_106N_03_0200145)")
    pm25_yearly = fetch_pm25_yearly(keys["KOSIS_KEY"])

    by_sido = {}
    sigun_full_names = {}
    for lawd_cd, full_name, display, slug, prefix in sigun_list:
        by_sido.setdefault(prefix, []).append((lawd_cd, full_name, display, slug))
        sigun_full_names[lawd_cd] = full_name

    for prefix in sorted(by_sido.keys()):
        meta = SIDO_META[prefix]
        print(f"    {meta[0]}: {len(by_sido[prefix])}개")

    all_records = []
    for prefix in sorted(by_sido.keys()):
        meta = SIDO_META[prefix]
        sido_full_name, sido_slug, airkorea_sido, hira_cds, neis_atpt = meta
        sigun_in_sido = by_sido[prefix]
        sigun_count = len(sigun_in_sido)
        sido_total = pop_data["_sido_totals"].get(prefix, {}).get("total")

        print(f"\n=== {sido_full_name} ({sigun_count}개) ===")
        env, _ = safe("environment", fetch_environment, keys["AIRKOREA_KEY"], airkorea_sido,
                      default={"_avg": None, "_measured_at": None})
        med, _ = safe("medical", fetch_medical, keys["HIRA_KEY"], hira_cds,
                      [r[0] for r in sigun_in_sido], sigun_full_names,
                      default={"_total": 0, "_per_lawd": {}})
        edu, _ = safe("education", fetch_education, keys["NEIS_KEY"], neis_atpt,
                      [r[0] for r in sigun_in_sido], sigun_full_names,
                      default={"_total": 0, "_per_lawd": {}})

        for i, (lawd_cd, full_name, display, slug) in enumerate(sigun_in_sido, 1):
            print(f"  [{i:2d}/{sigun_count}] {full_name}", flush=True)
            trade, _ = safe("    trade", fetch_real_estate_trade, keys["MOLIT_TRADE_KEY"], lawd_cd, default={})
            rent,  _ = safe("    rent",  fetch_real_estate_rent,  keys["MOLIT_RENT_KEY"],  lawd_cd, default={})

            pop_record = pop_data["_per_lawd"].get(lawd_cd, {})
            sgg_pop = pop_record.get("total")
            share = round(sgg_pop / sido_total * 100, 2) if sgg_pop and sido_total else None

            record = {
                "slug": slug,
                "name": display,
                "name_full": full_name,
                "sido_code": sido_slug,
                "sido_name": sido_full_name,
                "level": "sigungu",
                "lawd_cd": lawd_cd,
                "fetched_at": fetched_at,
                "sections": {
                    "real_estate_trade": trade,
                    "real_estate_rent": rent,
                    "environment": {
                        "sido_avg": env.get("_avg"),
                        "seoul_avg": env.get("_avg") if sido_slug == "seoul" else None,
                        "gu_station": None,
                        "gangnam_station": None,
                        "measured_at": env.get("_measured_at"),
                        "pm25_yearly": (
                            pm25_yearly.get(sido_full_name)
                            or pm25_yearly.get(sido_full_name.replace("특별시", "").replace("광역시", "").replace("특별자치시", "").replace("특별자치도", "").replace("도", "").strip())
                        ),
                    },
                    "medical": med.get("_per_lawd", {}).get(lawd_cd, {"sgg_count": 0, "by_type": {}}),
                    "education": edu.get("_per_lawd", {}).get(lawd_cd, {"sgg_count": 0, "by_type": {}}),
                    "population": {
                        "table_id": "DT_1B040A3",
                        "table_name": "행정구역(시군구)별/성별 인구수",
                        "period": pop_record.get("period") or pop_data.get("_period"),
                        "sgg_total": sgg_pop,
                        "gangnam_total": sgg_pop,
                        "sido_total": sido_total,
                        "seoul_total": sido_total if sido_slug == "seoul" else None,
                        "share_of_sido_pct": share,
                        "share_of_seoul_pct": share if sido_slug == "seoul" else None,
                    },
                    "population_age": pop_age_data.get(lawd_cd, {
                        "table_id": "DT_1B04005N",
                        "by_age_band": {},
                        "shares": {},
                        "total": 0,
                    }),
                },
                "errors": [],
            }
            all_records.append(record)

    OUTPUT_INTEGRATED.parent.mkdir(parents=True, exist_ok=True)
    sido_summary = []
    for prefix in sorted(by_sido.keys()):
        meta = SIDO_META[prefix]
        sido_summary.append({"code": meta[1], "name": meta[0], "count": len(by_sido[prefix])})

    payload = {
        "fetched_at": fetched_at,
        "sido_list": sido_summary,
        "total_count": len(all_records),
        "records": all_records,
    }
    OUTPUT_INTEGRATED.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 저장: {OUTPUT_INTEGRATED} ({len(all_records)}개)")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 페치 결과 (전국)\n\n- 총 시군구: {len(all_records)}\n\n")
            for s in sido_summary:
                f.write(f"- **{s['name']}**: {s['count']}개\n")


if __name__ == "__main__":
    main()
