#python -m streamlit run app.pyで強制的に実行
import streamlit as st
import pandas as pd
import urllib.request
import json
import pydeck as pdk
import numpy as np



# # 📍 大きなタイトル（HTMLでフォントサイズ調整）
# st.markdown(
#     """
#     <h1 style="
#         text-align: left; 
#         font-size: 60px; 
#         font-family: 'Oswald', 'Noto Sans JP', sans-serif;
#         white-space: normal;
#         word-wrap: break-word;
#         margin-left: 0;
#         width: 100%;
#         max-width: 800px;
#     ">
#         🌦️ IOTウェザーステーションApp
#     </h1>
#     """,
#     unsafe_allow_html=True
# )

st.markdown(
    """
    <style>
    # /* ① ページ全体の上にしっかり余白を確保 */
.stApp, section.main, section.main > div.block-container {
  padding-top: 56px !important;   /* ←必要なら 72px などに増やす */
#   overflow: visible !important;   /* 切れ防止 */
    /* 全体コンテナの基本設定（中央揃え・横スクロール防止） */
    .block-container {
        text-align: center;
        # max-width: 1000px;     /* 横幅制限（必要に応じて調整） */
        margin: 0 auto;
        padding: 0 20px;
        word-wrap: break-word;
    }

    /* タイトル専用スタイル */
    .main-title {
        font-size: 60px;                         /* 文字サイズ */
        font-family: 'Oswald', 'Noto Sans JP', sans-serif;
        text-align: center;                      /* 中央寄せ */
        white-space: normal;                     /* 改行OK */
        word-wrap: break-word;                   /* 長い語を折り返し */
        margin: 20px auto 40px auto;            /* 上下の余白 */
        display: block;
        width: 100%;
        max-width: 900px;                       /* ここでも横幅制限 */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# st.markdown("""
# <style>
# /* ① ページ全体の上にしっかり余白を確保 */
# .stApp, section.main, section.main > div.block-container {
#   padding-top: 56px !important;   /* ←必要なら 72px などに増やす */
#   overflow: visible !important;   /* 切れ防止 */
# }

# /* ② タイトルのデフォルト上マージンで食い込まないように */
# h1.main-title {
#   margin-top: 0 !important;       /* 食い込み防止 */
#   padding-top: 8px;               /* 見出し自身にも少し余白 */
#   line-height: 1.15;              /* つぶれ防止 */
#   white-space: normal;            /* はみ出し防止 */
#   word-wrap: break-word;
#   text-align: center;
#   font-size: clamp(40px, 6vw, 64px);
# }

# /* ③ ヘッダーを触っている場合の保険（非表示にしていても高さ調整） */
# header[data-testid="stHeader"] {
#   max-height: 0; 
#   height: 0; 
#   visibility: hidden;
#   overflow: visible !important;
# }
# </style>
# """, unsafe_allow_html=True)

# タイトルを呼び出す
st.markdown("<h1 class='main-title'>🌦️ IOTウェザーステーションApp</h1>", unsafe_allow_html=True)

# CSVファイルのURL（GitHub上のCSVをRaw形式で指定）
CSV_FILE_URL = "https://raw.githubusercontent.com/iii185/csv.demo1/refs/heads/main/0919(in).csv"
# -----------------------------
# 📥 CSVの読み込み
# -----------------------------
@st.cache_data
def read_csv_from_url(url):
    return pd.read_csv(url)

# データ読み込み
df = read_csv_from_url(CSV_FILE_URL)

# -----------------------------
# 📤 CSVファイルアップロード欄
# -----------------------------
uploaded_file = st.file_uploader(
    "CSVファイルをアップロードしてください（任意）", 
    type="csv"
)

# -----------------------------
# 📥 データ読み込み
# -----------------------------
if uploaded_file is not None:
    st.success("✅ アップロードしたCSVを読み込みました！")
    df = pd.read_csv(uploaded_file)  # ← アップロードしたCSVを読み込む
else:
    st.info("ℹ️ CSVがアップロードされていないため、デモ版CSVを使用します。")
    df = pd.read_csv(CSV_FILE_URL)   # ← GitHubのCSVを読み込む

# def read_csv_from_url(url):
# st.title("IOTウェザーステーションApp")

with st.sidebar:
    st.title("sidebar title")
    st.button("hello")
    st.text("hello world")
    st.divider()
    st.radio("year",["2025","2026","2027"])

# # データ読み込み
# data = read_json_lines_from_url(JSON_FILE_URL)  # () と URL を忘れずに
# # データを DataFrame に変換
# df = pd.DataFrame(data)

# 📥 データ読み込み（CSVの場合）
df = pd.read_csv(CSV_FILE_URL)  # ← これだけでOK！

# ✅ データ確認（任意）
st.write("📊 読み込んだデータ：", df.head())


# データカラム名を小文字に統一
df.columns = [col.lower() for col in df.columns]

# ---------------------------
# 🗺️ ここから地図（pydeck）セクション
# ---------------------------
st.subheader("🗺️ マップ（崇城大学内）")

# 崇城大学池田キャンパス中心（崇城大座標）
KUMAMOTO_LAT = 32.83074
KUMAMOTO_LON = 130.6964611
#  32.8304495
# もしデータ側に lat/lon があればそれを使う。無ければ熊本周辺にランダム生成
if {"lat", "lon"}.issubset(set(df.columns)):
    df_map = df[["lat", "lon"]].dropna()
else:
    # データ件数に応じて点を用意（最大1000点）
    n_points = int(min(max(len(df), 200), 1000))  # データ数が少なくても200点、最大1000点
    rng = np.random.default_rng(0)
    jitter = rng.standard_normal((n_points, 2)) / [120, 120]  # 約±0.01度 ≒ 1km弱
    coords = jitter + [KUMAMOTO_LAT, KUMAMOTO_LON]
    df_map = pd.DataFrame(coords, columns=["lat", "lon"])

# pydeckレイヤー作成（Hexagon + Scatter）
hex_layer = pdk.Layer(
    "HexagonLayer",
    data=df_map,
    get_position="[lon, lat]",
    radius=1,               # 200m
    elevation_scale=10,
    elevation_range=[0, 100],
    pickable=True,
    extruded=True,
)
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position="[lon, lat]",
    get_color="[200, 30, 0, 160]",
    get_radius=0.001,
)

deck = pdk.Deck(
    map_style=None,  # Streamlitのテーマに合わせる
    initial_view_state=pdk.ViewState(
        latitude=KUMAMOTO_LAT,
        longitude=KUMAMOTO_LON,
        zoom=18,
        pitch=50,
    ),
    layers=[hex_layer, scatter_layer],
)
st.pydeck_chart(deck)

# ---------------------------
# ここから元の可視化
# ---------------------------
st.title("ウェザーステーションデータ")
st.dataframe(df)

st.title("各グラフ")
# 温度グラフ
st.subheader("🌡️ 温度の推移")
if "temperature" in df.columns:
    st.line_chart(df["temperature"].astype(float))
else:
    st.info("temperature カラムが見つかりませんでした。")

# CO2のグラフ
st.subheader("🌫️ CO₂濃度の推移")
if "co2" in df.columns:
    st.line_chart(df["co2"].astype(float))
else:
    st.info("co2 カラムが見つかりませんでした。")

# 湿度のグラフ
st.subheader("💧 湿度の推移")
if "humidity" in df.columns:
    st.line_chart(df["humidity"].astype(float))
else:
    st.info("humidity カラムが見つかりませんでした。")

# 風速のグラフ
st.subheader("🍃 風速の推移")
if "windspeed" in df.columns:
    st.line_chart(df["windspeed"].astype(float))
else:
    st.info("windspeed カラムが見つかりませんでした。")

# 風向き 絵文字化
def angle_to_arrow(angle):
    try:
        angle = int(float(angle))
        if 337 <= angle or angle < 22:
            return "⬆️ N"
        elif 22 <= angle < 67:
            return "↗️ NE"
        elif 67 <= angle < 112:
            return "→ E"
        elif 112 <= angle < 157:
            return "↘️ SE"
        elif 157 <= angle < 202:
            return "↓ S"
        elif 202 <= angle < 247:
            return "↙️ SW"
        elif 247 <= angle < 292:
            return "← W"
        elif 292 <= angle < 337:
            return "↖️ NW"
        else:
            return "❓"
    except (ValueError, TypeError):
        return "❓"

if "windangle" in df.columns:
    df["wind direction"] = df["windangle"].apply(angle_to_arrow)
    st.subheader("🍃 風の向き（絵文字表示）")
    st.dataframe(df[["windangle", "wind direction"]])
else:
    st.info("windangle カラムが見つかりませんでした。")

# 照度
st.subheader("☀️ 照度の推移")
if "lux" in df.columns:
    st.line_chart(df["lux"].astype(float))
else:
    st.info("lux カラムが見つかりませんでした。")

# 年選択して複数センサーを比較
if "date" in df.columns:
    st.success("📅 日付カラムが見つかりました")
    try:
        st.write("日付サンプル:", df["date"].iloc[0])
        df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year

        if df["year"].isna().any():
            st.warning(f"⚠️ 一部の日付を変換できませんでした。変換できなかった行数: {df['year'].isna().sum()}")

        list_season = sorted(df["year"].dropna().unique().tolist())
        st.write("検出された年:", list_season)

        if list_season:
            selected_season = st.selectbox("Select year", list_season, key="selected_season_result")
            df_season = df[df["year"] == selected_season]

            # 風向きのラベル列など、数値でない列は除外
            exclude_cols = {"date", "year", "wind direction"}
            numeric_cols = [c for c in df_season.columns if c not in exclude_cols]
            # 数値に変換できるものだけを対象にする
            available_sensors = []
            for c in numeric_cols:
                try:
                    pd.to_numeric(df_season[c].dropna().head(5))
                    available_sensors.append(c)
                except Exception:
                    pass

            selected_sensors = st.multiselect(
                "Select sensors to display",
                options=available_sensors,
                default=available_sensors[:3] if len(available_sensors) >= 3 else available_sensors,
                key="selected_sensors_result",
            )

            if selected_sensors:
                st.subheader("📊 選択したセンサーデータ")
                st.line_chart(df_season[selected_sensors].apply(pd.to_numeric, errors="coerce"))
        else:
            st.warning("⚠️ 日付から有効な年を抽出できませんでした")
    except Exception as e:
        st.error(f"⚠️ 日付処理中にエラーが発生しました: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# -----------------------------
# 📊 表示
# -----------------------------
st.subheader("📈 全計測データ")
st.dataframe(df)
