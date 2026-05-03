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

# 모든 unique C1_NM 출력 (시군구 + 시도)
all_c1 = sorted(set(r.get("C1_NM", "") or "" for r in j))
print(f"=== 모든 unique C1_NM ({len(all_c1)}개) ===")
for c1 in all_c1:
    print(f'  "{c1}"')
