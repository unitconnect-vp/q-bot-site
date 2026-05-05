#!/usr/bin/env python3
"""대학알리미 API endpoint/응답 스키마 탐색 임시 스크립트.
fetch_town_data.py 본격 통합 전 응답 구조 확인용. 1회 사용 후 삭제 예정."""
import os, sys, json
import requests
from urllib.parse import quote, urlencode

KEY = os.environ.get("ACADEMYINFO_KEY", "").strip()
if not KEY:
    print("ERR: ACADEMYINFO_KEY missing")
    sys.exit(1)

masked = (KEY[:4] + "..." + KEY[-4:]) if len(KEY) > 8 else "***"
print(f"KEY masked: {masked} (raw_len={len(KEY)})")
print()

def safe_print(label, r):
    body = r.text if hasattr(r, "text") else str(r)
    body = body.replace(KEY, "[KEY]").replace(quote(KEY, safe=""), "[KEY]")
    print(f"  status={r.status_code}  ct={r.headers.get('content-type','?')[:50]}  len={len(body)}")
    print(f"  body[:1500]: {body[:1500]}")

# === 시도 1: odcloud 표준데이터셋 (15116816) ===
print("=" * 70)
print("TRY 1: odcloud standard dataset 15116816")
print("=" * 70)
for path_suffix in ["", "/v1"]:
    url = f"https://api.odcloud.kr/api/15116816{path_suffix}"
    print(f"\n→ {url}")
    try:
        r = requests.get(url, params={"serviceKey": KEY, "page": 1, "perPage": 3, "returnType": "json"}, timeout=15)
        safe_print(url, r)
    except Exception as e:
        print(f"  ERR: {e}")

# === 시도 2: 표준데이터셋 - 다른 패턴 ===
print("\n" + "=" * 70)
print("TRY 2: data.go.kr 직접 dataset 조회")
print("=" * 70)
url = "https://api.odcloud.kr/api/3084401/v1/uddi:35d50a55-5945-4ce1-b938-5ca8c34fff01"
print(f"\n→ {url} (sample uddi pattern test)")
try:
    r = requests.get(url, params={"serviceKey": KEY, "page": 1, "perPage": 3}, timeout=15)
    safe_print(url, r)
except Exception as e:
    print(f"  ERR: {e}")

# === 시도 3: 대학알리미 OpenAPI 직접 (BasicInformationService) ===
print("\n" + "=" * 70)
print("TRY 3: openapi.academyinfo.go.kr/BasicInformationService")
print("=" * 70)
academyinfo_endpoints = [
    ("getComparisonPubYear", {}),
    ("getCodeUniv", {"pubYear": "2024"}),
    ("getCodeRegion", {}),
    ("getCodeFndnTypeId", {}),
]
for op, extra in academyinfo_endpoints:
    url = f"http://openapi.academyinfo.go.kr/openapi/service/rest/BasicInformationService/{op}"
    params = {"serviceKey": KEY, **extra}
    print(f"\n→ {url}  params={extra}")
    try:
        r = requests.get(url, params=params, timeout=15)
        safe_print(url, r)
    except Exception as e:
        print(f"  ERR: {e}")

# === 시도 4: HTTPS 버전 ===
print("\n" + "=" * 70)
print("TRY 4: HTTPS academyinfo + main basic-info endpoint")
print("=" * 70)
for url in [
    "https://openapi.academyinfo.go.kr/openapi/service/rest/BasicInformationService/getComparisonPubYear",
    "https://www.academyinfo.go.kr/openapi/service/rest/BasicInformationService/getComparisonPubYear",
]:
    print(f"\n→ {url}")
    try:
        r = requests.get(url, params={"serviceKey": KEY}, timeout=15, verify=True)
        safe_print(url, r)
    except Exception as e:
        print(f"  ERR: {e}")

# === 시도 5: data.go.kr 일반 OpenAPI 게이트웨이 ===
print("\n" + "=" * 70)
print("TRY 5: apis.data.go.kr gateway")
print("=" * 70)
url = "https://apis.data.go.kr/B552123/StandardDataset/15116816"
print(f"\n→ {url}")
try:
    r = requests.get(url, params={"serviceKey": KEY, "page": 1, "perPage": 3, "returnType": "json"}, timeout=15)
    safe_print(url, r)
except Exception as e:
    print(f"  ERR: {e}")

print("\n" + "=" * 70)
print("DONE — 응답 분석 후 본격 fetch 함수 작성")
print("=" * 70)
