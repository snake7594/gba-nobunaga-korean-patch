# -*- coding: utf-8 -*-
"""번역 배치 + 글로서리 생성"""
import os, sys
import paths
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eumdok import KANJI_READ

S = os.path.dirname(os.path.abspath(__file__))
U = json.load(open(paths.inp('units2.json'), encoding="utf-8"))
es = json.load(open(paths.inp('master_strings.json'), encoding="utf-8"))
by_off = {e["off"]: e for e in es}

# 물리적 이웃 문자열(문맥용)
offs_sorted = sorted(by_off)
import bisect
def neighbors(off):
    i = bisect.bisect_left(offs_sorted, off)
    prev = by_off[offs_sorted[i-1]]["jp"] if i > 0 else ""
    nxt = by_off[offs_sorted[i+1]]["jp"] if i+1 < len(offs_sorted) else ""
    return prev, nxt

items = []
for u in U["solo"]:
    off0 = u["offs"][0]
    pv, nx = neighbors(off0)
    items.append({"type": "solo", "key": u["jp"], "jp": u["jp"],
                  "limit": u["limit"], "ctx": [pv[:20], nx[:20]], "sort": off0})
for k, sq in enumerate(U["seq"]):
    items.append({"type": "seq", "key": f"seq{k}", "jps": sq["jps"], "sort": sq["offs"][0]})

# 물리 주소순 정렬(문맥 지역성)
items.sort(key=lambda x: x["sort"])

batches = []
cur, cost = [], 0
for it in items:
    c = len(it["jp"]) if it["type"] == "solo" else sum(len(j) for j in it["jps"])
    cur.append(it); cost += max(c, 10)
    if cost >= 1050:
        batches.append(cur); cur, cost = [], 0
if cur: batches.append(cur)

os.makedirs(paths.out('tr_batches'), exist_ok=True)
for f in glob.glob(paths.out('tr_batches/*.json')): os.remove(f)
for k, b in enumerate(batches):
    json.dump(b, open(paths.out(f'tr_batches/batch_{k:03d}.json'), "w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("batches:", len(batches), " items:", len(items))

# 글로서리
gloss = {
  "terms": {
    "大名":"다이묘","武将":"무장","家臣":"가신","軍師":"군사","忍者":"닌자","兵糧":"병량",
    "石高":"석고","鉄砲":"철포","騎馬":"기마","足軽":"아시가루","茶器":"다기","南蛮":"남만",
    "朝廷":"조정","幕府":"막부","官位":"관위","合戦":"합전","評定":"평정","一揆":"잇키",
    "謀叛":"모반","謀反":"모반","隠居":"은거","元服":"성인식","国人":"국인","町":"마을",
    "城下":"성하","楽市":"낙시","検地":"검지","刀狩":"도수","委任":"위임","出陣":"출진",
    "撤退":"철수","降伏":"항복","同盟":"동맹","朝廷工作":"조정 공작","本能寺の変":"본능사의 변",
    "天下統一":"천하통일","下克上":"하극상","浪人":"낭인","姫":"공주","殿":"님/전하(문맥)",
    "様":"님","石":"석","貫":"관","俵":"섬","門徒":"문도","宿敵":"숙적","当主":"당주",
  },
  "notes": [
    "인명·지명·성(城)·구니(国)명은 한자 독음으로 변환 (첫 글자 두음법칙).",
    "예: 織田信長=직전신장, 豊臣秀吉=풍신수길, 徳川家康=덕천가강, 武田信玄=무전신현,",
    "上杉謙信=상삼겸신, 伊達政宗=이달정종, 明智光秀=명지광수, 羽柴秀吉=우시수길,",
    "北条=북조, 毛利=모리, 島津=도진, 長宗我部=장종아부, 本能寺=본능사, 尾張=미장, 京=경(교토)",
    "가나 표기 인명(요괴 등)은 외래어 표기법으로 음차: ぬらりひょん=누라리횬",
  ],
  "eumdok": KANJI_READ,
  "dueum": {
    "라":"나","락":"낙","란":"난","랄":"날","람":"남","랍":"납","랑":"낭","래":"내","랭":"냉",
    "량":"양","려":"여","력":"역","련":"연","렬":"열","렴":"염","렵":"엽","령":"영","례":"예",
    "로":"노","록":"녹","론":"논","롱":"농","뢰":"뇌","료":"요","룡":"용","루":"누","류":"유",
    "륙":"육","륜":"윤","률":"율","륭":"융","륵":"늑","름":"늠","릉":"능","리":"이","린":"인",
    "림":"임","립":"입","녀":"여","년":"연","념":"염","녕":"영","뇨":"요","뉴":"유","니":"이",
    "닉":"익","님":"임",
  },
}
json.dump(gloss, open(paths.out('glossary.json'), "w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("glossary saved")
