import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="MAYA AI - True Sequence & Black Box", layout="wide")

st.title("MAYA AI 🦅: True Sequence & Zero-Fail Priority ⚡")
st.markdown("Aapki strict conditions lagoo hain: **1. ZERO-FAIL (Kal Pass) = Rank 1 Priority! 2. TRUE SEQUENCE (Kam se kam 3-4 baar repeat hona zaroori hai). 3. Black Box (Kaale dhabbe) safe hain!**")

# --- RESULT MEMORY ---
if 'results_cache' not in st.session_state:
    st.session_state.results_cache = {}

def reset_memory():
    st.session_state.results_cache = {}

st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'], on_change=reset_memory)
selected_end_date = st.sidebar.date_input("Calculation Date (T)", on_change=reset_memory)

if st.sidebar.button("Clear Memory & Re-Run"):
    reset_memory()
    st.rerun()

shift_order = ["DB", "SG", "FD", "GD", "ZA", "GL", "DS"]

@st.cache_data
def load_data(file_val):
    if file_val.name.endswith('.csv'): df = pd.read_csv(file_val)
    else: df = pd.read_excel(file_val)
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    df = df.sort_values(by='DATE').reset_index(drop=True)
    for col in shift_order:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)
        filtered_df = df[df['DATE'].dt.date <= selected_end_date].copy()
        if len(filtered_df) == 0: st.stop()
        
        target_date_next = selected_end_date + timedelta(days=1)
        st.info(f"📅 **Data Read Up To:** {selected_end_date.strftime('%d %B %Y')} | 🎯 **Target Date:** {target_date_next.strftime('%A, %d %B %Y')}")

        @st.cache_data
        def get_all_tiers_cached(past_tuple):
            scores = {n: 0 for n in range(100)}
            for days in range(1, min(46, len(past_tuple) + 1)):
                sheet = past_tuple[-days:]
                for num, freq in Counter(sheet).items(): scores[num] += freq * (1 + (1/days)) 
            ranked = sorted(range(100), key=lambda x: scores[x], reverse=True)
            return {'H': ranked[0:33], 'M': ranked[33:66], 'L': ranked[66:100]}

        def get_tier_name(num, tiers_dict):
            if num in tiers_dict['H']: return 'H'
            elif num in tiers_dict['M']: return 'M'
            elif num in tiers_dict['L']: return 'L'
            return 'FAIL'

        @st.cache_data
        def detect_player_load_trap(history_tuple):
            history_list = list(history_tuple)
            player_traps = []
            if len(history_list) < 2: return player_traps
            last_num = history_list[-1]
            prev_num = history_list[-2]
            player_traps.append((last_num + 1) % 100)
            player_traps.append((last_num - 1) % 100)
            player_traps.append(int(str(last_num).zfill(2)[::-1]))
            gap = last_num - prev_num
            player_traps.append((last_num + gap) % 100)
            for num, count in Counter(history_list[-5:]).items():
                if count >= 2: player_traps.append(num)
            return list(set(player_traps))

        @st.cache_data
        def get_doomed_timeframe_predictions(history_tuple):
            h_list = list(history_tuple)
            black_traps = set()
            for tf in range(1, 46):
                hit_history = []
                for i in range(15, len(h_list)):
                    pat = h_list[:i][-tf:]
                    nxt = [h_list[:i][k+tf] for k in range(len(h_list[:i])-tf) if h_list[:i][k:k+tf] == pat]
                    if not nxt: hit_history.append(False)
                    else:
                        top = Counter(nxt).most_common(1)[0][0]
                        td = get_all_tiers_cached(tuple(h_list[:i]))
                        hit_history.append(get_tier_name(top, td) == get_tier_name(h_list[i], td))
                
                if len(hit_history) < 10: continue
                will_fail = False
                
                if hit_history[-1] == True:
                    pass_twice = sum(1 for i in range(1, len(hit_history)) if hit_history[i] and hit_history[i-1])
                    if pass_twice == 0: will_fail = True
                elif hit_history[-1] == False:
                    curr_f = 0
                    for k in range(len(hit_history)-1, -1, -1):
                        if not hit_history[k]: curr_f += 1
                        else: break
                    past_fails = []
                    f_count = 0
                    for h in hit_history[:-curr_f]:
                        if not h: f_count += 1
                        elif f_count > 0: 
                            past_fails.append(f_count)
                            f_count = 0
                    if past_fails:
                        if curr_f < min(past_fails): will_fail = True
                            
                if will_fail:
                    pat = h_list[-tf:]
                    nxt = [h_list[i+tf] for i in range(len(h_list)-tf) if h_list[i:i+tf] == pat]
                    if nxt:
                        doomed_preds = [item[0] for item in Counter(nxt).most_common(5)]
                        black_traps.update(doomed_preds)
            return list(black_traps)

        @st.cache_data
        def get_unified_best_timeframe(history_tuple, dates_tuple):
            h_list = list(history_tuple)
            d_list = list(dates_tuple)
            candidates = []
            
            for tf in range(1, 46):
                hit_history = []
                for i in range(15, len(h_list)):
                    pat = h_list[:i][-tf:]
                    nxt = [h_list[:i][k+tf] for k in range(len(h_list[:i])-tf) if h_list[:i][k:k+tf] == pat]
                    if not nxt: hit_history.append(False)
                    else:
                        top = Counter(nxt).most_common(1)[0][0]
                        td = get_all_tiers_cached(tuple(h_list[:i]))
                        hit_history.append(get_tier_name(top, td) == get_tier_name(h_list[i], td))
                
                if not hit_history: continue
                
                is_zero_fail = False
                is_true_seq = False
                logic_name = ""
                
                if hit_history[-1] == True:
                    is_zero_fail = True
                    logic_name = "ZERO FAIL (High Quality: Kal Pass Tha)"
                    curr_f = 0
                else:
                    rle = []
                    c_val = hit_history[0]
                    c_count = 1
                    for v in hit_history[1:]:
                        if v == c_val: c_count += 1
                        else:
                            rle.append((c_val, c_count))
                            c_val = v
                            c_count = 1
                    rle.append((c_val, c_count))
                    
                    curr_f = rle[-1][1] 
                    
                    # TRUE SEQUENCE DETECTOR (Aapka logic: 3-4 times repeat ho tabhi Sequence manenge)
                    if len(rle) >= 5:
                        # Check karega ki kya pichli 2 baar bhi same 'curr_f' jitne fail de kar paas hua tha?
                        if rle[-3][0] == False and rle[-3][1] == curr_f and \
                           rle[-5][0] == False and rle[-5][1] == curr_f:
                            is_true_seq = True
                            logic_name = f"TRUE SEQUENCE ({curr_f} Fail ka pattern 3+ baar verified)"
                            
                    if not is_zero_fail and not is_true_seq:
                        logic_name = f"MASTER FALLBACK ({curr_f} Fail Se Hai)"
                
                jan_apr = sum(1 for i in range(1, len(hit_history)) if hit_history[i] and hit_history[i-1] and (1 <= d_list[i+15].month <= 4))
                        
                max_f = 0
                c_f = 0
                for h in hit_history:
                    if not h: 
                        c_f += 1
                        if c_f > max_f: max_f = c_f
                    else: c_f = 0
                        
                candidates.append({
                    'tf': tf, 'logic': logic_name, 'score': jan_apr, 'max_f': max_f,
                    'is_zero_fail': is_zero_fail, 'is_true_seq': is_true_seq, 'curr_f': curr_f
                })

            if candidates:
                # 🏆 THE PERFECT SORTING RULE: Zero-Fail First -> True Sequence Second -> Lowest Max Fail Third!
                best = sorted(candidates, key=lambda x: (not x['is_zero_fail'], not x['is_true_seq'], x['max_f'], -x['score']))[0]
                return best['tf'], best['logic'], best['curr_f'], best['score'], best['max_f'], best['is_zero_fail'], best['is_true_seq']
            else:
                return 15, "DEFAULT FALLBACK", 0, 0, 99, False, False

        def render_ank(nums, traps, black_boxes):
            nums = list(set(nums)); nums.sort()
            html = "<div style='display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;'>"
            for n in nums:
                if n in black_boxes:
                    bg = "#000000"; border = "#555"; font_c = "white"; extra = "box-shadow: 0 0 8px rgba(255,0,0,0.8);"
                elif n in traps:
                    bg = "#1a1a1a"; border = "#333"; font_c = "#555"; extra = "text-decoration: line-through;"
                else:
                    bg = "#00FF7F"; border = "#008000"; font_c = "black"; extra = ""
                html += f"<div style='background:{bg}; padding:10px; border-radius:8px; text-align:center; min-width:45px; border:2px solid {border}; {extra}'>" \
                        f"<span style='font-size:20px; font-weight:bold; color:{font_c};'>{n:02d}</span></div>"
            html += "</div>"
            return html

        for shift in shift_order:
            if shift not in df.columns: continue
            
            st.markdown("---")
            
            if shift not in st.session_state.results_cache:
                with st.spinner(f"Searching {shift}... Fixing sorting priorities (Zero-Fail First)!"):
                    s_data = filtered_df[['DATE', shift]].dropna()
                    hist = s_data[shift].astype(int).tolist()
                    d_list = s_data['DATE'].tolist()
                    
                    if len(hist) < 60: continue
                    
                    res_vals = get_unified_best_timeframe(tuple(hist), tuple(d_list))
                    tf_final = res_vals[0]
                    
                    tiers = get_all_tiers_cached(tuple(hist))
                    nxt = [hist[i+tf_final] for i in range(len(hist)-tf_final) if hist[i:i+tf_final] == hist[-tf_final:]]
                    tier_best = get_tier_name(Counter(nxt).most_common(1)[0][0], tiers) if nxt else 'H'
                    
                    last_n = hist[-1]
                    prev_n = hist[-2]
                    traps = set([(last_n+1)%100, (last_n-1)%100, int(str(last_n).zfill(2)[::-1]), (last_n + (last_n - prev_n))%100])
                    for n, count in Counter(hist[-5:]).items():
                        if count >= 2: traps.add(n)
                        
                    doomed_black_boxes = get_doomed_timeframe_predictions(tuple(hist))
                    
                    pure_green_nums = [n for n in tiers[tier_best] if n not in traps and n not in doomed_black_boxes]
                    
                    st.session_state.results_cache[shift] = {
                        'logic': res_vals[1], 'tf': tf_final, 'curr_f': res_vals[2], 
                        'score': res_vals[3], 'max_f': res_vals[4], 'is_zero_fail': res_vals[5], 'is_true_seq': res_vals[6],
                        'tier': tier_best, 'traps': list(traps), 'black_boxes': doomed_black_boxes, 'raw_tier_nums': tiers[tier_best],
                        'pure_green': pure_green_nums
                    }

            res = st.session_state.results_cache[shift]
            
            dates_today = filtered_df[filtered_df[shift].notna()]['DATE'].tolist()
            date_kal = dates_today[-1].strftime('%d %b %Y') if len(dates_today) > 0 else ""
            date_start_fail = dates_today[-1 - res['curr_f']].strftime('%d %b %Y') if len(dates_today) > res['curr_f'] else ""
            
            st.subheader(f"🧩 Shift: {shift}")
            
            if res['is_zero_fail']:
                banner_bg = "#28a745"; border_c = "#1e7e34"; text_col = "white"
                banner_text = f"✅ <b>ZERO FAIL (High Quality):</b> Pichla din (<b>{date_kal}</b>) PAAS tha! Priority 1 Timeframe applied."
            elif res['is_true_seq']:
                banner_bg = "#ffc107"; border_c = "#d39e00"; text_col = "black"
                banner_text = f"🔥 <b>TRUE SEQUENCE MATCHER:</b> <b>{date_start_fail}</b> se fail chal raha hai. History mein exactly <b>{res['curr_f']} Fail</b> ke baad pass hota aaya hai!"
            else:
                banner_bg = "#FF4B4B"; border_c = "#c82333"; text_col = "white"
                banner_text = f"⚠️ <b>MASTER FALLBACK:</b> 0-Fail ya Sequence nahi mila. Sabse kam Max-Fail ({res['max_f']} din) wala chuna gaya."

            st.markdown(f"<div style='background:{banner_bg}; padding:10px; border-radius:8px; border: 2px solid {border_c}; text-align:center; color:{text_col}; margin-bottom:10px;'>{banner_text}</div>", unsafe_allow_html=True)

            c1, c2 = st.columns([1, 2.5])
            with c1:
                actual_row = df[df['DATE'].dt.date == target_date_next]
                actual_val = int(actual_row.iloc[0][shift]) if not actual_row.empty and pd.notna(actual_row.iloc[0][shift]) else None
                
                is_hit = actual_val in res['pure_green'] if actual_val is not None else False
                
                if actual_val is not None:
                    m_color = "#28a745" if is_hit else "#FF4B4B"
                    st.markdown(f"<div style='background:{m_color}; padding:10px; border-radius:8px; text-align:center; color:white;'>Match Result ({target_date_next.strftime('%d %b')}):<br><b style='font-size:26px;'>{actual_val:02d}</b><br>{'HIT! ✅' if is_hit else 'MISS ❌'}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background:#555; padding:10px; border-radius:8px; text-align:center; color:white;'>Result:<br><b>Waiting...</b></div>", unsafe_allow_html=True)
            
            with c2:
                border_col = "#00FF7F"
                bg_col = "#00FF7F15"
                st.markdown(f"<div style='border:2px solid {border_col}; padding:10px; border-radius:8px; background:{bg_col}; font-size:14px;'>"
                            f"<b>Logic:</b> {res['logic']} | <b>Selected Gear:</b> <code>{res['tf']}-Din TF</code><br>"
                            f"<i>❄️ Jan-Apr Score: <b>{res['score']} baar</b> direct paas.<br>"
                            f"🔥 <b>MIN MAX-FAIL:</b> History ka sabse lamba fail <b>{res['max_f']} din</b> gaya hai!</i><br>"
                            f"<hr style='margin:5px 0; border-top:1px solid #444;'>"
                            f"✅ <b>HARA (Play):</b> {len(res['pure_green'])} Nums | ⬛ <b>KAALA (Doomed):</b> {len([n for n in res['raw_tier_nums'] if n in res['black_boxes']])} Nums"
                            f"</div>", unsafe_allow_html=True)

            st.markdown(render_ank(res['raw_tier_nums'], res['traps'], res['black_boxes']), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
                
