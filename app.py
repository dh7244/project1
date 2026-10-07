    st.divider()
    st.subheader("⭐ 퀀트 탑픽 5선 (Quant Top Picks)")

    tab_pure, tab_theme = st.tabs(["🔥 SML 순수 득점 Top 5", "⚖️ 테마 분산 5대 엄선주"])

    with tab_pure:
        st.caption("💡 아래 종목을 클릭하면 하단 상세 팩터 분석으로 바로 연동됩니다.")
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
        st.caption("💡 각 슬롯의 행을 클릭하면 하단 상세 팩터 분석으로 바로 연동됩니다.")
        valid_pool = df_show[df_show["Price_Val"] > 0].copy()
        theme_picks = []
        selected_tickers = set()

        # Slot 1~5 수집
        s1 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="Inflow_M", ascending=False)
        if not s1.empty:
            t1 = s1.iloc[0]
            theme_picks.append({"전략 슬롯": "🐋 고래 매집", "티커": t1["Ticker"], "기업명": t1["Name"], "SML점수": t1["SML_Score"], "현재가($)": t1["Price_Val"], "공시후변동률": t1["Pct_Chg"], "선정 이유": "순유입액 1위"})
            selected_tickers.add(t1["Ticker"])

        s2 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="Dist_52W", ascending=True)
        if not s2.empty:
            t2 = s2.iloc[0]
            theme_picks.append({"전략 슬롯": "📉 바닥 소외", "티커": t2["Ticker"], "기업명": t2["Name"], "SML점수": t2["SML_Score"], "현재가($)": t2["Price_Val"], "공시후변동률": t2["Pct_Chg"], "선정 이유": f"52주 낙폭 {t2['Dist_52W']:.1f}%"})
            selected_tickers.add(t2["Ticker"])

        s3 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="M3", ascending=False)
        if not s3.empty:
            t3 = s3.iloc[0]
            theme_picks.append({"전략 슬롯": "⚡ 수급 급증", "티커": t3["Ticker"], "기업명": t3["Name"], "SML점수": t3["SML_Score"], "현재가($)": t3["Price_Val"], "공시후변동률": t3["Pct_Chg"], "선정 이유": f"M3 Z-Score {t3['M3']:.1f}점"})
            selected_tickers.add(t3["Ticker"])

        s4 = valid_pool[(~valid_pool["Ticker"].isin(selected_tickers)) & (valid_pool["AD_Pass"] == True)].sort_values(by="AD_Chg_Pct", ascending=False)
        if not s4.empty:
            t4 = s4.iloc[0]
            theme_picks.append({"전략 슬롯": "🌊 차트 매집", "티커": t4["Ticker"], "기업명": t4["Name"], "SML점수": t4["SML_Score"], "현재가($)": t4["Price_Val"], "공시후변동률": t4["Pct_Chg"], "선정 이유": f"A/D {t4['AD_Chg_Pct']:+.1f}%"})
            selected_tickers.add(t4["Ticker"])

        s5 = valid_pool[~valid_pool["Ticker"].isin(selected_tickers)].sort_values(by="M2", ascending=False)
        if not s5.empty:
            t5 = s5.iloc[0]
            theme_picks.append({"전략 슬롯": "💎 밸류 앙상블", "티커": t5["Ticker"], "기업명": t5["Name"], "SML점수": t5["SML_Score"], "현재가($)": t5["Price_Val"], "공시후변동률": t5["Pct_Chg"], "선정 이유": f"M2 순위 {t5['M2']:.1f}점"})
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
                }
            )
            if t_event and t_event.selection and t_event.selection.rows:
                sel_row_idx = t_event.selection.rows[0]
                if sel_row_idx < len(t_df):
                    st.session_state["selected_ticker"] = t_df.iloc[sel_row_idx]["티커"]
