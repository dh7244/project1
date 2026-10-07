# -*- coding: utf-8 -*-
import datetime
import json
import re
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import requests
from scipy import stats
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="13F SmartScore v1.5", page_icon="📈", layout="wide"
)

USER_AGENT = "QuantStreamlitApp research@internaldesk.org"
HEADERS = {"User-Agent": USER_AGENT}

POPULAR_FUNDS = {
    "버크셔 해서웨이 (Berkshire Hathaway)": "0001067983",
    "브릿지워터 (Bridgewater Associates)": "0001350694",
    "시타델 (Citadel Advisors)": "0001423053",
    "르네상스 테크놀로지 (Renaissance Tech)": "0001037389",
    "소로스 펀드 (Soros Fund Management)": "0001029160",
    "타이거 글로벌 (Tiger Global)": "0001167483",
    "아크 인베스트 (ARK Investment)": "0001697748",
    "블랙록 (BlackRock Fund Advisors)": "0001364742",
}

TICKER_MAP = {
    "037833100": "AAPL",
    "594918104": "MSFT",
    "67066G104": "NVDA",
    "023135106": "AMZN",
    "02079K305": "GOOGL",
    "02079K107": "GOOG",
    "30303M102": "META",
    "88160R101": "TSLA",
    "064058100": "AVGO",
    "46625H100": "JPM",
    "532457108": "LLY",
    "931142103": "WMT",
    "92826C839": "V",
    "254687106": "DIS",
    "69608A108": "PLTR",
    "22788C105": "CRWD",
    "874039100": "TSM",
    "007903107": "AMD",
    "74340W103": "QCOM",
    "09247X101": "BLK",
    "025816109": "AXP",
    "060505104": "BAC",
    "191216100": "KO",
    "166764100": "CVX",
}


def clean_name(name):
  name = re.sub(
      r"\b(INC|CORP|COMPANY|CO|LTD|HOLDINGS|HLDG|LLC|PLC|DE|NEW|CLASS [A-Z]|CL"
      r" [A-Z]|COM)\b",
      "",
      name,
      flags=re.IGNORECASE,
  )
  name = re.sub(r"[^a-zA-Z0-9 ]", " ", name)
  return " ".join(name.split())


def resolve_ticker(cusip, name):
  if cusip in TICKER_MAP:
    return TICKER_MAP[cusip]
  cl = clean_name(name).split()
  if cl and 1 <= len(cl[0]) <= 5 and cl[0].isalpha():
    return cl[0].upper()
  return "-"


def get_filings(cik):
  url = f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
  try:
    res = requests.get(url, headers=HEADERS, timeout=10)
    if res.status_code != 200:
      return []
    filings = res.json()["filings"]["recent"]
    out = []
    for i in range(len(filings["accessionNumber"])):
      if filings["form"][i] in ["13F-HR", "13F-HR/A"]:
        out.append({
            "acc": filings["accessionNumber"][i],
            "date": filings["filingDate"][i],
        })
        if len(out) == 2:
          break
    return out
  except Exception:
    return []


def get_holdings(cik, acc):
  acc_clean = acc.replace("-", "")
  cik_clean = str(int(cik))
  url = f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_clean}/"
  try:
    res = requests.get(url, headers=HEADERS, timeout=10)
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

    xml_res = requests.get(f"{url}{target}", headers=HEADERS, timeout=10)
    xml_clean = re.sub(r'\sxmlns="[^"]+"', "", xml_res.text, count=1)
    root = ET.fromstring(xml_clean)

    h = {}
    for t in root.findall(".//infoTable"):
      cusip = t.findtext("cusip", "").strip()
      nm = t.findtext("nameOfIssuer", "UNKNOWN").strip()
      v_str = t.findtext("value", "0").replace(",", "").strip()
      try:
        v = int(float(v_str))
      except:
        v = 0
      s_node = t.find(".//sshPrnamt")
      shares = (
          int(float(s_node.text.replace(",", "").strip()))
          if s_node is not None and s_node.text
          else 0
      )
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
  mn, mx = s.min(), s.max()
  if mn == mx:
    return pd.Series(50.0, index=s.index)
  if invert:
    return (mx - s) / (mx - mn) * 100.0
  return (s - mn) / (mx - mn) * 100.0


def calc_score(df, sector_neutral=False):
  d = df.copy()
  if sector_neutral and "Sector" in d.columns:
    d["Rel_Return"] = d.groupby("Sector")["Rel_Return"].transform(
        lambda s: s - s.mean()
    )

  m1_inst = (
      0.35 * min_max(d["Fund_Count"])
      + 0.35 * min_max(d["Inflow_M"])
      + 0.30 * min_max(d["Shares_Sum"])
  )
  m2_inst = (
      d["Fund_Count"].rank(pct=True) * 50.0 + d["Inflow_M"].rank(pct=True) * 50.0
  )
  z_inst = stats.zscore(d["Fund_Count"].fillna(0))

  m1_lag = 0.60 * min_max(d["Rel_Return"], invert=True) + 0.40 * min_max(
      d["Dist_52W"], invert=True
  )
  m2_lag = (
      (-d["Rel_Return"]).rank(pct=True) * 50.0
      + (-d["Dist_52W"]).rank(pct=True) * 50.0
  )
  z_lag = -stats.zscore(d["Rel_Return"].fillna(0))

  d["M1"] = (0.55 * m1_inst + 0.45 * m1_lag).round(1)
  d["M2"] = (0.55 * m2_inst + 0.45 * m2_lag).round(1)
  z_comp = 0.55 * z_inst + 0.45 * z_lag
  d["M3"] = (stats.norm.cdf(z_comp) * 100.0).round(1)
  d["SmartScore"] = (0.20 * d["M1"] + 0.40 * d["M2"] + 0.40 * d["M3"]).round(1)

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
  d["Rank"] = d["SmartScore"].rank(ascending=False, method="min").astype(int)
  return d.sort_values(by="Rank").reset_index(drop=True)


# --- UI 레이아웃 ---
st.title("🎯 SEC 13F 스마트스코어 & 시그널 v1.5")
st.caption("3-Factor 앙상블 | 마이크로스트럭처(A/D Line) 검증 | 섹터 중립화")

col1, col2 = st.columns([1, 1])
with col1:
  sec_neutral = st.checkbox("섹터 중립화(Sector Neutral) 적용", value=False)
with col2:
  pass_only = st.checkbox("A/D Line 통과(PASS) 종목만 표시", value=False)

if st.button("🚀 13F 전수 수급 집계 & 퀀트 스코어링 실행", type="primary"):
  with st.spinner("SEC 13F 최신 공시 수집 및 주가 데이터 분석 중..."):
    curr_records = []
    prev_records = {}

    for name, cik in POPULAR_FUNDS.items():
      f = get_filings(cik)
      if not f:
        continue
      h1 = get_holdings(cik, f[0]["acc"])
      for cusip, val in h1.items():
        curr_records.append({
            "cik": cik,
            "fund": name,
            "cusip": cusip,
            "name": val["name"],
            "val": val["val"],
            "shares": val["shares"],
        })
      if len(f) > 1:
        h2 = get_holdings(cik, f[1]["acc"])
        for cusip, val in h2.items():
          prev_records[(cik, cusip)] = val

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
        diff_s = (
            max(0, r["shares"] - p["shares"])
            if r["shares"] > p["shares"]
            else 0
        )

      if diff_v > 0 or k not in prev_records:
        if c not in tot:
          tot[c] = {
              "name": r["name"],
              "funds": set(),
              "inflow": 0,
              "shares": 0,
              "details": [],
          }
        tot[c]["funds"].add(r["fund"])
        tot[c]["inflow"] += diff_v
        tot[c]["shares"] += diff_s
        tot[c]["details"].append({
            "fund": r["fund"],
            "type": "신규" if k not in prev_records else "확대",
            "shares": diff_s,
            "val_m": round(diff_v / 1000.0, 1),
        })

    ranked = sorted(
        tot.items(),
        key=lambda x: (len(x[1]["funds"]), x[1]["inflow"]),
        reverse=True,
    )[:25]

    data_rows = []
    for cusip, d in ranked:
      tk = resolve_ticker(cusip, d["name"])
      rel_ret, dist_52w, ad_pass, cur_p = -15.0, -20.0, True, 0.0

      if tk != "-":
        try:
          t = yf.Ticker(tk)
          hist = t.history(period="3mo")
          if not hist.empty and len(hist) > 10:
            cur_p = hist["Close"].iloc[-1]
            dist_52w = (
                (cur_p - hist["High"].max()) / hist["High"].max()
            ) * 100.0
            rel_ret = (
                (cur_p - hist["Close"].iloc[0]) / hist["Close"].iloc[0]
            ) * 100.0
            clv = (
                (hist["Close"] - hist["Low"]) - (hist["High"] - hist["Close"])
            ) / (hist["High"] - hist["Low"] + 1e-9)
            ad = (clv * hist["Volume"]).cumsum()
            ad_pass = ad.iloc[-1] >= ad.iloc[-10]
        except:
          pass

      data_rows.append({
          "CUSIP": cusip,
          "Ticker": tk,
          "Name": d["name"],
          "Sector": (
              "Tech"
              if tk in ["NVDA", "AAPL", "MSFT", "AVGO", "PLTR"]
              else "General"
          ),
          "Fund_Count": len(d["funds"]),
          "Inflow_M": round(d["inflow"] / 1000.0, 1),
          "Shares_Sum": d["shares"],
          "Rel_Return": round(rel_ret, 1),
          "Dist_52W": round(dist_52w, 1),
          "AD_Pass": ad_pass,
          "Price": f"${cur_p:.2f}" if cur_p > 0 else "-",
          "details": d["details"],
      })

    res_df = calc_score(pd.DataFrame(data_rows), sector_neutral=sec_neutral)
    st.session_state["result_df"] = res_df

if "result_df" in st.session_state:
  df_show = st.session_state["result_df"].copy()
  if pass_only:
    df_show = df_show[df_show["AD_Pass"] == True]

  st.subheader("📋 퀀트 랭킹 & 투자 시그널")
  table_df = df_show[[
      "Rank",
      "Ticker",
      "Name",
      "SmartScore",
      "Signal",
      "M1",
      "M2",
      "M3",
      "Fund_Count",
      "Inflow_M",
      "Price",
  ]]
  table_df.columns = [
      "순위",
      "티커",
      "기업명",
      "스마트스코어",
      "투자시그널",
      "M1",
      "M2",
      "M3",
      "기관수",
      "유입액($M)",
      "현재가",
  ]
  st.dataframe(table_df, use_container_width=True, hide_index=True)

  st.divider()
  st.subheader("🔍 종목별 매수 기관 드릴다운 상세")
  sel_tk = st.selectbox("확인할 종목을 선택하세요:", df_show["Ticker"].tolist())
  if sel_tk:
    sel_row = df_show[df_show["Ticker"] == sel_tk].iloc[0]
    st.markdown(
        f"**{sel_row['Name']} ({sel_tk})** | 스마트스코어: **{sel_row['SmartScore']}점**"
        f" ({sel_row['Signal']})"
    )
    dt_df = pd.DataFrame(sel_row["details"])
    dt_df.columns = ["기관명", "구분", "매수주식수", "매수금액($M)"]
    st.dataframe(dt_df, use_container_width=True, hide_index=True)
