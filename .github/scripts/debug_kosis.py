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

print("=== 시도 합계 row ===")
sido_endings = ("도", "특별시", "광역시", "특별자치도", "특별자치시")
for row in j:
    c1 = (row.get("C1") or "").strip()
    c1_nm = (row.get("C1_NM") or "").strip()
    c1_eng = (row.get("C1_NM_ENG") or "").strip()
    dt = row.get("DT")
    if c1_nm.endswith(sido_endings) or c1_nm == "전국":
        print("  C1=" + c1.rjust(5) + " | " + c1_nm.rjust(15) + " | " + c1_eng.rjust(30) + " | DT=" + str(dt))

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
    sample = names[0] + ", " + (names[1] if len(names) > 1 else "") + ", ... " + names[-1]
    print("  prefix=" + prefix + ": " + str(len(names)) + "개  (" + sample + ")")

print("\n총 시군구: " + str(total_sigungu) + "개")
print("총 row: " + str(len(j)) + "개")
