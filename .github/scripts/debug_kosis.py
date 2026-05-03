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
print(f"총 row 수: {len(j) if isinstance(j, list) else 'N/A'}")
print(f"응답 타입: {type(j).__name__}")
if not isinstance(j, list):
    print(f"응답 본문: {str(j)[:500]}")
    raise SystemExit(0)

# 경기도 관련 row만 필터링해서 출력
print("\n=== 서울 row 샘플 (5개) ===")
seoul_rows = [r for r in j if "서울" in (r.get("C1_NM", "") or "") or "서울" in (r.get("C2_NM", "") or "")]
for r in seoul_rows[:5]:
    print(f"  C1_NM=\"{r.get(chr(67)+chr(49)+chr(95)+chr(78)+chr(77))}\" C2_NM=\"{r.get(chr(67)+chr(50)+chr(95)+chr(78)+chr(77))}\" DT={r.get('DT')}")

print("\n=== 경기 row 샘플 (15개) ===")
gyeonggi_rows = [r for r in j if "경기" in (r.get("C1_NM", "") or "") or "경기" in (r.get("C2_NM", "") or "") or "수원" in (r.get("C1_NM", "") or "") or "수원" in (r.get("C2_NM", "") or "")]
print(f"  매칭된 row: {len(gyeonggi_rows)}개")
for r in gyeonggi_rows[:20]:
    c1 = r.get("C1_NM", "")
    c2 = r.get("C2_NM", "")
    print(f"  C1=\"{c1}\" C2=\"{c2}\" DT={r.get('DT')}")

# 모든 unique C1_NM, C2_NM 분포 (시도 단위)
print("\n=== unique C1_NM 분포 (처음 30개) ===")
c1_set = set()
for r in j:
    c1 = r.get("C1_NM", "") or ""
    c1_set.add(c1)
for c1 in sorted(c1_set)[:30]:
    print(f"  \"{c1}\"")
print(f"  ... 총 {len(c1_set)}개")
