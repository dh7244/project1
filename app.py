# -*- coding: utf-8 -*-
import datetime
import json
import re
import time
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="13F SML Radar v2.0",
    page_icon="📈",
    layout="wide"
)

USER_AGENT = "QuantStreamlitApp quant_analyst@quantfirm.org"
HEADERS = {"User-Agent": USER_AGENT}

DEFAULT_FUNDS = {"시타델 (Citadel Advisors)": "0001423053", "르네상스 테크놀로지 (Renaissance Tech)": "0001037389", "밀레니엄 매니지먼트 (Millennium Mgmt)": "0001273087", "투 시그마 (Two Sigma Investments)": "0001179392", "D.E. 쇼 (D.E. Shaw & Co.)": "0001009207", "포인트72 (Point72 / Steve Cohen)": "0001603466", "AQR 캐피탈 (AQR Capital Mgmt)": "0001167557", "브릿지워터 (Bridgewater Associates)": "0001350694", "발리아스니 (Balyasny Asset Mgmt)": "0001262279", "엑소더스포인트 (ExodusPoint Capital)": "0001744489", "버크셔 해서웨이 (Berkshire Hathaway)": "0001067983", "타이거 글로벌 (Tiger Global)": "0001167483", "코튜 매니지먼트 (Coatue / Philippe Laffont)": "0001422183", "바이킹 글로벌 (Viking Global / Halvorsen)": "0001103804", "퍼싱 스퀘어 (Pershing Square / Ackman)": "0001336528", "아팔루사 (Appaloosa / David Tepper)": "0001006438", "듀케인 패밀리오피스 (Duquesne / Druckenmiller)": "0001536411", "소로스 펀드 (Soros Fund Management)": "0001029160", "서드 포인트 (Third Point / Dan Loeb)": "0001040273", "그린라이트 캐피탈 (Greenlight / David Einhorn)": "0001079114", "바우포스트 그룹 (Baupost / Seth Klarman)": "0001061768", "론 파인 캐피탈 (Lone Pine / Steve Mandel)": "0001061165", "아크 인베스트 (ARK Invest / Cathie Wood)": "0001697748", "엘리엇 매니지먼트 (Elliott Investment Mgmt)": "0001048445", "스타보드 밸류 (Starboard Value)": "0001513824", "아이칸 엔터프라이즈 (Carl Icahn)": "0000921669", "페어홀름 (Fairholme Capital / Berkowitz)": "0001111565", "세스콰하나 (Susquehanna International)": "0001446194", "블랙록 (BlackRock Fund Advisors)": "0001364742", "뱅가드 그룹 (Vanguard Group)": "0000102909", "피델리티 (FMR LLC)": "0000315066", "스테이트 스트리트 (State Street Corp)": "0000093751", "웰링턴 매니지먼트 (Wellington Management)": "0000902219", "T. 로우 프라이스 (T. Rowe Price)": "0000080255", "캐피탈 리서치 (Capital Research Global)": "0001423052", "베일리 기포드 (Baillie Gifford & Co)": "0001088875", "인베스코 (Invesco Ltd.)": "0000914208", "노던 트러스트 (Northern Trust Corp)": "0000073124", "프랭클린 리소시스 (Franklin Resources)": "0000038777", "얼라이언스 번스틴 (AllianceBernstein)": "0001109448", "JP모건 체이스 (JPMorgan Chase & Co)": "0000019617", "골드만 삭스 (Goldman Sachs Group)": "0000886982", "모건 스탠리 (Morgan Stanley)": "0000895421", "뱅크 오브 아메리카 (Bank of America)": "0000070858", "시티그룹 (Citigroup Inc)": "0000831001", "웰스 파고 (Wells Fargo & Co)": "0000072971", "UBS 그룹 (UBS Group AG)": "0001610520", "노르웨이 국부펀드 (Norges Bank)": "0001270787", "Dodge & Cox (Dodge & Cox)": "0000200217", "아티산 파트너스 (Artisan Partners)": "0001466153"}

EXTENDED_FUNDS = {"시타델 (Citadel Advisors)": "0001423053", "르네상스 테크놀로지 (Renaissance Tech)": "0001037389", "밀레니엄 매니지먼트 (Millennium Mgmt)": "0001273087", "투 시그마 (Two Sigma Investments)": "0001179392", "D.E. 쇼 (D.E. Shaw & Co.)": "0001009207", "포인트72 (Point72 / Steve Cohen)": "0001603466", "AQR 캐피탈 (AQR Capital Mgmt)": "0001167557", "브릿지워터 (Bridgewater Associates)": "0001350694", "발리아스니 (Balyasny Asset Mgmt)": "0001262279", "엑소더스포인트 (ExodusPoint Capital)": "0001744489", "버크셔 해서웨이 (Berkshire Hathaway)": "0001067983", "타이거 글로벌 (Tiger Global)": "0001167483", "코튜 매니지먼트 (Coatue / Philippe Laffont)": "0001422183", "바이킹 글로벌 (Viking Global / Halvorsen)": "0001103804", "퍼싱 스퀘어 (Pershing Square / Ackman)": "0001336528", "아팔루사 (Appaloosa / David Tepper)": "0001006438", "듀케인 패밀리오피스 (Duquesne / Druckenmiller)": "0001536411", "소로스 펀드 (Soros Fund Management)": "0001029160", "서드 포인트 (Third Point / Dan Loeb)": "0001040273", "그린라이트 캐피탈 (Greenlight / David Einhorn)": "0001079114", "바우포스트 그룹 (Baupost / Seth Klarman)": "0001061768", "론 파인 캐피탈 (Lone Pine / Steve Mandel)": "0001061165", "아크 인베스트 (ARK Invest / Cathie Wood)": "0001697748", "엘리엇 매니지먼트 (Elliott Investment Mgmt)": "0001048445", "스타보드 밸류 (Starboard Value)": "0001513824", "아이칸 엔터프라이즈 (Carl Icahn)": "0000921669", "페어홀름 (Fairholme Capital / Berkowitz)": "0001111565", "세스콰하나 (Susquehanna International)": "0001446194", "블랙록 (BlackRock Fund Advisors)": "0001364742", "뱅가드 그룹 (Vanguard Group)": "0000102909", "피델리티 (FMR LLC)": "0000315066", "스테이트 스트리트 (State Street Corp)": "0000093751", "웰링턴 매니지먼트 (Wellington Management)": "0000902219", "T. 로우 프라이스 (T. Rowe Price)": "0000080255", "캐피탈 리서치 (Capital Research Global)": "0001423052", "베일리 기포드 (Baillie Gifford & Co)": "0001088875", "인베스코 (Invesco Ltd.)": "0000914208", "노던 트러스트 (Northern Trust Corp)": "0000073124", "프랭클린 리소시스 (Franklin Resources)": "0000038777", "얼라이언스 번스틴 (AllianceBernstein)": "0001109448", "JP모건 체이스 (JPMorgan Chase & Co)": "0000019617", "골드만 삭스 (Goldman Sachs Group)": "0000886982", "모건 스탠리 (Morgan Stanley)": "0000895421", "뱅크 오브 아메리카 (Bank of America)": "0000070858", "시티그룹 (Citigroup Inc)": "0000831001", "웰스 파고 (Wells Fargo & Co)": "0000072971", "UBS 그룹 (UBS Group AG)": "0001610520", "노르웨이 국부펀드 (Norges Bank)": "0001270787", "Dodge & Cox (Dodge & Cox)": "0000200217", "아티산 파트너스 (Artisan Partners)": "0001466153", "데이비스 셀렉티드 (Davis Selected Advisers)": "0001036325", "뉴버거 버먼 (Neuberger Berman)": "0001465109", "폴렌 캐피탈 (Polen Capital)": "0001034524", "파르나서스 인베스트먼트 (Parnassus)": "0000948669", "블랙스톤 (Blackstone)": "0001393818", "TIAA CREF Investment Management": "0000887793", "트라이언 펀드 (Trian Partners)": "0001345471", "글렌뷰 캐피탈 (Glenview Capital)": "0001138995", "코벡스 매니지먼트 (Corvex)": "0001535472", "파라론 캐피탈 (Farallon Capital)": "0000909661", "에미넌스 캐피탈 (Eminence Capital)": "0001107310", "매버릭 캐피탈 (Maverick Capital)": "0000934639", "JANA Partners": "0001998597", "Dragoneer Investment Group": "0001602189", "D1 Capital Partners": "0001747057", "Himalaya Capital Management": "0001709323", "HHLR Advisors (Hillhouse)": "0001762304", "제인 스트리트 (Jane Street Group)": "0001599947", "위즈덤트리 (WisdomTree Inc)": "0001350487", "ValueAct Capital": "0001104659", "KKR & Co.": "0001404912", "Apollo Global Management": "0001411494", "Carlyle Group": "0001527166", "Ares Management": "0001482430", "Oaktree Capital Management": "0000948484", "Verde Partners": "0001534505", "Cooper Investors": "0001051003", "Ensign Peak Advisors": "0001589029", "GEODE Capital Management": "0001052871", "Dimensional Fund Advisors": "0000354204", "Janus Henderson Investors": "0001270511", "Lazard Asset Management": "0001059556", "MFS Investment Management": "0001166559", "Federated Hermes": "0001056288", "Nuveen Asset Management": "0000809417", "Columbia Threadneedle Investments": "0001072950", "First Eagle Investment Management": "0001073753", "Jennison Associates": "0000822478", "American Century Investment Services": "0000783412", "Victory Capital Management": "0001593604", "RBC Global Asset Management": "0000907404", "PIMCO": "0001099248", "Franklin Advisory Services": "0000916540", "Legg Mason": "0000703636", "Hotchkis & Wiley Capital Management": "0000880774", "Causeway Capital Management": "0001051659", "Davis Selected Advisers (duplicate check)": "0001036325", "Sands Capital Management": "0000927240", "RWC Asset Management": "0001544538", "Pzena Investment Management": "0001031888"}

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

# SEC ticker directory는 앱 시작 시 네트워크 요청을 하지 않는다.
# 실제 티커 매칭이 필요할 때만 lazy-load하여 첫 화면 로딩을 가볍게 한다.
@st.cache_data(ttl=86400, show_spinner=False)
def get_name_dict():
    return load_sec_ticker_directory()

@st.cache_data(ttl=86400, show_spinner=False)
def search_yahoo_ticker(query_name):
    # 최후의 fallback만 사용한다. 10,000개 후보를 Yahoo Search API에
    # 하나씩 보내면 rate-limit/timeout으로 분석이 멈출 수 있으므로
    # 이 함수는 아래 resolve_ticker_advanced에서 제한적으로 호출한다.
    clean_q = re.sub(r"[^a-zA-Z0-9 ]", " ", str(query_name)).strip()
    words = clean_q.split()[:4]
    if not words:
        return "-"
    search_str = " ".join(words)
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={search_str}&quotesCount=5&newsCount=0"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=2)
        if r.status_code == 200:
            quotes = r.json().get("quotes", [])
            for q in quotes:
                sym = str(q.get("symbol", "")).upper()
                qt = str(q.get("quoteType", "")).upper()
                if sym and qt in ("EQUITY", "ETF"):
                    return sym
    except Exception:
        pass
    return "-"


@st.cache_data(ttl=86400, show_spinner=False)
def build_sec_name_index():
    """SEC 공식 company_tickers를 issuer명 매칭용 역색인으로 만든다."""
    data = get_name_dict()
    index = {}
    suffixes = {
        "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY",
        "LTD", "LIMITED", "PLC", "LLC", "LP", "HOLDINGS", "HOLDING",
        "GROUP", "CLASS", "COMMON", "SHARES", "THE"
    }
    for nm, tk in data.items():
        tokens = [x for x in re.findall(r"[A-Z0-9]+", nm) if x not in suffixes and len(x) >= 3]
        for token in set(tokens):
            index.setdefault(token, set()).add((nm, tk, len(tokens)))
    return index


@st.cache_data(ttl=86400, show_spinner=False)
def resolve_ticker_local(cusip, name):
    """네트워크 없이 CUSIP/SEC 공식 issuer명으로 ticker를 최대한 결정한다."""
    if cusip in COMMON_CUSIP_MAP:
        return COMMON_CUSIP_MAP[cusip]
    nm_upper = str(name).upper()
    for kw, sym in EXPLICIT_NAME_MAP.items():
        if kw in nm_upper:
            return sym

    data = get_name_dict()
    clean = re.sub(r"[^A-Z0-9]", "", nm_upper)
    if clean in data:
        return data[clean]

    # 법인 suffix 제거 후 token 역색인으로 후보를 크게 줄인다.
    base = re.sub(r"\b(INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LTD|LIMITED|PLC|LLC|LP|HOLDINGS?|GROUP)\b", " ", nm_upper)
    # token 역색인으로 후보를 크게 줄인 뒤 가장 높은 overlap을 선택한다.
    tokens = set(re.findall(r"[A-Z0-9]+", base))
    tokens = {t for t in tokens if len(t) >= 3}
    idx = build_sec_name_index()
    candidates = {}
    for token in tokens:
        for sec_nm, tk, n_tok in idx.get(token, ()):
            candidates[(sec_nm, tk)] = n_tok
    if candidates:
        best = None
        best_score = -1.0
        for (sec_nm, tk), n_tok in candidates.items():
            sec_tokens = set(re.findall(r"[A-Z0-9]+", sec_nm)) - {"INC","INCORPORATED","CORP","CORPORATION","CO","COMPANY","LTD","LIMITED","PLC","LLC","LP","HOLDINGS","HOLDING","GROUP"}
            inter = len(tokens & sec_tokens)
            union = len(tokens | sec_tokens)
            score = (inter / union if union else 0.0) + (0.15 if tokens and tokens.issubset(sec_tokens) else 0.0)
            if inter >= 1 and score > best_score:
                best_score = score
                best = tk
        # 부분 일치가 단 하나뿐인 경우에는 오매칭 위험이 높으므로
        # 충분히 높은 유사도에서만 자동 채택한다.
        if best is not None and best_score >= 0.55:
            return best
    return "-"


def resolve_ticker_advanced(cusip, name, allow_yahoo=False):
    """안전 우선 ticker resolver.

    1) CUSIP/명시 매핑
    2) SEC 공식 ticker directory exact/정규화/엄격 fuzzy
    3) allow_yahoo=True인 소수의 미매칭 후보에 한해 Yahoo fallback

    Yahoo는 대량 호출하지 않고 상한을 호출부에서 관리한다.
    """
    tk = resolve_ticker_local(cusip, name)
    if tk != "-":
        return tk
    if allow_yahoo:
        return search_yahoo_ticker(name)
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

@st.cache_data(persist=True, show_spinner=False)
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

@st.cache_data(persist=True, show_spinner=False)
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
    - CMF는 이진 필터가 아니라 별도 Market Accumulation 확인점수로 사용
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

    # 설명용 하위 점수: 현재 SML 2.0의 세부 축을 설명하기 위한 보조 점수
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
# Cached market-data helpers
# ============================================================
@st.cache_data(ttl=1800, show_spinner=False)
def _normalize_yf_history(h, ticker=None):
    """yfinance 반환값을 항상 단일 OHLCV DataFrame으로 정규화한다."""
    if h is None or not isinstance(h, pd.DataFrame) or h.empty:
        return None
    x = h.copy()
    if isinstance(x.columns, pd.MultiIndex):
        # (Ticker, Field) / (Field, Ticker) 양쪽 모두 대응
        if ticker is not None:
            for level in range(x.columns.nlevels):
                vals = [str(v) for v in x.columns.get_level_values(level)]
                if str(ticker) in vals:
                    try:
                        x = x.xs(ticker, axis=1, level=level, drop_level=True)
                        break
                    except Exception:
                        pass
        if isinstance(x.columns, pd.MultiIndex):
            x.columns = [str(c[-1] if str(c[-1]).lower() in {"open","high","low","close","adj close","volume"} else c[0]) for c in x.columns]
    rename = {str(c).strip().lower(): c for c in x.columns}
    field_map = {}
    for want in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
        src = rename.get(want.lower())
        if src is not None:
            field_map[src] = want
    x = x.rename(columns=field_map)
    if "Close" not in x.columns and "Adj Close" in x.columns:
        x["Close"] = x["Adj Close"]
    if "Close" not in x.columns:
        return None
    x = x.loc[:, ~x.columns.duplicated()].copy()
    x.index = pd.to_datetime(x.index)
    if getattr(x.index, "tz", None) is not None:
        x.index = x.index.tz_localize(None)
    return x.dropna(subset=["Close"], how="all")

@st.cache_data(ttl=1800, show_spinner=False)
def download_price_history(tickers, start=None, end=None, period=None):
    """Yahoo 시세 수집기. 배치 다운로드 후 누락 ticker만 개별 재시도한다."""
    tickers = tuple(dict.fromkeys(str(t).strip().upper() for t in tickers if t and t != "-"))
    if not tickers:
        return {}
    out = {}

    def _kwargs(ts, threads=False):
        kw = dict(tickers=ts, interval="1d", auto_adjust=False, progress=False,
                  group_by="ticker", threads=threads)
        if period:
            kw["period"] = period
        else:
            kw["start"] = start
            kw["end"] = end
        return kw

    # 1차: 40개씩 배치. 큰 배치보다 실패/Rate limit에 강하다.
    for i in range(0, len(tickers), 40):
        chunk = list(tickers[i:i+40])
        try:
            dl = yf.download(**_kwargs(chunk, threads=False))
            if isinstance(dl.columns, pd.MultiIndex):
                for tk in chunk:
                    h = _normalize_yf_history(dl, tk)
                    if h is not None and len(h) > 0:
                        out[tk] = h
            elif len(chunk) == 1:
                h = _normalize_yf_history(dl, chunk[0])
                if h is not None and len(h) > 0:
                    out[chunk[0]] = h
        except Exception:
            pass

    # 2차: 배치에서 빠진 ticker만 개별 호출.
    missing = [tk for tk in tickers if tk not in out]
    for tk in missing:
        try:
            dl = yf.download(**_kwargs(tk, threads=False))
            h = _normalize_yf_history(dl, tk)
            if h is not None and len(h) >= 2:
                out[tk] = h
        except Exception:
            continue
    return out

@st.cache_data(ttl=1800, show_spinner=False)
def download_spy_history(start=None, end=None, period=None):
    try:
        kwargs = dict(tickers="SPY", interval="1d", auto_adjust=False, progress=False,
                      group_by="ticker", threads=False)
        if period:
            kwargs["period"] = period
        else:
            kwargs["start"] = start
            kwargs["end"] = end
        h = yf.download(**kwargs)
        out = _normalize_yf_history(h, "SPY")
        return out if out is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(persist=True, show_spinner=False)
def download_backtest_price_history(tickers, start, end):
    """백테스트 전용 영구 캐시. 동일 과거 구간은 앱을 재실행해도 재다운로드하지 않는다."""
    return download_price_history(tickers, start=start, end=end)

@st.cache_data(persist=True, show_spinner=False)
def download_backtest_spy_history(start, end):
    """백테스트 SPY 과거 시세 영구 캐시."""
    return download_spy_history(start=start, end=end)

# ============================================================
# Historical walk-forward backtest engine
# ============================================================
@st.cache_data(persist=True, show_spinner=False)
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
                              market_neutral=True, forward_days=(21,63,126),
                              progress_callback=None, status_callback=None):
    """13F filing-date 기준의 순차적(out-of-sample) SML 백테스트.

    각 분기마다:
      1) 해당 filing과 직전 filing의 보유주식수로 수급 계산
      2) filing 이전 가격만으로 SML 점수 계산
      3) 이후 21/63/126 거래일 수익률을 측정
    """
    def _progress(v):
        if progress_callback:
            progress_callback(max(0, min(100, int(v))))
    def _status(msg):
        if status_callback:
            status_callback(msg)

    all_filings = {}
    fund_items = list(funds_to_analyze.items())
    for i, (name, cik) in enumerate(fund_items, 1):
        _status(f"📥 **[1/5 과거 공시 수집 {i}/{len(fund_items)}]** `{name}`의 과거 13F를 불러오는 중")
        fs = load_historical_filings(cik, n_quarters=n_quarters + 1)
        if fs:
            all_filings[(name, cik)] = fs
        _progress(5 + 15 * i / max(len(fund_items), 1))

    periods = sorted({f["period"] for fs in all_filings.values() for f in fs}, reverse=True)
    periods = periods[:int(n_quarters)]
    if not periods:
        return pd.DataFrame(), pd.DataFrame()

    quarter_rows = []
    total_periods = len(periods)
    for qi, period in enumerate(sorted(periods)):
        _status(f"📊 **[2/5 분기별 수급 집계 {qi+1}/{total_periods}]** {period} 13F 변동을 집계하는 중")
        _progress(20 + 20 * qi / max(total_periods, 1))
        curr_records, prev_records = [], {}
        filing_dates = []
        for (name, cik), fs in all_filings.items():
            current = next((f for f in fs if f["period"] == period), None)
            if not current:
                continue
            prev = next((f for f in fs if f["period"] < period), None)
            filing_dates.append(current["date"])
            h1 = get_holdings(cik, current["acc"])
            h2 = get_holdings(cik, prev["acc"]) if prev else {}
            for cusip, val in h1.items():
                curr_records.append({"cik": cik, "fund": name, "cusip": cusip,
                                     "name": val["name"], "val": val["val"],
                                     "shares": val["shares"], "f_date": current["date"],
                                     "period": period})
            for cusip, val in h2.items():
                prev_records[(cik, cusip)] = val

        # 모든 선택 기관의 해당 분기 정보가 공개된 뒤를 공통 기준일로 사용한다.
        period_date = max(filing_dates) if filing_dates else period

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

        # 중요: 기관수/유입액으로 후보를 먼저 Top-N 절단하지 않는다.
        # 전체 매수 후보를 SML universe로 만든 뒤 SML percentile을 계산한다.
        _status(f"🔎 **[3/5 티커 매칭]** {period} 후보 {len(tot):,}개를 전체 SML 유니버스로 유지하며 매칭 중")
        resolved = []
        yahoo_fallback_budget = 300
        yahoo_fallback_used = 0
        yahoo_fallback_hits = 0
        local_match_count = 0
        for ri, (c, d) in enumerate(tot.items(), 1):
            local_tk = resolve_ticker_local(c, d["name"])
            allow_yahoo = (local_tk == "-" and yahoo_fallback_used < yahoo_fallback_budget)
            if allow_yahoo:
                yahoo_fallback_used += 1
            tk = resolve_ticker_advanced(c, d["name"], allow_yahoo=allow_yahoo)
            if local_tk != "-":
                local_match_count += 1
            if allow_yahoo and tk != "-":
                yahoo_fallback_hits += 1
            resolved.append((c, d, tk))
            if ri % 100 == 0 or ri == len(tot):
                _progress(40 + 10 * ri / max(len(tot), 1))
        _status(f"🧭 티커 매칭 완료 · SEC/로컬 {local_match_count:,} · Yahoo 보조 {yahoo_fallback_hits:,}/{yahoo_fallback_used:,} · 미매칭 {sum(1 for x in resolved if x[2]=='-'):,}")
        resolved = [x for x in resolved if x[2] != "-"]
        # 동일 Yahoo ticker가 중복되는 경우 첫 관측치만 사용
        seen_tickers = set()
        resolved_unique = []
        for x in resolved:
            if x[2] in seen_tickers:
                continue
            seen_tickers.add(x[2])
            resolved_unique.append(x)
        resolved = resolved_unique
        tickers = list(dict.fromkeys([x[2] for x in resolved]))
        start_dt = pd.Timestamp(period_date) - pd.Timedelta(days=430)
        end_dt = pd.Timestamp(period_date) + pd.Timedelta(days=320)
        _status(f"📈 **[4/5 시세 다운로드]** {period} 유효 티커 {len(tickers):,}개 + SPY 과거 시세를 조회하는 중")
        _progress(52)
        price_hist = download_backtest_price_history(
            tickers, start=start_dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d")
        )
        spy = download_backtest_spy_history(
            start=start_dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d")
        )

        # CMF는 반드시 공통 정보일(period_date) 직전 거래일까지의 10거래일로 계산한다.
        # period_date는 해당 분기의 선택 기관 중 가장 늦게 공개된 13F filing date이므로,
        # 이 날짜 이전의 시장 데이터만 사용하면 백테스트 시점의 look-ahead를 차단할 수 있다.
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
                # 개별 기관의 filing date와 별도로, 실제 SML 신호를 확정할 수 있는
                # 공통 정보 기준일을 저장한다. CMF 역시 이 날짜 직전 10거래일 기준이다.
                "Filing_Date": d["f_date"], "Signal_AsOf_Date": period_date, "CMF_AsOf_Date": period_date,
                "CMF_Status": "PASS" if pd.notna(feat["CMF_10D"]) and feat["CMF_10D"] >= 0 else "FAIL",
                "period": period,
                "details": []
            }
            rows.append(row)

        _status(f"🧮 **[5/5 SML 계산]** {period} 가격팩터와 수급팩터를 결합해 점수를 계산하는 중")
        _progress(65 + 25 * (qi + 1) / max(total_periods, 1))
        raw = pd.DataFrame(rows)
        required = ["Price_Val", "Rel_Return", "Return_3M", "Dist_52W", "CMF_10D"]
        raw = raw.dropna(subset=required).copy()
        raw = raw[raw["Price_Val"] > 0].copy()
        scored = calc_score(raw, market_neutral=market_neutral) if not raw.empty else pd.DataFrame()
        if scored.empty:
            continue
        # 해당 분기의 전체 유효 후보를 기준으로 SML 백분위를 확정한다.
        scored["SML_Percentile"] = (scored["SML_Score"].rank(pct=True, method="average") * 100.0).round(1)

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
    # 분위수별 성과를 계산한다. Top 1/5/10/15/20/30%를 동시에 비교해
    # SML 순위가 높아질수록 미래성과가 좋아지는지 확인할 수 있다.
    summary_rows = []
    quantiles = [1, 5, 10, 15, 20, 30]
    for fd in forward_days:
        col = f"Fwd_{fd}D"
        alpha_col = f"FwdAlpha_{fd}D"
        for q in quantiles:
            subset = bt[bt["SML_Percentile"] >= (100-q)]
            vals = pd.to_numeric(subset[col], errors="coerce").dropna()
            alphas = pd.to_numeric(subset[alpha_col], errors="coerce").dropna()
            summary_rows.append({
                "기간": f"{fd}D", "SML_상위": f"Top {q}%", "N": len(vals),
                "평균수익률": vals.mean() if len(vals) else np.nan,
                "중앙수익률": vals.median() if len(vals) else np.nan,
                "승률": (vals > 0).mean() if len(vals) else np.nan,
                "평균시장초과": alphas.mean() if len(alphas) else np.nan,
                "표준편차": vals.std(ddof=1) if len(vals) > 1 else np.nan,
            })
        allv = pd.to_numeric(bt[col], errors="coerce").dropna()
        alla = pd.to_numeric(bt[alpha_col], errors="coerce").dropna()
        summary_rows.append({
            "기간": f"{fd}D", "SML_상위": "전체", "N": len(allv),
            "평균수익률": allv.mean() if len(allv) else np.nan,
            "중앙수익률": allv.median() if len(allv) else np.nan,
            "승률": (allv > 0).mean() if len(allv) else np.nan,
            "평균시장초과": alla.mean() if len(alla) else np.nan,
            "표준편차": allv.std(ddof=1) if len(allv) > 1 else np.nan,
        })

        # 분기별 동일가중 Top10 - Bottom10 Long-Short
        ls = []
        lsa = []
        for period in bt["period"].dropna().unique():
            qdf = bt[bt["period"] == period]
            top = pd.to_numeric(qdf[qdf["SML_Percentile"] >= 90][col], errors="coerce").dropna()
            bot = pd.to_numeric(qdf[qdf["SML_Percentile"] <= 10][col], errors="coerce").dropna()
            if len(top) and len(bot):
                ls.append(top.mean() - bot.mean())
                ta = pd.to_numeric(qdf[qdf["SML_Percentile"] >= 90][alpha_col], errors="coerce").dropna()
                ba = pd.to_numeric(qdf[qdf["SML_Percentile"] <= 10][alpha_col], errors="coerce").dropna()
                if len(ta) and len(ba): lsa.append(ta.mean() - ba.mean())
        summary_rows.append({
            "기간": f"{fd}D", "SML_상위": "Long Top10% - Short Bottom10%", "N": len(ls),
            "평균수익률": np.mean(ls) if ls else np.nan,
            "중앙수익률": np.median(ls) if ls else np.nan,
            "승률": np.mean(np.array(ls) > 0) if ls else np.nan,
            "평균시장초과": np.mean(lsa) if lsa else np.nan,
            "표준편차": np.std(ls, ddof=1) if len(ls) > 1 else np.nan,
        })
    _status("✅ **백테스트 완료** — 분위수별 미래수익률과 Long-Short 성과를 정리했습니다.")
    _progress(100)
    return bt, pd.DataFrame(summary_rows)

# --- UI 레이아웃 ---
st.title("🎯 SEC 13F SML 레이더 v2.0")
st.caption("13F 스마트머니 수급 × 가격 소외 × 시장상대수익률 | Core 50 / Extended 100 고정 Universe 지원 | 실시간 데이터는 실행 시에만 수집")

with st.expander("📖 SML 2.0 모델·데이터·시그널 가이드 (필독)", expanded=False):
    st.markdown(
        """
        ### 1. 이 시스템이 찾는 종목
        **SML(Smart Money Lag)**은 선택한 기관들이 13F에서 보유주식을 늘린 종목 중에서, 기관 수급 강도는 높은데 주가가 시장 대비 아직 뒤처진 종목을 찾는 상대순위 모델입니다.

        ### 2. SML 2.0 점수 구성
        최종 점수는 **수급 55점 + 가격 소외 45점 = 100점**입니다. 각 입력은 횡단면 percentile rank를 기본으로 하고, 극단값은 1~99% 구간으로 winsorize합니다.

        **① 기관 수급 점수(55%)**
        - 기관 참여폭(Breadth): 10%
        - 13F 현재 보유액 대비 추정 유입 비율: 10%
        - 최근 20일 평균거래대금 대비 추정 유입 비율: 20%
        - 추정 절대 유입액: 10%
        - 신규 진입 기관 수: 5%

        **② 가격 소외 점수(45%)**
        - 6개월 SPY 대비 초과수익의 역순위: 15%
        - 3개월 SPY 대비 초과수익의 역순위: 10%
        - 52주 고점 대비 하락폭의 역순위: 10%
        - 10일 CMF(가격·거래량 기반 매집 확인): 10%

        따라서 **SML이 높다는 것은 단순히 주가가 많이 빠졌다는 뜻이 아니라, 기관 수급 강도와 상대적 가격 소외가 동시에 높다는 뜻**입니다.

        ### 3. 13F 유입액의 의미와 한계
        13F에는 실제 체결 거래내역이 공개되지 않습니다. 따라서 이 시스템의 `추정 유입액`은 **보유주식 증가분 × 해당 분기 보고가격**으로 계산한 수급 강도 proxy입니다. 실제 매수 체결금액과 동일하지 않습니다.

        또한 13F는 분기말 보유내역을 사후 공개하므로, **13F 보고일과 실제 매수 시점 사이에 시차**가 존재합니다.

        ### 4. CMF / A·D의 의미
        CMF는 기관의 13F 수급이 아니라 **시장 가격과 거래량에서 관찰되는 매집/분산 확인 신호**입니다. 현재 모델에서는 이를 수급의 직접 증거가 아니라 가격 소외를 보완하는 확인점수로 사용합니다.

        ### 5. 시그널
        - 🟢 **STRONG_BUY**: SML 백분위 95 이상 + 매집점수 50 이상
        - 🔵 **ACCUMULATE**: SML 백분위 85 이상 + 매집점수 50 이상
        - 🟡 **WATCH_LAG**: SML 백분위 85 이상이나 매집 확인이 약함
        - 🟠 **WATCH**: SML 백분위 70 이상
        - ⚪ **NEUTRAL**: 그 외

        이는 **백테스트로 최적화된 매매 임계값이 아니라 현재 모델의 휴리스틱 분류 기준**입니다.

        ### 6. 워크포워드 백테스트
        백테스트에서는 각 분기의 전체 유효 13F 매수 후보에서 SML을 계산하고, 모든 선택 기관의 해당 분기 정보가 공개된 **가장 늦은 공시일 다음 거래일**을 진입 기준으로 합니다. 그 뒤 21/63/126 거래일의 미래수익률과 SPY 대비 초과수익을 측정합니다.

        **중요:** 백테스트는 현재 점수의 성능을 보여주는 검증 도구이며, 아직 장기간 out-of-sample 최적화나 거래비용을 포함한 실전 성과 검증을 완료한 것은 아닙니다.

        ### 7. 데이터 수집/속도
        앱을 열기만 했을 때는 SEC·Yahoo 데이터를 내려받지 않습니다. 실제 분석/백테스트 버튼을 눌렀을 때만 데이터를 수집하며, SEC 공시/보유내역과 Yahoo 시세는 캐시를 사용합니다.
        """
    )

if "custom_funds" not in st.session_state:
    st.session_state["custom_funds"] = dict(DEFAULT_FUNDS)

with st.expander("🏛️ 분석 대상 기관 Universe", expanded=False):
    st.caption(
        "기관 수를 임의로 섞지 않고, 사전 정의된 50개 Core와 100개 Extended Universe 중 하나를 기계적으로 선택합니다. "
        "Core는 대형 패시브 운용사를 과도하게 넣지 않고 헤지펀드·액티비스트·집중형 액티브 운용사를 중심으로 구성했으며, "
        "Extended는 여기에 추가 액티비스트·글로벌 액티브·대형 운용사를 더해 표본을 넓힙니다."
    )
    universe_mode = st.radio(
        "분석 Universe",
        ["Core 50", "Extended 100", "사용자 지정"],
        horizontal=True,
        index=0,
        key="universe_mode"
    )

    if universe_mode == "Core 50":
        active_universe = dict(DEFAULT_FUNDS)
        selected_fund_names = list(active_universe.keys())
        st.success(f"Core Universe: {len(active_universe)}개 기관이 자동 선택되었습니다.")
    elif universe_mode == "Extended 100":
        active_universe = dict(EXTENDED_FUNDS)
        selected_fund_names = list(active_universe.keys())
        st.info(f"Extended Universe: {len(active_universe)}개 기관이 자동 선택되었습니다.")
    else:
        active_universe = dict(EXTENDED_FUNDS)
        selected_fund_names = st.multiselect(
            "사용자 지정 기관",
            options=list(active_universe.keys()),
            default=list(DEFAULT_FUNDS.keys())
        )

    with st.expander("선정 원칙 보기", expanded=False):
        st.markdown(
            "- **Core 50:** 대형 퀀트/멀티전략, 집중형 롱숏, 가치·액티비스트, 장기 집중투자 성향을 우선.\n"
            "- **Extended 100:** Core에 추가 액티비스트·성장/가치 액티브 매니저·글로벌 대형 운용사를 추가.\n"
            "- **중복 방지:** 동일 CIK를 여러 이름으로 중복 집계하지 않도록 구성.\n"
            "- **주의:** 13F는 분기말 보유내역의 사후 공시이므로 이 목록은 ‘예측력이 검증된 순위’가 아니라 SML 연구용 고정 Universe입니다.\n"
        )

col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1.2])
with col1:
    # 💡 기본값 300, 최댓값 500 반영
    top_n = st.slider("최종 출력 종목 수 (상위 N개)", min_value=20, max_value=500, value=300, step=10)
with col2:
    sec_neutral = st.checkbox("시장(SPY) 대비 상대수익률 적용", value=True)
with col3:
    pass_only = st.checkbox("CMF 매집 확인(PASS)만", value=False)
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
    k: active_universe[k]
    for k in selected_fund_names
    if k in active_universe
}

if "result_universe_count" in st.session_state:
    st.caption(f"전체 유효 SML 유니버스 {st.session_state['result_universe_count']:,}개에서 점수를 계산하고, 화면에는 선택한 Top N만 표시합니다. 첫 화면에서는 외부 데이터를 조회하지 않습니다.")

if "last_run_diagnostics" in st.session_state:
    diag = st.session_state["last_run_diagnostics"]
    with st.expander("🔧 데이터 수집/계산 진단", expanded=False):
        st.write({k: v for k, v in diag.items() if not isinstance(v, list)})
        for title, key in [("공시 수집 실패", "공시 수집 실패 목록"), ("티커 매칭 실패", "티커 매칭 실패 목록"), ("시세 조회 실패", "시세 조회 실패 목록"), ("팩터 계산 예외", "팩터 계산 예외 목록")]:
            vals = diag.get(key, [])
            if vals:
                st.caption(f"{title} (최대 100개)")
                st.dataframe(pd.DataFrame({title: vals}), use_container_width=True, hide_index=True)

if run_btn:
    if not funds_to_analyze:
        st.error("최소 1개 이상의 기관을 선택해야 합니다.")
    else:
        status_box = st.empty()
        prog = st.progress(0.0)
        
        curr_records = []
        prev_records = {}
        filing_dates = []
        collection_failures = []
        ticker_failures = []
        price_failures = []
        factor_failures = []
        
        fund_items = list(funds_to_analyze.items())
        tot_cnt = len(fund_items)
        
        for idx, (name, cik) in enumerate(fund_items):
            status_box.markdown(f"📥 **[1단계: 공시 수집 {idx+1}/{tot_cnt}]** `{name}` 최신 13F 파싱 중...")
            prog.progress(int(((idx + 1) / tot_cnt) * 50))
            
            f = get_filings(cik)
            if not f:
                collection_failures.append(name)
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

        # 전체 후보에서 SML을 계산한다. top_n은 최종 화면 표시 개수일 뿐,
        # 점수 계산 전에 후보를 잘라내지 않는다. 이것이 SML percentile의 핵심이다.
        resolved = []
        total_candidates = len(tot)
        yahoo_fallback_budget = 300
        yahoo_fallback_used = 0
        yahoo_fallback_hits = 0
        local_match_count = 0
        for ridx, (cusip, d) in enumerate(tot.items()):
            if ridx % 50 == 0:
                status_box.markdown(f"🔎 **티커 매칭 {ridx}/{total_candidates}** — 전체 후보를 SML 유니버스로 유지합니다.")
            local_tk = resolve_ticker_local(cusip, d["name"])
            allow_yahoo = (local_tk == "-" and yahoo_fallback_used < yahoo_fallback_budget)
            if allow_yahoo:
                yahoo_fallback_used += 1
            tk_resolved = resolve_ticker_advanced(cusip, d["name"], allow_yahoo=allow_yahoo)
            if local_tk != "-":
                local_match_count += 1
            if allow_yahoo and tk_resolved != "-":
                yahoo_fallback_hits += 1
            if tk_resolved == "-":
                ticker_failures.append(d["name"])
            resolved.append((cusip, d, tk_resolved))
        status_box.markdown(f"🧭 **티커 매칭 완료** · SEC/로컬 {local_match_count:,} · Yahoo 보조 {yahoo_fallback_hits:,}/{yahoo_fallback_used:,} · 미매칭 {sum(1 for x in resolved if x[2]=='-'):,}")
        resolved = [x for x in resolved if x[2] != "-"]
        tickers = list(dict.fromkeys([tk for _, _, tk in resolved]))
        market_hist = download_price_history(tickers, period="1y")

        # SPY는 캐시된 단일 시계열을 사용한다.
        spy_hist = download_spy_history(period="1y")

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
            if h is None or h.empty or len(h) < 20:
                price_failures.append(tk)
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
                    factor_failures.append(tk)

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

        res_df = calc_score(pd.DataFrame(data_rows), market_neutral=sec_neutral)
        st.session_state["last_run_diagnostics"] = {
            "기관 공시 수집 실패": len(collection_failures),
            "티커 매칭 실패": len(ticker_failures),
            "시세 조회 실패": len(price_failures),
            "팩터 계산 예외": len(factor_failures),
            "SML 계산 후보": len(res_df),
            "공시 수집 실패 목록": collection_failures[:100],
            "티커 매칭 실패 목록": ticker_failures[:100],
            "시세 조회 실패 목록": price_failures[:100],
            "팩터 계산 예외 목록": factor_failures[:100],
        }
        if collection_failures or ticker_failures or price_failures or factor_failures:
            st.info(
                f"데이터 진단 — 공시 실패 {len(collection_failures)}개 · "
                f"티커 실패 {len(ticker_failures)}개 · 시세 실패 {len(price_failures)}개 · "
                f"팩터 예외 {len(factor_failures)}개 · 최종 SML {len(res_df):,}개"
            )
        prog.empty()
        status_box.empty()
        # top_n은 표시 개수만 제한한다. SML percentile은 전체 유효 후보를 기준으로 계산된 뒤 유지된다.
        display_df = res_df.head(int(top_n)).copy()
        st.session_state["result_df"] = display_df
        st.session_state["selected_ticker"] = display_df["Ticker"].iloc[0] if not display_df.empty else None
        st.session_state["result_universe_count"] = len(res_df)

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
            p_table.columns = ["선정", "티커", "기업명", "SML점수", "현재가($)", "공시후변동률", "CMF(10D)", "시그널"]
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
                    "CMF(10D)": st.column_config.NumberColumn(format="%+.1f%%"),
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
                "CMF(10D)": t1["AD_Chg_Pct"], "선정 이유": "순유입액 1위"
            })
            selected_tickers.add(t1["Ticker"])

        s2 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="Dist_52W", ascending=True)
        if not s2.empty:
            t2 = s2.iloc[0]
            theme_picks.append({
                "전략 슬롯": "📉 바닥 소외", "티커": t2["Ticker"], "기업명": t2["Name"],
                "SML점수": t2["SML_Score"], "현재가($)": t2["Price_Val"], "공시후변동률": t2["Pct_Chg"],
                "CMF(10D)": t2["AD_Chg_Pct"], "선정 이유": f"52주 낙폭 {t2['Dist_52W']:.1f}%"
            })
            selected_tickers.add(t2["Ticker"])

        s3 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="Flow_Score", ascending=False)
        if not s3.empty:
            t3 = s3.iloc[0]
            theme_picks.append({
                "전략 슬롯": "⚡ 수급 급증", "티커": t3["Ticker"], "기업명": t3["Name"],
                "SML점수": t3["SML_Score"], "현재가($)": t3["Price_Val"], "공시후변동률": t3["Pct_Chg"],
                "CMF(10D)": t3["AD_Chg_Pct"], "선정 이유": f"상대 수급강도 {t3['Flow_Score']:.1f}점"
            })
            selected_tickers.add(t3["Ticker"])

        s4 = valid_pool[(~valid_pool["Ticker"].isin(selected_tickers)) & (valid_pool["AD_Pass"] == True)].sort_values(by="AD_Chg_Pct", ascending=False)
        if not s4.empty:
            t4 = s4.iloc[0]
            theme_picks.append({
                "전략 슬롯": "🌊 차트 매집", "티커": t4["Ticker"], "기업명": t4["Name"],
                "SML점수": t4["SML_Score"], "현재가($)": t4["Price_Val"], "공시후변동률": t4["Pct_Chg"],
                "CMF(10D)": t4["AD_Chg_Pct"], "선정 이유": f"CMF {t4['AD_Chg_Pct']:+.1f}%"
            })
            selected_tickers.add(t4["Ticker"])

        s5 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="SML_Percentile", ascending=False)
        if not s5.empty:
            t5 = s5.iloc[0]
            theme_picks.append({
                "전략 슬롯": "💎 밸류 앙상블", "티커": t5["Ticker"], "기업명": t5["Name"],
                "SML점수": t5["SML_Score"], "현재가($)": t5["Price_Val"], "공시후변동률": t5["Pct_Chg"],
                "CMF(10D)": t5["AD_Chg_Pct"], "선정 이유": f"SML 상위 {100-t5['SML_Percentile']+1:.1f}%"
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
                    "CMF(10D)": st.column_config.NumberColumn(format="%+.1f%%"),
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
                    
                    pass_str = "✅ PASS (10일 CMF 양수: 매집 확인)" if sel_row["AD_Pass"] else "❌ FAIL (10일 CMF 음수: 매집 확인 약함)"
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
    "기관수/유입액으로 후보를 먼저 잘라내지 않습니다. 각 분기의 전체 13F 매수 후보에서 SML을 계산하고, "
    "모든 선택 기관의 정보가 공개된 공통 기준일 다음 거래일부터 21/63/126 거래일 성과를 측정합니다."
)

bt_c1, bt_c2, bt_c3 = st.columns([1, 1, 1.3])
with bt_c1:
    bt_quarters = st.slider("백테스트 분기 수", min_value=2, max_value=12, value=8, step=1)
with bt_c2:
    bt_market_neutral = st.checkbox("SPY 대비 상대수익률 적용", value=True, key="bt_market_neutral")
with bt_c3:
    bt_run = st.button("🧪 백테스트 실행", type="primary", key="run_backtest")

if bt_run:
    if not funds_to_analyze:
        st.error("백테스트할 기관을 최소 1개 이상 선택하세요.")
    else:
        bt_status = st.empty()
        bt_prog = st.progress(0)
        bt_status.markdown("🧪 **백테스트 준비 중...**")
        bt_detail, bt_summary = run_walk_forward_backtest(
            funds_to_analyze,
            n_quarters=bt_quarters,
            market_neutral=bt_market_neutral,
            forward_days=(21, 63, 126),
            progress_callback=bt_prog.progress,
            status_callback=bt_status.markdown,
        )
        bt_prog.empty()
        bt_status.empty()
        st.session_state["backtest_detail"] = bt_detail
        st.session_state["backtest_summary"] = bt_summary

if "backtest_summary" in st.session_state:
    bt_summary = st.session_state["backtest_summary"]
    bt_detail = st.session_state.get("backtest_detail", pd.DataFrame())
    if bt_summary.empty or bt_detail.empty:
        st.warning("백테스트 결과가 없습니다. SEC 공시 또는 과거 시세 데이터를 확인하세요.")
    else:
        st.markdown("### ① SML 분위수별 성과")
        show = bt_summary.copy()
        for c in ["평균수익률", "중앙수익률", "평균시장초과", "표준편차"]:
            show[c] = pd.to_numeric(show[c], errors="coerce").round(2)
        show["승률"] = (pd.to_numeric(show["승률"], errors="coerce") * 100).round(1)
        st.dataframe(show, use_container_width=True, hide_index=True,
            column_config={
                "평균수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                "중앙수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                "승률": st.column_config.NumberColumn(format="%.1f%%"),
                "평균시장초과": st.column_config.NumberColumn(format="%+.2f%%"),
                "표준편차": st.column_config.NumberColumn(format="%.2f%%"),
            })

        st.markdown("### ② CMF PASS만 적용했을 때의 백테스트")
        st.caption(
            "CMF(10D)는 각 분기의 **공통 정보 기준일(Signal As-Of Date) 직전 10거래일**로 계산합니다. "
            "즉 공시 이후의 가격·거래량은 CMF 판정에 절대 사용하지 않습니다. "
            "CMF PASS 종목만 남긴 뒤 원래 SML 백분위를 유지하여, CMF 필터의 추가 효과를 검증합니다."
        )
        cmf_detail = bt_detail[
            (bt_detail.get("CMF_Status", "FAIL") == "PASS")
        ].copy() if "CMF_Status" in bt_detail.columns else pd.DataFrame()
        if cmf_detail.empty:
            st.warning("CMF PASS 조건을 만족하면서 미래수익률까지 계산 가능한 관측치가 없습니다.")
        else:
            cmf_rows = []
            for fd in [21, 63, 126]:
                col = f"Fwd_{fd}D"
                alpha_col = f"FwdAlpha_{fd}D"
                for label, mask in [
                    ("CMF PASS 전체", pd.Series(True, index=cmf_detail.index)),
                    ("CMF PASS + SML Top 20%", cmf_detail["SML_Percentile"] >= 80),
                    ("CMF PASS + SML Top 10%", cmf_detail["SML_Percentile"] >= 90),
                    ("CMF PASS + SML Top 5%", cmf_detail["SML_Percentile"] >= 95),
                ]:
                    sub = cmf_detail[mask]
                    vals = pd.to_numeric(sub[col], errors="coerce").dropna()
                    alphas = pd.to_numeric(sub[alpha_col], errors="coerce").dropna()
                    cmf_rows.append({
                        "기간": f"{fd}D", "기준": label, "N": len(vals),
                        "평균수익률": vals.mean() if len(vals) else np.nan,
                        "중앙수익률": vals.median() if len(vals) else np.nan,
                        "승률": (vals > 0).mean() if len(vals) else np.nan,
                        "평균시장초과": alphas.mean() if len(alphas) else np.nan,
                    })
            cmf_show = pd.DataFrame(cmf_rows)
            st.dataframe(
                cmf_show,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "평균수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                    "중앙수익률": st.column_config.NumberColumn(format="%+.2f%%"),
                    "승률": st.column_config.NumberColumn(format="%.1f%%"),
                    "평균시장초과": st.column_config.NumberColumn(format="%+.2f%%"),
                    "N": st.column_config.NumberColumn(format="%d"),
                }
            )

        st.markdown("### ③ 핵심 검증")

        # 126D는 최근 분기의 경우 아직 미래 데이터가 충분하지 않을 수 있다.
        # 따라서 NaN을 그대로 표시하지 않고, 유효 관측치가 가장 많은 장기 구간을 우선 사용한다.
        horizon_order = ["126D", "63D", "21D"]
        horizon_stats = []
        for h in horizon_order:
            hdf = bt_summary[bt_summary["기간"] == h]
            top5_h = hdf[hdf["SML_상위"] == "Top 5%"]
            valid_n = int(top5_h.iloc[0]["N"]) if not top5_h.empty and pd.notna(top5_h.iloc[0]["N"]) else 0
            horizon_stats.append((h, valid_n))
        # 126D를 기본으로 하되, 유효 표본이 전혀 없으면 63D/21D로 자동 fallback
        selected_horizon = next((h for h, n in horizon_stats if n > 0), "126D")
        six = bt_summary[bt_summary["기간"] == selected_horizon]
        top5 = six[six["SML_상위"] == "Top 5%"]
        top15 = six[six["SML_상위"] == "Top 15%"]
        ls6 = six[six["SML_상위"] == "Long Top10% - Short Bottom10%"]

        def _metric_pct(df, col, multiplier=1.0, decimals=2):
            if df.empty or col not in df.columns:
                return "N/A"
            v = pd.to_numeric(df.iloc[0][col], errors="coerce")
            if pd.isna(v):
                return "N/A"
            return f"{v * multiplier:+.{decimals}f}%"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"Top 5% {selected_horizon} 평균", _metric_pct(top5, "평균수익률"))
        c2.metric(f"Top 15% {selected_horizon} 평균", _metric_pct(top15, "평균수익률"))
        c3.metric(f"Top 5% 승률", _metric_pct(top5, "승률", multiplier=100.0, decimals=1))
        c4.metric(f"Top10 - Bottom10 ({selected_horizon})", _metric_pct(ls6, "평균수익률"))

        if selected_horizon != "126D":
            st.warning(
                f"최근 분기는 아직 6개월(126거래일) 미래수익률이 확정되지 않아 {selected_horizon} 기준으로 표시했습니다. "
                "126D 결과는 충분한 시간이 지난 과거 분기가 쌓이면 자동으로 채워집니다."
            )
        st.info(
            "좋은 SML이라면 Top 1% → 5% → 10% → 15% → 20% → 30%로 갈수록 미래수익률이 대체로 높아지고, "
            "동시에 Top10% - Bottom10% Long-Short가 반복적으로 양수여야 합니다. "
            "각 기간의 N은 실제로 미래수익률이 계산 가능한 유효 표본 수입니다."
        )

        st.markdown("### ④ 개별 관측치")
        cols = ["period", "Filing_Date", "Ticker", "Name", "Fund_Count", "Inflow_M", "SML_Score",
                "SML_Percentile", "Inst_Score", "Lag_Score", "Accumulation_Score", "Fwd_21D",
                "Fwd_63D", "Fwd_126D", "FwdAlpha_21D", "FwdAlpha_63D", "FwdAlpha_126D"]
        cols = [c for c in cols if c in bt_detail.columns]
        view = bt_detail[cols].sort_values(["period", "SML_Score"], ascending=[False, False]).copy()
        view = view.rename(columns={
            "period":"보고분기", "Filing_Date":"공통정보일", "Ticker":"티커", "Name":"기업명",
            "Fund_Count":"기관수", "Inflow_M":"추정유입($M)", "SML_Score":"SML점수",
            "SML_Percentile":"SML백분위", "Inst_Score":"수급점수", "Lag_Score":"소외도",
            "Accumulation_Score":"매집점수", "Fwd_21D":"21D수익률", "Fwd_63D":"63D수익률",
            "Fwd_126D":"126D수익률", "FwdAlpha_21D":"21D초과수익", "FwdAlpha_63D":"63D초과수익",
            "FwdAlpha_126D":"126D초과수익"})
        st.dataframe(view, use_container_width=True, hide_index=True,
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
                "126D초과수익": st.column_config.NumberColumn(format="%+.2f%%")})
        st.markdown("### ⑤ 백테스트 해석")
        st.info(
            "이번 버전은 기존의 '기관수/유입액 Top N → 그 안에서 SML' 구조를 제거했습니다. "
            "따라서 이제 분위수별 성과는 SML 순위 자체의 정보력을 검증하는 결과입니다. "
            "다만 현재는 짧은 표본을 빠르게 검증하는 단계이므로, 유효성이 확인되면 더 긴 기간의 walk-forward와 out-of-sample 최적화를 진행하는 것이 좋습니다."
        )
        csv = bt_detail.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 전체 백테스트 결과 CSV 다운로드", data=csv,
                           file_name="sml_walk_forward_backtest_full_universe.csv", mime="text/csv", key="download_bt_csv")

