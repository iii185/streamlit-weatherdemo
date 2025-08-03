import streamlit as st
import pandas as pd
import urllib.request
import json

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
    st.radio("fruits",["apple","orange","melon"])

# データ読み込み
data = read_json_lines_from_url(JSON_FILE_URL)

# データをDataFrameに変換
df = pd.DataFrame(data)

# Streamlitで表示
st.title("ウェザーステーションデータ")
st.dataframe(df)

# 温度グラフ
st.subheader("🌡️ 温度の推移")
st.line_chart(df["Temperature"].astype(float),
    # x="col1",
    # y=["col2", "col3"],
    color=["#FF0000"]# Optional
)

# CO2のグラフ
st.subheader("🌫️ CO₂濃度の推移")
st.line_chart(df["CO2"].astype(float))

# 湿度のグラフ
st.subheader("💧 湿度の推移")
st.line_chart(df["Humidity"].astype(float))

#風速のグラフ
st.subheader("🍃 風速の推移")
st.line_chart(df["windSpeed"].astype(float))

#風の角度

def angle_to_arrow(angle):
    angle = int(angle)
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

# dfに新しい列を追加（絵文字＋方角）
df["Wind Direction"] = df["windAngle"].apply(angle_to_arrow)

# 表示
st.subheader("🍃 風の向き（絵文字表示）")
st.dataframe(df[["windAngle", "Wind Direction"]])

st.subheader("☀️ 照度の推移")
st.line_chart(df["Lux"].astype(float))
# 
# fig = px.line(
#     df_season_drivers,
#     x="round",
#     y="points",
#     color="driverRef",
#     labels={"driverRef": "driver", "name": "Grand Prix"},
#     category_orders={"driverRef": list_order_points},
# )
# st.plotly_chart(fig, use_container_width=True)
# 
# selected_season = st.selectbox(
#     "Select season", list_season, key="selected_season_season_result"
# )
# df_season = df[df["year"] == selected_season]
# 
# selected_items = st.multiselect(
#     "Select drivers (default = top 5 of the season)",
#     options=list_drivers,
#     default=list_default_drivers,
#     key="selected_drivers_season_result",
# )
# 
# df_season_drivers = df_season[df_season["driverRef"].isin(selected_items)]
# データからカラムを取得（存在する場合）
if 'date' in df.columns:
    # 日付から年を抽出
    df['year'] = pd.to_datetime(df['date']).dt.year
    list_season = sorted(df['year'].unique().tolist())

    # 年の選択
    selected_season = st.selectbox(
        "Select year", list_season, key="selected_season_result"
    )
    df_season = df[df["year"] == selected_season]

    # センサーデータのタイプ選択
    available_sensors = [col for col in df.columns if col not in ['date', 'year', 'Wind Direction']]
    selected_sensors = st.multiselect(
        "Select sensors to display",
        options=available_sensors,
        default=available_sensors[:3] if len(available_sensors) >= 3 else available_sensors,
        key="selected_sensors_result",
    )

    # 選択されたセンサーデータの表示
    if selected_sensors:
        st.subheader("📊 選択したセンサーデータ")
        st.line_chart(df_season[selected_sensors])
