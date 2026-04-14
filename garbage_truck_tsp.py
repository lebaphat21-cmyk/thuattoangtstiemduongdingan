import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Circle, FancyBboxPatch
import matplotlib.patheffects as pe
import time
import copy
import io

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🚛 Tối Ưu Xe Gom Rác – Quận Tân Phú",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;600;800&family=IBM+Plex+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }

.hero {
    background: linear-gradient(135deg, #0a0f1e 0%, #1a2744 40%, #0d3b1e 100%);
    border: 1px solid #2a4a6b;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: "🗺️";
    position: absolute; right: 24px; top: 50%;
    transform: translateY(-50%);
    font-size: 5rem; opacity: 0.12;
}
.hero-title {
    font-size: 2.2rem; font-weight: 800;
    color: #f0f0f0; margin: 0;
    text-shadow: 0 0 30px rgba(0,200,150,0.4);
}
.hero-sub { color: #7ecfb3; font-size: 1rem; margin-top: 4px; }

.section-card {
    background: #0d1b2a;
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 18px 20px;
    margin: 12px 0;
}
.section-title {
    font-size: 1.1rem; font-weight: 600;
    color: #7ecfb3;
    border-bottom: 1px solid #1e3a5f;
    padding-bottom: 8px; margin-bottom: 14px;
}
.metric-box {
    background: linear-gradient(135deg, #0a1628, #112240);
    border: 1px solid #1e4d8c;
    border-radius: 10px;
    padding: 14px; text-align: center;
}
.metric-val { font-size: 2rem; font-weight: 800; color: #f7c948; font-family: 'IBM Plex Mono', monospace; }
.metric-lbl { font-size: 0.78rem; color: #8899aa; margin-top: 2px; }
.metric-save { font-size: 1.8rem; font-weight: 800; color: #4cff91; }

.route-step {
    display: flex; align-items: center; gap: 10px;
    padding: 6px 12px; margin: 3px 0;
    background: #0d1b2a; border-radius: 8px;
    border-left: 3px solid #2a6496;
    font-size: 0.9rem;
}
.badge {
    display: inline-block;
    padding: 2px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600;
}
.badge-gts  { background:#1a3a5c; color:#7ecfb3; }
.badge-opt  { background:#1a3d25; color:#4cff91; }
.badge-km   { color:#f7c948; font-family:'IBM Plex Mono',monospace; font-weight:600; }

.stTabs [data-baseweb="tab"] { font-family:'Kanit',sans-serif; font-size:0.95rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# DỮ LIỆU LOCATIONS + TỌA ĐỘ (Quận Tân Phú, HCMC)
# ──────────────────────────────────────────────────────────────────────────────
LOCATIONS = [
    "UBND Quận Tân Phú",   "AEON Mall Tân Phú",   "Công viên Đầm Sen",
    "THPT Tây Thạnh",      "Chợ Tân Hương",       "P. Tân Sơn Nhì",
    "P. Phú Thọ Hòa",      "P. Tây Thạnh",        "P. Hòa Thạnh",
    "Celadon City",        "ĐH Văn Hiến",         "BigC Trường Chinh",
    "Chợ Phiết Bách",      "KCN Tân Bình",        "P. Phú Thành",
]

# Tọa độ (lon, lat) xấp xỉ thực tế Quận Tân Phú
COORDS = np.array([
    [106.6280, 10.7820],  # UBND Quận Tân Phú
    [106.6170, 10.7900],  # AEON Mall
    [106.6480, 10.7680],  # Đầm Sen
    [106.6340, 10.7960],  # THPT Tây Thạnh
    [106.6260, 10.7780],  # Chợ Tân Hương
    [106.6200, 10.7850],  # P. Tân Sơn Nhì
    [106.6320, 10.7720],  # P. Phú Thọ Hòa
    [106.6360, 10.7940],  # P. Tây Thạnh
    [106.6420, 10.7880],  # P. Hòa Thạnh
    [106.6140, 10.7960],  # Celadon City
    [106.6580, 10.7760],  # ĐH Văn Hiến
    [106.6500, 10.7820],  # BigC Trường Chinh
    [106.6440, 10.7700],  # Chợ Phiết Bách
    [106.6560, 10.7880],  # KCN Tân Bình
    [106.6300, 10.7800],  # P. Phú Thành
])

N = len(LOCATIONS)

# Ma trận mặc định (đối xứng, đơn vị: km × 10)
_DEFAULT_RAW = """
0 23 15 18 8 12 14 20 19 28 22 17 16 25 10
23 0 30 14 18 11 22 16 24 9 31 27 29 33 20
15 30 0 22 12 19 10 25 18 35 14 9 8 18 16
18 14 22 0 15 9 17 7 12 21 24 20 23 27 14
8 18 12 15 0 8 7 16 14 24 17 13 12 20 6
12 11 19 9 8 0 11 10 13 17 22 18 20 25 9
14 22 10 17 7 11 0 18 12 28 16 11 10 19 8
20 16 25 7 16 10 18 0 9 22 27 23 25 28 15
19 24 18 12 14 13 12 9 0 26 20 16 17 22 12
28 9 35 21 24 17 28 22 26 0 36 30 33 38 25
22 31 14 24 17 22 16 27 20 36 0 8 10 15 19
17 27 9 20 13 18 11 23 16 30 8 0 5 11 15
16 29 8 23 12 20 10 25 17 33 10 5 0 9 14
25 33 18 27 20 25 19 28 22 38 15 11 9 0 22
10 20 16 14 6 9 8 15 12 25 19 15 14 22 0
"""

def parse_default_matrix():
    rows = [r.strip() for r in _DEFAULT_RAW.strip().split("\n")]
    return [[int(v) for v in r.split()] for r in rows]

# ──────────────────────────────────────────────────────────────────────────────
# THUẬT TOÁN
# ──────────────────────────────────────────────────────────────────────────────
def calc_distance(dist_mat, tour):
    return sum(dist_mat[tour[i]][tour[i+1]] for i in range(len(tour)-1))

def greedy_nearest_neighbor(dist_mat, start=0):
    visited = [False]*N
    tour = [start]
    visited[start] = True
    steps = []
    curr = start
    while len(tour) < N:
        nearest, min_d = -1, float("inf")
        for i in range(N):
            if not visited[i] and dist_mat[curr][i] < min_d:
                min_d = dist_mat[curr][i]; nearest = i
        steps.append((curr, nearest, min_d))
        visited[nearest] = True
        tour.append(nearest)
        curr = nearest
    tour.append(tour[0])
    return tour, steps

def two_opt(dist_mat, tour_in):
    tour = tour_in[:]
    improved = True
    history = []
    while improved:
        improved = False
        best = calc_distance(dist_mat, tour)
        for i in range(1, len(tour)-2):
            for k in range(i+1, len(tour)-1):
                new_tour = tour[:i] + tour[i:k+1][::-1] + tour[k+1:]
                nd = calc_distance(dist_mat, new_tour)
                if nd < best:
                    best = nd; tour = new_tour; improved = True
                    history.append({"step": len(history)+1, "distance": nd,
                                    "swap": f"{LOCATIONS[tour[i]]} ↔ {LOCATIONS[tour[k]]}"})
    return tour, history

def validate_matrix(mat):
    for i in range(N):
        if mat[i][i] != 0: return False, f"Đường chéo [{i},{i}] ≠ 0"
        for j in range(N):
            if mat[i][j] < 0: return False, f"Giá trị âm [{i},{j}]"
            if mat[i][j] != mat[j][i]: return False, f"Không đối xứng [{i},{j}]"
    return True, "OK"

# ──────────────────────────────────────────────────────────────────────────────
# VẼ BẢN ĐỒ TUYẾN ĐƯỜNG
# ──────────────────────────────────────────────────────────────────────────────
def draw_route_map(tour, title, color_edge="#00c896", highlight_start=True):
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("#07111e")
    ax.set_facecolor("#07111e")

    # Vẽ cạnh
    for i in range(len(tour)-1):
        a, b = tour[i], tour[i+1]
        ax.annotate("",
            xy=(COORDS[b,0], COORDS[b,1]),
            xytext=(COORDS[a,0], COORDS[a,1]),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color_edge, lw=1.5,
                connectionstyle="arc3,rad=0.08",
                mutation_scale=14,
            ),
            zorder=2,
        )

    # Nodes
    for idx, (lx, ly) in enumerate(COORDS):
        is_start = (idx == tour[0])
        c = "#f7c948" if is_start else "#2a6496"
        ec = "#fff" if is_start else "#7ecfb3"
        size = 180 if is_start else 120
        ax.scatter(lx, ly, s=size, c=c, edgecolors=ec, linewidths=1.5, zorder=4)
        ax.text(lx, ly+0.0012, LOCATIONS[idx],
                ha="center", va="bottom", fontsize=6.5,
                color="#ddeeff", fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="#07111e")],
                zorder=5)
        ax.text(lx, ly-0.0014, str(idx),
                ha="center", va="top", fontsize=5.5,
                color="#aabbcc", zorder=5)

    ax.set_title(title, color="#f0f0f0", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors="#445566")
    for sp in ax.spines.values(): sp.set_color("#1a3a5f")
    ax.set_xlabel("Kinh độ", color="#556677", fontsize=8)
    ax.set_ylabel("Vĩ độ",   color="#556677", fontsize=8)
    plt.tight_layout()
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# HOẠT ẢNH XE GOM RÁC
# ──────────────────────────────────────────────────────────────────────────────
def draw_truck_frame(tour, step_idx, dist_mat, collected):
    """Vẽ 1 frame: xe đang ở cạnh thứ step_idx trong tour."""
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor("#07111e")
    ax.set_facecolor("#07111e")

    # Tất cả cạnh mờ
    for i in range(len(tour)-1):
        a, b = tour[i], tour[i+1]
        ax.plot([COORDS[a,0], COORDS[b,0]], [COORDS[a,1], COORDS[b,1]],
                color="#1a3a5f", lw=1, linestyle="--", zorder=1)

    # Cạnh đã đi – sáng
    for i in range(step_idx):
        a, b = tour[i], tour[i+1]
        ax.annotate("",
            xy=(COORDS[b,0], COORDS[b,1]),
            xytext=(COORDS[a,0], COORDS[a,1]),
            arrowprops=dict(arrowstyle="-|>", color="#00c896",
                            lw=2, connectionstyle="arc3,rad=0.08",
                            mutation_scale=14),
            zorder=2)

    # Cạnh đang đi – vàng
    if step_idx < len(tour)-1:
        a, b = tour[step_idx], tour[step_idx+1]
        ax.annotate("",
            xy=(COORDS[b,0], COORDS[b,1]),
            xytext=(COORDS[a,0], COORDS[a,1]),
            arrowprops=dict(arrowstyle="-|>", color="#f7c948",
                            lw=2.5, connectionstyle="arc3,rad=0.08",
                            mutation_scale=18),
            zorder=3)

    # Nodes
    for idx, (lx, ly) in enumerate(COORDS):
        if idx in collected:
            c, ec, size = "#4cff91", "#fff", 160
        elif idx == tour[0]:
            c, ec, size = "#f7c948", "#fff", 180
        else:
            c, ec, size = "#1a3a5f", "#7ecfb3", 100
        ax.scatter(lx, ly, s=size, c=c, edgecolors=ec, linewidths=1.5, zorder=4)
        ax.text(lx, ly+0.0012, LOCATIONS[idx],
                ha="center", va="bottom", fontsize=6.5, color="#ddeeff",
                fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="#07111e")],
                zorder=5)

    # Icon xe tải tại vị trí hiện tại
    if step_idx < len(tour)-1:
        curr_node = tour[step_idx]
        tx, ty = COORDS[curr_node, 0], COORDS[curr_node, 1]
        ax.scatter(tx, ty, s=500, c="#ff6b35", edgecolors="#fff",
                   linewidths=2, marker="D", zorder=6)
        ax.text(tx, ty, "🚛", ha="center", va="center",
                fontsize=14, zorder=7)

    # Thông tin
    done = calc_distance(dist_mat, tour[:step_idx+1]+[tour[step_idx]]) if step_idx > 0 else 0
    total = calc_distance(dist_mat, tour)
    pct = step_idx / (len(tour)-1) * 100

    info = (f"Bước {step_idx}/{len(tour)-1}  |  "
            f"Điểm hiện tại: {LOCATIONS[tour[step_idx]]}  |  "
            f"Tiến độ: {pct:.0f}%")
    ax.set_title(info, color="#f7c948", fontsize=10, fontweight="bold", pad=10)

    # Legend
    handles = [
        mpatches.Patch(color="#4cff91", label="Đã thu gom ✓"),
        mpatches.Patch(color="#f7c948", label="Điểm xuất phát / đang đến"),
        mpatches.Patch(color="#1a3a5f", label="Chưa đến"),
        mpatches.Patch(color="#ff6b35", label="Vị trí xe hiện tại"),
    ]
    ax.legend(handles=handles, loc="lower right",
              facecolor="#0d1b2a", edgecolor="#2a4a6b",
              labelcolor="#ddeeff", fontsize=8)

    ax.set_xlabel("Kinh độ", color="#556677", fontsize=8)
    ax.set_ylabel("Vĩ độ",   color="#556677", fontsize=8)
    ax.tick_params(colors="#445566")
    for sp in ax.spines.values(): sp.set_color("#1a3a5f")
    plt.tight_layout()
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR – NHẬP MA TRẬN
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Cài đặt")
    input_mode = st.radio("Nguồn dữ liệu:", ["Ma trận mặc định", "Upload file TXT"])
    start_node = st.selectbox("Điểm xuất phát:", range(N),
                               format_func=lambda i: f"{i} – {LOCATIONS[i]}")
    speed = st.slider("Tốc độ hoạt ảnh (giây/bước):", 0.1, 2.0, 0.5, 0.1)

    st.markdown("---")
    st.markdown("**Chú giải màu sắc:**")
    st.markdown("""
    - 🟡 Xuất phát
    - 🟢 Đã thu gom
    - 🔵 Chưa đến
    - 🔶 Xe hiện tại
    - ➡️ Đường vàng: đang đi
    - ➡️ Đường xanh: đã đi qua
    """)

# ──────────────────────────────────────────────────────────────────────────────
# LOAD MATRIX
# ──────────────────────────────────────────────────────────────────────────────
if input_mode == "Upload file TXT":
    uploaded = st.sidebar.file_uploader("File ma trận (15×15, cách nhau bởi space):", type=["txt"])
    if uploaded:
        try:
            content = uploaded.read().decode("utf-8")
            rows = [r.strip() for r in content.strip().split("\n")]
            dist_mat = [[int(v) for v in r.split()] for r in rows]
            ok, msg = validate_matrix(dist_mat)
            if not ok:
                st.sidebar.error(f"Ma trận không hợp lệ: {msg}"); dist_mat = parse_default_matrix()
            else:
                st.sidebar.success("✅ Ma trận hợp lệ!")
        except Exception as e:
            st.sidebar.error(f"Lỗi đọc file: {e}"); dist_mat = parse_default_matrix()
    else:
        st.sidebar.info("Chưa có file – dùng ma trận mặc định."); dist_mat = parse_default_matrix()
else:
    dist_mat = parse_default_matrix()

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <p class="hero-title">🚛 Tối Ưu Tuyến Đường Xe Gom Rác</p>
  <p class="hero-sub">Quận Tân Phú, TP.HCM — Greedy Nearest Neighbor + 2-Opt Optimization</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab_matrix, tab_gts, tab_opt, tab_anim, tab_compare = st.tabs([
    "📋 Ma Trận",
    "🧭 Thuật Toán GTS",
    "⚡ Tối Ưu 2-Opt",
    "🎬 Hoạt Ảnh Xe Gom Rác",
    "📊 So Sánh & Thống Kê",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – MA TRẬN
# ═══════════════════════════════════════════════════════════════════════════════
with tab_matrix:
    st.markdown('<div class="section-title">Ma trận khoảng cách (km)</div>', unsafe_allow_html=True)

    df_mat = pd.DataFrame(dist_mat,
                          index=[f"{i}.{LOCATIONS[i][:18]}" for i in range(N)],
                          columns=[str(i) for i in range(N)])

    def color_cell(val):
        if val == 0: return "background-color:#0a1628; color:#334;"
        if val <= 8:  return "background-color:#0d3b2a; color:#4cff91;"
        if val <= 15: return "background-color:#1a3a1a; color:#a8e6cf;"
        if val <= 25: return "background-color:#1a2d0a; color:#d4edda;"
        return "background-color:#2a1a0a; color:#f7c948;"

    st.dataframe(df_mat, use_container_width=True, height=420)

    st.caption("🟢 Rất gần (≤8km)  🟡 Gần (≤15km)  🟠 Trung bình (≤25km)  🟤 Xa (>25km)")

    # Thống kê ma trận
    vals = [dist_mat[i][j] for i in range(N) for j in range(i+1, N)]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Khoảng cách TB", f"{np.mean(vals):.1f} km")
    c2.metric("Ngắn nhất", f"{min(vals)} km")
    c3.metric("Dài nhất",  f"{max(vals)} km")
    c4.metric("Tổng cạnh", f"{N*(N-1)//2}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – GREEDY NEAREST NEIGHBOR
# ═══════════════════════════════════════════════════════════════════════════════
with tab_gts:
    gts_tour, gts_steps = greedy_nearest_neighbor(dist_mat, start_node)
    gts_dist = calc_distance(dist_mat, gts_tour)

    st.markdown(f"""
    <div class="section-card">
      <div class="section-title">Thuật Toán Tham Lam – Nearest Neighbor</div>
      <p style="color:#aabbcc; font-size:0.9rem;">
        Xuất phát từ <strong style="color:#f7c948">{LOCATIONS[start_node]}</strong> → 
        mỗi bước chọn điểm <em>chưa đến + gần nhất</em> → lặp đến khi thăm hết → quay về.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Các bước chọn đỉnh
    st.markdown("#### 📍 Từng bước chọn điểm")
    step_data = []
    running = 0
    for i, (frm, to, d) in enumerate(gts_steps):
        running += d
        step_data.append({
            "Bước": i+1,
            "Từ": LOCATIONS[frm],
            "Đến": LOCATIONS[to],
            "Khoảng cách (km)": d,
            "Cộng dồn (km)": running,
        })
    # Bước cuối – về depot
    df_steps = pd.DataFrame(step_data)
    st.dataframe(df_steps, use_container_width=True, hide_index=True, height=320)

    # Tổng khoảng cách
    st.markdown(f"""
    <div class="metric-box" style="max-width:320px;">
      <div class="metric-lbl">Tổng quãng đường GTS</div>
      <div class="metric-val">{gts_dist} km</div>
    </div>
    """, unsafe_allow_html=True)

    # Bản đồ GTS
    st.markdown("#### 🗺️ Bản đồ lộ trình GTS")
    fig_gts = draw_route_map(gts_tour, f"Lộ trình GTS – {gts_dist} km", color_edge="#e06c75")
    st.pyplot(fig_gts)
    plt.close(fig_gts)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – 2-OPT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_opt:
    opt_tour, opt_history = two_opt(dist_mat, gts_tour)
    opt_dist  = calc_distance(dist_mat, opt_tour)
    saved     = gts_dist - opt_dist
    pct_saved = saved / gts_dist * 100 if gts_dist > 0 else 0

    st.markdown(f"""
    <div class="section-card">
      <div class="section-title">Thuật Toán 2-Opt</div>
      <p style="color:#aabbcc; font-size:0.9rem;">
        Lặp đảo ngược từng cặp cạnh → nếu tổng giảm thì giữ. Lặp đến khi không cải thiện được nữa.
      </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-lbl">Trước 2-Opt (GTS)</div>
          <div class="metric-val" style="color:#e06c75;">{gts_dist} km</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-lbl">Sau 2-Opt</div>
          <div class="metric-val">{opt_dist} km</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-box">
          <div class="metric-lbl">Tiết kiệm được</div>
          <div class="metric-save">↓ {saved} km ({pct_saved:.1f}%)</div>
        </div>""", unsafe_allow_html=True)

    # Lịch sử cải thiện
    if opt_history:
        st.markdown("#### 🔄 Các lần cải thiện 2-Opt")
        df_hist = pd.DataFrame(opt_history)
        st.dataframe(df_hist, use_container_width=True, hide_index=True, height=200)

        fig_conv, ax_c = plt.subplots(figsize=(8, 3))
        fig_conv.patch.set_facecolor("#07111e")
        ax_c.set_facecolor("#0d1b2a")
        kms = [gts_dist] + [h["distance"] for h in opt_history]
        ax_c.plot(range(len(kms)), kms, color="#4cff91", lw=2.5, marker="o", ms=5)
        ax_c.fill_between(range(len(kms)), kms, alpha=0.15, color="#4cff91")
        ax_c.set_title("Hội tụ 2-Opt", color="#f0f0f0", fontsize=11)
        ax_c.tick_params(colors="#aabbcc"); ax_c.set_xlabel("Lần cải thiện", color="#aabbcc")
        ax_c.set_ylabel("Tổng km", color="#aabbcc")
        for sp in ax_c.spines.values(): sp.set_color("#1a3a5f")
        st.pyplot(fig_conv); plt.close(fig_conv)
    else:
        st.info("GTS đã tối ưu – 2-Opt không cải thiện thêm.")

    # Bản đồ 2-Opt
    st.markdown("#### 🗺️ Bản đồ lộ trình tối ưu")
    fig_opt = draw_route_map(opt_tour, f"Lộ trình 2-Opt – {opt_dist} km", color_edge="#00c896")
    st.pyplot(fig_opt); plt.close(fig_opt)

    # Danh sách chi tiết từng đoạn
    st.markdown("#### 📋 Chi tiết từng đoạn đường")
    seg_data = []
    for i in range(len(opt_tour)-1):
        a, b = opt_tour[i], opt_tour[i+1]
        seg_data.append({
            "Từ": LOCATIONS[a], "Đến": LOCATIONS[b],
            "Khoảng cách (km)": dist_mat[a][b]
        })
    st.dataframe(pd.DataFrame(seg_data), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – HOẠT ẢNH
# ═══════════════════════════════════════════════════════════════════════════════
with tab_anim:
    st.markdown("""
    <div class="section-card">
      <div class="section-title">🎬 Hoạt Ảnh Xe Gom Rác Di Chuyển</div>
      <p style="color:#aabbcc; font-size:0.9rem;">
        Xe sẽ di chuyển theo lộ trình <strong style="color:#4cff91">đã tối ưu (2-Opt)</strong>,
        thu gom rác tại từng điểm theo thứ tự.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col_btn1, col_btn2, col_btn3 = st.columns([1,1,3])
    with col_btn1:
        start_anim = st.button("▶️ Bắt đầu hoạt ảnh", type="primary", use_container_width=True)
    with col_btn2:
        show_static = st.button("🗺️ Xem bản đồ tĩnh", use_container_width=True)

    anim_placeholder = st.empty()
    info_placeholder = st.empty()

    # Progress bar
    prog_bar  = st.progress(0)
    status_tx = st.empty()

    if show_static:
        fig_s = draw_route_map(opt_tour, f"Lộ trình tối ưu – {opt_dist} km")
        anim_placeholder.pyplot(fig_s); plt.close(fig_s)

    if start_anim:
        collected = set()
        collected.add(opt_tour[0])  # Điểm xuất phát đã ở đó

        total_steps = len(opt_tour) - 1

        for step in range(total_steps + 1):
            # Thu gom điểm đang đến
            if step < total_steps:
                collected.add(opt_tour[step])

            frame = draw_truck_frame(opt_tour, step, dist_mat, collected)
            anim_placeholder.pyplot(frame)
            plt.close(frame)

            # Cập nhật info
            pct = step / total_steps * 100
            prog_bar.progress(min(pct/100, 1.0))

            if step < total_steps:
                curr  = LOCATIONS[opt_tour[step]]
                nxt   = LOCATIONS[opt_tour[step+1]]
                d_seg = dist_mat[opt_tour[step]][opt_tour[step+1]]
                status_tx.markdown(
                    f"🚛 Đang đi: **{curr}** → **{nxt}** | "
                    f"Khoảng cách đoạn: **{d_seg} km** | "
                    f"Tiến độ: **{step}/{total_steps}**"
                )
            else:
                status_tx.markdown("✅ **Hoàn thành! Xe đã gom rác toàn bộ tuyến đường.**")

            time.sleep(speed)

        prog_bar.progress(1.0)
        st.balloons()
        st.success(f"🎉 Hoàn thành! Tổng quãng đường: **{opt_dist} km** | "
                   f"Tiết kiệm: **{saved} km** so với ban đầu.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 – SO SÁNH & THỐNG KÊ
# ═══════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown("### 📊 So Sánh Trực Quan GTS vs 2-Opt")

    # Side-by-side maps
    c_left, c_right = st.columns(2)
    with c_left:
        fig_l = draw_route_map(gts_tour, f"GTS – {gts_dist} km", color_edge="#e06c75")
        st.pyplot(fig_l); plt.close(fig_l)
    with c_right:
        fig_r = draw_route_map(opt_tour, f"2-Opt – {opt_dist} km", color_edge="#00c896")
        st.pyplot(fig_r); plt.close(fig_r)

    # Bảng so sánh
    st.markdown("### 📋 Bảng Tổng Hợp")
    compare_df = pd.DataFrame([
        {
            "Thuật toán": "Greedy Nearest Neighbor (GTS)",
            "Tổng km": gts_dist,
            "Số điểm": N,
            "Phức tạp": "O(n²)",
            "Ghi chú": "Nhanh, không tối ưu",
        },
        {
            "Thuật toán": "2-Opt Optimization",
            "Tổng km": opt_dist,
            "Số điểm": N,
            "Phức tạp": "O(n²) mỗi pass",
            "Ghi chú": f"Tiết kiệm {saved} km ({pct_saved:.1f}%)",
        },
    ])
    st.dataframe(compare_df, use_container_width=True, hide_index=True)

    # Biểu đồ cột
    fig_bar, ax_b = plt.subplots(figsize=(6, 3.5))
    fig_bar.patch.set_facecolor("#07111e")
    ax_b.set_facecolor("#0d1b2a")
    bars = ax_b.bar(["GTS (ban đầu)", "2-Opt (tối ưu)"],
                    [gts_dist, opt_dist],
                    color=["#e06c75", "#4cff91"],
                    width=0.45, edgecolor="#1a3a5f", linewidth=1.5)
    for bar, val in zip(bars, [gts_dist, opt_dist]):
        ax_b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                  f"{val} km", ha="center", va="bottom",
                  color="#f0f0f0", fontweight="bold", fontsize=11)
    ax_b.set_title("So sánh tổng quãng đường", color="#f0f0f0", fontsize=12)
    ax_b.tick_params(colors="#aabbcc")
    ax_b.set_ylabel("km", color="#aabbcc")
    for sp in ax_b.spines.values(): sp.set_color("#1a3a5f")
    ax_b.set_ylim(0, max(gts_dist, opt_dist)*1.15)
    st.pyplot(fig_bar); plt.close(fig_bar)

    # Thống kê phân phối khoảng cách các đoạn
    st.markdown("### 📈 Phân Phối Khoảng Cách Từng Đoạn (2-Opt)")
    segs_opt = [dist_mat[opt_tour[i]][opt_tour[i+1]] for i in range(len(opt_tour)-1)]
    fig_hist, ax_h = plt.subplots(figsize=(7, 3))
    fig_hist.patch.set_facecolor("#07111e")
    ax_h.set_facecolor("#0d1b2a")
    ax_h.hist(segs_opt, bins=8, color="#00c896", edgecolor="#0d1b2a", alpha=0.85)
    ax_h.axvline(np.mean(segs_opt), color="#f7c948", lw=2, linestyle="--",
                 label=f"TB = {np.mean(segs_opt):.1f} km")
    ax_h.set_title("Histogram độ dài từng đoạn", color="#f0f0f0", fontsize=11)
    ax_h.tick_params(colors="#aabbcc")
    ax_h.set_xlabel("km", color="#aabbcc"); ax_h.set_ylabel("Số đoạn", color="#aabbcc")
    ax_h.legend(facecolor="#0d1b2a", edgecolor="#2a4a6b", labelcolor="#f7c948")
    for sp in ax_h.spines.values(): sp.set_color("#1a3a5f")
    st.pyplot(fig_hist); plt.close(fig_hist)

    # Kết luận
    st.markdown(f"""
    <div class="section-card">
      <div class="section-title">🏁 Kết Luận</div>
      <p style="color:#c8e6f0;">
        ✅ Lộ trình tối ưu bắt đầu và kết thúc tại 
        <strong style="color:#f7c948">{LOCATIONS[opt_tour[0]]}</strong>.
      </p>
      <p style="color:#c8e6f0;">
        🚛 Xe gom rác đi qua <strong style="color:#4cff91">{N} điểm</strong> với 
        tổng quãng đường <strong style="color:#4cff91">{opt_dist} km</strong>.
      </p>
      <p style="color:#c8e6f0;">
        💡 Thuật toán 2-Opt tiết kiệm <strong style="color:#f7c948">{saved} km 
        ({pct_saved:.1f}%)</strong> so với Greedy ban đầu.
      </p>
      <p style="color:#7ecfb3; font-size:0.85rem;">
        📌 Phức tạp: GTS O(n²) + 2-Opt O(n²·pass). Phù hợp bài toán ≤ 50 điểm.
        Với bài toán lớn hơn nên dùng Lin-Kernighan hoặc OR-Tools.
      </p>
    </div>
    """, unsafe_allow_html=True)
