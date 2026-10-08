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
def get_filings(cik, limit=2):
    time.sleep(0.12)
    url = f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return []
        filings = res.json()["filings"]["recent"]
        out = []
        seen_periods = set()
        for i in range(len(filings["accessionNumber"])):
            if filings["form"][i] not in ["13F-HR", "13F-HR/A"]:
                continue
            period = filings.get("reportDate", [""] * len(filings["accessionNumber"]))[i]
            # 같은 분기의 원보고서/수정보고서는 최신 제출본 하나만 사용한다.
            if period and period in seen_periods:
                continue
            seen_periods.add(period)
            out.append({
                "acc": filings["accessionNumber"][i],
                "date": filings["filingDate"][i],
                "period": period or filings["filingDate"][i]
            })
            if len(out) >= int(limit):
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

def winsorize(s, lower=0.01, upper=0.99):
    s = pd.to_numeric(s, errors="coerce")
    if s.dropna().empty:
        return s.fillna(0.0)
    lo = s.quantile(lower)
    hi = s.quantile(upper)
    return s.clip(lo, hi).fillna(s.median())


def pct_rank(s, invert=False):
    x = pd.to_numeric(s, errors="coerce")
    if invert:
        x = -x
    return x.rank(pct=True, method="average").fillna(0.5) * 100.0


def robust_score(s, invert=False):
    """1~99% winsorization 후 percentile rank. 횡단면 heavy-tail/outlier에 강함."""
    x = winsorize(s)
    return pct_rank(x, invert=invert)


def calc_score(df, market_neutral=False):
    """SML 2.0
    - 정규화 방법의 중복(MinMax/Percentile/Z-CDF)을 제거
    - 기관수급을 Breadth + Absolute/Relative Flow로 분해
    - 가격 소외를 시장 대비 Alpha + 3M Alpha + 52W 위치 + 가격 안정화로 구성
    - A/D는 이진 필터가 아니라 별도 Market Accumulation 확인점수로 사용
    """
    if df.empty:
        return df
    d = df.copy()

    # 시장 중립화: 기존의 임의 Sector 라벨 대신 SPY 대비 초과수익 사용
    if market_neutral and "Rel_Return" in d.columns and "Market_Return_6M" in d.columns:
        d["Alpha_6M"] = d["Rel_Return"] - d["Market_Return_6M"]
    else:
        d["Alpha_6M"] = d["Rel_Return"]

    if "Return_3M" not in d.columns:
        d["Return_3M"] = d["Rel_Return"]
    if "Market_Return_3M" in d.columns:
        d["Alpha_3M"] = d["Return_3M"] - d["Market_Return_3M"]
    else:
        d["Alpha_3M"] = d["Return_3M"]

    # -----------------------------
    # Institutional Accumulation (55)
    # -----------------------------
    # 기관 참여폭: 단순 기관 수를 사용하되, 전체 분석기관 수 대비 비율도 반영
    total_funds = max(int(d["Total_Funds"].max()) if "Total_Funds" in d.columns else 1, 1)
    d["Breadth_Pct"] = d["Fund_Count"] / total_funds * 100.0

    # Absolute flow: mega-cap 우대를 완전히 없애지 않기 위한 요소
    f_abs = robust_score(d["Inflow_M"])
    f_breadth = robust_score(d["Breadth_Pct"])
    f_hold = robust_score(d["Flow_Holdings_Ratio"], invert=False)
    f_adv = robust_score(d["Flow_ADV_Ratio"], invert=False)
    f_new = robust_score(d["New_Fund_Count"])

    # Relative flow를 중심으로 두고 절대금액은 보조로 유지
    d["Inst_Score"] = (
        0.10 * f_breadth +
        0.10 * f_hold +
        0.20 * f_adv +
        0.10 * f_abs +
        0.05 * f_new
    ) / 0.55

    # -----------------------------
    # Price Lag / Alpha (45)
    # -----------------------------
    f_alpha6 = robust_score(d["Alpha_6M"], invert=True)
    f_alpha3 = robust_score(d["Alpha_3M"], invert=True)
    f_dist = robust_score(d["Dist_52W"], invert=True)
    f_stab = robust_score(d["CMF_10D"])

    # 가격이 덜 올랐다는 것만 보지 않고, 최근 매집/안정화 여부를 일부 반영
    d["Lag_Score"] = (
        0.15 * f_alpha6 +
        0.10 * f_alpha3 +
        0.10 * f_dist +
        0.10 * f_stab
    ) / 0.45

    d["Inst_Score"] = d["Inst_Score"].clip(0, 100).round(1)
    d["Lag_Score"] = d["Lag_Score"].clip(0, 100).round(1)
    d["Inst_Contrib"] = (d["Inst_Score"] * 0.55).round(1)
    d["Lag_Contrib"] = (d["Lag_Score"] * 0.45).round(1)
    d["SML_Score"] = (d["Inst_Contrib"] + d["Lag_Contrib"]).round(1)

    # 설명용 하위 점수: 기존 M1/M2/M3보다 정보의 종류가 명확하도록 변경
    d["Flow_Score"] = (
        0.40 * f_abs + 0.20 * f_hold + 0.40 * f_adv
    ).round(1)
    d["Lag_Position_Score"] = (
        0.45 * f_alpha6 + 0.25 * f_alpha3 + 0.30 * f_dist
    ).round(1)
    d["Accumulation_Score"] = robust_score(d["CMF_10D"]).round(1)
    d["SML_Percentile"] = d["SML_Score"].rank(pct=True, method="average") * 100.0
    d["SML_Percentile"] = d["SML_Percentile"].round(1)

    # Percentile 기반 시그널: 70/55 고정 threshold보다 유니버스 크기에 강건함
    sigs = []
    for _, r in d.iterrows():
        p_val = r.get("Price_Val", 0)
        tk = r.get("Ticker", "-")
        if p_val <= 0 or tk == "-":
            sigs.append("⚪ NO_DATA")
            continue

        pct = r["SML_Percentile"]
        acc = r.get("Accumulation_Score", 50.0)
        i_c = r["Inst_Contrib"]
        l_c = r["Lag_Contrib"]

        if pct >= 95.0 and acc >= 50.0:
            if i_c >= 35.0:
                sigs.append("🟢 STRONG_BUY (수급주도)")
            elif l_c >= 28.0:
                sigs.append("🟢 STRONG_BUY (역발상바닥)")
            else:
                sigs.append("🟢 STRONG_BUY (균형성장)")
        elif pct >= 85.0 and acc >= 50.0:
            sigs.append("🔵 ACCUMULATE (분할매집)")
        elif pct >= 85.0:
            sigs.append("🟡 WATCH_LAG (매집주의)")
        elif pct >= 70.0:
            sigs.append("🟠 WATCH (관찰)")
        else:
            sigs.append("⚪ NEUTRAL")
    d["Signal"] = sigs
    d["Rank"] = d["SML_Score"].rank(ascending=False, method="min").fillna(len(d)).astype(int)
    return d.sort_values(by=["SML_Score", "SML_Percentile"], ascending=False).reset_index(drop=True)

# ============================================================
# Historical walk-forward backtest engine
# ============================================================
@st.cache_data(ttl=86400, show_spinner=False)
def load_historical_filings(cik, n_quarters=6):
    """최근 N개 분기의 13F를 가져온다. 동일 report period의 중복 제출은 제거."""
    return get_filings(cik, limit=max(int(n_quarters) + 2, 4))[:int(n_quarters)]


def _hist_return(hist, end_pos, n):
    if hist is None or hist.empty or end_pos < 1:
        return np.nan
    start_pos = end_pos - n
    if start_pos < 0:
        return np.nan
    try:
        a = float(hist["Close"].iloc[start_pos])
        b = float(hist["Close"].iloc[end_pos])
        return (b / a - 1.0) * 100.0 if a > 0 else np.nan
    except Exception:
        return np.nan


def _forward_return(hist, start_pos, n):
    if hist is None or hist.empty:
        return np.nan
    end_pos = start_pos + n
    if start_pos < 0 or end_pos >= len(hist):
        return np.nan
    try:
        a = float(hist["Close"].iloc[start_pos])
        b = float(hist["Close"].iloc[end_pos])
        return (b / a - 1.0) * 100.0 if a > 0 else np.nan
    except Exception:
        return np.nan


def _hist_features(hist, filing_date):
    """filing_date 이전 데이터만 사용하여 점수 입력 변수를 계산한다."""
    if hist is None or hist.empty:
        return {"Price_Val": 0.0, "Rel_Return": np.nan, "Return_3M": np.nan,
                "Dist_52W": np.nan, "CMF_10D": np.nan, "Flow_ADV_Ratio": 0.0,
                "Base_Price": 0.0}
    h = hist.copy().dropna(how="all")
    idx = pd.to_datetime(h.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    h.index = idx
    dt = pd.Timestamp(filing_date)
    # filing date 당일 장 마감 가격은 공개시각에 따라 미래정보가 될 수 있으므로
    # 실제 정보 이용 가능성을 보수적으로 잡아 직전 거래일까지 사용한다.
    pre = h[h.index < dt]
    if len(pre) < 20:
        return {"Price_Val": 0.0, "Rel_Return": np.nan, "Return_3M": np.nan,
                "Dist_52W": np.nan, "CMF_10D": np.nan, "Flow_ADV_Ratio": 0.0,
                "Base_Price": 0.0}
    close = pre["Close"].astype(float)
    cur = float(close.iloc[-1])
    r6 = _hist_return(pre, len(pre)-1, 126)
    r3 = _hist_return(pre, len(pre)-1, 63)
    hi = float(pre["High"].astype(float).max())
    dist = ((cur / hi) - 1.0) * 100.0 if hi > 0 else np.nan
    recent = pre.tail(10)
    high = recent["High"].astype(float)
    low = recent["Low"].astype(float)
    vol = recent["Volume"].astype(float)
    den = (high - low).replace(0, np.nan)
    clv = (((recent["Close"].astype(float) - low) - (high - recent["Close"].astype(float))) / den).fillna(0.0).clip(-1,1)
    vs = float(vol.sum())
    cmf = float((clv * vol).sum() / vs) if vs > 0 else 0.0
    adv = float((close.tail(20) * pre["Volume"].astype(float).tail(20)).mean()) / 1e6
    return {"Price_Val": cur, "Rel_Return": r6, "Return_3M": r3,
            "Dist_52W": dist, "CMF_10D": cmf, "Flow_ADV_Ratio": adv,
            "Base_Price": cur}


def run_walk_forward_backtest(funds_to_analyze, n_quarters=6, top_n=100,
                              market_neutral=True, forward_days=(21,63,126)):
    """13F filing-date 기준의 순차적(out-of-sample) SML 백테스트.

    각 분기마다:
      1) 해당 filing과 직전 filing의 보유주식수로 수급 계산
      2) filing 이전 가격만으로 SML 점수 계산
      3) 이후 21/63/126 거래일 수익률을 측정
    """
    all_filings = {}
    for name, cik in funds_to_analyze.items():
        fs = load_historical_filings(cik, n_quarters=n_quarters + 1)
        if fs:
            all_filings[(name, cik)] = fs

    periods = sorted({f["period"] for fs in all_filings.values() for f in fs}, reverse=True)
    periods = periods[:int(n_quarters)]
    if not periods:
        return pd.DataFrame(), pd.DataFrame()

    quarter_rows = []
    for qi, period in enumerate(sorted(periods)):
        curr_records, prev_records = [], {}
        period_date = None
        for (name, cik), fs in all_filings.items():
            current = next((f for f in fs if f["period"] == period), None)
            if not current:
                continue
            prev = next((f for f in fs if f["period"] < period), None)
            if period_date is None:
                period_date = current["date"]
            h1 = get_holdings(cik, current["acc"])
            h2 = get_holdings(cik, prev["acc"]) if prev else {}
            for cusip, val in h1.items():
                curr_records.append({"cik": cik, "fund": name, "cusip": cusip,
                                     "name": val["name"], "val": val["val"],
                                     "shares": val["shares"], "f_date": current["date"],
                                     "period": period})
            for cusip, val in h2.items():
                prev_records[(cik, cusip)] = val

        tot = {}
        for r in curr_records:
            key = (r["cik"], r["cusip"])
            prev = prev_records.get(key)
            is_new = prev is None
            p_shares = prev["shares"] if prev else 0
            p_val = prev["val"] if prev else 0
            diff_s = r["shares"] if is_new else max(0, r["shares"] - p_shares)
            if diff_s <= 0:
                continue
            if r["shares"] > 0:
                reported_price = (r["val"] * 1000.0) / r["shares"]
                diff_v = reported_price * diff_s
            else:
                diff_v = max(0, r["val"] - p_val) if not is_new else r["val"]
            c = r["cusip"]
            if c not in tot:
                tot[c] = {"name": r["name"], "funds": set(), "new_funds": set(),
                          "inflow": 0.0, "shares": 0, "current_value": 0.0,
                          "f_date": r["f_date"], "details": []}
            tot[c]["funds"].add(r["fund"])
            if is_new:
                tot[c]["new_funds"].add(r["fund"])
            tot[c]["inflow"] += diff_v
            tot[c]["shares"] += diff_s
            tot[c]["current_value"] += r["val"]

        ranked = sorted(tot.items(), key=lambda x: (len(x[1]["funds"]), x[1]["inflow"]), reverse=True)[:int(top_n)]
        resolved = [(c,d,resolve_ticker_advanced(c,d["name"])) for c,d in ranked]
        tickers = list(dict.fromkeys([x[2] for x in resolved if x[2] != "-"]))
        price_hist = {}
        start_dt = pd.Timestamp(period_date) - pd.Timedelta(days=430)
        end_dt = pd.Timestamp(period_date) + pd.Timedelta(days=220)
        if tickers:
            try:
                dl = yf.download(tickers=tickers, start=start_dt.strftime("%Y-%m-%d"),
                                  end=end_dt.strftime("%Y-%m-%d"), interval="1d",
                                  auto_adjust=False, progress=False, group_by="ticker", threads=True)
                if isinstance(dl.columns, pd.MultiIndex):
                    for tk in tickers:
                        if tk in dl.columns.get_level_values(0):
                            h = dl[tk].dropna(how="all")
                            if not h.empty: price_hist[tk] = h
                elif len(tickers) == 1 and not dl.empty:
                    price_hist[tickers[0]] = dl.dropna(how="all")
            except Exception:
                price_hist = {}

        spy = None
        try:
            spy = yf.download("SPY", start=start_dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d"),
                              interval="1d", auto_adjust=False, progress=False, threads=False)
            if isinstance(spy.columns, pd.MultiIndex):
                spy = spy.xs("SPY", axis=1, level=1)
            spy = spy.dropna(how="all")
        except Exception:
            spy = None

        spy_feat = _hist_features(spy, period_date)
        rows = []
        for c,d,tk in resolved:
            feat = _hist_features(price_hist.get(tk), period_date)
            adv_m = feat.pop("Flow_ADV_Ratio")
            inflow_m = d["inflow"] / 1000.0
            current_m = d["current_value"] / 1000.0
            # feat의 adv_m는 실제 ADV가 아니라 계산된 값이므로 ratio를 재계산한다.
            ratio_adv = inflow_m / adv_m if adv_m > 0 else 0.0
            hold_ratio = inflow_m / current_m if current_m > 0 else 0.0
            # 시장 수익률은 동일한 filing-date cut으로 계산
            market_6 = spy_feat.get("Rel_Return", np.nan)
            market_3 = spy_feat.get("Return_3M", np.nan)
            row = {
                "CUSIP": c, "Ticker": tk, "Name": d["name"],
                "Fund_Count": len(d["funds"]), "New_Fund_Count": len(d["new_funds"]),
                "Total_Funds": len(funds_to_analyze), "Inflow_M": inflow_m,
                "Current_Holdings_M": current_m, "Flow_ADV_Ratio": ratio_adv,
                "Flow_Holdings_Ratio": hold_ratio, "Rel_Return": feat["Rel_Return"],
                "Return_3M": feat["Return_3M"], "Market_Return_6M": market_6,
                "Market_Return_3M": market_3, "Dist_52W": feat["Dist_52W"],
                "CMF_10D": feat["CMF_10D"], "Price_Val": feat["Price_Val"],
                "Filing_Date": d["f_date"], "period": period,
                "details": []
            }
            rows.append(row)

        scored = calc_score(pd.DataFrame(rows), market_neutral=market_neutral) if rows else pd.DataFrame()
        if scored.empty:
            continue

        for _, r in scored.iterrows():
            tk = r["Ticker"]
            h = price_hist.get(tk)
            if h is None or h.empty or tk == "-":
                continue
            hh = h.copy()
            idx = pd.to_datetime(hh.index)
            if getattr(idx, "tz", None) is not None: idx = idx.tz_localize(None)
            hh.index = idx
            # 공시가 장중/장후 언제 나왔는지 알 수 없으므로 보수적으로
            # '공시일 다음 거래일' 종가를 진입 기준으로 사용한다.
            start_candidates = hh.index[hh.index > pd.Timestamp(period_date)]
            if len(start_candidates) == 0: continue
            start_pos = int(hh.index.get_loc(start_candidates[0]))
            for fd in forward_days:
                r[f"Fwd_{fd}D"] = _forward_return(hh, start_pos, fd)
            # 시장 대비 forward alpha
            if spy is not None and not spy.empty:
                sh = spy.copy()
                si = pd.to_datetime(sh.index)
                if getattr(si, "tz", None) is not None: si = si.tz_localize(None)
                sh.index = si
                sc = sh.index[sh.index > pd.Timestamp(period_date)]
                if len(sc):
                    sp = int(sh.index.get_loc(sc[0]))
                    for fd in forward_days:
                        sr = _forward_return(sh, sp, fd)
                        r[f"FwdAlpha_{fd}D"] = r.get(f"Fwd_{fd}D", np.nan) - sr if pd.notna(sr) else np.nan
            quarter_rows.append(r.to_dict())

    bt = pd.DataFrame(quarter_rows)
    if bt.empty:
        return bt, pd.DataFrame()
    summary_rows = []
    for fd in forward_days:
        col = f"Fwd_{fd}D"
        alpha_col = f"FwdAlpha_{fd}D"
        vals = pd.to_numeric(bt[col], errors="coerce") if col in bt else pd.Series(dtype=float)
        alphas = pd.to_numeric(bt[alpha_col], errors="coerce") if alpha_col in bt else pd.Series(dtype=float)
        strong = bt[bt["SML_Percentile"] >= 95] if "SML_Percentile" in bt else bt.iloc[0:0]
        top15 = bt[bt["SML_Percentile"] >= 85] if "SML_Percentile" in bt else bt.iloc[0:0]
        svals = pd.to_numeric(strong[col], errors="coerce") if col in strong else pd.Series(dtype=float)
        tvals = pd.to_numeric(top15[col], errors="coerce") if col in top15 else pd.Series(dtype=float)
        summary_rows.append({
            "기간": f"{fd}D",
            "전체 평균수익률": vals.mean(),
            "전체 중앙수익률": vals.median(),
            "SML 상위5% 평균": svals.mean(),
            "SML 상위15% 평균": tvals.mean(),
            "상위5% 승률": (svals > 0).mean() if len(svals) else np.nan,
            "전체 시장초과수익": alphas.mean(),
            "상위5% 시장초과": pd.to_numeric(strong[alpha_col], errors="coerce").mean() if alpha_col in strong else np.nan
        })
    return bt, pd.DataFrame(summary_rows)

# --- UI 레이아웃 ---
st.title("🎯 SEC 13F SML 레이더 v1.5")
st.caption("스마트머니 래그(SML) 분석 | 수급 vs 소외 기여도 분해 | 절대금액 + 상대수급 균형 | 공시 일정 모니터링")

with st.expander("📖 SML 점수 및 퀀트 팩터(SML 2.0) 상세 가이드 (필독)", expanded=False):
    st.markdown(
        """
        ### 1. SML 점수(Smart Money Lag Score)란?
        * **개념**: **"스마트머니(월가 대형 기관)의 집중 매수가 유입되었음에도, 주가는 아직 오르지 않고 뒤처진(Lag) 저평가 종목"**을 발굴하는 퀀트 앙상블 스코어입니다 (100점 만점).
        * **핵심 가설**: 거대 자본을 굴리는 전문 기관들은 장기간에 걸쳐 분할 매집하며, 공시 이후 시장의 관심이 쏠리면서 뒤늦게 주가가 제자리를 찾아가는 '시차 반등(Lag Reversal)' 현상을 노립니다.
        * **종합 공식**: 
          $$\\text{SML 점수} = \\underbrace{(\\text{수급 점수} \\times 0.55)}_{\\text{스마트머니 수급 기여도 (최대 55점)}} + \\underbrace{(\\text{소외 점수} \\times 0.45)}_{\\text{가격 저평가/래깅 기여도 (최대 45점)}}$$
        * **앙상블 서브 모델 가중치**: $0.40 \\times M_1 + 0.35 \\times M_2 + 0.25 \\times M_3$

        ---
        ### 2. 투자 시그널 기준 (대형주 개편 모델 최적화)
        * **🟢 STRONG_BUY (적극 매수)**: SML 상위 5% + 10일 CMF 양수
        * **🔵 ACCUMULATE (분할 매집)**: SML 상위 5~15%
        * **🟡 WATCH_LAG (단기 관망)**: SML 상위 15%이나 10일 CMF가 약함
        * **🟠 WATCH (관찰)**: SML 상위 30% 이내
        * **⚪ NEUTRAL (중립/대기)**: 그 외
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
    # 💡 기본값 300, 최댓값 500 반영
    top_n = st.slider("최종 출력 종목 수 (상위 N개)", min_value=20, max_value=500, value=300, step=10)
with col2:
    sec_neutral = st.checkbox("시장(SPY) 대비 상대수익률 적용", value=True)
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
        
        status_box.markdown("📊 **스마트머니 순유입 및 직전 공시 대조 집계 중...**")
        prog.progress(55)
        
        tot = {}
        for r in curr_records:
            k = (r["cik"], r["cusip"])
            c = r["cusip"]
            is_new = (k not in prev_records)
            p_val = prev_records[k]["val"] if not is_new else 0
            p_shares = prev_records[k]["shares"] if not is_new else 0
            curr_shares = r["shares"]

            # 13F 평가액 증가는 주가 상승만으로도 발생할 수 있으므로
            # '실제 보유주식 증가'를 핵심 수급 이벤트로 사용한다.
            share_diff = max(0, curr_shares - p_shares)
            if is_new:
                buy_type = "신규"
                diff_s = curr_shares
            elif share_diff > 0:
                buy_type = "확대"
                diff_s = share_diff
            else:
                continue

            # 13F 평가액 변화는 주가 상승에도 발생하므로, 실제 주식수 증가를
            # 해당 분기 보고가격(value / shares)으로 환산한 추정 매수대금을 사용한다.
            # 13F는 거래내역을 공개하지 않으므로 '실제 체결금액'이 아닌 수급 강도 proxy다.
            if curr_shares > 0:
                reported_price = (r["val"] * 1000.0) / curr_shares
                diff_v_reported = reported_price * diff_s
            else:
                diff_v_reported = max(0, r["val"] - p_val) if not is_new else r["val"]
            if c not in tot:
                tot[c] = {
                    "name": r["name"],
                    "funds": set(),
                    "new_funds": set(),
                    "inflow": 0.0,
                    "shares": 0,
                    "current_value": 0.0,
                    "f_date": r["f_date"],
                    "details": []
                }
            tot[c]["funds"].add(r["fund"])
            if is_new:
                tot[c]["new_funds"].add(r["fund"])
            tot[c]["inflow"] += diff_v_reported
            tot[c]["shares"] += diff_s
            tot[c]["current_value"] += r["val"]
            tot[c]["details"].append({
                "fund": r["fund"],
                "type": buy_type,
                "had_prev": "O (기보유)" if not is_new else "X (미보유)",
                "prev_shares": p_shares,
                "diff_shares": diff_s,
                "shares_pct": round((diff_s / p_shares * 100.0), 1) if p_shares > 0 else 999.9,
                "prev_val_m": round(p_val / 1000.0, 1),
                "diff_val_m": round(diff_v_reported / 1000.0, 1)
            })

        # 기관 수급 breadth를 먼저 확보하되, 순위 후보는 절대금액만으로 자르지 않는다.
        ranked = sorted(
            tot.items(),
            key=lambda x: (len(x[1]["funds"]), x[1]["inflow"]),
            reverse=True
        )[:top_n]

        # 티커 해석은 캐시된 함수들을 이용하고, 시세는 가능한 한 한 번에 내려받는다.
        resolved = []
        for cusip, d in ranked:
            resolved.append((cusip, d, resolve_ticker_advanced(cusip, d["name"])))
        tickers = list(dict.fromkeys([tk for _, _, tk in resolved if tk != "-"]))
        market_hist = {}
        if tickers:
            try:
                dl = yf.download(
                    tickers=tickers,
                    period="1y",
                    interval="1d",
                    auto_adjust=False,
                    progress=False,
                    group_by="ticker",
                    threads=True
                )
                if isinstance(dl.columns, pd.MultiIndex):
                    for tk in tickers:
                        if tk in dl.columns.get_level_values(0):
                            h = dl[tk].dropna(how="all")
                            if not h.empty:
                                market_hist[tk] = h
                elif len(tickers) == 1 and not dl.empty:
                    market_hist[tickers[0]] = dl.dropna(how="all")
            except Exception:
                market_hist = {}

        # 시장 기준 ETF는 한 번만 조회. '섹터 중립'이라는 잘못된 가짜 sector mapping 대신 시장 상대수익률을 사용.
        spy_hist = None
        try:
            spy_hist = yf.download("SPY", period="1y", interval="1d", auto_adjust=False, progress=False, threads=False)
            if isinstance(spy_hist.columns, pd.MultiIndex):
                spy_hist = spy_hist.xs("SPY", axis=1, level=1)
            spy_hist = spy_hist.dropna(how="all")
        except Exception:
            spy_hist = None

        def trailing_return(hist, n):
            if hist is None or hist.empty or len(hist) < 2:
                return 0.0
            base = float(hist["Close"].iloc[max(0, len(hist) - n)])
            cur = float(hist["Close"].iloc[-1])
            return ((cur / base) - 1.0) * 100.0 if base > 0 else 0.0

        market_ret_6m = trailing_return(spy_hist, 126)
        market_ret_3m = trailing_return(spy_hist, 63)

        data_rows = []
        tot_stocks = len(resolved)
        total_funds_selected = max(len(funds_to_analyze), 1)
        for s_idx, (cusip, d, tk) in enumerate(resolved):
            status_box.markdown(f"📈 **[2단계: 시세/팩터 검증 {s_idx+1}/{tot_stocks}]** `{d['name'][:25]}` (티커: `{tk}`) 데이터 분석 중...")
            prog.progress(55 + int(((s_idx + 1) / max(tot_stocks, 1)) * 45))

            rel_ret, ret_3m, dist_52w = 0.0, 0.0, 0.0
            ad_pass, cmf_10d, avg_clv = False, 0.0, 0.0
            cur_p, base_p, price_chg, pct_chg = 0.0, 0.0, 0.0, 0.0
            h = market_hist.get(tk)
            if h is not None and not h.empty and len(h) >= 20:
                try:
                    close = h["Close"].astype(float)
                    cur_p = float(close.iloc[-1])
                    start_6m = float(close.iloc[max(0, len(close) - 126)])
                    start_3m = float(close.iloc[max(0, len(close) - 63)])
                    rel_ret = ((cur_p / start_6m) - 1.0) * 100.0 if start_6m > 0 else 0.0
                    ret_3m = ((cur_p / start_3m) - 1.0) * 100.0 if start_3m > 0 else 0.0
                    max_p = float(h["High"].astype(float).max())
                    dist_52w = ((cur_p - max_p) / max_p) * 100.0 if max_p > 0 else 0.0

                    # 공시일 이후 수익률: 실제 투자자가 정보를 얻은 filing date 이후부터 계산
                    target_dt = pd.Timestamp(d["f_date"])
                    if getattr(h.index, "tz", None) is not None:
                        target_dt = target_dt.tz_localize(h.index.tz)
                    hist_since = h[h.index >= target_dt]
                    base_p = float(hist_since["Close"].iloc[0]) if not hist_since.empty else cur_p
                    price_chg = cur_p - base_p
                    pct_chg = (price_chg / base_p) * 100.0 if base_p > 0 else 0.0

                    high = h["High"].astype(float)
                    low = h["Low"].astype(float)
                    volume = h["Volume"].astype(float)
                    denom = (high - low).replace(0, np.nan)
                    clv = (((close - low) - (high - close)) / denom).fillna(0.0).clip(-1, 1)
                    recent = pd.DataFrame({"clv": clv, "vol": volume}).tail(10)
                    vol_sum = float(recent["vol"].sum())
                    cmf_10d = float((recent["clv"] * recent["vol"]).sum() / vol_sum) if vol_sum > 0 else 0.0
                    avg_clv = float(recent["clv"].mean())
                    ad_pass = cmf_10d >= 0.0
                except Exception:
                    pass

            inflow_m = d["inflow"] / 1000.0
            current_holdings_m = d["current_value"] / 1000.0
            # 평균 일 거래대금: 최근 20일 dollar volume 기준
            adv_m = 0.0
            if h is not None and not h.empty:
                try:
                    adv_m = float((h["Close"].astype(float) * h["Volume"].astype(float)).tail(20).mean()) / 1_000_000.0
                except Exception:
                    adv_m = 0.0
            flow_adv_ratio = inflow_m / adv_m if adv_m > 0 else 0.0
            flow_holdings_ratio = inflow_m / current_holdings_m if current_holdings_m > 0 else 0.0

            data_rows.append({
                "CUSIP": cusip,
                "Ticker": tk,
                "Name": d["name"],
                "Sector": "General",
                "Fund_Count": len(d["funds"]),
                "New_Fund_Count": len(d["new_funds"]),
                "Total_Funds": total_funds_selected,
                "Inflow_M": round(inflow_m, 1),
                "Shares_Sum": d["shares"],
                "Current_Holdings_M": round(current_holdings_m, 1),
                "Flow_ADV_Ratio": flow_adv_ratio,
                "Flow_Holdings_Ratio": flow_holdings_ratio,
                "Rel_Return": round(rel_ret, 2),
                "Return_3M": round(ret_3m, 2),
                "Market_Return_6M": round(market_ret_6m, 2),
                "Market_Return_3M": round(market_ret_3m, 2),
                "Dist_52W": round(dist_52w, 2),
                "AD_Pass": ad_pass,
                "CMF_10D": cmf_10d,
                "AD_Chg_Pct": round(cmf_10d * 100.0, 1),
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
        
        res_df = calc_score(pd.DataFrame(data_rows), market_neutral=sec_neutral)
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
    # 탑픽 5 (Top Picks 5) 모듈
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

        s3 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="Flow_Score", ascending=False)
        if not s3.empty:
            t3 = s3.iloc[0]
            theme_picks.append({
                "전략 슬롯": "⚡ 수급 급증", "티커": t3["Ticker"], "기업명": t3["Name"],
                "SML점수": t3["SML_Score"], "현재가($)": t3["Price_Val"], "공시후변동률": t3["Pct_Chg"],
                "A/D변화": t3["AD_Chg_Pct"], "선정 이유": f"상대 수급강도 {t3['Flow_Score']:.1f}점"
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

        s5 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="SML_Percentile", ascending=False)
        if not s5.empty:
            t5 = s5.iloc[0]
            theme_picks.append({
                "전략 슬롯": "💎 밸류 앙상블", "티커": t5["Ticker"], "기업명": t5["Name"],
                "SML점수": t5["SML_Score"], "현재가($)": t5["Price_Val"], "공시후변동률": t5["Pct_Chg"],
                "A/D변화": t5["AD_Chg_Pct"], "선정 이유": f"SML 상위 {100-t5['SML_Percentile']+1:.1f}%"
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

    # ==========================================
    # 메인 퀀트 테이블 (수급 vs 소외도 컬럼 탑재)
    # ==========================================
    st.subheader(f"📋 퀀트 랭킹 & 공시일 대비 성과 (총 {len(df_show)}개 종목)")
    st.caption("💡 **수급점수 또는 소외도 헤더를 클릭**하면 자금 유입 최상위주 또는 바닥 소외주 순서로 바로 재정렬할 수 있습니다.")

    table_df = df_show[[
        "Rank", "Ticker", "Name", "SML_Score", "SML_Percentile", "Inst_Score", "Lag_Score",
        "Accumulation_Score", "Signal", "Base_Price", "Price_Val", "Price_Chg", "Pct_Chg",
        "Fund_Count", "Inflow_M"
    ]].copy()
    
    table_df.columns = [
        "순위", "티커", "기업명", "SML 점수", "SML 백분위", "수급점수(55%)", "소외도(45%)",
        "10D 매집점수", "투자시그널", "공시일주가($)", "현재가($)", "공시후변동($)", "공시후변동률(%)",
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
            "SML 백분위": st.column_config.NumberColumn(format="%.1f %%ile"),
            "수급점수(55%)": st.column_config.NumberColumn(format="%.1f 점"),
            "소외도(45%)": st.column_config.NumberColumn(format="%.1f 점"),
            "10D 매집점수": st.column_config.NumberColumn(format="%.1f 점"),
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
        
        # --- 종목 상세 분석 및 기여도 분해 영역 ---
        st.subheader(f"🔍 [{current_tk}] {sel_row['Name']} 심층 팩터 분석 & 매수 기관")
        
        col_m1, col_m2, col_m3 = st.columns([1.2, 1, 1])
        with col_m1:
            st.metric("종합 SML 점수", f"{sel_row['SML_Score']:.1f} 점", sel_row['Signal'])
        with col_m2:
            st.metric("🏛️ 기관 수급 점수 (55% 축)", f"{sel_row['Inst_Score']:.1f} 점", f"기여: +{sel_row['Inst_Contrib']:.1f}점 / 55.0")
        with col_m3:
            st.metric("📉 가격 소외도 (45% 축)", f"{sel_row['Lag_Score']:.1f} 점", f"기여: +{sel_row['Lag_Contrib']:.1f}점 / 45.0")

        inst_ratio = int((sel_row['Inst_Contrib'] / max(sel_row['SML_Score'], 0.1)) * 100)
        lag_ratio = 100 - inst_ratio
        st.caption(f"⚖️ **상승 모멘텀 원천 분석**: 수급 주도형 `{inst_ratio}%` vs 바닥 반등형 `{lag_ratio}%`")
        st.progress(min(max(inst_ratio / 100.0, 0.0), 1.0))

        with st.expander("📐 SML 점수 계산 요소별 비중 및 기여도 (Factor Breakdown)", expanded=True):
            st.markdown("**점수 분해 공식**:")
            latex_expr = (
                r"\text{SML 점수} = (" + f"{sel_row['Inst_Score']:.1f}" + r" \times 0.55) + ("
                + f"{sel_row['Lag_Score']:.1f}" + r" \times 0.45) = \mathbf{+"
                + f"{sel_row['Inst_Contrib']:.1f}" + r"\text{점(수급)}} + \mathbf{+"
                + f"{sel_row['Lag_Contrib']:.1f}" + r"\text{점(소외)}} = \mathbf{"
                + f"{sel_row['SML_Score']:.1f}" + r"\text{점}}"
            )
            st.latex(latex_expr)

            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.markdown(f"##### 🏛️ 스마트머니 수급 지표 (기여: +{sel_row['Inst_Contrib']:.1f}점)")
                st.write(f"- **기관 참여폭**: {sel_row['Fund_Count']}개 사")
                st.write(f"- **13F 평가액 순증분(참고)**: ${sel_row['Inflow_M']:,.1f} M")
                
            with b_col2:
                st.markdown(f"##### 📉 가격 소외 및 시장 매집강도 지표 (기여: +{sel_row['Lag_Contrib']:.1f}점)")
                if sel_row["Price_Val"] > 0:
                    st.write(f"- **6개월 시장 대비 상대수익률**: {sel_row['Rel_Return']:+.1f}%")
                    st.write(f"- **52주 고점 대비 괴리율**: {sel_row['Dist_52W']:.1f}%")
                    
                    chg_sign = "🔴 +" if sel_row["Price_Chg"] > 0 else ("🔵 -" if sel_row["Price_Chg"] < 0 else "")
                    chg_abs = abs(sel_row["Price_Chg"])
                    pct_str = f"{sel_row['Pct_Chg']:+.2f}%"
                    st.write(
                        f"- **공시 시점 대비 주가 추이**: \\${sel_row['Base_Price']:.2f} → **\\${sel_row['Price_Val']:.2f}** "
                        f"({chg_sign}\\${chg_abs:.2f}, {pct_str})"
                    )
                    
                    pass_str = "✅ PASS (매집 유입 확인)" if sel_row["AD_Pass"] else "❌ FAIL (분산/차익매도 우려)"
                    st.markdown(f"- **10일 시장 매집강도(CMF)**: **{pass_str}**")
                    st.write(f"  * **최근 10일 CMF**: `{sel_row['CMF_10D']:+.3f}` *(+1에 가까울수록 매집 압력 우세)*")
                    st.write(f"  * **평균 장중 종가 위치 (CLV)**: `{sel_row['Avg_CLV']:+.2f}` *(범위: -1.0 ~ +1.0 / +에 가까울수록 고가 마감)*")
                else:
                    st.warning("⚠️ 실시간 시세 미조회 종목으로 가격 지표 및 추천 시그널이 산출되지 않았습니다.")

        # 매수 기관 목록
        st.markdown(f"##### 📋 {sel_row['Name']} 매수 참여 기관 목록 (직전 공시 대조)")
        dt_df = pd.DataFrame(sel_row["details"])
        dt_df = dt_df.sort_values(by="diff_val_m", ascending=False).reset_index(drop=True)
        
        def fmt_shares_growth(r):
            if r["type"] == "신규":
                return "신규 편입 (NEW)"
            elif r["shares_pct"] >= 999.0:
                return "대폭 확대"
            else:
                return f"+{r['shares_pct']:.1f}%"

        dt_df["주식증감률"] = dt_df.apply(fmt_shares_growth, axis=1)

        dt_table = dt_df[[
            "fund", "type", "had_prev", "prev_shares", "diff_shares", "주식증감률", "prev_val_m", "diff_val_m"
        ]].copy()
        
        dt_table.columns = [
            "기관명", "매수구분", "직전보유여부", "직전보유주식수", "이번매수주식수", "주식증감률", "직전보유액($M)", "이번매수액($M)"
        ]
        
        st.dataframe(
            dt_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "직전보유주식수": st.column_config.NumberColumn(format="%d 주"),
                "이번매수주식수": st.column_config.NumberColumn(format="%d 주"),
                "주식증감률": st.column_config.TextColumn(),
                "직전보유액($M)": st.column_config.NumberColumn(format="$%.1f M"),
                "이번매수액($M)": st.column_config.NumberColumn(format="$%.1f M"),
            }
        )
    else:
        st.info("선택한 필터 조건에 부합하는 종목이 없습니다.")

# ============================================================
# 📊 Walk-forward Backtest UI
# ============================================================
st.divider()
st.subheader("📊 SML 2.0 워크포워드 백테스트")
st.caption(
    "과거 13F 공시 시점에서 당시 공개된 정보만으로 SML을 계산한 뒤, 이후 실제 주가 성과를 검증합니다. "
    "현재 점수의 사후적 성과가 아니라 '그때 이 종목을 골랐다면?'을 재현하는 방식입니다."
)

bt_c1, bt_c2, bt_c3, bt_c4 = st.columns([1, 1, 1, 1.3])
with bt_c1:
    bt_quarters = st.slider("백테스트 분기 수", min_value=2, max_value=8, value=4, step=1)
with bt_c2:
    bt_top_n = st.slider("분기별 후보 종목 수", min_value=50, max_value=300, value=100, step=25)
with bt_c3:
    bt_market_neutral = st.checkbox("SPY 대비 초과수익 사용", value=True, key="bt_market_neutral")
with bt_c4:
    bt_run = st.button("🧪 백테스트 실행", type="primary", key="run_backtest")

if bt_run:
    if not funds_to_analyze:
        st.error("백테스트할 기관을 최소 1개 이상 선택하세요.")
    else:
        with st.spinner(
            f"과거 {bt_quarters}개 분기의 13F → 가격데이터 → SML → 미래수익률을 순차적으로 계산 중입니다..."
        ):
            bt_detail, bt_summary = run_walk_forward_backtest(
                funds_to_analyze,
                n_quarters=bt_quarters,
                top_n=bt_top_n,
                market_neutral=bt_market_neutral,
                forward_days=(21, 63, 126)
            )
        st.session_state["backtest_detail"] = bt_detail
        st.session_state["backtest_summary"] = bt_summary

if "backtest_summary" in st.session_state:
    bt_summary = st.session_state["backtest_summary"]
    bt_detail = st.session_state.get("backtest_detail", pd.DataFrame())

    if bt_summary.empty or bt_detail.empty:
        st.warning("백테스트 결과가 없습니다. SEC 공시 또는 과거 시세 데이터를 확인하세요.")
    else:
        st.markdown("### ① 성과 요약")
        show_summary = bt_summary.copy()
        for c in ["전체 평균수익률", "전체 중앙수익률", "SML 상위5% 평균", "SML 상위15% 평균", "전체 시장초과수익", "상위5% 시장초과"]:
            if c in show_summary.columns:
                show_summary[c] = pd.to_numeric(show_summary[c], errors="coerce").round(2)
        if "상위5% 승률" in show_summary.columns:
            show_summary["상위5% 승률"] = (pd.to_numeric(show_summary["상위5% 승률"], errors="coerce") * 100).round(1)
        st.dataframe(
            show_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "전체 평균수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                "전체 중앙수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                "SML 상위5% 평균": st.column_config.NumberColumn(format="%+.2f%%"),
                "SML 상위15% 평균": st.column_config.NumberColumn(format="%+.2f%%"),
                "상위5% 승률": st.column_config.NumberColumn(format="%.1f%%"),
                "전체 시장초과수익": st.column_config.NumberColumn(format="%+.2f%%"),
                "상위5% 시장초과": st.column_config.NumberColumn(format="%+.2f%%"),
            }
        )

        # 가장 중요한 검증 포인트: SML 상위군이 실제로 미래수익률을 개선시키는지
        st.markdown("### ② 핵심 검증")
        latest_126 = bt_summary[bt_summary["기간"] == "126D"]
        if not latest_126.empty:
            x = latest_126.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("상위 5% 6개월 평균", f"{x['SML 상위5% 평균']:+.2f}%")
            c2.metric("상위 15% 6개월 평균", f"{x['SML 상위15% 평균']:+.2f}%")
            c3.metric("상위 5% 승률", f"{x['상위5% 승률']*100:.1f}%")
            c4.metric("상위 5% 시장초과", f"{x['상위5% 시장초과']:+.2f}%")

        # 분기별로 실제 어떤 종목이 선택되었는지 확인
        st.markdown("### ③ 백테스트 개별 관측치")
        bt_view_cols = [
            "period", "Filing_Date", "Ticker", "Name", "Fund_Count", "Inflow_M",
            "SML_Score", "SML_Percentile", "Inst_Score", "Lag_Score",
            "Accumulation_Score", "Fwd_21D", "Fwd_63D", "Fwd_126D",
            "FwdAlpha_21D", "FwdAlpha_63D", "FwdAlpha_126D"
        ]
        bt_view_cols = [c for c in bt_view_cols if c in bt_detail.columns]
        bt_view = bt_detail[bt_view_cols].copy()
        bt_view = bt_view.sort_values(["period", "SML_Score"], ascending=[False, False])
        rename_bt = {
            "period": "보고분기", "Filing_Date": "공시일", "Ticker": "티커", "Name": "기업명",
            "Fund_Count": "기관수", "Inflow_M": "추정유입($M)", "SML_Score": "SML점수",
            "SML_Percentile": "SML백분위", "Inst_Score": "수급점수", "Lag_Score": "소외도",
            "Accumulation_Score": "매집점수", "Fwd_21D": "21D수익률", "Fwd_63D": "63D수익률",
            "Fwd_126D": "126D수익률", "FwdAlpha_21D": "21D초과수익", "FwdAlpha_63D": "63D초과수익",
            "FwdAlpha_126D": "126D초과수익"
        }
        bt_view = bt_view.rename(columns=rename_bt)
        st.dataframe(
            bt_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "추정유입($M)": st.column_config.NumberColumn(format="$%.1f M"),
                "SML점수": st.column_config.NumberColumn(format="%.1f"),
                "SML백분위": st.column_config.NumberColumn(format="%.1f%%ile"),
                "수급점수": st.column_config.NumberColumn(format="%.1f"),
                "소외도": st.column_config.NumberColumn(format="%.1f"),
                "매집점수": st.column_config.NumberColumn(format="%.1f"),
                "21D수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                "63D수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                "126D수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                "21D초과수익": st.column_config.NumberColumn(format="%+.2f%%"),
                "63D초과수익": st.column_config.NumberColumn(format="%+.2f%%"),
                "126D초과수익": st.column_config.NumberColumn(format="%+.2f%%"),
            }
        )

        st.markdown("### ④ 해석 가이드")
        st.info(
            "이 백테스트에서 가장 중요한 것은 단순 평균수익률보다 **SML 상위 5%가 상위 15%/전체보다 일관되게 높은지**, "
            "그리고 **SPY 대비 초과수익이 양수인지**입니다. 또한 분기별 표에서 특정 종목이나 한 분기에 의해 결과가 왜곡되는지도 확인해야 합니다. "
            "현재 결과는 전략의 유효성을 증명하는 것이 아니라, 다음 단계인 가중치·임계값 최적화를 위한 검증 데이터입니다."
        )

        csv = bt_detail.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ 전체 백테스트 결과 CSV 다운로드",
            data=csv,
            file_name="sml_walk_forward_backtest.csv",
            mime="text/csv",
            key="download_bt_csv"
        )
