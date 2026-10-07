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
    page_title="13F SmartScore v1.5",
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

# 1. CUSIP 기준 직접 매핑 (정확도 100%)
COMMON_CUSIP_MAP = {
    "84615Q103": "SPCX",   # Space Exploration Technologies Corp (스페이스X)
    "037833100": "AAPL",   # Apple Inc
    "594918104": "MSFT",   # Microsoft Corp
    "67066G104": "NVDA",   # NVIDIA Corp
    "023135106": "AMZN",   # Amazon.com Inc
    "02079K305": "GOOGL",  # Alphabet Class A
    "02079K107": "GOOG",   # Alphabet Class C
    "30303M102": "META",   # Meta Platforms
    "88160R101": "TSLA",   # Tesla Inc
    "064058100": "AVGO",   # Broadcom Inc
    "46625H100": "JPM",    # JPMorgan Chase
    "532457108": "LLY",    # Eli Lilly
    "931142103": "WMT",    # Walmart Inc
    "92826C839": "V",      # Visa Inc
    "254687106": "DIS",    # Walt Disney Co
    "69608A108": "PLTR",   # Palantir Technologies
    "22788C105": "CRWD",   # CrowdStrike
    "874039100": "TSM",    # Taiwan Semiconductor
    "007903107": "AMD",    # Advanced Micro Devices
    "74340W103": "QCOM",   # Qualcomm Inc
    "09247X101": "BLK",    # BlackRock Inc
    "025816109": "AXP",    # American Express
    "060505104": "BAC",    # Bank of America
    "191216100": "KO",     # Coca-Cola Co
    "166764100": "CVX",    # Chevron Corp
    "713448108": "PEP",    # PepsiCo
    "478160104": "JNJ",    # Johnson & Johnson
    "00206R102": "T",      # AT&T
    "91324P102": "UNH"     # UnitedHealth
}

# 2. 기업명 키워드 매핑 테이블
EXPLICIT_NAME_MAP = {
    "SPACE EXPLORATION": "SPCX",
    "SPACEX": "SPCX",
    "MICROSOFT": "MSFT",
    "APPLE": "AAPL",
    "NVIDIA": "NVDA",
    "AMAZON": "AMZN",
    "ALPHABET": "GOOGL",
    "GOOGLE": "GOOGL",
    "META PLATFORMS": "META",
    "FACEBOOK": "META",
    "TESLA": "TSLA",
    "BROADCOM": "AVGO",
    "PALANTIR": "PLTR",
    "TAIWAN SEMICONDUCTOR": "TSM",
    "BERKSHIRE HATHAWAY": "BRK-B"
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
    """야후 파이낸스 실시간 심볼 검색 Fallback"""
    clean_q = re.sub(r'[^a-zA-Z0-9 ]', ' ', query_name).strip()
    words = clean_q.split()[:3]
    if not words:
        return "-"
    search_str = " ".join(words)
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={search_str}&quotesCount=1&newsCount=0"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
        if r.status_code == 200:
            quotes = r.json().get("quotes", [])
            if quotes and "symbol" in quotes[0]:
                sym = quotes[0]["symbol"].upper()
                # 옵션이나 복잡한 파생 심볼 제외
                if len(sym) <= 5 and sym.isalpha():
                    return sym
    except Exception:
        pass
    return "-"

def resolve_ticker_advanced(cusip, name):
    # 1. CUSIP 직접 매칭
    if cusip in COMMON_CUSIP_MAP:
        return COMMON_CUSIP_MAP[cusip]
    
    # 2. 기업명 명시적 키워드 검사 (예: SPACE EXPLORATION -> SPCX)
    nm_upper = name.upper()
    for kw, sym in EXPLICIT_NAME_MAP.items():
        if kw in nm_upper:
            return sym
            
    # 3. SEC 공식 Ticker 데이터베이스 매칭
    clean_n = re.sub(r'[^A-Z0-9]', '', nm_upper)
    if clean_n in NAME_DICT:
        return NAME_DICT[clean_n]
    
    # 4. 야후 파이낸스 실시간 매칭
    found_tk = search_yahoo_ticker(name)
    if found_tk != "-":
        return found_tk

    return "-"

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
    
    raw_smart = 0.20 * d["M1"] + 0.40 * d["M2"] + 0.40 * d["M3"]
    d["SmartScore"] = raw_smart.round(1).fillna(50.0)

    sigs = []
    for _, r in d.iterrows():
        sc = r["SmartScore"]
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
    
    d["Rank"] = d["SmartScore"].rank(ascending=False, method="min").fillna(len(d)).astype(int)
    return d.sort_values(by="Rank").reset_index(drop=True)

# --- UI 레이아웃 ---
st.title("🎯 SEC 13F 스마트스코어 & 시그널 v1.5")
st.caption("월가 Top 50 기관 전수 분석 | 3-Factor 앙상블 | 마이크로스트럭처(A/D Line) 검증 | 섹터 중립화")

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

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    top_n = st.slider("최종 출력 종목 수 (상위 N개)", min_value=20, max_value=300, value=50, step=10)
with col2:
    sec_neutral = st.checkbox("섹터 중립화(Sector Neutral) 적용", value=False)
with col3:
    pass_only = st.checkbox("A/D Line 통과(PASS) 종목만 표시", value=False)

if st.button("🚀 13F 전수 수급 집계 & 퀀트 스코어링 실행", type="primary"):
    funds_to_analyze = {
        k: st.session_state["custom_funds"][k]
        for k in selected_fund_names
        if k in st.session_state["custom_funds"]
    }
    
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
            status_box.markdown(f"**[{idx+1}/{tot_cnt}]** `{name}` 최신 13F 공시 수집 중...")
            prog.progress((idx + 1) / tot_cnt)
            
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
        
        status_box.markdown("📊 **기관 수급 집계 및 정확한 티커/주가 검증 중...**")
        prog.empty()
        status_box.empty()
        
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
        for cusip, d in ranked:
            tk = resolve_ticker_advanced(cusip, d["name"])
            rel_ret, dist_52w, ad_pass, cur_p = -15.0, -20.0, True, 0.0
            price_chg, pct_chg = 0.0, 0.0

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
                        clv = ((hist["Close"] - hist["Low"]) - (hist["High"] - hist["Close"])) / denom
                        ad = (clv * hist["Volume"]).cumsum()
                        ad_pass = bool(ad.iloc[-1] >= ad.iloc[-10])
                except Exception:
                    pass
            
            data_rows.append({
                "CUSIP": cusip,
                "Ticker": tk,
                "Name": d["name"],
                "Sector": "Aerospace/Tech" if tk in ["SPCX", "NVDA", "AAPL", "MSFT", "AVGO", "PLTR"] else "General",
                "Fund_Count": len(d["funds"]),
                "Inflow_M": round(d["inflow"] / 1000.0, 1),
                "Shares_Sum": d["shares"],
                "Rel_Return": round(rel_ret, 1),
                "Dist_52W": round(dist_52w, 1),
                "AD_Pass": ad_pass,
                "Price_Val": round(cur_p, 2),
                "Price_Chg": round(price_chg, 2),
                "Pct_Chg": round(pct_chg, 2),
                "details": d["details"]
            })
        
        res_df = calc_score(pd.DataFrame(data_rows), sector_neutral=sec_neutral)
        st.session_state["result_df"] = res_df
        st.session_state["selected_ticker"] = res_df["Ticker"].iloc[0] if not res_df.empty else None

if "result_df" in st.session_state:
    df_show = st.session_state["result_df"].copy()
    if pass_only:
        df_show = df_show[df_show["AD_Pass"] == True].reset_index(drop=True)
        
    st.subheader(f"📋 퀀트 랭킹 & 공시일 대비 성과 (총 {len(df_show)}개 종목)")
    st.caption("💡 **표에서 확인하고 싶은 기업의 행을 클릭**하면 아래에 상세 팩터 분석 및 매수 기관 정보가 즉시 나타납니다.")

    table_df = df_show[[
        "Rank", "Ticker", "Name", "SmartScore", "M1", "M2", "M3",
        "Signal", "Price_Val", "Price_Chg", "Pct_Chg",
        "Fund_Count", "Inflow_M"
    ]].copy()
    
    table_df.columns = [
        "순위", "티커", "기업명", "스마트스코어", "M1", "M2", "M3",
        "투자시그널", "현재가($)", "공시후변동($)", "공시후변동률(%)",
        "기관수", "유입액($M)"
    ]

    event = st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "순위": st.column_config.NumberColumn(format="%d"),
            "스마트스코어": st.column_config.NumberColumn(format="%.1f 점"),
            "M1": st.column_config.NumberColumn(format="%.1f"),
            "M2": st.column_config.NumberColumn(format="%.1f"),
            "M3": st.column_config.NumberColumn(format="%.1f"),
            "현재가($)": st.column_config.NumberColumn(format="$%.2f"),
            "공시후변동($)": st.column_config.NumberColumn(format="+$%.2f"),
            "공시후변동률(%)": st.column_config.NumberColumn(format="+%.2f%%"),
            "기관수": st.column_config.NumberColumn(format="%d 개"),
            "유입액($M)": st.column_config.NumberColumn(format="$%.1f M"),
        }
    )

    if event and event.selection and event.selection.rows:
        sel_idx = event.selection.rows[0]
        if sel_idx < len(df_show):
            st.session_state["selected_ticker"] = df_show.iloc[sel_idx]["Ticker"]
    elif "selected_ticker" not in st.session_state or st.session_state["selected_ticker"] not in df_show["Ticker"].values:
        st.session_state["selected_ticker"] = df_show["Ticker"].iloc[0]

    current_tk = st.session_state["selected_ticker"]
    sel_row = df_show[df_show["Ticker"] == current_tk].iloc[0]

    st.divider()
    
    # --- 종목 상세 분석 및 팩터 비중 분해 영역 ---
    st.subheader(f"🔍 [{current_tk}] {sel_row['Name']} 심층 팩터 분석 & 매수 기관")
    
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    with col_info1:
        st.metric("종합 SmartScore", f"{sel_row['SmartScore']:.1f} 점", sel_row['Signal'])
    with col_info2:
        st.metric("M1 (선형 스케일링)", f"{sel_row['M1']:.1f} 점", "앙상블 비중 20%")
    with col_info3:
        st.metric("M2 (백분위 랭크)", f"{sel_row['M2']:.1f} 점", "앙상블 비중 40%")
    with col_info4:
        st.metric("M3 (Z-Score 정규화)", f"{sel_row['M3']:.1f} 점", "앙상블 비중 40%")

    with st.expander("📐 M1, M2, M3 계산 요소별 비중 및 기여도 (Factor Breakdown)", expanded=True):
        st.markdown(
            """
            **SmartScore 앙상블 공식**:  
            $$\\text{SmartScore} = 0.20 \\times M_1 + 0.40 \\times M_2 + 0.40 \\times M_3$$
            각 서브 모델($M_1, M_2, M_3$)은 **기관 수급 점수(55%)**와 **가격 래깅/소외 점수(45%)**의 결합으로 산출됩니다.
            """
        )
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown("##### 🏛️ 기관 수급 지표 (전체 비중 55%)")
            st.write(f"- **매수 기관 수 (비중 35%)**: {sel_row['Fund_Count']}개 사")
            st.write(f"- **순유입 대금 (비중 35%)**: ${sel_row['Inflow_M']:,.1f} M")
            st.write(f"- **신규/추가 주식수 (비중 30%)**: {sel_row['Shares_Sum']:,} 주")
            
        with b_col2:
            st.markdown("##### 📉 가격 소외/래깅 지표 (전체 비중 45%)")
            st.write(f"- **기간 상대 수익률 (비중 60%)**: {sel_row['Rel_Return']:+.1f}%")
            st.write(f"- **52주 최고가 괴리율 (비중 40%)**: {sel_row['Dist_52W']:.1f}%")
            st.write(f"- **A/D Line(매집 강도) 통과 여부**: {'✅ PASS (수급 양호)' if sel_row['AD_Pass'] else '❌ FAIL (분산 우려)'}")

    st.markdown(f"##### 📋 {sel_row['Name']} 매수 참여 기관 목록")
    dt_df = pd.DataFrame(sel_row["details"])
    dt_df.columns = ["기관명", "매수구분", "매수주식수", "매수금액($M)"]
    st.dataframe(dt_df, use_container_width=True, hide_index=True)
