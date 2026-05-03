#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q렌즈 동네 카드 — 페치 스크립트 v3 (서울 + 경기)
시도 단위로 그룹화. 향후 부산·인천 등 추가 시 SIDO_LIST에 항목만 추가.
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
# 시도 메타데이터 + 시군구 매핑
# ─────────────────────────────────────────────────
SIDO_LIST = [
    {
        "sido_name": "서울특별시",
        "sido_short": "서울",
        "sido_slug": "seoul",
        "airkorea_name": "서울",
        "hira_sido_cds": ["110000"],   # fallback 가능하도록 리스트
        "neis_atpt": "B10",
        "sgg_list": [
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
        ],
    },
    {
        "sido_name": "경기도",
        "sido_short": "경기",
        "sido_slug": "gyeonggi",
        "airkorea_name": "경기",
        "hira_sido_cds": ["310000", "410000"],  # 둘 중 하나
        "neis_atpt": "J10",
        "sgg_list": [
            # 자치구 있는 시: 시명 + 구명
            ("41111", "수원시 장안구",   "suwon-jangan"),
            ("41113", "수원시 권선구",   "suwon-gwonseon"),
            ("41115", "수원시 팔달구",   "suwon-paldal"),
            ("41117", "수원시 영통구",   "suwon-yeongtong"),
            ("41131", "성남시 수정구",   "seongnam-sujeong"),
            ("41133", "성남시 중원구",   "seongnam-jungwon"),
            ("41135", "성남시 분당구",   "seongnam-bundang"),
            ("41171", "안양시 만안구",   "anyang-manan"),
            ("41173", "안양시 동안구",   "anyang-dongan"),
            ("41271", "안산시 상록구",   "ansan-sangrok"),
            ("41273", "안산시 단원구",   "ansan-danwon"),
            ("41281", "고양시 덕양구",   "goyang-deogyang"),
            ("41285", "고양시 일산동구", "goyang-ilsandong"),
            ("41287", "고양시 일산서구", "goyang-ilsanseo"),
            ("41461", "용인시 처인구",   "yongin-cheoin"),
            ("41463", "용인시 기흥구",   "yongin-giheung"),
            ("41465", "용인시 수지구",   "yongin-suji"),
            # 일반시 + 군
            ("41150", "의정부시",   "uijeongbu"),
            ("41190", "부천시",     "bucheon"),
            ("41210", "광명시",     "gwangmyeong"),
            ("41220", "평택시",     "pyeongtaek"),
            ("41250", "동두천시",   "dongducheon"),
            ("41290", "과천시",     "gwacheon"),
            ("41310", "구리시",     "guri"),
            ("41360", "남양주시",   "namyangju"),
            ("41370", "오산시",     "osan"),
            ("41390", "시흥시",     "siheung"),
            ("41410", "군포시",     "gunpo"),
            ("41430", "의왕시",     "uiwang"),
            ("41450", "하남시",     "hanam"),
            ("41480", "파주시",     "paju"),
            ("41500", "이천시",     "icheon"),
            ("41550", "안성시",     "anseong"),
            ("41570", "김포시",     "gimpo"),
            ("41590", "화성시",     "hwaseong"),
            ("41610", "광주시",     "gwangju-gg"),  # 경기 광주 (광주광역시와 구분)
            ("41630", "양주시",     "yangju"),
            ("41650", "포천시",     "pocheon"),
            ("41670", "여주시",     "yeoju"),
            ("41800", "연천군",     "yeoncheon"),
            ("41820", "가평군",     "gapyeong"),
            ("41830", "양평군",     "yangpyeong"),
        ],
    },
]

OUTPUT_INTEGRATED = Path("town/data/all.json")
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
# 자치구별 부동산 페치
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
# 시도 단위 공통 페치
# ─────────────────────────────────────────────────

def fetch_environment(key, sido_short):
    """시도별 실시간 측정 — 평균 + 시군구 측정소."""
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {
        "serviceKey": key, "returnType": "json",
        "numOfRows": "200", "pageNo": "1",
        "sidoName": sido_short, "ver": "1.0",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT)
    j = r.json()
    items = j.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return {"sido_avg": None, "per_gu": {}, "measured_at": None}

    pm10s = [v for v in (to_int_or_none(it.get("pm10Value")) for it in items) if v is not None]
    pm25s = [v for v in (to_int_or_none(it.get("pm25Value")) for it in items) if v is not None]
    sido_avg = {
        "pm10": int(statistics.mean(pm10s)) if pm10s else None,
        "pm25": int(statistics.mean(pm25s)) if pm25s else None,
        "station_count": len(items),
    }

    return {
        "sido_avg": sido_avg,
        "items": items,  # 후처리에서 자치구별 매칭
        "measured_at": items[0].get("dataTime"),
    }


def match_environment_for_sgg(env_data, sgg_name):
    """환경 데이터에서 자치구 매칭 (이름 기반)."""
    items = env_data.get("items", [])
    # 자치구명에서 핵심 지명 추출 (예: "수원시 영통구" → "영통", "강남구" → "강남")
    candidates = []
    parts = sgg_name.split()
    for p in parts:
        candidates.append(p.replace("구", "").replace("시", "").replace("군", ""))
    candidates = [c for c in candidates if c]

    for it in items:
        station = it.get("stationName", "") or ""
        for c in candidates:
            if c and c in station:
                return {
                    "station": station,
                    "pm10": to_int_or_none(it.get("pm10Value")),
                    "pm25": to_int_or_none(it.get("pm25Value")),
                }
    return None


def fetch_medical(key, hira_sido_cds):
    """HIRA 시도 단위 페치 — 여러 sido_cd fallback."""
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    for sido_cd in hira_sido_cds:
        all_hosp = []
        for page in range(1, 11):
            params = {
                "ServiceKey": key, "_type": "json",
                "numOfRows": "1000", "pageNo": str(page),
                "sidoCd": sido_cd,
            }
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
            return {"items": all_hosp, "sido_cd_used": sido_cd, "total": len(all_hosp)}
    return {"items": [], "sido_cd_used": None, "total": 0}


def match_medical_for_sgg(med_data, sgg_name):
    items = med_data.get("items", [])
    # "수원시 영통구" → "수원" + "영통구" 둘 다 포함되는 항목 매칭
    parts = sgg_name.split()
    if len(parts) > 1:
        # 시·구 분리: 둘 다 포함
        si, gu = parts[0], parts[1]
        gu_hosps = [h for h in items if si in (h.get("addr", "") or "") and gu in (h.get("addr", "") or "")]
    else:
        gu_hosps = [h for h in items if sgg_name in (h.get("addr", "") or "")]

    type_counts = {}
    for h in gu_hosps:
        t = h.get("clCdNm", "기타")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {"sgg_count": len(gu_hosps), "by_type": type_counts}


def fetch_education(key, atpt_code):
    """NEIS 시도교육청 단위 페치."""
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
    return {"items": all_schools, "total": len(all_schools)}


def match_education_for_sgg(edu_data, sgg_name):
    items = edu_data.get("items", [])
    parts = sgg_name.split()
    if len(parts) > 1:
        si, gu = parts[0], parts[1]
        gu_schools = [s for s in items if si in (s.get("ORG_RDNMA", "") or "") and gu in (s.get("ORG_RDNMA", "") or "")]
    else:
        gu_schools = [s for s in items if sgg_name in (s.get("ORG_RDNMA", "") or "")]

    type_counts = {}
    for s in gu_schools:
        t = s.get("SCHUL_KND_SC_NM", "기타")
        type_counts[t] = type_counts.get(t, 0) + 1
    return {"sgg_count": len(gu_schools), "by_type": type_counts}


def fetch_population_all(key):
    """KOSIS — 한 번 호출로 전국 시군구."""
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
        return {"items": [], "period": None}
    if not isinstance(j, list):
        return {"items": [], "period": None}

    # 디버그: 첫 5행 구조 출력
    print("  [KOSIS 응답 구조 — 첫 5행]")
    for row in j[:5]:
        print(f"    C1_NM={row.get('C1_NM')!r}, C2_NM={row.get('C2_NM')!r}, DT={row.get('DT')}")
    print(f"  총 {len(j)}행")

    return {"items": j, "period": j[0].get("PRD_DE") if j else None}


def match_population_for_sgg(pop_data, sgg_name, sido_name):
    items = pop_data.get("items", [])
    period = pop_data.get("period")
    parts = sgg_name.split()

    for row in items:
        c1_nm = (row.get("C1_NM") or "").strip()
        c2_nm = (row.get("C2_NM") or "").strip()
        full = (c1_nm + " " + c2_nm).strip()

        # 시도 합계 행 / 전국 행은 스킵
        if not c2_nm and c1_nm in (sido_name, "전국", "서울특별시", "경기도"):
            if c1_nm != sgg_name:
                continue

        if len(parts) > 1:
            # "수원시 영통구": 시·구 모두 포함
            si, gu = parts[0], parts[1]
            if si in full and gu in full:
                return {"sgg_total": to_int_or_none(row.get("DT")), "period": period}
        else:
            # 단일 자치구: 정확 매칭 우선
            if c2_nm == sgg_name or c1_nm == sgg_name:
                return {"sgg_total": to_int_or_none(row.get("DT")), "period": period}
            # substring 매칭 + 시도 검증
            if sgg_name in full:
                if sido_name in full or (c1_nm and c1_nm[:2] == sido_name[:2]):
                    return {"sgg_total": to_int_or_none(row.get("DT")), "period": period}

    return {"sgg_total": None, "period": period}


def get_sido_total(pop_data, sido_name):
    items = pop_data.get("items", [])
    for row in items:
        c1_nm = row.get("C1_NM", "") or ""
        c2_nm = row.get("C2_NM", "") or ""
        if c1_nm == sido_name and not c2_nm:
            return to_int_or_none(row.get("DT"))
    return None


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

    # 인구는 전국 한 번에
    print("[STEP 0] 인구 데이터 (KOSIS, 전국 한 번)")
    pop_data, _ = safe("population", fetch_population_all, keys["KOSIS_KEY"], default={"items": [], "period": None})

    sidos_output = []
    total_records = 0

    for sido in SIDO_LIST:
        print(f"\n[{sido['sido_name']}] 시도 단위 공통 페치")
        env_data, _ = safe("environment", fetch_environment, keys["AIRKOREA_KEY"], sido["sido_short"], default={"sido_avg": None, "items": [], "measured_at": None})
        med_data, _ = safe("medical",     fetch_medical,     keys["HIRA_KEY"],     sido["hira_sido_cds"], default={"items": [], "total": 0})
        edu_data, _ = safe("education",   fetch_education,   keys["NEIS_KEY"],     sido["neis_atpt"], default={"items": [], "total": 0})

        sido_total = get_sido_total(pop_data, sido["sido_name"])

        records = []
        sgg_list = sido["sgg_list"]
        print(f"\n[{sido['sido_name']}] 시군구별 부동산 페치 ({len(sgg_list)}개)")
        for i, (lawd_cd, name, slug) in enumerate(sgg_list, 1):
            print(f"  [{i:2d}/{len(sgg_list)}] {name} ({lawd_cd})", flush=True)
            trade, _ = safe("    trade", fetch_real_estate_trade, keys["MOLIT_TRADE_KEY"], lawd_cd, default={})
            rent, _  = safe("    rent",  fetch_real_estate_rent,  keys["MOLIT_RENT_KEY"],  lawd_cd, default={})

            pop_match = match_population_for_sgg(pop_data, name, sido["sido_name"])

            record = {
                "slug": f"{sido['sido_slug']}/{slug}",
                "sido_slug": sido["sido_slug"],
                "sido_name": sido["sido_name"],
                "name": name,
                "name_full": f"{sido['sido_name']} {name}",
                "level": "sgg",
                "lawd_cd": lawd_cd,
                "fetched_at": fetched_at,
                "sections": {
                    "real_estate_trade": trade,
                    "real_estate_rent": rent,
                    "environment": {
                        "sido_avg": env_data.get("sido_avg"),
                        "gu_station": match_environment_for_sgg(env_data, name),
                        "measured_at": env_data.get("measured_at"),
                    },
                    "medical": match_medical_for_sgg(med_data, name),
                    "education": match_education_for_sgg(edu_data, name),
                    "population": {
                        "table_id": "DT_1B040A3",
                        "table_name": "행정구역(시군구)별/성별 인구수",
                        "period": pop_match.get("period"),
                        "sgg_total": pop_match.get("sgg_total"),
                        "sido_total": sido_total,
                        "share_of_sido_pct": (
                            round(pop_match["sgg_total"] / sido_total * 100, 2)
                            if pop_match.get("sgg_total") and sido_total else None
                        ),
                    },
                },
                "errors": [],
            }
            records.append(record)
            total_records += 1

        sidos_output.append({
            "sido_name": sido["sido_name"],
            "sido_short": sido["sido_short"],
            "sido_slug": sido["sido_slug"],
            "sgg_count": len(records),
            "records": records,
        })

    # 통합 JSON 저장
    OUTPUT_INTEGRATED.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_INTEGRATED.write_text(
        json.dumps({
            "fetched_at": fetched_at,
            "total_sido": len(sidos_output),
            "total_sgg": total_records,
            "sidos": sidos_output,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n✓ 통합 저장: {OUTPUT_INTEGRATED}")
    print(f"  시도: {len(sidos_output)}개, 시군구: {total_records}개")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 페치 결과\n\n")
            f.write(f"- 시도: {len(sidos_output)}개\n")
            f.write(f"- 시군구: {total_records}개\n\n")
            for sido in sidos_output:
                f.write(f"\n## {sido['sido_name']} ({sido['sgg_count']}개)\n\n")
                f.write("| 자치구 | 매매 | 전세 | 의료 | 학교 | 인구 |\n")
                f.write("|---|---|---|---|---|---|\n")
                for r in sido["records"]:
                    t = r["sections"]["real_estate_trade"]
                    rt = r["sections"]["real_estate_rent"]
                    m = r["sections"]["medical"]
                    e = r["sections"]["education"]
                    p = r["sections"]["population"]
                    f.write(
                        f"| {r['name']} | {t.get('count', '—')}건 "
                        f"| {rt.get('jeonse_count', '—')}건 "
                        f"| {m.get('sgg_count', 0)} "
                        f"| {e.get('sgg_count', 0)} "
                        f"| {p.get('sgg_total') or '—'} |\n"
                    )


if __name__ == "__main__":
    main()
