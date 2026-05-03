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

# 첫 row의 모든 키 확인
print("=== 첫 row의 모든 키 ===")
print(json.dumps(j[0], ensure_ascii=False, indent=2))

# 강남구 row 출력
print("\n=== 강남구 row ===")
for row in j:
    if row.get("C1_NM") == "강남구":
        print(json.dumps(row, ensure_ascii=False, indent=2))
        break

# 분당구 row 출력
print("\n=== 분당구 row ===")
for row in j:
    if row.get("C1_NM") == "분당구":
        print(json.dumps(row, ensure_ascii=False, indent=2))
        break

# "중구" 동음이의 확인
print("\n=== 중구 row 전체 ===")
for row in j:
    if row.get("C1_NM") == "중구":
        c1 = row.get("C1", "")
        dt = row.get("DT", "")
        print(f"  C1={c1} C1_NM=중구 DT={dt}")
