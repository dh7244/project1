                    # 💡 달러 기호($) 이스케이프 및 자연스러운 가격 추이 문구로 개선
                    chg_sign = "🔴 +" if sel_row["Price_Chg"] > 0 else ("🔵 -" if sel_row["Price_Chg"] < 0 else "")
                    chg_abs = abs(sel_row["Price_Chg"])
                    pct_str = f"{sel_row['Pct_Chg']:+.2f}%"
                    
                    st.write(
                        f"- **공시 시점 대비 주가 추이**: \${sel_row['Base_Price']:.2f} → **\${sel_row['Price_Val']:.2f}** "
                        f"({chg_sign}\${chg_abs:.2f}, {pct_str})"
                    )
