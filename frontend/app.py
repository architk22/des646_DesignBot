import os
import base64
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="DDI Checker", layout="wide")

def _inject_css(css: str):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def apply_wallpaper(mode: str = "Gradient", img_bytes: bytes | None = None):
    if mode == "Gradient":
        _inject_css("""
        .stApp{background:radial-gradient(1200px 600px at 10% 10%, #1f2937 0%, #0b0f16 40%),
                           radial-gradient(900px 500px at 90% 20%, #0ea5e9 0%, transparent 60%),
                           radial-gradient(800px 600px at 50% 100%, #22c55e22 0%, transparent 50%), #0f1115;
               background-attachment:fixed;}
        """)
    elif mode == "Aurora":
        _inject_css("""
        @keyframes auroraMove{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
        .stApp{background:linear-gradient(120deg,#0ea5e933,#a855f733,#22c55e33,#f59e0b33);
               background-size:300% 300%;animation:auroraMove 18s ease infinite;}
        """)
    elif mode == "Custom" and img_bytes:
        b64 = base64.b64encode(img_bytes).decode()
        _inject_css(f"""
        .stApp{{background-image:url('data:image/png;base64,{b64}');
                background-size:cover;background-position:center center;background-attachment:fixed;}}
        """)
    _inject_css("""
    .stApp::before{content:"";position:fixed;inset:0;background:linear-gradient(180deg,#0f11158a 0%,#0f111599 40%,#0f1115cc 100%);pointer-events:none;z-index:0;}
    .block-container{position:relative;z-index:1;}
    :root{--card-bg:#14161a;--chip-bg:#22252b;--chip-txt:#c9d1d9;}
    .stApp{color:#e5e7eb;}
    .ddi-card{padding:22px;border-radius:18px;background:rgba(26,29,36,.55);border:1px solid rgba(255,255,255,.06);
              backdrop-filter:blur(6px) saturate(130%);-webkit-backdrop-filter:blur(6px) saturate(130%);box-shadow:0 8px 32px rgba(0,0,0,.35);margin-bottom:18px;}
    .ddi-title{font-weight:700;font-size:1.25rem;margin-bottom:.35rem;display:flex;align-items:center;gap:.6rem;}
    .ddi-chip{display:inline-flex;align-items:center;gap:.4rem;padding:4px 10px;border-radius:999px;font-size:.85rem;font-weight:600;background:var(--chip-bg);color:var(--chip-txt);border:1px solid rgba(255,255,255,.06);}
    .ddi-desc{color:#d0d6e0;margin:.35rem 0 .6rem 0;line-height:1.4;}
    .ddi-manage{color:#e2e8f0;}
    .progress-wrap{background:#1c1f25;border:1px solid #242833;border-radius:10px;height:10px;overflow:hidden;}
    .progress-bar{height:100%;border-radius:8px;}
    .smallmuted{color:#9aa4b2;font-size:.85rem;}
    .rowgap{margin-top:8px;}
    """)

sev_meta = {
    "Contraindicated": {"emoji": "⛔", "color": "#ef4444"},
    "Major": {"emoji": "⚠️", "color": "#f59e0b"},
    "Moderate": {"emoji": "🟡", "color": "#eab308"},
    "Minor": {"emoji": "🟢", "color": "#22c55e"},
}

with st.sidebar:
    st.subheader("Wallpaper")
    wp_choice = st.radio("Style", ["Gradient", "Aurora", "Custom"], index=0)
    up_bytes = None
    if wp_choice == "Custom":
        f = st.file_uploader("Upload background image", type=["png", "jpg", "jpeg"])
        if f: up_bytes = f.read()

apply_wallpaper(wp_choice, up_bytes)

st.markdown("<h1>Drug–Drug Interaction Checker</h1>", unsafe_allow_html=True)

c1, c2 = st.columns([1, 1])
with c1:
    new = st.text_input("New drug", placeholder="e.g., warfarin")
with c2:
    curr = st.text_area("Current meds (comma-separated)", placeholder="e.g., metronidazole, fluconazole, ciprofloxacin", height=90)

t1, t2, t3 = st.columns([0.18, 0.25, 0.57])
with t1:
    run = st.button("Check", use_container_width=True)
with t2:
    show_details = st.toggle("Show technical details", value=False)
with t3:
    st.caption(f"Backend: {BACKEND_URL}")

def post_check(new_drug, meds):
    r = requests.post(f"{BACKEND_URL}/check", json={"new_drug": new_drug, "current": meds}, timeout=15)
    r.raise_for_status()
    return r.json()

def parse_meds(s):
    return [x.strip() for x in s.split(",") if x.strip()]

def pill_html(sev, score):
    m = sev_meta.get(sev, {"emoji": "💊", "color": "#DAE1E1"})
    return f"""<div class="ddi-chip" style="border-color:{m['color']}55;color:{m['color']};background:{m['color']}14;">{m['emoji']} {sev} • {score:.2f}</div>"""

def progress_html(score, sev):
    pct = max(0, min(100, int(score * 100)))
    color = sev_meta.get(sev, {"color": "#DAE1E1"})["color"]
    return f"""<div class="progress-wrap"><div class="progress-bar" style="width:{pct}%; background:{color};"></div></div><div class="smallmuted rowgap">severity {score:.2f}</div>"""

def render_alert(a):
    sev = a.get("severity", "")
    score = float(a.get("severity_score", 0.0))
    drugs = f"{a['pair'][0]} × {a['pair'][1]}"
    desc = a.get("description", "").strip()
    mgmt = a.get("management", "").strip()
    m = sev_meta.get(sev, {"emoji": "💊", "color": "#DAE1E1"})
    st.markdown(f"""
    <div class="ddi-card">
      <div class="ddi-title">{m['emoji']} {drugs}</div>
      {pill_html(sev, score)}
      <div class="ddi-desc">{desc}</div>
      {("<div class='ddi-manage'><b>Management:</b> "+mgmt+"</div>") if mgmt else ""}
      <div class="rowgap"></div>
      {progress_html(score, sev)}
    </div>
    """, unsafe_allow_html=True)
    if show_details:
        with st.expander("Why this alert?"):
            st.json({"proof": a.get("proof", {}), "sources": a.get("sources", [])})

if run:
    meds = parse_meds(curr)
    if not new or not meds:
        st.error("Please enter a new drug and at least one current medication.")
    else:
        try:
            data = post_check(new, meds)
        except Exception as e:
            st.error(f"Backend error: {e}")
        else:
            alerts = data.get("alerts", [])
            misses = data.get("not_found", [])
            if not alerts:
                st.success("No interactions found.")
            else:
                order = {"Contraindicated": 3, "Major": 2, "Moderate": 1, "Minor": 0}
                alerts.sort(key=lambda x: (order.get(x.get("severity", ""), -1), x.get("severity_score", 0.0)), reverse=True)
                for a in alerts:
                    render_alert(a)
            if misses:
                st.write("")
                st.markdown("**Pairs not in database**")
                for m in misses:
                    a, b = m["pair"]
                    st.info(f"{a} × {b}: not found")
