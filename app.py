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

USER_AGENT = "QuantStreamlitApp research_desk@internalorg.com"
HEADERS = {"User-Agent": USER_AGENT}

DEFAULT_FUNDS = {
    "버크셔 해서웨이 (Berkshire Hathaway)": "0001067983",
    "브릿지워터 (Bridgewater Associates)": "0001350694",
    "시타델 (Citadel Advisors)": "0001423053",
    "르네상스 테크놀로지 (Renaissance Tech)": "0001037389",
    "밀레니엄 매니지먼트 (Millennium Mgmt)": "0001273087",
    "투 시그마 (Two Sigma Investments)": "0001179392",
    "D.E. 쇼 (D.E. Shaw & Co.)": "0001009207",
    "포인트72 (Point72 Asset Mgmt)": "0001603466",
    "소로스 펀드 (Soros Fund Mgmt)": "0001029160",
    "타이거 글로벌 (Tiger Global)": "0001167483",
    "코튜 매니지먼트 (Coatue Management)": "0001422183",
    "아크 인베스트 (ARK Investment)": "0001697748",
    "베일리 기포드 (Baillie Gifford)": "0001088875",
    "블랙록 (BlackRock Fund Advisors)": "0001364742",
    "뱅가드 그룹 (Vanguard Group)": "0000102909",
    "피델리티 (FMR LLC)": "0000315066",
    "스테이트 스트리트 (State Street Corp)": "0000093751",
    "JP모건 체이스 (JPMorgan Chase)": "0000019617",
    "골드만 삭스 (Goldman Sachs Group)": "0000886982",
    "모건 스탠리 (Morgan Stanley)": "0000895421",
    "서드 포인트 (Third Point / Loeb)": "0001040273",
    "그린라이트 캐피탈 (Greenlight Capital)": "0001079114",
    "퍼싱 스퀘어 (Pershing Square / Ackman)": "0001336528",
    "앱팔루사 (Appaloosa Mgmt / Tepper)": "0001006438",
    "드러켄밀러 (Duquesne Family Office)": "0001536411"
}

TICKER_MAP = {
    "037833100": "AAPL", "594918104": "MSFT", "67066G104": "NVDA", "023135106": "AMZN",
    "02079K305": "GOOGL", "02079K107": "GOOG", "30303M102": "META", "88160R101": "TSLA",
    "064058100": "AVGO", "46625H100": "JPM", "532457108": "LLY", "931142103": "WMT",
    "92826C839": "V", "254687106": "DIS", "69608A108": "PLTR", "22788C105": "CRWD",
    "874039100": "TSM", "007903107": "AMD", "74340W103": "QCOM", "09247X101": "BLK",
    "025816109": "AXP", "060505104": "BAC", "191216100": "KO", "166764100": "CVX"
}

def clean_name(name):
    name = re.sub(r'\b(INC|CORP|COMPANY|CO|LTD|HOLDINGS|HLDG|LLC|PLC|DE|NEW|CLASS [A-Z]|CL [A-Z]|COM)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-zA-Z0-9 ]', ' ', name)
    return ' '.join(name.split())

def resolve_ticker(cusip, name):
    if cusip in TICKER_MAP:
        return TICKER_MAP[cusip]
    cl = clean_name(name).split()
    if cl and 1 <= len(cl[0]) <= 5 and cl[0].isalpha():
        return cl[0].upper()
    return "-"

@st.cache_data(ttl=86400)
def search_sec_company(keyword):
    """SEC 회사명 / CIK 매핑 리스트에서 검색"""
    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            kw = keyword.lower().strip()
            results = {}
            for item in data.values():
                title = item.get("title", "")
                cik = str(item.get("cik_str", "")).zfill(10)
                ticker = item.get("ticker", "")
                if kw in title.lower() or kw in cik or kw == ticker.lower():
                    results[f"{title} ({ticker})"] = cik
                    if len(results) >= 10:
                        break
            return results
    except Exception:
        pass
    return {}

def get_filings(cik):
    time.sleep(0.12)
    url = f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
    try:
        res = requests.get(url, headers=HEADERS, timeout
