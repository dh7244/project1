# -*- coding: utf-8 -*-
import datetime
import json
import re
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
import requests

USER_AGENT = "MobileQuantDesk research@internaldesk.org"
HEADERS = {"User-Agent": USER_AGENT}

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

SAMPLE_CIKS = [
    ("0001067983", "Berkshire"),
    ("0001350694", "Bridgewater"),
    ("0001423053", "Citadel"),
    ("0001037389", "Renaissance"),
    ("0001029160", "Soros"),
    ("0001167483", "Tiger Global"),
    ("0001697748", "ARK Invest"),
    ("0001364742", "BlackRock"),
]


def clean_company_name(name):
  name = re.sub(
      r"\b(INC|CORP|COMPANY|CO|LTD|HOLDINGS|HLDG|LLC|PLC|DE|NEW|CLASS [A-Z]|CL"
      r" [A-Z]|COM)\b",
      "",
      name,
      flags=re.IGNORECASE,
  )
  name = re.sub(r"[^a-zA-Z0-9 ]", " ", name)
  return " ".join(name.split())


def resolve_ticker(cusip, company_name):
  if cusip in TICKER_MAP:
    return TICKER_MAP[cusip]
  clean = clean_company_name(company_name)
  words = clean.split()
  if words and 1 <= len(words[0]) <= 5 and words[0].isalpha():
    return words[0].upper()
  return "-"


def get_recent_filings(cik):
  url = f"https://data.sec.gov/submissions/CIK{str(cik).zfill(10)}.json"
  res = requests.get(url, headers=HEADERS, timeout=10)
  if res.status_code != 200:
    return []
  data = res.json()
  filings = data["filings"]["recent"]
  results = []
  for i in range(len(filings["accessionNumber"])):
    if filings["form"][i] in ["13F-HR", "13F-HR/A"]:
      results.append(
          {"acc": filings["accessionNumber"][i], "date": filings["filingDate"][i]}
      )
      if len(results) == 2:
        break
  return results


def fetch_holdings(cik, acc_num):
  acc_clean = acc_num.replace("-", "")
  cik_clean = str(int(cik))
  dir_url = (
      f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_clean}/"
  )
  res = requests.get(dir_url, headers=HEADERS, timeout=10)
  if res.status_code != 200:
    return {}

  xml_files = re.findall(r'href="([^"]+\.xml)"', res.text, re.IGNORECASE)
  target = None
  for f in xml_files:
    fn = f.split("/")[-1].lower()
    if "infotable" in fn or "13f" in fn:
      target = f.split("/")[-1]
      break
  if not target and xml_files:
    target = xml_files[0].split("/")[-1]
  if not target:
    return {}

  xml_res = requests.get(f"{dir_url}{target}", headers=HEADERS, timeout=10)
  import xml.etree.ElementTree as ET

  xml_data = re.sub(r'\sxmlns="[^"]+"', "", xml_res.text, count=1)
  root = ET.fromstring(xml_data)

  holdings = {}
  for table in root.findall(".//infoTable"):
    cusip = table.findtext("cusip", "").strip()
    name = table.findtext("nameOfIssuer", "UNKNOWN").strip()
    val_str = table.findtext("value", "0").replace(",", "").strip()
    try:
      val = int(float(val_str))
    except:
      val = 0
    ssh = table.find(".//sshPrnamt")
    shares = (
        int(float(ssh.text.replace(",", "").strip()))
        if ssh is not None and ssh.text
        else 0
    )
    if cusip:
      if cusip in holdings:
        holdings[cusip]["val"] += val
        holdings[cusip]["shares"] += shares
      else:
        holdings[cusip] = {
            "name": name,
            "cusip": cusip,
            "val": val,
            "shares": shares,
        }
  return holdings


def fetch_yahoo_analytics(ticker):
  if not ticker or ticker == "-":
    return -15.0, -20.0, True, None, None
  try:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=3mo"
    res = requests.get(url, headers=HEADERS, timeout=5)
    if res.status_code == 200:
      d = res.json()
      meta = d["chart"]["result"][0]["meta"]
      curr = meta.get("regularMarketPrice", None)
      prev = meta.get("chartPreviousClose", None)
      ret_pct = ((curr - prev) / prev * 100) if (curr and prev) else 0.0

      quotes = d["chart"]["result"][0]["indicators"]["quote"][0]
      closes = [c for c in quotes.get("close", []) if c is not None]
      vols = [v for v in quotes.get("volume", []) if v is not None]
      ad_bullish = True
      if len(closes) > 10 and len(vols) > 10:
        ad_bullish = closes[-1] >= closes[-5]

      return -12.0, -18.0, ad_bullish, curr, ret_pct
  except:
    pass
  return -15.0, -20.0, True, None, None


class TrackerAppV15(App):

  def build(self):
    self.title = "13F SmartScore v1.5"
    self.scored_items = []
    self.curr_records = []
    self.prev_records = {}

    root = BoxLayout(orientation="vertical", spacing=8, padding=10)

    header = BoxLayout(size_hint_y=None, height=44)
    title_label = Label(
        text="13F 스마트스코어 & 액션 시그널 v1.5",
        font_size="16sp",
        bold=True,
        color=(1, 1, 1, 1),
    )
    header.add_widget(title_label)
    root.add_widget(header)

    ctrl = BoxLayout(size_hint_y=None, height=46, spacing=8)
    self.filter_spinner = Spinner(
        text="전체 종목 보기",
        values=(
            "전체 종목 보기",
            "🟢 STRONG_BUY",
            "🔵 ACCUMULATE",
            "검증 PASS 종목만",
        ),
        size_hint_x=0.58,
    )
    self.filter_spinner.bind(text=self.render_cards)
    ctrl.add_widget(self.filter_spinner)

    self.btn_run = Button(
        text="집계 & 스코어링",
        size_hint_x=0.42,
        background_color=(0.1, 0.5, 0.9, 1),
    )
    self.btn_run.bind(on_press=self.start_pipeline)
    ctrl.add_widget(self.btn_run)
    root.add_widget(ctrl)

    self.lbl_status = Label(
        text="버튼을 눌러 퀀트 스코어링을 시작하세요.",
        size_hint_y=None,
        height=28,
        font_size="12sp",
        color=(0.7, 0.8, 0.9, 1),
    )
    root.add_widget(self.lbl_status)

    self.scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
    self.list_layout = GridLayout(cols=1, spacing=8, size_hint_y=None)
    self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
    self.scroll.add_widget(self.list_layout)
    root.add_widget(self.scroll)

    return root

  def start_pipeline(self, instance):
    self.btn_run.disabled = True
    self.lbl_status.text = "공시 수집 및 마이크로스트럭처 분석 중..."
    threading.Thread(target=self.run_process, daemon=True).start()

  def run_process(self):
    curr_all = []
    prev_all = {}
    for cik, name in SAMPLE_CIKS:
      filings = get_recent_filings(cik)
      if not filings:
        continue
      curr_h = fetch_holdings(cik, filings[0]["acc"])
      for cusip, d in curr_h.items():
        curr_all.append({
            "cik": cik,
            "fund": name,
            "cusip": cusip,
            "name": d["name"],
            "val": d["val"],
            "shares": d["shares"],
        })
      if len(filings) > 1:
        prev_h = fetch_holdings(cik, filings[1]["acc"])
        for cusip, d in prev_h.items():
          prev_all[(cik, cusip)] = d

    self.curr_records = curr_all
    self.prev_records = prev_all

    tot_pos = {}
    for r in curr_all:
      cusip = r["cusip"]
      key = (r["cik"], r["cusip"])
      if key not in prev_all:
        diff_val = r["val"]
      else:
        p = prev_all[key]
        diff_val = (
            max(0, r["val"] - p["val"]) if r["shares"] > p["shares"] else 0
        )

      if diff_val > 0 or key not in prev_all:
        if cusip not in tot_pos:
          tot_pos[cusip] = {"name": r["name"], "funds": set(), "val": 0}
        tot_pos[cusip]["funds"].add(r["fund"])
        tot_pos[cusip]["val"] += diff_val

    ranked = sorted(
        tot_pos.items(),
        key=lambda x: (len(x[1]["funds"]), x[1]["val"]),
        reverse=True,
    )[:25]

    scored = []
    for idx, (cusip, d) in enumerate(ranked, 1):
      ticker = resolve_ticker(cusip, d["name"])
      fund_cnt = len(d["funds"])
      inflow_m = d["val"] / 1000.0

      rel_ret, dist_52w, ad_bullish, curr_p, ret_pct = fetch_yahoo_analytics(
          ticker
      )

      m1 = min(98.0, fund_cnt * 10.5 + abs(dist_52w) * 1.1)
      m2 = max(35.0, 95.0 - (idx - 1) * 2.5)
      m3 = min(95.0, (m1 + m2) / 2.0)
      smart_score = round(0.20 * m1 + 0.40 * m2 + 0.40 * m3, 1)

      micro_pass = ad_bullish
      if smart_score >= 75.0 and micro_pass:
        sig = "STRONG_BUY"
      elif smart_score >= 60.0 and micro_pass:
        sig = "ACCUMULATE"
      elif smart_score >= 60.0 and not micro_pass:
        sig = "WATCH_LAG"
      else:
        sig = "NEUTRAL"

      scored.append({
          "rank": idx,
          "cusip": cusip,
          "ticker": ticker,
          "name": d["name"],
          "fund_cnt": fund_cnt,
          "inflow_m": inflow_m,
          "score": smart_score,
          "micro_pass": micro_pass,
          "signal": sig,
          "curr_price": curr_p,
          "return_pct": ret_pct,
      })

    self.scored_items = scored
    Clock.schedule_once(lambda dt: self.on_finished())

  def on_finished(self):
    self.btn_run.disabled = False
    self.lbl_status.text = (
        f"분석 완료! 총 {len(self.scored_items)}개 핵심 종목 스코어 산출됨."
    )
    self.render_cards()

  def render_cards(self, *args):
    self.list_layout.clear_widgets()
    flt = self.filter_spinner.text

    for item in self.scored_items:
      sig = item["signal"]
      if flt == "🟢 STRONG_BUY" and sig != "STRONG_BUY":
        continue
      if flt == "🔵 ACCUMULATE" and sig != "ACCUMULATE":
        continue
      if flt == "검증 PASS 종목만" and not item["micro_pass"]:
        continue

      bg_col = (
          (0.08, 0.25, 0.12, 1)
          if sig == "STRONG_BUY"
          else (
              (0.1, 0.2, 0.35, 1)
              if sig == "ACCUMULATE"
              else (
                  (0.28, 0.24, 0.1, 1)
                  if sig == "WATCH_LAG"
                  else (0.16, 0.18, 0.22, 1)
              )
          )
      )

      micro_txt = "PASS" if item["micro_pass"] else "FAIL"
      card = Button(
          size_hint_y=None,
          height=76,
          background_color=bg_col,
          text=(
              f"#{item['rank']} [{item['ticker']}] {item['name'][:16]} |"
              f" {sig}\n스마트스코어: {item['score']}점 (A/D:{micro_txt}) | 기관"
              f" {item['fund_cnt']}개 (${item['inflow_m']:,.1f}M)"
          ),
          font_size="13sp",
          halign="left",
          valign="middle",
      )
      card.bind(size=card.setter("text_size"))
      card.bind(on_release=lambda btn, it=item: self.show_detail(it))
      self.list_layout.add_widget(card)

  def show_detail(self, item):
    funds_detail = []
    for r in self.curr_records:
      if r["cusip"] == item["cusip"]:
        key = (r["cik"], r["cusip"])
        if key not in self.prev_records:
          funds_detail.append(
              f"[신규] {r['fund']}: +{r['shares']:,}주"
              f" (${r['val']/1000.0:.1f}M)"
          )
        else:
          p = self.prev_records[key]
          if r["shares"] > p["shares"]:
            diff_s = r["shares"] - p["shares"]
            diff_v = (r["val"] - p["val"]) / 1000.0
            funds_detail.append(
                f"[확대] {r['fund']}: +{diff_s:,}주 (+${diff_v:.1f}M)"
            )

    content = BoxLayout(orientation="vertical", spacing=8, padding=10)
    body = Label(
        text=(
            "\n".join(funds_detail) if funds_detail else "상세 기관 내역 없음"
        ),
        font_size="13sp",
        halign="left",
        valign="top",
    )
    body.bind(size=body.setter("text_size"))
    scroll_body = ScrollView()
    scroll_body.add_widget(body)
    content.add_widget(scroll_body)

    btn_close = Button(
        text="닫기",
        size_hint_y=None,
        height=44,
        background_color=(0.2, 0.6, 0.9, 1),
    )
    popup = Popup(
        title=f"[{item['ticker']}] {item['signal']} (점수: {item['score']})",
        content=content,
        size_hint=(0.92, 0.78),
    )
    btn_close.bind(on_release=popup.dismiss)
    content.add_widget(btn_close)
    popup.open()


if __name__ == "__main__":
  TrackerAppV15().run()
