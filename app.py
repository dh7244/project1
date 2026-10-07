# -*- coding: utf-8 -*-
import datetime
import json
import re
import time
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import requests
from scipy import stats
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="13F SML Radar v1.5",
    page_icon="📈",
    layout="wide"
)

USER_AGENT = "QuantStreamlitApp quant_analyst@quantfirm.org"
HEADERS = {"User-Agent": USER_AGENT}

DEFAULT_FUNDS = {
    # 1. 퀀트 & 멀티스트래티지 헤지펀드
    "시타델 (Citadel Advisors)": "0001423053",
    "르네상스 테크놀로지 (Renaissance Tech)": "0001037389",
    "밀레니엄 매니지먼트 (Millennium Mgmt)": "0001273087",
    "투 시그마 (Two Sigma Investments)": "0001179392",
    "D.E. 쇼 (D.E. Shaw & Co.)": "0001009207",
    "포인트72 (Point72 / Steve Cohen)": "0001603466",
    "AQR 캐피탈 (AQR Capital Mgmt)": "0001167557",
    "브릿지워터 (Bridgewater Associates)": "0001350694",
    "발리아스니 (Balyasny Asset Mgmt)": "0001262279",
    "엑소더스포인트 (ExodusPoint Capital)": "0001744489",
    
    # 2. 전설적 투자자 & 행동주의 / 롱숏 헤지펀드
    "버크셔 해서웨이 (Berkshire Hathaway)": "0001067983",
    "타이거 글로벌 (Tiger Global)": "0001167483",
    "코튜 매니지먼트 (Coatue / Philippe Laffont)": "0001422183",
    "바이킹 글로벌 (Viking Global / Halvorsen)": "0001103804",
    "퍼싱 스퀘어 (Pershing Square / Ackman)": "0001336528",
    "아팔루사 (Appaloosa / David Tepper)": "0001006438",
    "듀케인 패밀리오피스 (Duquesne / Druckenmiller)": "0001536411",
    "소로스 펀드 (Soros Fund Management)": "0001029160",
    "서드 포인트 (Third Point / Dan Loeb)": "0001040273",
    "그린라이트 캐피탈 (Greenlight / David Einhorn)": "0001079114",
    "바우포스트 그룹 (Baupost / Seth Klarman)": "0001061768",
    "론 파인 캐피탈 (Lone Pine / Steve Mandel)": "0001061165",
    "아크 인베스트 (ARK Invest / Cathie Wood)": "0001697748",
    "엘리엇 매니지먼트 (Elliott Investment Mgmt)": "0001048445",
    "스타보드 밸류 (Starboard Value)": "0001513824",
    "아이칸 엔터프라이즈 (Carl Icahn)": "0000921669",
    "페어홀름 (Fairholme Capital / Berkowitz)": "0001111565",
    "세스콰하나 (Susquehanna International)": "0001446194",
    "제인 스트리트 (Jane Street Group)": "0001599947",
    "위즈덤트리 (WisdomTree Inc)": "0001350487",

    # 3. 글로벌 초대형 자산운용사
    "블랙록 (BlackRock Fund Advisors)": "0001364742",
    "뱅가드 그룹 (Vanguard Group)": "0000102909",
    "피델리티 (FMR LLC)": "0000315066",
    "스테이트 스트리트 (State Street Corp)": "0000093751",
    "웰링턴 매니지먼트 (Wellington Management)": "0000902219",
    "T. 로우 프라이스 (T. Rowe Price)": "0000080255",
    "캐피탈 리서치 (Capital Research Global)": "0001423052",
    "베일리 기포드 (Baillie Gifford & Co)": "0001088875",
    "인베스코 (Invesco Ltd.)": "0000914208",
    "노던 트러스트 (Northern Trust Corp)": "0000073124",
    "프랭클린 리소시스 (Franklin Resources)": "0000038777",
    "얼라이언스 번스틴 (AllianceBernstein)": "0001109448",

    # 4. 글로벌 대형 IB 및 국부펀드
    "JP모건 체이스 (JPMorgan Chase & Co)": "0000019617",
    "골드만 삭스 (Goldman Sachs Group)": "0000886982",
    "모건 스탠리 (Morgan Stanley)": "0000895421",
    "뱅크 오브 아메리카 (Bank of America)": "0000070858",
    "시티그룹 (Citigroup Inc)": "0000831001",
    "웰스 파고 (Wells Fargo & Co)": "0000072971",
    "UBS 그룹 (UBS Group AG)": "0001610520",
    "노르웨이 국부펀드 (Norges Bank)": "0001270787"
}

COMMON_CUSIP_MAP = {
    "G7945M107": "STX", "H7945M107": "STX", "81180R107": "STX",
    "31428X106": "FDX", "84615Q103": "SPCX", "037833100": "AAPL",
    "594918104": "MSFT", "67066G104": "NVDA", "023135106": "AMZN",
    "02079K305": "GOOGL", "02079K107": "GOOG", "30303M102": "META",
    "88160R101": "TSLA", "064058100": "AVGO", "46625H100": "JPM",
    "532457108": "LLY", "931142103": "WMT", "92826C839": "V",
    "254687106": "DIS", "69608A108": "PLTR", "22788C105": "CRWD",
    "874039100": "TSM", "007903107": "AMD", "74340W103": "QCOM",
    "09247X101": "BLK", "025816109": "AXP", "060505104": "BAC",
    "191216100": "KO", "166764100": "CVX", "713448108": "PEP",
    "478160104": "JNJ", "00206R102": "T", "91324P102": "UNH",
    "64110D104": "NFLX", "22160K105": "COST", "00724F101": "ADBE",
    "90353T100": "UBER", "009066101": "ABNB", "17275R102": "CSCO",
    "458140100": "INTC"
}

EXPLICIT_NAME_MAP = {
    "SEAGATE": "STX", "FEDEX": "FDX", "FEDERAL EXPRESS": "FDX",
    "SPACE EXPLORATION": "SPCX", "SPACEX": "SPCX", "MICROSOFT": "MSFT",
    "APPLE": "AAPL", "NVIDIA": "NVDA", "AMAZON": "AMZN",
    "ALPHABET": "GOOGL", "GOOGLE": "GOOGL", "META PLATFORMS": "META",
    "FACEBOOK": "META", "TESLA": "TSLA", "BROADCOM": "AVGO",
    "PALANTIR": "PLTR", "TAIWAN SEMICONDUCTOR": "TSM",
    "BERKSHIRE HATHAWAY": "BRK-B", "NETFLIX": "NFLX", "COSTCO": "COST",
    "ADOBE": "ADBE", "UBER TECHNOLOGIES": "UBER", "AIRBNB": "ABNB",
    "ELI LILLY": "LLY", "JPMORGAN": "JPM", "WALT DISNEY": "DIS",
    "CROWDSTRIKE": "CRWD", "QUALCOMM": "QCOM", "CHEVRON": "CVX",
    "PEPSICO": "PEP", "COCA COLA": "KO", "WALMART": "WMT"
}

@st.cache_data(ttl=86400)
def load_sec_ticker_directory():
    url = "https://www.sec.gov/files/company_tickers.json"
    name_to_tk = {}
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            for v in data.values():
                tk = v.get("ticker", "").upper()
                nm = re.sub(r'[^A-Z0-9]', '', v.get("title", "").upper())
                if tk and nm:
                    name_to_tk[nm] = tk
    except Exception:
        pass
    return name_to_tk

NAME_DICT = load_sec_ticker_directory()

@st.cache_data(ttl=86400)
def search_yahoo_ticker(query_name):
    clean_q = re.sub(r'[^a-zA-Z0-9 ]', ' ', query_name).strip()
    words = clean_q.split()[:3]
    if not words:
        return "-"
    search_str = " ".join(words)
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={search_str}&quotesCount=1&newsCount=0"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=3)
        if r.status_code == 200:
            quotes = r.json().get("quotes", [])
            if quotes and "symbol" in quotes[0]:
                sym = quotes[0]["symbol"].upper()
                if len(sym) <= 5 and sym.isalpha():
                    return sym
    except Exception:
        pass
    return "-"

def resolve_ticker_advanced(cusip, name):
    if cusip in COMMON_CUSIP_MAP:
        return COMMON_CUSIP_MAP[cusip]
    nm_upper = name.upper()
    for kw, sym in EXPLICIT_NAME_MAP.items():
        if kw in nm_upper:
            return sym
    clean_n = re.sub(r'[^A-Z0-9]', '', nm_upper)
    if clean_n in NAME_DICT:
        return NAME_DICT[clean_n]
    found_tk = search_yahoo_ticker(name)
    if found_tk != "-":
        return found_tk
    return "-"

def calc_next_filing_deadline(latest_date_str):
    try:
        dt = datetime.datetime.strptime(latest_date_str, "%Y-%m-%d").date()
    except Exception:
        dt = datetime.date.today()

    yr = dt.year
    deadlines = [
        datetime.date(yr, 2, 14),
        datetime.date(yr, 5, 15),
        datetime.date(yr, 8, 14),
        datetime.date(yr, 11, 14),
        datetime.date(yr + 1, 2, 14),
        datetime.date(yr + 1, 5, 15)
    ]
    
    today = datetime.date.today()
    next_dl = None
    for d in deadlines:
        if d > dt and d >= today:
            next_dl = d
            break
            
    if not next_dl:
        next_dl = datetime.date(today.year, 11, 14)
        
    days_left = (next_dl - today).days
    return dt.strftime("%Y-%m-%d"), next_dl.strftime("%Y-%m-%d"), days_left

@st.cache_data(ttl=43200)
def get_filings(cik):
    time.sleep(0.12)
    url = f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return []
        filings = res.json()["filings"]["recent"]
        out = []
        for i in range(len(filings["accessionNumber"])):
            if filings["form"][i] in ["13F-HR", "13F-HR/A"]:
                out.append({
                    "acc": filings["accessionNumber"][i],
                    "date": filings["filingDate"][i]
                })
                if len(out) == 2:
                    break
        return out
    except Exception:
        return []

@st.cache_data(ttl=43200)
def get_holdings(cik, acc):
    time.sleep(0.12)
    acc_clean = acc.replace("-", "")
    cik_clean = str(int(cik))
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_clean}/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return {}
        xmls = re.findall(r'href="([^"]+\.xml)"', res.text, re.IGNORECASE)
        target = None
        for f in xmls:
            fn = f.split("/")[-1].lower()
            if "infotable" in fn or "13f" in fn:
                target = f.split("/")[-1]
                break
        if not target and xmls:
            target = xmls[0].split("/")[-1]
        if not target:
            return {}
        
        xml_res = requests.get(f"{url}{target}", headers=HEADERS, timeout=8)
        xml_clean = re.sub(r'\sxmlns="[^"]+"', '', xml_res.text, count=1)
        root = ET.fromstring(xml_clean)
        
        h = {}
        for t in root.findall(".//infoTable"):
            cusip = t.findtext("cusip", "").strip()
            nm = t.findtext("nameOfIssuer", "UNKNOWN").strip()
            v_str = t.findtext("value", "0").replace(",", "").strip()
            try:
                v = int(float(v_str))
            except Exception:
                v = 0
            s_node = t.find(".//sshPrnamt")
            shares = int(float(s_node.text.replace(",", "").strip())) if (s_node is not None and s_node.text) else 0
            if cusip:
                if cusip in h:
                    h[cusip]["val"] += v
                    h[cusip]["shares"] += shares
                else:
                    h[cusip] = {"name": nm, "cusip": cusip, "val": v, "shares": shares}
        return h
    except Exception:
        return {}

def min_max(s, invert=False):
    s = s.fillna(0)
    mn, mx = s.min(), s.max()
    if mn == mx:
        return pd.Series(50.0, index=s.index)
    if invert:
        return (mx - s) / (mx - mn) * 100.0
    return (s - mn) / (mx - mn) * 100.0

def calc_score(df, sector_neutral=False):
    if df.empty:
        return df
    d = df.copy()
    if sector_neutral and "Sector" in d.columns:
        d["Rel_Return"] = d.groupby("Sector")["Rel_Return"].transform(lambda s: s - s.mean())

    d["Factor_Inst_Count"] = min_max(d["Fund_Count"]).round(1)
    d["Factor_Inst_Inflow"] = min_max(d["Inflow_M"]).round(1)
    d["Factor_Inst_Shares"] = min_max(d["Shares_Sum"]).round(1)
    d["Factor_Lag_Return"] = min_max(d["Rel_Return"], invert=True).round(1)
    d["Factor_Lag_Dist52W"] = min_max(d["Dist_52W"], invert=True).round(1)

    m1_inst = (
        0.35 * d["Factor_Inst_Count"]
        + 0.35 * d["Factor_Inst_Inflow"]
        + 0.30 * d["Factor_Inst_Shares"]
    )
    m2_inst = (
        d["Fund_Count"].rank(pct=True).fillna(0.5) * 50.0
        + d["Inflow_M"].rank(pct=True).fillna(0.5) * 50.0
    )
    
    f_counts = d["Fund_Count"].fillna(0).to_numpy()
    z_inst = stats.zscore(f_counts) if len(f_counts) > 1 and np.std(f_counts) > 0 else np.zeros(len(d))

    m1_lag = (
        0.60 * d["Factor_Lag_Return"]
        + 0.40 * d["Factor_Lag_Dist52W"]
    )
    m2_lag = (
        (-d["Rel_Return"]).rank(pct=True).fillna(0.5) * 50.0
        + (-d["Dist_52W"]).rank(pct=True).fillna(0.5) * 50.0
    )
    
    r_rets = d["Rel_Return"].fillna(0).to_numpy()
    z_lag = -stats.zscore(r_rets) if len(r_rets) > 1 and np.std(r_rets) > 0 else np.zeros(len(d))

    d["M1"] = (0.55 * m1_inst + 0.45 * m1_lag).round(1).fillna(50.0)
    d["M2"] = (0.55 * m2_inst + 0.45 * m2_lag).round(1).fillna(50.0)
    z_comp = 0.55 * np.nan_to_num(z_inst) + 0.45 * np.nan_to_num(z_lag)
    d["M3"] = (stats.norm.cdf(z_comp) * 100.0).round(1)
    
    # 💡 방법 1 반영: 대형주 수급 규모(M1) 가중치 확대 (M1 40% : M2 35% : M3 25%)
    raw_sml = 0.40 * d["M1"] + 0.35 * d["M2"] + 0.25 * d["M3"]
    d["SML_Score"] = raw_sml.round(1).fillna(50.0)

    sigs = []
    for _, r in d.iterrows():
        p_val = r["Price_Val"]
        tk = r["Ticker"]
        
        if p_val <= 0 or tk == "-":
            sigs.append("⚪ NO_DATA")
            continue
            
        sc = r["SML_Score"]
        ad = r["AD_Pass"]
        if sc >= 75.0 and ad:
            sigs.append("🟢 STRONG_BUY")
        elif sc >= 60.0 and ad:
            sigs.append("🔵 ACCUMULATE")
        elif sc >= 60.0 and not ad:
            sigs.append("🟡 WATCH_LAG")
        else:
            sigs.append("⚪ NEUTRAL")
    d["Signal"] = sigs
    
    d["Rank"] = d["SML_Score"].rank(ascending=False, method="min").fillna(len(d)).astype(int)
    return d.sort_values(by="Rank").reset_index(drop=True)

# --- UI 레이아웃 ---
st.title("🎯 SEC 13F SML 레이더 v1.5")
st.caption("스마트머니 래그(SML) 분석 | 대형주 우대 앙상블 | 마이크로스트럭처(A/D Line) 수치화 검증 | 공시 일정 모니터링")

with st.expander("📖 SML 점수 및 퀀트 팩터(M1·M2·M3) 상세 가이드 (필독)", expanded=False):
    st.markdown(
        """
        ### 1. SML 점수(Smart Money Lag Score)란?
        * **개념**: **"스마트머니(월가 대형 기관)의 집중 매수가 유입되었음에도, 주가는 아직 오르지 않고 뒤처진(Lag) 저평가 종목"**을 발굴하는 퀀트 앙상블 스코어입니다 (100점 만점).
        * **핵심 가설**: 거대 자본을 굴리는 전문 기관들은 장기간에 걸쳐 분할 매집하며, 공시 이후 시장의 관심이 쏠리면서 뒤늦게 주가가 제자리를 찾아가는 '시차 반등(Lag Reversal)' 현상을 노립니다.
        * **종합 공식 (대형주 우대 배분)**: 
          $$\\text{SML 점수} = 0.40 \\times M_1 + 0.35 \\times M_2 + 0.25 \\times M_3$$
        * **내부 평가 비중**: 모든 모델은 **기관 수급 강도(55%)** + **주가 저평가/소외도(45%)**를 결합하여 산출됩니다.

        ---
        ### 2. 세부 팩터 모델(M1, M2, M3)의 작동 원리
        * **M1 (선형 스케일 / 40%)**: 수천억~수조 원 규모의 압도적인 금액/주식이 유입된 **초대형 매집주/대형 우량주**에 높은 가점을 부여합니다.
        * **M2 (백분위 순위 / 35%)**: 절대 금액 차이를 배제하고 상대 순위(상위 %)로 변환하여 팩터 밸런스를 유지합니다.
        * **M3 (Z-Score 정규화 / 25%)**: 평균 대비 통계적으로 이례적인 **자금 집중 징후(Spike)**를 포착합니다.

        ---
        ### 3. 마이크로스트럭처(A/D Line 매집강도)와 실전 투자 시그널
        13F 공시는 분기 마감 후 최대 45일 뒤에 제출되므로 **'공시 시점에는 이미 기관이 차익실현 중일 수 있는 지연 리스크'**를 방지하기 위해 최근 10거래일 **A/D Line(축적/분산선)**의 자금 유출입을 기술적으로 교차 검증합니다.
        * **A/D 10일 변화율**: 최근 2주간 누적 자금 유입선이 상승했는지를 백분율(%)로 추적.
        * **평균 CLV(장중 매집 비율)**: -1.0(최저가 마감/매도 투하) ~ +1.0(최고가 마감/강한 매집) 사이에서 장중 매수세 우위를 측정.
        """
    )

if "custom_funds" not in st.session_state:
    st.session_state["custom_funds"] = dict(DEFAULT_FUNDS)

with st.expander(f"🏛️ 분석 대상 기관 관리 (총 {len(st.session_state['custom_funds'])}개 기관 등록됨)", expanded=False):
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("전체 선택"):
            st.session_state["sel_funds"] = list(st.session_state["custom_funds"].keys())
    with col_btn2:
        if st.button("전체 해제"):
            st.session_state["sel_funds"] = []

    default_selected = st.session_state.get("sel_funds", list(st.session_state["custom_funds"].keys()))
    selected_fund_names = st.multiselect(
        "분석할 기관들을 선택하세요:",
        options=list(st.session_state["custom_funds"].keys()),
        default=default_selected
    )

col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1.2])
with col1:
    top_n = st.slider("최종 출력 종목 수 (상위 N개)", min_value=20, max_value=300, value=50, step=10)
with col2:
    sec_neutral = st.checkbox("섹터 중립화 적용", value=False)
with col3:
    pass_only = st.checkbox("A/D Line 통과(PASS)만", value=False)
with col4:
    valid_price_only = st.checkbox("시세 조회 성공 종목만 보기", value=True)

btn_col1, btn_col2 = st.columns([3, 1])
with btn_col1:
    run_btn = st.button("🚀 13F 전수 수급 집계 & 퀀트 스코어링 실행", type="primary")
with btn_col2:
    if st.button("🔄 캐시 초기화 (새로고침)"):
        st.cache_data.clear()
        st.session_state.pop("result_df", None)
        st.rerun()

funds_to_analyze = {
    k: st.session_state["custom_funds"][k]
    for k in selected_fund_names
    if k in st.session_state["custom_funds"]
}

if run_btn:
    if not funds_to_analyze:
        st.error("최소 1개 이상의 기관을 선택해야 합니다.")
    else:
        status_box = st.empty()
        prog = st.progress(0.0)
        
        curr_records = []
        prev_records = {}
        filing_dates = []
        
        fund_items = list(funds_to_analyze.items())
        tot_cnt = len(fund_items)
        
        for idx, (name, cik) in enumerate(fund_items):
            status_box.markdown(f"📥 **[1단계: 공시 수집 {idx+1}/{tot_cnt}]** `{name}` 최신 13F 파싱 중...")
            prog.progress(int(((idx + 1) / tot_cnt) * 50))
            
            f = get_filings(cik)
            if not f:
                continue
            filing_dates.append(f[0]["date"])
            h1 = get_holdings(cik, f[0]["acc"])
            for cusip, val in h1.items():
                curr_records.append({
                    "cik": cik, "fund": name, "cusip": cusip,
                    "name": val["name"], "val": val["val"], "shares": val["shares"],
                    "f_date": f[0]["date"]
                })
            if len(f) > 1:
                h2 = get_holdings(cik, f[1]["acc"])
                for cusip, val in h2.items():
                    prev_records[(cik, cusip)] = val
        
        status_box.markdown("📊 **스마트머니 순유입 및 기관 수급 변화량 집계 중...**")
        prog.progress(55)
        
        tot = {}
        for r in curr_records:
            k = (r["cik"], r["cusip"])
            c = r["cusip"]
            if k not in prev_records:
                diff_v = r["val"]
                diff_s = r["shares"]
            else:
                p = prev_records[k]
                diff_v = max(0, r["val"] - p["val"]) if r["shares"] > p["shares"] else 0
                diff_s = max(0, r["shares"] - p["shares"]) if r["shares"] > p["shares"] else 0
            
            if diff_v > 0 or k not in prev_records:
                if c not in tot:
                    tot[c] = {
                        "name": r["name"],
                        "funds": set(),
                        "inflow": 0,
                        "shares": 0,
                        "f_date": r["f_date"],
                        "details": []
                    }
                tot[c]["funds"].add(r["fund"])
                tot[c]["inflow"] += diff_v
                tot[c]["shares"] += diff_s
                tot[c]["details"].append({
                    "fund": r["fund"],
                    "type": "신규" if k not in prev_records else "확대",
                    "shares": diff_s,
                    "val_m": round(diff_v / 1000.0, 1)
                })
        
        ranked = sorted(
            tot.items(),
            key=lambda x: (len(x[1]["funds"]), x[1]["inflow"]),
            reverse=True
        )[:top_n]
        
        data_rows = []
        tot_stocks = len(ranked)
        
        for s_idx, (cusip, d) in enumerate(ranked):
            tk = resolve_ticker_advanced(cusip, d["name"])
            status_box.markdown(f"📈 **[2단계: 시세/팩터 검증 {s_idx+1}/{tot_stocks}]** `{d['name'][:25]}` (티커: `{tk}`) 데이터 분석 중...")
            prog.progress(55 + int(((s_idx + 1) / max(tot_stocks, 1)) * 45))
            
            rel_ret, dist_52w, ad_pass, cur_p, base_p = 0.0, 0.0, False, 0.0, 0.0
            price_chg, pct_chg = 0.0, 0.0
            ad_chg_pct, avg_clv = 0.0, 0.0

            if tk != "-":
                try:
                    t = yf.Ticker(tk)
                    hist = t.history(period="6mo", timeout=3)
                    if not hist.empty and len(hist) > 10:
                        cur_p = float(hist["Close"].iloc[-1])
                        max_p = float(hist["High"].max())
                        start_p = float(hist["Close"].iloc[0])
                        
                        dist_52w = ((cur_p - max_p) / max_p) * 100.0 if max_p > 0 else 0.0
                        rel_ret = ((cur_p - start_p) / start_p) * 100.0 if start_p > 0 else 0.0
                        
                        target_dt = pd.to_datetime(d["f_date"]).tz_localize(hist.index.tz)
                        hist_since = hist[hist.index >= target_dt]
                        base_p = float(hist_since["Close"].iloc[0]) if not hist_since.empty else start_p
                        
                        price_chg = cur_p - base_p
                        pct_chg = (price_chg / base_p) * 100.0 if base_p > 0 else 0.0
                        
                        denom = (hist["High"] - hist["Low"]).replace(0, 1e-9)
                        clv_series = ((hist["Close"] - hist["Low"]) - (hist["High"] - hist["Close"])) / denom
                        ad_series = (clv_series * hist["Volume"]).cumsum()
                        
                        ad_cur = float(ad_series.iloc[-1])
                        ad_prev = float(ad_series.iloc[-10])
                        ad_pass = bool(ad_cur >= ad_prev)
                        
                        denom_ad = abs(ad_prev) if abs(ad_prev) > 0 else 1.0
                        ad_chg_pct = ((ad_cur - ad_prev) / denom_ad) * 100.0
                        avg_clv = float(clv_series.iloc[-10:].mean())
                except Exception:
                    pass
            
            data_rows.append({
                "CUSIP": cusip,
                "Ticker": tk,
                "Name": d["name"],
                "Sector": "Tech/Aerospace" if tk in ["STX", "FDX", "SPCX", "NVDA", "AAPL", "MSFT", "AVGO", "PLTR"] else "General",
                "Fund_Count": len(d["funds"]),
                "Inflow_M": round(d["inflow"] / 1000.0, 1),
                "Shares_Sum": d["shares"],
                "Rel_Return": round(rel_ret, 1),
                "Dist_52W": round(dist_52w, 1),
                "AD_Pass": ad_pass,
                "AD_Chg_Pct": round(ad_chg_pct, 1),
                "Avg_CLV": round(avg_clv, 2),
                "Base_Price": round(base_p, 2),
                "Price_Val": round(cur_p, 2),
                "Price_Chg": round(price_chg, 2),
                "Pct_Chg": round(pct_chg, 2),
                "Filing_Date": d["f_date"],
                "details": d["details"]
            })
        
        status_box.markdown("✨ **SML 점수 앙상블 및 랭킹 정렬 완료!**")
        prog.progress(100)
        time.sleep(0.5)
        
        prog.empty()
        status_box.empty()
        
        res_df = calc_score(pd.DataFrame(data_rows), sector_neutral=sec_neutral)
        st.session_state["result_df"] = res_df
        st.session_state["selected_ticker"] = res_df["Ticker"].iloc[0] if not res_df.empty else None

if "result_df" in st.session_state and not st.session_state["result_df"].empty:
    df_show = st.session_state["result_df"].copy()
    
    if valid_price_only:
        df_show = df_show[df_show["Price_Val"] > 0].reset_index(drop=True)

    if pass_only:
        df_show = df_show[df_show["AD_Pass"] == True].reset_index(drop=True)
        
    latest_filing_str = df_show["Filing_Date"].max() if "Filing_Date" in df_show.columns else "2026-08-14"
    prev_f_date, next_f_date, d_days = calc_next_filing_deadline(latest_filing_str)
    
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric("📅 직전 13F 공시 기준일", prev_f_date)
    with col_d2:
        st.metric("⏳ 다음 13F 공시 마감일", next_f_date)
    with col_d3:
        d_sign = f"D-{d_days}일" if d_days > 0 else f"D+{abs(d_days)}일"
        st.metric("⏱️ 다음 공시까지 남은 기간", d_sign, "공시 45일 주기 모니터링")

    def fmt_price_chg_symbol(v):
        if pd.isna(v) or v == 0.0:
            return "$0.00"
        elif v > 0:
            return f"🔴 +${v:.2f}"
        else:
            return f"🔵 -${abs(v):.2f}"

    def fmt_pct_chg_symbol(v):
        if pd.isna(v) or v == 0.0:
            return "0.00%"
        elif v > 0:
            return f"🔴 +{v:.2f}%"
        else:
            return f"🔵 -{abs(v):.2f}%"

    # ==========================================
    # 탑픽 5 (Top Picks 5) 컴팩트 요약표 모듈
    # ==========================================
    st.divider()
    st.subheader("⭐ 퀀트 탑픽 5선 (Quant Top Picks)")

    tab_pure, tab_theme = st.tabs(["🔥 SML 순수 득점 Top 5", "⚖️ 테마 분산 5대 엄선주"])

    with tab_pure:
        st.caption("💡 아래 종목의 행을 터치/클릭하면 하단 상세 팩터 분석으로 바로 연동됩니다.")
        pure_candidates = df_show[(df_show["AD_Pass"] == True) & (df_show["Price_Val"] > 0)]
        pure_top5 = pure_candidates.head(5) if len(pure_candidates) >= 5 else df_show.head(5)

        if not pure_top5.empty:
            p_table = pure_top5[["Ticker", "Name", "SML_Score", "Price_Val", "Pct_Chg", "AD_Chg_Pct", "Signal"]].copy()
            p_table.insert(0, "선정", [f"Top {i+1}" for i in range(len(p_table))])
            p_table.columns = ["선정", "티커", "기업명", "SML점수", "현재가($)", "공시후변동률", "A/D변화", "시그널"]
            p_table["공시후변동률"] = p_table["공시후변동률"].apply(fmt_pct_chg_symbol)

            p_event = st.dataframe(
                p_table,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="pure_top5_grid",
                column_config={
                    "SML점수": st.column_config.NumberColumn(format="%.1f 점"),
                    "현재가($)": st.column_config.NumberColumn(format="$%.2f"),
                    "A/D변화": st.column_config.NumberColumn(format="%+.1f%%"),
                }
            )
            if p_event and p_event.selection and p_event.selection.rows:
                sel_row_idx = p_event.selection.rows[0]
                if sel_row_idx < len(pure_top5):
                    st.session_state["selected_ticker"] = pure_top5.iloc[sel_row_idx]["Ticker"]

    with tab_theme:
        st.caption("💡 각 슬롯의 행을 터치/클릭하면 하단 상세 팩터 분석으로 바로 연동됩니다.")
        valid_pool = df_show[df_show["Price_Val"] > 0].copy()
        theme_picks = []
        selected_tickers = set()

        s1 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="Inflow_M", ascending=False)
        if not s1.empty:
            t1 = s1.iloc[0]
            theme_picks.append({
                "전략 슬롯": "🐋 고래 매집", "티커": t1["Ticker"], "기업명": t1["Name"],
                "SML점수": t1["SML_Score"], "현재가($)": t1["Price_Val"], "공시후변동률": t1["Pct_Chg"],
                "A/D변화": t1["AD_Chg_Pct"], "선정 이유": "순유입액 1위"
            })
            selected_tickers.add(t1["Ticker"])

        s2 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="Dist_52W", ascending=True)
        if not s2.empty:
            t2 = s2.iloc[0]
            theme_picks.append({
                "전략 슬롯": "📉 바닥 소외", "티커": t2["Ticker"], "기업명": t2["Name"],
                "SML점수": t2["SML_Score"], "현재가($)": t2["Price_Val"], "공시후변동률": t2["Pct_Chg"],
                "A/D변화": t2["AD_Chg_Pct"], "선정 이유": f"52주 낙폭 {t2['Dist_52W']:.1f}%"
            })
            selected_tickers.add(t2["Ticker"])

        s3 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="M3", ascending=False)
        if not s3.empty:
            t3 = s3.iloc[0]
            theme_picks.append({
                "전략 슬롯": "⚡ 수급 급증", "티커": t3["Ticker"], "기업명": t3["Name"],
                "SML점수": t3["SML_Score"], "현재가($)": t3["Price_Val"], "공시후변동률": t3["Pct_Chg"],
                "A/D변화": t3["AD_Chg_Pct"], "선정 이유": f"M3 Z-Score {t3['M3']:.1f}점"
            })
            selected_tickers.add(t3["Ticker"])

        s4 = valid_pool[(~valid_pool["Ticker"].isin(selected_tickers)) & (valid_pool["AD_Pass"] == True)].sort_values(by="AD_Chg_Pct", ascending=False)
        if not s4.empty:
            t4 = s4.iloc[0]
            theme_picks.append({
                "전략 슬롯": "🌊 차트 매집", "티커": t4["Ticker"], "기업명": t4["Name"],
                "SML점수": t4["SML_Score"], "현재가($)": t4["Price_Val"], "공시후변동률": t4["Pct_Chg"],
                "A/D변화": t4["AD_Chg_Pct"], "선정 이유": f"A/D {t4['AD_Chg_Pct']:+.1f}%"
            })
            selected_tickers.add(t4["Ticker"])

        s5 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="M2", ascending=False)
        if not s5.empty:
            t5 = s5.iloc[0]
            theme_picks.append({
                "전략 슬롯": "💎 밸류 앙상블", "티커": t5["Ticker"], "기업명": t5["Name"],
                "SML점수": t5["SML_Score"], "현재가($)": t5["Price_Val"], "공시후변동률": t5["Pct_Chg"],
                "A/D변화": t5["AD_Chg_Pct"], "선정 이유": f"M2 순위 {t5['M2']:.1f}점"
            })
            selected_tickers.add(t5["Ticker"])

        if theme_picks:
            t_df = pd.DataFrame(theme_picks)
            t_df["공시후변동률"] = t_df["공시후변동률"].apply(fmt_pct_chg_symbol)

            t_event = st.dataframe(
                t_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="theme_top5_grid",
                column_config={
                    "SML점수": st.column_config.NumberColumn(format="%.1f 점"),
                    "현재가($)": st.column_config.NumberColumn(format="$%.2f"),
                    "A/D변화": st.column_config.NumberColumn(format="%+.1f%%"),
                }
            )
            if t_event and t_event.selection and t_event.selection.rows:
                sel_row_idx = t_event.selection.rows[0]
                if sel_row_idx < len(t_df):
                    st.session_state["selected_ticker"] = t_df.iloc[sel_row_idx]["티커"]

    st.divider()

    st.subheader(f"📋 퀀트 랭킹 & 공시일 대비 성과 (총 {len(df_show)}개 종목)")
    st.caption("💡 **표에서 확인하고 싶은 기업의 행을 터치/클릭**하면 바로 아래에 상세 팩터 분석 및 매수 기관 정보가 연동됩니다.")

    table_df = df_show[[
        "Rank", "Ticker", "Name", "SML_Score", "M1", "M2", "M3",
        "Signal", "Base_Price", "Price_Val", "Price_Chg", "Pct_Chg",
        "Fund_Count", "Inflow_M"
    ]].copy()
    
    table_df.columns = [
        "순위", "티커", "기업명", "SML 점수", "M1", "M2", "M3",
        "투자시그널", "공시일주가($)", "현재가($)", "공시후변동($)", "공시후변동률(%)",
        "기관수", "유입액($M)"
    ]

    table_df["공시후변동($)"] = table_df["공시후변동($)"].apply(fmt_price_chg_symbol)
    table_df["공시후변동률(%)"] = table_df["공시후변동률(%)"].apply(fmt_pct_chg_symbol)

    event = st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "순위": st.column_config.NumberColumn(format="%d"),
            "SML 점수": st.column_config.NumberColumn(format="%.1f 점"),
            "M1": st.column_config.NumberColumn(format="%.1f"),
            "M2": st.column_config.NumberColumn(format="%.1f"),
            "M3": st.column_config.NumberColumn(format="%.1f"),
            "공시일주가($)": st.column_config.NumberColumn(format="$%.2f"),
            "현재가($)": st.column_config.NumberColumn(format="$%.2f"),
            "공시후변동($)": st.column_config.TextColumn(),
            "공시후변동률(%)": st.column_config.TextColumn(),
            "기관수": st.column_config.NumberColumn(format="%d 개"),
            "유입액($M)": st.column_config.NumberColumn(format="$%.1f M"),
        }
    )

    if event and event.selection and event.selection.rows:
        sel_idx = event.selection.rows[0]
        if sel_idx < len(df_show):
            st.session_state["selected_ticker"] = df_show.iloc[sel_idx]["Ticker"]
    elif "selected_ticker" not in st.session_state or st.session_state["selected_ticker"] not in df_show["Ticker"].values:
        if not df_show.empty:
            st.session_state["selected_ticker"] = df_show["Ticker"].iloc[0]

    if not df_show.empty:
        current_tk = st.session_state["selected_ticker"]
        sel_row = df_show[df_show["Ticker"] == current_tk].iloc[0]

        st.divider()
        
        # --- 종목 상세 분석 및 팩터 비중 분해 영역 ---
        st.subheader(f"🔍 [{current_tk}] {sel_row['Name']} 심층 팩터 분석 & 매수 기관")
        
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        with col_info1:
            st.metric("종합 SML 점수", f"{sel_row['SML_Score']:.1f} 점", sel_row['Signal'])
        with col_info2:
            st.metric("M1 (선형 스케일)", f"{sel_row['M1']:.1f} 점", "앙상블 비중 40% (체급 우대)")
        with col_info3:
            st.metric("M2 (백분위 순위)", f"{sel_row['M2']:.1f} 점", "앙상블 비중 35%")
        with col_info4:
            st.metric("M3 (Z-Score 정규화)", f"{sel_row['M3']:.1f} 점", "앙상블 비중 25%")

        with st.expander("📐 SML 점수 계산 요소별 비중 및 기여도 (Factor Breakdown)", expanded=True):
            st.markdown(
                """
                **SML 점수 앙상블 공식 (대형주 우대 배분)**:  
                $$\\text{SML 점수} = 0.40 \\times M_1 + 0.35 \\times M_2 + 0.25 \\times M_3$$
                각 서브 모델($M_1, M_2, M_3$)은 **스마트머니 수급 점수(55%)**와 **주가 래깅/소외 점수(45%)**의 결합으로 산출됩니다.
                """
            )
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.markdown("##### 🏛️ 스마트머니 수급 지표 (전체 비중 55%)")
                st.write(f"- **매수 기관 수 (비중 35%)**: {sel_row['Fund_Count']}개 사")
                st.write(f"- **순유입 대금 (비중 35%)**: ${sel_row['Inflow_M']:,.1f} M")
                st.write(f"- **신규/추가 주식수 (비중 30%)**: {sel_row['Shares_Sum']:,} 주")
                
            with b_col2:
                st.markdown("##### 📉 가격 소외 및 매집강도(A/D) 지표 (전체 비중 45%)")
                if sel_row["Price_Val"] > 0:
                    st.write(f"- **기간 상대 수익률 (비중 60%)**: {sel_row['Rel_Return']:+.1f}%")
                    st.write(f"- **52주 최고가 괴리율 (비중 40%)**: {sel_row['Dist_52W']:.1f}%")
                    
                    chg_sign = "🔴 +" if sel_row["Price_Chg"] > 0 else ("🔵 -" if sel_row["Price_Chg"] < 0 else "")
                    chg_abs = abs(sel_row["Price_Chg"])
                    pct_str = f"{sel_row['Pct_Chg']:+.2f}%"
                    st.write(
                        f"- **공시 시점 대비 주가 추이**: \\${sel_row['Base_Price']:.2f} → **\\${sel_row['Price_Val']:.2f}** "
                        f"({chg_sign}\\${chg_abs:.2f}, {pct_str})"
                    )
                    
                    pass_str = "✅ PASS (매집 유입 확인)" if sel_row["AD_Pass"] else "❌ FAIL (분산/차익매도 우려)"
                    st.markdown(f"- **A/D Line 매집강도 판정**: **{pass_str}**")
                    st.write(f"  * **최근 10일 A/D 추세 변화율**: `{sel_row['AD_Chg_Pct']:+.1f}%` *(양수일수록 매집 강함)*")
                    st.write(f"  * **평균 장중 매집 강도 (CLV 점수)**: `{sel_row['Avg_CLV']:+.2f}` *(범위: -1.0 ~ +1.0 / +에 가까울수록 고가 마감)*")
                else:
                    st.warning("⚠️ 실시간 시세 미조회 종목으로 가격 지표 및 추천 시그널이 산출되지 않았습니다.")

        # 매수 기관 목록
        st.markdown(f"##### 📋 {sel_row['Name']} 매수 참여 기관 목록")
        dt_df = pd.DataFrame(sel_row["details"])
        dt_df = dt_df.sort_values(by="val_m", ascending=False).reset_index(drop=True)
        dt_df.columns = ["기관명", "매수구분", "매수주식수", "매수금액($M)"]
        
        st.dataframe(
            dt_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "매수주식수": st.column_config.NumberColumn(format="%d 주"),
                "매수금액($M)": st.column_config.NumberColumn(format="$%.1f M"),
            }
        )
    else:
        st.info("선택한 필터 조건에 부합하는 종목이 없습니다.")
