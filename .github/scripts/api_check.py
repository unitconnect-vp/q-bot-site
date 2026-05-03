#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q렌즈 동네 카드 — API 인증키 검증 스크립트
각 API에 1회씩 호출하여 키 유효성을 확인합니다.
"""

import os
import re
import sys
import json
from datetime import datetime
from urllib.parse import urlencode
import requests

# 강남구 = 11680
LAWD_CD_GANGNAM = "11680"
DEAL_YMD = "202512"
TIMEOUT = 15


def parse_xml_result(text):
    """공공데이터포털 표준 XML 응답 파싱."""
    if "SERVICE_KEY_IS_NOT_REGISTERED" in text or "SERVICE KEY IS NOT REGISTERED" in text:
        return ("FAIL", "키 미등록 — 포털 승인 대기 또는 키 오타")
    if "<errMsg>" in text:
        m = re.search(r"<errMsg>([^<]+)</errMsg>", text)
        em = re.search(r"<returnReasonCode>([^<]+)</returnReasonCode>", text)
        return ("FAIL", f"포털 에러: {em.group(1) if em else '?'} / {m.group(1) if m else '?'}")
    if "<resultCode>00</resultCode>" in text or "NORMAL SERVICE" in text or "NORMAL_CODE" in text:
        return ("PASS", "정상 응답")
    if "<resultCode>" in text:
        c = re.search(r"<resultCode>(\d+)</resultCode>", text)
        m = re.search(r"<resultMsg>([^<]+)</resultMsg>", text)
        return ("FAIL", f"resultCode={c.group(1) if c else '?'} / {m.group(1) if m else '?'}")
    if "<items>" in text or "<item>" in text:
        return ("PASS", "정상 응답 (데이터 포함)")
    return ("UNKNOWN", text[:150].replace("\n", " "))


def parse_json_result(text):
    """공공데이터포털 표준 JSON 응답 파싱."""
    if "SERVICE_KEY_IS_NOT_REGISTERED" in text or "SERVICE KEY IS NOT REGISTERED" in text:
        return ("FAIL", "키 미등록 — 포털 승인 대기 또는 키 오타")
    try:
        j = json.loads(text)
    except json.JSONDecodeError:
        return parse_xml_result(text)

    # 표준 헤더 형식
    rh = j.get("response", {}).get("header", {}) if isinstance(j, dict) else {}
    code = rh.get("resultCode")
    if code == "00":
        return ("PASS", "정상 응답")
    if code is not None:
        return ("FAIL", f"resultCode={code} / {rh.get('resultMsg', '?')}")

    # KOSIS 형식: 정상이면 리스트
    if isinstance(j, list):
        return ("PASS", f"정상 응답 ({len(j)}건)")
    if isinstance(j, dict) and ("err" in j or "errMsg" in j):
        return ("FAIL", f"KOSIS 에러: {j.get('err') or j.get('errMsg')}")
    return ("UNKNOWN", text[:150].replace("\n", " "))


def call(url, params, parser):
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return ("FAIL", f"HTTP {r.status_code}")
        return parser(r.text)
    except requests.exceptions.Timeout:
        return ("FAIL", f"타임아웃 ({TIMEOUT}s)")
    except Exception as e:
        return ("FAIL", f"예외: {type(e).__name__}: {str(e)[:80]}")


# ─────────────────────────────────────────────────
# 5개 API 호출 함수
# ─────────────────────────────────────────────────

def check_molit_trade(key):
    """국토교통부 아파트 매매 실거래가 (강남구 / 2025-12)."""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    return call(url, {
        "serviceKey": key,
        "LAWD_CD": LAWD_CD_GANGNAM,
        "DEAL_YMD": DEAL_YMD,
        "numOfRows": "1",
    }, parse_xml_result)


def check_molit_rent(key):
    """국토교통부 아파트 전월세 실거래가 (강남구 / 2025-12)."""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
    return call(url, {
        "serviceKey": key,
        "LAWD_CD": LAWD_CD_GANGNAM,
        "DEAL_YMD": DEAL_YMD,
        "numOfRows": "1",
    }, parse_xml_result)


def check_airkorea(key):
    """에어코리아 시도별 실시간 측정 (서울)."""
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    return call(url, {
        "serviceKey": key,
        "returnType": "json",
        "numOfRows": "1",
        "pageNo": "1",
        "sidoName": "서울",
        "ver": "1.0",
    }, parse_json_result)


def check_hira(key):
    """심평원 병원기본목록 (서울)."""
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    return call(url, {
        "ServiceKey": key,
        "_type": "json",
        "numOfRows": "1",
        "pageNo": "1",
        "sidoCd": "110000",
    }, parse_json_result)


def check_kosis(key):
    """KOSIS 통계표 목록 검색 (가장 가벼운 호출)."""
    url = "https://kosis.kr/openapi/statisticsList.do"
    return call(url, {
        "method": "getList",
        "apiKey": key,
        "vwCd": "MT_ZTITLE",
        "parentListId": "A",
        "format": "json",
        "jsonVD": "Y",
    }, parse_json_result)


# ─────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────

CHECKS = [
    ("MOLIT_TRADE_KEY", "아파트 매매 실거래가",  "국토교통부",     check_molit_trade),
    ("MOLIT_RENT_KEY",  "아파트 전월세 실거래가", "국토교통부",     check_molit_rent),
    ("AIRKOREA_KEY",    "대기오염 정보",          "한국환경공단",   check_airkorea),
    ("HIRA_KEY",        "병원·약국 정보",         "건강보험심사평가원", check_hira),
    ("KOSIS_KEY",       "통계표 목록",            "통계청 KOSIS",   check_kosis),
]


def main():
    now_kst = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append(f"# Q렌즈 동네 카드 — API 인증키 검증")
    lines.append("")
    lines.append(f"실행 시각: {now_kst}")
    lines.append("")
    lines.append("| 결과 | 인증키 | API | 운영기관 | 상세 |")
    lines.append("|------|--------|-----|----------|------|")

    pass_count = 0
    fail_count = 0
    unknown_count = 0

    for env_name, label, agency, fn in CHECKS:
        key = os.environ.get(env_name, "").strip()
        if not key:
            mark = "❌"
            status = "MISSING"
            detail = "환경변수 비어있음 — Secrets 미등록 또는 워크플로우 누락"
            fail_count += 1
        else:
            status, detail = fn(key)
            if status == "PASS":
                mark = "✅"
                pass_count += 1
            elif status == "UNKNOWN":
                mark = "⚠️"
                unknown_count += 1
            else:
                mark = "❌"
                fail_count += 1

        # 마크다운 표 안전 처리
        detail_safe = detail.replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(f"| {mark} {status} | `{env_name}` | {label} | {agency} | {detail_safe} |")

    lines.append("")
    lines.append(f"**합계** — ✅ {pass_count}건 / ⚠️ {unknown_count}건 / ❌ {fail_count}건")
    lines.append("")
    lines.append("## 결과 해석 가이드")
    lines.append("")
    lines.append("- **✅ PASS** — 키 유효, 즉시 사용 가능")
    lines.append("- **⚠️ UNKNOWN** — 응답이 표준 형식과 다름. 엔드포인트/파라미터 재확인 필요 (키 자체는 유효할 가능성 높음)")
    lines.append("- **❌ FAIL** — 키 미등록(승인 대기), 잘못된 키, 또는 엔드포인트 오류")
    lines.append("")
    lines.append("⚠️ 엔드포인트는 가장 일반적인 형태로 가정. 실제 신청한 API의 상세페이지 확인 필요할 수 있음.")

    output = "\n".join(lines)
    print(output)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(output + "\n")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
