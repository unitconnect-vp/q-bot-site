#!/usr/bin/env python3
import os, json, requests
key = os.environ["KOSIS_KEY"].strip()
url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
params = {
    "method": "getList", "apiKey": key, "itmId": "T20", "objL1": "ALL",
    "format": "json", "jsonVD": "Y", "prdSe": "M", "newEstPrdCnt": "1",
    "orgId": "101", "tblId": "DT_1B040A3",
}
r = requests.get(url, params=params, timeout=30)
j = r.json()

# 시도 합계 (C1 길이 1~3자리 또는 이름이 시도형)
print("=== 시도 합계 row ===")
sido_endings = ("도", "특별시", "광역시", "특별자치도", "특별자치시")
for row in j:
    c1 = (row.get("C1") or "").strip()
    c1_nm = (row.get("C1_NM") or "").strip()
    c1_eng = (row.get("C1_NM_ENG") or "").strip()
    dt = row.get("DT")
    if c1_nm.endswith(sido_endings) or c1_nm == "전국":
        print(f"  C1={c1:>5s} | {c1_nm:>15s} | {c1_eng:>30s} | DT={dt}")

# 시군구 prefix별 카운트
print("\n=== 시군구 prefix 분포 ===")
by_prefix = {}
total_sigungu = 0
for row in j:
    c1 = (row.get("C1") or "").strip()
    c1_nm = (row.get("C1_NM") or "").strip()
    if c1_nm.endswith(sido_endings) or c1_nm == "전국" or "출장소" in c1_nm:
        continue
    if len(c1) == 5:
        prefix = c1[:2]
        by_prefix.setdefault(prefix, []).append(c1_nm)
        total_sigungu += 1

for prefix in sorted(by_prefix.keys()):
    names = by_prefix[prefix]
    print(f"  prefix={prefix}: {len(names)}개  (예: {names[0]}, {names[1] if len(names)>1 else ""}, {names[-1]})")

print(f"\n총 시군구: {total_sigungu}개")
print(f"총 row: {len(j)}개")

# 출장소 등 "비표준" 시군구 (5자리 아닌 것) 출력
print("\n=== 비표준 시군구 (5자리 아닌 row, 시도 합계 제외) ===")
for row in j:
    c1 = (row.get("C1") or "").strip()
    c1_nm = (row.get("C1_NM") or "").strip()
    if c1_nm.endswith(sido_endings) or c1_nm == "전국":
        continue
    if len(c1) != 5:
        print(f"  C1={c1} {c1_nm}")
