#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Q렌즈 동네 카드 — 페치 v3 (서울 25 + 경기 42 = 67개)"""

import os
import sys
import json
import statistics
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

SEOUL_GU = [
    ("11110", "종로구",     "종로구",   "seoul/jongno"),
    ("11140", "중구",       "중구",     "seoul/junggu"),
    ("11170", "용산구",     "용산구",   "seoul/yongsan"),
    ("11200", "성동구",     "성동구",   "seoul/seongdong"),
    ("11215", "광진구",     "광진구",   "seoul/gwangjin"),
    ("11230", "동대문구",   "동대문구", "seoul/dongdaemun"),
    ("11260", "중랑구",     "중랑구",   "seoul/jungnang"),
    ("11290", "성북구",     "성북구",   "seoul/seongbuk"),
    ("11305", "강북구",     "강북구",   "seoul/gangbuk"),
    ("11320", "도봉구",     "도봉구",   "seoul/dobong"),
    ("11350", "노원구",     "노원구",   "seoul/nowon"),
    ("11380", "은평구",     "은평구",   "seoul/eunpyeong"),
    ("11410", "서대문구",   "서대문구", "seoul/seodaemun"),
    ("11440", "마포구",     "마포구",   "seoul/mapo"),
    ("11470", "양천구",     "양천구",   "seoul/yangcheon"),
    ("11500", "강서구",     "강서구",   "seoul/gangseo"),
    ("11530", "구로구",     "구로구",   "seoul/guro"),
    ("11545", "금천구",     "금천구",   "seoul/geumcheon"),
    ("11560", "영등포구",   "영등포구", "seoul/yeongdeungpo"),
    ("11590", "동작구",     "동작구",   "seoul/dongjak"),
    ("11620", "관악구",     "관악구",   "seoul/gwanak"),
    ("11650", "서초구",     "서초구",   "seoul/seocho"),
    ("11680", "강남구",     "강남구",   "seoul/gangnam"),
    ("11710", "송파구",     "송파구",   "seoul/songpa"),
    ("11740", "강동구",     "강동구",   "seoul/gangdong"),
]

GYEONGGI_SIGUN = [
    ("41111", "수원시 장안구",   "수원 장안",   "gyeonggi/suwon-jangan"),
    ("41113", "수원시 권선구",   "수원 권선",   "gyeonggi/suwon-gwonseon"),
    ("41115", "수원시 팔달구",   "수원 팔달",   "gyeonggi/suwon-paldal"),
    ("41117", "수원시 영통구",   "수원 영통",   "gyeonggi/suwon-yeongtong"),
    ("41131", "성남시 수정구",   "성남 수정",   "gyeonggi/seongnam-sujeong"),
    ("41133", "성남시 중원구",   "성남 중원",   "gyeonggi/seongnam-jungwon"),
    ("41135", "성남시 분당구",   "성남 분당",   "gyeonggi/seongnam-bundang"),
    ("41171", "안양시 만안구",   "안양 만안",   "gyeonggi/anyang-manan"),
    ("41173", "안양시 동안구",   "안양 동안",   "gyeonggi/anyang-dongan"),
    ("41271", "안산시 상록구",   "안산 상록",   "gyeonggi/ansan-sangnok"),
    ("41273", "안산시 단원구",   "안산 단원",   "gyeonggi/ansan-danwon"),
    ("41281", "고양시 덕양구",   "고양 덕양",   "gyeonggi/goyang-deogyang"),
    ("41285", "고양시 일산동구", "고양 일산동", "gyeonggi/goyang-ilsandong"),
    ("41287", "고양시 일산서구", "고양 일산서", "gyeonggi/goyang-ilsanseo"),
    ("41461", "용인시 처인구",   "용인 처인",   "gyeonggi/yongin-cheoin"),
    ("41463", "용인시 기흥구",   "용인 기흥",   "gyeonggi/yongin-giheung"),
    ("41465", "용인시 수지구",   "용인 수지",   "gyeonggi/yongin-suji"),
    ("41150", "의정부시",     "의정부시",   "gyeonggi/uijeongbu"),
    ("41190", "부천시",       "부천시",     "gyeonggi/bucheon"),
    ("41210", "광명시",       "광명시",     "gyeonggi/gwangmyeong"),
    ("41220", "평택시",       "평택시",     "gyeonggi/pyeongtaek"),
    ("41250", "동두천시",     "동두천시",   "gyeonggi/dongducheon"),
    ("41290", "과천시",       "과천시",     "gyeonggi/gwacheon"),
    ("41310", "구리시",       "구리시",     "gyeonggi/guri"),
    ("41360", "남양주시",     "남양주시",   "gyeonggi/namyangju"),
    ("41370", "오산시",       "오산시",     "gyeonggi/osan"),
    ("41390", "시흥시",       "시흥시",     "gyeonggi/siheung"),
    ("41410", "군포시",       "군포시",     "gyeonggi/gunpo"),
    ("41430", "의왕시",       "의왕시",     "gyeonggi/uiwang"),
    ("41450", "하남시",       "하남시",     "gyeonggi/hanam"),
    ("41480", "파주시",       "파주시",     "gyeonggi/paju"),
    ("41500", "이천시",       "이천시",     "gyeonggi/icheon"),
    ("41550", "안성시",       "안성시",     "gyeonggi/anseong"),
    ("41570", "김포시",       "김포시",     "gyeonggi/gimpo"),
    ("41590", "화성시",       "화성시",     "gyeonggi/hwaseong"),
    ("41610", "광주시",       "광주시",     "gyeonggi/gwangju"),
    ("41630", "양주시",       "양주시",     "gyeonggi/yangju"),
    ("41650", "포천시",       "포천시",     "gyeonggi/pocheon"),
    ("41670", "여주시",       "여주시",     "gyeonggi/yeoju"),
    ("41800", "연천군",       "연천군",     "gyeonggi/yeoncheon"),
    ("41820", "가평군",       "가평군",     "gyeonggi/gapyeong"),
    ("41830", "양평군",       "양평군",     "gyeonggi/yangpyeong"),
]

SIDO_LIST = [
    {
        "code": "seoul",
        "name": "서울특별시",
        "sigun_list": SEOUL_GU,
        "airkorea_sido": "서울",
        "hira_sido_cds": ["110000"],
        "neis_atpt": "B10",
    },
    {
        "code": "gyeonggi",
        "name": "경기도",
        "sigun_list": GYEONGGI_SIGUN,
        "airkorea_sido": "경기",
        "hira_sido_cds": ["310000", "410000"],
        "neis_atpt": "J10",
    },
]

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


def fetch_environment(key, sido_name, sigun_list):
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    params = {"serviceKey": key, "returnType": "json", "numOfRows": "200", "pageNo": "1", "sidoName": sido_name, "ver": "1.0"}
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        j = r.json()
    except (requests.RequestException, json.JSONDecodeError):
        return {"_avg": None, "_per_sigun": {}, "_measured_at": None}

    items = j.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return {"_avg": None, "_per_sigun": {}, "_measured_at": None}

    pm10s = [v for v in (to_int_or_none(it.get("pm10Value")) for it in items) if v is not None]
    pm25s = [v for v in (to_int_or_none(it.get("pm25Value")) for it in items) if v is not None]
    avg = {
        "pm10": int(statistics.mean(pm10s)) if pm10s else None,
        "pm25": int(statistics.mean(pm25s)) if pm25s else None,
        "station_count": len(items),
    }

    per_sigun = {}
    for code, full_name, short, slug in sigun_list:
        candidates = []
        for w in short.replace("시", "").replace("구", "").replace("군", "").split():
            if w and len(w) >= 2:
                candidates.append(w)
        for w in full_name.replace("시", " ").replace("구", " ").replace("군", " ").split():
            if w and len(w) >= 2 and w not in candidates:
                candidates.append(w)
        for it in items:
            station = it.get("stationName", "") or ""
            for kw in candidates:
                if kw in station:
                    per_sigun[slug] = {
                        "station": station,
                        "pm10": to_int_or_none(it.get("pm10Value")),
                        "pm25": to_int_or_none(it.get("pm25Value")),
                    }
                    break
            if slug in per_sigun:
                break

    return {
        "_avg": avg,
        "_measured_at": items[0].get("dataTime") if items else None,
        "_per_sigun": per_sigun,
    }


def fetch_medical(key, sido_cds, sigun_list):
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    final_hosp = []

    for sido_cd in sido_cds:
        all_hosp = []
        for page in range(1, 12):
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

    per_sigun = {}
    for code, full_name, short, slug in sigun_list:
        gu_hosps = [h for h in final_hosp if full_name in (h.get("addr", "") or "")]
        type_counts = {}
        for h in gu_hosps:
            t = h.get("clCdNm", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_sigun[slug] = {"sgg_count": len(gu_hosps), "by_type": type_counts}

    return {"_total": len(final_hosp), "_per_sigun": per_sigun}


def fetch_education(key, atpt_code, sigun_list):
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

    per_sigun = {}
    for code, full_name, short, slug in sigun_list:
        gu_schools = [s for s in all_schools if full_name in (s.get("ORG_RDNMA", "") or "")]
        type_counts = {}
        for s in gu_schools:
            t = s.get("SCHUL_KND_SC_NM", "기타")
            type_counts[t] = type_counts.get(t, 0) + 1
        per_sigun[slug] = {"sgg_count": len(gu_schools), "by_type": type_counts}

    return {"_total": len(all_schools), "_per_sigun": per_sigun}


def fetch_population_all(key, all_sigun_with_sido):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
    params = {
        "method": "getList", "apiKey": key, "itmId": "T20", "objL1": "ALL",
        "format": "json", "jsonVD": "Y", "prdSe": "M", "newEstPrdCnt": "1",
        "orgId": "101", "tblId": "DT_1B040A3",
    }
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        j = r.json()
    except (requests.RequestException, json.JSONDecodeError):
        return {"_per_slug": {}, "_period": None, "_sido_totals": {}}

    if not isinstance(j, list):
        return {"_per_slug": {}, "_period": None, "_sido_totals": {}}

    period = None
    sido_totals = {}
    per_slug = {}
    for row in j:
        c1 = row.get("C1_NM", "") or ""
        c2 = row.get("C2_NM", "") or ""
        if not period:
            period = row.get("PRD_DE")
        if not c2:
            if c1 in ("서울특별시", "경기도"):
                sido_totals[c1] = to_int_or_none(row.get("DT"))
        combined = (c1 + " " + c2).strip()
        for sido_name, full_name, slug in all_sigun_with_sido:
            if slug in per_slug:
                continue
            if full_name in combined or full_name == c1 or full_name == c2:
                per_slug[slug] = {
                    "total": to_int_or_none(row.get("DT")),
                    "period": row.get("PRD_DE"),
                    "sido_name": sido_name,
                }

    return {"_per_slug": per_slug, "_period": period, "_sido_totals": sido_totals}


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

    print("[KOSIS] 전국 시군구 인구 호출")
    all_sigun_for_pop = []
    for sido in SIDO_LIST:
        for code, full_name, short, slug in sido["sigun_list"]:
            all_sigun_for_pop.append((sido["name"], full_name, slug))
    pop_data, _ = safe("population_all", fetch_population_all, keys["KOSIS_KEY"], all_sigun_for_pop,
                       default={"_per_slug": {}, "_period": None, "_sido_totals": {}})

    total_sigun = sum(len(s['sigun_list']) for s in SIDO_LIST)
    print(f"\n총 시도: {len(SIDO_LIST)}, 총 시군구: {total_sigun}")

    all_records = []
    for sido in SIDO_LIST:
        sido_name = sido["name"]
        sido_total_pop = pop_data.get("_sido_totals", {}).get(sido_name)
        sigun_count = len(sido["sigun_list"])

        print(f"\n=== {sido_name} ({sigun_count}개) ===")
        env, _ = safe("environment", fetch_environment, keys["AIRKOREA_KEY"], sido["airkorea_sido"], sido["sigun_list"],
                      default={"_avg": None, "_per_sigun": {}, "_measured_at": None})
        med, _ = safe("medical",     fetch_medical,     keys["HIRA_KEY"],     sido["hira_sido_cds"], sido["sigun_list"],
                      default={"_total": 0, "_per_sigun": {}})
        edu, _ = safe("education",   fetch_education,   keys["NEIS_KEY"],     sido["neis_atpt"],     sido["sigun_list"],
                      default={"_total": 0, "_per_sigun": {}})

        for i, (lawd_cd, full_name, short, slug) in enumerate(sido["sigun_list"], 1):
            print(f"  [{i:2d}/{sigun_count}] {full_name}", flush=True)
            trade, _ = safe("    trade", fetch_real_estate_trade, keys["MOLIT_TRADE_KEY"], lawd_cd, default={})
            rent,  _ = safe("    rent",  fetch_real_estate_rent,  keys["MOLIT_RENT_KEY"],  lawd_cd, default={})

            pop_record = pop_data.get("_per_slug", {}).get(slug, {})
            sgg_pop = pop_record.get("total")
            share = round(sgg_pop / sido_total_pop * 100, 2) if sgg_pop and sido_total_pop else None

            record = {
                "slug": slug,
                "name": short,
                "name_full": f"{sido_name} {full_name}",
                "sido_code": sido["code"],
                "sido_name": sido_name,
                "level": "sigungu",
                "lawd_cd": lawd_cd,
                "fetched_at": fetched_at,
                "sections": {
                    "real_estate_trade": trade,
                    "real_estate_rent": rent,
                    "environment": {
                        "sido_avg": env.get("_avg"),
                        "seoul_avg": env.get("_avg") if sido["code"] == "seoul" else None,
                        "gu_station": env.get("_per_sigun", {}).get(slug),
                        "gangnam_station": env.get("_per_sigun", {}).get(slug),
                        "measured_at": env.get("_measured_at"),
                    },
                    "medical": med.get("_per_sigun", {}).get(slug, {"sgg_count": 0, "by_type": {}}),
                    "education": edu.get("_per_sigun", {}).get(slug, {"sgg_count": 0, "by_type": {}}),
                    "population": {
                        "table_id": "DT_1B040A3",
                        "table_name": "행정구역(시군구)별/성별 인구수",
                        "period": pop_record.get("period") or pop_data.get("_period"),
                        "sgg_total": sgg_pop,
                        "gangnam_total": sgg_pop,
                        "sido_total": sido_total_pop,
                        "seoul_total": sido_total_pop if sido["code"] == "seoul" else None,
                        "share_of_sido_pct": share,
                        "share_of_seoul_pct": share if sido["code"] == "seoul" else None,
                    },
                },
                "errors": [],
            }
            all_records.append(record)

    OUTPUT_INTEGRATED.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": fetched_at,
        "sido_list": [{"code": s["code"], "name": s["name"], "count": len(s["sigun_list"])} for s in SIDO_LIST],
        "total_count": len(all_records),
        "records": all_records,
    }
    OUTPUT_INTEGRATED.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 통합 저장: {OUTPUT_INTEGRATED} ({len(all_records)}개 시군구)")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(f"# 페치 결과\n\n- 총 시군구: {len(all_records)}\n\n")
            for sido in SIDO_LIST:
                f.write(f"## {sido['name']} ({len(sido['sigun_list'])}개)\n\n")
                f.write("| 시군구 | 매매 | 전세 | 의료 | 학교 | 인구 |\n|---|---|---|---|---|---|\n")
                for r in all_records:
                    if r["sido_code"] != sido["code"]:
                        continue
                    t = r["sections"]["real_estate_trade"]
                    rt = r["sections"]["real_estate_rent"]
                    m = r["sections"]["medical"]
                    e = r["sections"]["education"]
                    p = r["sections"]["population"]
                    f.write(f"| {r['name']} | {t.get('count', '—')} | {rt.get('jeonse_count', '—')} | {m.get('sgg_count', '—')} | {e.get('sgg_count', '—')} | {p.get('sgg_total') or '—'} |\n")
                f.write("\n")


if __name__ == "__main__":
    main()
