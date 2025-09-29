import streamlit as st
import pandas as pd
import urllib.request
import json
import pydeck as pdk
import numpy as np

# GitHub上のJSONファイルのURL（1行1レコードの形式）
JSON_FILE_URL = "https://raw.githubusercontent.com/iii185/Jsonurl1/main/data.json"

# JSON Lines（1行ずつJSON）の読み込み関数
def read_json_lines_from_url(url):
    with urllib.request.urlopen(url) as response:
        lines = response.read().decode("utf-8").splitlines()
        return [json.loads(line) for line in lines]

st.title("main title")
with st.sidebar:
    st.title("sidebar title")
    st.button("hello")
    st.text("hello world")
    st.divider()
    st.radio("year",["2025","2026","2027"])

# データ読み込み
data = read_json_lines_from_url(JSON_FILE_URL)

# データをDataFrameに変換
df = pd.DataFrame(data)

# データカラム名を小文字に統一
df.columns = [col.lower() for col in df.columns]

# ---------------------------
# 🗺️ ここから地図（pydeck）セクション
# ---------------------------
st.subheader("🗺️ 観測地点マップ（熊本市 周辺）")

# 熊本市中心（熊本市役所あたり）
KUMAMOTO_LAT = 32.8031
KUMAMOTO_LON = 130.7079

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
    radius=200,               # 200m
    elevation_scale=4,
    elevation_range=[0, 1000],
    pickable=True,
    extruded=True,
)
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position="[lon, lat]",
    get_color="[200, 30, 0, 160]",
    get_radius=120,
)

deck = pdk.Deck(
    map_style=None,  # Streamlitのテーマに合わせる
    initial_view_state=pdk.ViewState(
        latitude=KUMAMOTO_LAT,
        longitude=KUMAMOTO_LON,
        zoom=11,
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

# データ構造のデバッグ
st.subheader("📋 データ構造情報")
st.write("データカラム:", df.columns.tolist())
st.write("データサンプル（先頭行）:")
st.write(df.head(1))

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
else:
    st.warning("⚠️ データに'date'カラムが見つかりません。時系列分析ができません。")
    st.write("利用可能なカラム:", df.columns.tolist())



# import streamlit as st
# import pandas as pd
# import urllib.request
# import json
#
# # GitHub上のJSONファイルのURL（1行1レコードの形式）
# JSON_FILE_URL = "https://raw.githubusercontent.com/iii185/Jsonurl1/main/data.json"
#
# # JSON Lines（1行ずつJSON）の読み込み関数
# def read_json_lines_from_url(url):
#     with urllib.request.urlopen(url) as response:
#         lines = response.read().decode("utf-8").splitlines()
#         return [json.loads(line) for line in lines]
#
# st.title("main title")
# with st.sidebar:
#     st.title("sidebar title")
#     st.button("hello")
#     st.text("hello world")
#     st.divider()
#     st.radio("year",["2025","2026","2027"])
#
# # データ読み込み
# data = read_json_lines_from_url(JSON_FILE_URL)
#
# # データをDataFrameに変換
# df = pd.DataFrame(data)
#
# # データカラム名を小文字に統一（大文字小文字の違いによる問題を避けるため）
# df.columns = [col.lower() for col in df.columns]
#
# # Streamlitで表示
# st.title("ウェザーステーションデータ")
# st.dataframe(df)
#
# # 温度グラフ
# st.subheader("🌡️ 温度の推移")
# st.line_chart(df["temperature"].astype(float),
#     # x="col1",
#     # y=["col2", "col3"],
#     color=["#FF0000"]# Optional
# )
#
# # CO2のグラフ
# st.subheader("🌫️ CO₂濃度の推移")
# st.line_chart(df["co2"].astype(float))
#
# # 湿度のグラフ
# st.subheader("💧 湿度の推移")
# st.line_chart(df["humidity"].astype(float))
#
# #風速のグラフ
# st.subheader("🍃 風速の推移")
# st.line_chart(df["windspeed"].astype(float))
#
# #風の角度
#
# def angle_to_arrow(angle):
#     try:
#         angle = int(float(angle))
#         if 337 <= angle or angle < 22:
#             return "⬆️ N"
#         elif 22 <= angle < 67:
#             return "↗️ NE"
#         elif 67 <= angle < 112:
#             return "→ E"
#         elif 112 <= angle < 157:
#             return "↘️ SE"
#         elif 157 <= angle < 202:
#             return "↓ S"
#         elif 202 <= angle < 247:
#             return "↙️ SW"
#         elif 247 <= angle < 292:
#             return "← W"
#         elif 292 <= angle < 337:
#             return "↖️ NW"
#         else:
#             return "❓"
#     except (ValueError, TypeError):
#         return "❓"
#
# # dfに新しい列を追加（絵文字＋方角）
# df["wind direction"] = df["windangle"].apply(angle_to_arrow)
#
# # 表示
# st.subheader("🍃 風の向き（絵文字表示）")
# st.dataframe(df[["windangle", "wind direction"]])
#
# st.subheader("☀️ 照度の推移")
# st.line_chart(df["lux"].astype(float))
#
# # データ構造のデバッグ情報を表示
# st.subheader("📋 データ構造情報")
# st.write("データカラム:", df.columns.tolist())
# st.write("データサンプル（先頭行）:")
# st.write(df.head(1))
#
# # 日付カラムの確認と処理
# if 'date' in df.columns:
#     st.success("📅 日付カラムが見つかりました")
#     try:
#         # 日付形式のデバッグ表示
#         st.write("日付サンプル:", df['date'].iloc[0])
#
#         # 日付から年を抽出（エラーハンドリング追加）
#         df['year'] = pd.to_datetime(df['date'], errors='coerce').dt.year
#
#         # NaNのチェック
#         if df['year'].isna().any():
#             st.warning(f"⚠️ 一部の日付を変換できませんでした。変換できなかった行数: {df['year'].isna().sum()}")
#
#         list_season = sorted(df['year'].dropna().unique().tolist())
#         st.write("検出された年:", list_season)
#
#         if list_season:  # リストが空でないことを確認
#             # 年の選択
#             selected_season = st.selectbox(
#                 "Select year", list_season, key="selected_season_result"
#             )
#             df_season = df[df["year"] == selected_season]
#
#             # センサーデータのタイプ選択
#             available_sensors = [col for col in df.columns if col not in ['date', 'year', 'Wind Direction']]
#             selected_sensors = st.multiselect(
#                 "Select sensors to display",
#                 options=available_sensors,
#                 default=available_sensors[:3] if len(available_sensors) >= 3 else available_sensors,
#                 key="selected_sensors_result",
#             )
#
#             # 選択されたセンサーデータの表示
#             if selected_sensors:
#                 st.subheader("📊 選択したセンサーデータ")
#                 st.line_chart(df_season[selected_sensors])
#         else:
#             st.warning("⚠️ 日付から有効な年を抽出できませんでした")
#     except Exception as e:
#         st.error(f"⚠️ 日付処理中にエラーが発生しました: {str(e)}")
#         import traceback
#         st.code(traceback.format_exc())
# else:
#     st.warning("⚠️ データに'date'カラムが見つかりません。時系列分析ができません。")
#     st.write("利用可能なカラム:", df.columns.tolist())
# git commit -m "first commit"
# git branch -M main
# git push -u origin main
