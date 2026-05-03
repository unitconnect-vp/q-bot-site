#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q렌즈 동네 카드 — API 인증키 검증 스크립트 (v2)
변경:
  - resultCode 파서: 00, 000, 0000 모두 정상 처리 (v1 버그 수정)
  - MOLIT 매매 엔드포인트 fallback: Dev → 일반 순차 시도
"""

import os
import re
import sys
import json
from datetime import datetime
import requests

LAWD_CD_GANGNAM = "11680"
DEAL_YMD = "202512"
TIMEOUT = 15


def is_normal_code(code: str) -> bool:
    """공공데이터포털 표준 정상 코드 — 0으로만 구성된 코드 (00, 000, 0000)."""
    return bool(code) and code.strip("0") == ""


def parse_xml_result(text):
    """공공데이터포털 표준 XML 응답 파싱."""
    if "SERVICE_KEY_IS_NOT_REGISTERED" in text or "SERVICE KEY IS NOT REGISTERED" in text:
        return ("FAIL", "키 미등록 — 포털 승인 대기 또는 키 오타")
    if "<errMsg>" in text:
        m = re.search(r"<errMsg>([^<]+)</errMsg>", text)
        em = re.search(r"<returnReasonCode>([^<]+)</returnReasonCode>", text)
        return ("FAIL", f"포털 에러: {em.group(1) if em else '?'} / {m.group(1) if m else '?'}")

    rc_match = re.search(r"<resultCode>([^<]+)</resultCode>", text)
    if rc_match:
        code = rc_match.group(1).strip()
        msg_match = re.search(r"<resultMsg>([^<]+)</resultMsg>", text)
        msg = msg_match.group(1).strip() if msg_match else "?"
        if is_normal_code(code):
            return ("PASS", f"정상 응답 (resultCode={code} / {msg})")
        return ("FAIL", f"resultCode={code} / {msg}")

    if "NORMAL SERVICE" in text or "NORMAL_CODE" in text:
        return ("PASS", "정상 응답")
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

    rh = j.get("response", {}).get("header", {}) if isinstance(j, dict) else {}
    code = rh.get("resultCode")
    if code is not None:
        code_str = str(code).strip()
        msg = rh.get("resultMsg", "?")
        if is_normal_code(code_str):
            return ("PASS", f"정상 응답 (resultCode={code_str} / {msg})")
        return ("FAIL", f"resultCode={code_str} / {msg}")

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
# API 호출 함수
# ─────────────────────────────────────────────────

def check_molit_trade(key):
    """국토교통부 아파트 매매 실거래가 — Dev/일반 fallback."""
    endpoints = [
        ("Dev/상세", "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"),
        ("일반",     "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"),
    ]
    last_status, last_detail = "FAIL", "?"
    for label, url in endpoints:
        params = {
            "serviceKey": key,
            "LAWD_CD": LAWD_CD_GANGNAM,
            "DEAL_YMD": DEAL_YMD,
            "numOfRows": "1",
        }
        status, detail = call(url, params, parse_xml_result)
        if status == "PASS":
            return ("PASS", f"{label} 엔드포인트 정상 — {detail}")
        last_status, last_detail = status, f"{label} 실패: {detail}"
    return (last_status, last_detail)


def check_molit_rent(key):
    """국토교통부 아파트 전월세 실거래가."""
    url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
    return call(url, {
        "serviceKey": key,
        "LAWD_CD": LAWD_CD_GANGNAM,
        "DEAL_YMD": DEAL_YMD,
        "numOfRows": "1",
    }, parse_xml_result)


def check_airkorea(key):
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
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    return call(url, {
        "ServiceKey": key,
        "_type": "json",
        "numOfRows": "1",
        "pageNo": "1",
        "sidoCd": "110000",
    }, parse_json_result)


def check_kosis(key):
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
    ("MOLIT_TRADE_KEY", "아파트 매매 실거래가",  "국토교통부",         check_molit_trade),
    ("MOLIT_RENT_KEY",  "아파트 전월세 실거래가", "국토교통부",         check_molit_rent),
    ("AIRKOREA_KEY",    "대기오염 정보",          "한국환경공단",       check_airkorea),
    ("HIRA_KEY",        "병원·약국 정보",         "건강보험심사평가원", check_hira),
    ("KOSIS_KEY",       "통계표 목록",            "통계청 KOSIS",       check_kosis),
]


def main():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append(f"# Q렌즈 동네 카드 — API 인증키 검증 (v2)")
    lines.append("")
    lines.append(f"실행 시각: {now}")
    lines.append("")
    lines.append("| 결과 | 인증키 | API | 운영기관 | 상세 |")
    lines.append("|------|--------|-----|----------|------|")

    pc = fc = uc = 0
    for env_name, label, agency, fn in CHECKS:
        key = os.environ.get(env_name, "").strip()
        if not key:
            mark, status, detail = "❌", "MISSING", "환경변수 비어있음"
            fc += 1
        else:
            status, detail = fn(key)
            if status == "PASS":
                mark, _ = "✅", pc := pc + 1
            elif status == "UNKNOWN":
                mark, _ = "⚠️", uc := uc + 1
            else:
                mark, _ = "❌", fc := fc + 1

        d = detail.replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(f"| {mark} {status} | `{env_name}` | {label} | {agency} | {d} |")

    lines.append("")
    lines.append(f"**합계** — ✅ {pc}건 / ⚠️ {uc}건 / ❌ {fc}건")

    output = "\n".join(lines)
    print(output)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(output + "\n")

    sys.exit(0 if fc == 0 else 1)


if __name__ == "__main__":
    main()
