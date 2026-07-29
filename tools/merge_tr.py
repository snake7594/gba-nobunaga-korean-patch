# -*- coding: utf-8 -*-
"""tr_out/*.json 병합 -> tr_merged.json, 누락 배치 보고"""
import json, os, glob, sys

S = os.path.dirname(os.path.abspath(__file__))
nb = len(glob.glob(S+r"\tr_batches\batch_*.json"))
merged = {}
missing_files = []
bad = []
paths = [S + rf"\tr_out\batch_{k:03d}.json" for k in range(nb)]
if os.path.exists(S + r"\tr_out\batch_fix.json"):
    paths.append(S + r"\tr_out\batch_fix.json")
for k, p in enumerate(paths):
    if not os.path.exists(p):
        missing_files.append(k); continue
    try:
        data = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        bad.append((k, repr(e))); continue
    if isinstance(data, dict) and "items" in data: data = data["items"]
    for it in data:
        key = it.get("key")
        if key is None: continue
        if "kos" in it: merged[key] = {"kos": it["kos"]}
        elif "ko" in it: merged[key] = {"ko": it["ko"]}

# 기대 키 대비 누락
U = json.load(open(S+r"\units2.json", encoding="utf-8"))
want = set(u["jp"] for u in U["solo"]) | set(f"seq{k}" for k in range(len(U["seq"])))
have = set(merged)
missing_keys = want - have

print(f"batches: {nb}, missing files: {len(missing_files)} {missing_files[:20]}")
print(f"bad json: {bad}")
print(f"keys merged: {len(have)} / expected {len(want)}, missing keys: {len(missing_keys)}")
json.dump(merged, open(S+r"\tr_merged.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(sorted(missing_keys), open(S+r"\tr_missing_keys.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
print("saved tr_merged.json")
for k in list(missing_keys)[:15]: print("  missing:", repr(k[:40]))
