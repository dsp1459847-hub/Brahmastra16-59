import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="MAYA AI - The Perfect Engine", layout="wide")

st.title("MAYA AI 🦅: The Perfect Golden Engine ⚡")
st.markdown("Aapki saari baatein lagoo hain: **1. Zero-Fail (Kal Pass) ko No. 1 Priority, 2. Sequence Matcher (1 Pass 1 Fail etc.), 3. Saare 45 TFs (Pahade In), 4. Exact Dates on Banner, 5. Result Freezer!**")

# --- RESULT MEMORY (DIARY) ---
if 'results_cache' not in st.session_state:
    st.session_state.results_cache = {}

def reset_memory():
    st.session_state.results_cache = {}

# --- 1. Sidebar ---
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

        # --- CORE CACHED FUNCTIONS ---
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

        # ==========================================
        # 🚀 THE NEW UNIFIED EVALUATOR (Zero-Fail & Sequence Matcher)
        # ==========================================
        @st.cache_data
        def get_unified_best_timeframe(history_tuple, dates_tuple):
            h_list = list(history_tuple)
            d_list = list(dates_tuple)
            candidates = []
            
            # Saare 45 Timeframes Check Honge (Pahade bhi aur Ajeeb bhi)
            for tf in range(1, 46):
                # Is Timeframe ki history banao
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
                
                is_valid = False
                logic_name = ""
                curr_f = 0
                
                # --- CONDITION 1: ZERO FAIL (Kal Pass Hua Hai) ---
                if hit_history[-1] == True:
                    is_valid = True
                    logic_name = "ZERO FAIL (High Quality: Kal Pass Tha)"
                
                # --- CONDITION 2: SEQUENCE MATCHER (Kal Fail Hua Hai) ---
                else:
                    # History ko gino (Run Length Encoding)
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
                    
                    curr_f = rle[-1][1] # Abhi kitne din se fail chal raha hai
                    
                    # History me check karo ki kya pehle bhi exact itne fail ke baad PASS hua tha?
                    seq_matched = False
                    for k in range(len(rle)-1):
                        if rle[k] == (False, curr_f) and rle[k+1][0] == True:
                            seq_matched = True
                            break
                            
                    if seq_matched:
                        is_valid = True
                        logic_name = f"SEQUENCE PATTERN ({curr_f} Fail ke baad Pass hota hai)"
                
                # --- SCORE CALCULATOR (Jan-Apr & Max-Fail) ---
                jan_apr = 0
                for i in range(1, len(hit_history)):
                    if hit_history[i] and hit_history[i-1] and (1 <= d_list[i+15].month <= 4): jan_apr += 1
                        
                max_f = 0
                c_f = 0
                for h in hit_history:
                    if not h: 
                        c_f += 1
                        if c_f > max_f: max_f = c_f
                    else: c_f = 0
                        
                # Agar Candidate valid hai (Zero Fail ya Sequence hai), toh list mein daalo
                if is_valid:
                    candidates.append({
                        'tf': tf, 'logic': logic_name, 'score': jan_apr, 'max_f': max_f,
                        'is_zero_fail': hit_history[-1], 'curr_f': curr_f
                    })

            # --- WINNER SELECTION ---
            if candidates:
                # Rank 1: Minimum Max-Fail (Sabse Safe)
                # Rank 2: Agar Max-Fail same hai, toh 'Zero Fail' ko Priority do!
                # Rank 3: Jan-Apr Score
                best = sorted(candidates, key=lambda x: (x['max_f'], not x['is_zero_fail'], -x['score']))[0]
                return best['tf'], best['logic'], best['curr_f'], best['score'], best['max_f']
            else:
                return 15, "DEFAULT FALLBACK (Koi shart poori nahi hui)", 0, 0, 99

        # --- SHIFT PROCESSING (With Screenshot/Freezer) ---
        for shift in shift_order:
            if shift not in df.columns: continue
            
            st.markdown("---")
            
            if shift not in st.session_state.results_cache:
                with st.spinner(f"Searching {shift}... Zero-Fail & Sequences check ho rahe hain!"):
                    s_data = filtered_df[['DATE', shift]].dropna()
                    hist = s_data[shift].astype(int).tolist()
                    d_list = s_data['DATE'].tolist()
                    
                    if len(hist) < 60: continue
                    
                    # AI khud decide karega best timeframe
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
                        
                    green_nums = [n for n in tiers[tier_best] if n not in traps]
                    
                    # Store in Screenshot Diary
                    st.session_state.results_cache[shift] = {
                        'logic': res_vals[1], 'tf': tf_final, 'curr_f': res_vals[2], 
                        'score': res_vals[3], 'max_f': res_vals[4], 'tier': tier_best,
                        'nums': green_nums, 'traps': list(traps), 'raw_tier_nums': tiers[tier_best]
                    }

            # --- DISPLAY WITH EXACT DATES ---
            res = st.session_state.results_cache[shift]
            
            dates_today = filtered_df[filtered_df[shift].notna()]['DATE'].tolist()
            date_kal = dates_today[-1].strftime('%d %b %Y') if len(dates_today) > 0 else ""
            date_parso = dates_today[-2].strftime('%d %b %Y') if len(dates_today) > 1 else ""
            
            st.subheader(f"🧩 Shift: {shift}")
            
            # AAPKE MANGE HUE EXACT BANNER TEXTS
            if res['curr_f'] == 0:
                banner_bg = "#28a745"
                border_c = "#1e7e34"
                text_col = "white"
                banner_text = f"✅ <b>ZERO FAIL (High Quality):</b> Pichla din (<b>{date_kal}</b>) PAAS tha! Aaj seedha continuous hit hoga."
            else:
                banner_bg = "#ffc107" if res['curr_f'] == 1 else "#FF4B4B"
                border_c = "#d39e00" if res['curr_f'] == 1 else "#c82333"
                text_col = "black" if res['curr_f'] == 1 else "white"
                
                date_start_fail = dates_today[-1 - res['curr_f']].strftime('%d %b %Y') if len(dates_today) > res['curr_f'] else ""
                
                if res['curr_f'] == 1:
                     banner_text = f"⚠️ <b>SEQUENCE MATCH (1 Fail):</b> <b>{date_parso}</b> ko Pass tha, aur kal (<b>{date_kal}</b>) Fail hua. History me ye sequence hamesha rebound hota hai!"
                else:
                     banner_text = f"🔥 <b>SEQUENCE MATCH ({res['curr_f']} Fail):</b> <b>{date_start_fail}</b> se fail chal raha tha, kal (<b>{date_kal}</b>) final fail quota poora hua!"

            st.markdown(f"<div style='background:{banner_bg}; padding:10px; border-radius:8px; border: 2px solid {border_c}; text-align:center; color:{text_col}; margin-bottom:10px;'>{banner_text}</div>", unsafe_allow_html=True)

            c1, c2 = st.columns([1, 2.5])
            with c1:
                actual_row = df[df['DATE'].dt.date == target_date_next]
                actual_val = int(actual_row.iloc[0][shift]) if not actual_row.empty and pd.notna(actual_row.iloc[0][shift]) else None
                is_hit = actual_val in res['nums'] if actual_val is not None else False
                
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
                            f"🔥 <b>SABSE BADI BAAT:</b> Is timeframe ki poori history mein <b>sabse lamba fail sirf {res['max_f']} din</b> gaya hai!</i>", unsafe_allow_html=True)
                
                st.markdown(f"<hr style='margin:5px 0; border-top:1px solid #444;'>🥇 Prediction Tier: <b style='color:{border_col}; font-size:18px;'>{res['tier']}</b></div>", unsafe_allow_html=True)

            nums_html = "<div style='display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px;'>"
            for n in sorted(res['raw_tier_nums']):
                if n in res['traps']:
                    bg = "#1a1a1a"; border = "#333"; font_c = "#555"; extra = "text-decoration: line-through;"
                else:
                    bg = "#00FF7F"; border = "#008000"; font_c = "black"; extra = ""
                nums_html += f"<div style='background:{bg}; padding:10px; border-radius:8px; text-align:center; min-width:45px; border:2px solid {border}; box-shadow: 2px 2px 5px rgba(0,0,0,0.5); {extra}'><span style='font-size:20px; font-weight:bold; color:{font_c};'>{n:02d}</span></div>"
            nums_html += "</div>"
            st.markdown(nums_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
      
