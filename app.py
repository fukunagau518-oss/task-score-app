import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="職業タスクスコア",
    page_icon="📊",
    layout="wide"
)

# データ読み込み
@st.cache_data
def load_data():
    return pd.read_csv("task_scores.csv")

df = load_data()

# 指標の設定
score_columns = {
    "非定型分析": "加重_非定型分析",
    "非定型相互": "加重_非定型相互",
    "定型認識": "加重_定型認知",
    "定型手仕事": "加重_定型手作業",
    "非定型手仕事": "加重_非定型手作業"
}

score_names = list(score_columns.keys())
major_groups = sorted(df["大分類"].dropna().unique())

# 大分類ごとの加重平均
def weighted_average(data, column):
    valid = data.dropna(subset=[column, "就業者数"])
    if valid.empty or valid["就業者数"].sum() == 0:
        return 0
    return (
        valid[column] * valid["就業者数"]
    ).sum() / valid["就業者数"].sum()

def major_score(major, column):
    group = df[df["大分類"] == major]
    return weighted_average(group, column)

# 全職業の加重平均
all_average = {
    col: weighted_average(df, col)
    for col in score_columns.values()
}

st.title("職業タスクスコア")
st.caption("職業ごとのタスク構成を5つの指標から確認できます。")

tab1, tab2 = st.tabs(["職種・大分類を調べる", "全職種一覧"])

# -------------------------
# タブ1：職種・大分類を調べる
# -------------------------
with tab1:
    st.subheader("職種を選択")

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_major = st.selectbox(
            "大分類",
            major_groups
        )

    major_df = df[df["大分類"] == selected_major]
    occupations = sorted(major_df["職業名"].dropna().unique())

    with col2:
        selected_occupation = st.selectbox(
            "職種（大分類全体の平均も選べます／入力して検索できます）",
            ["【大分類全体】"] + occupations
        )

    # 選択した職種のデータを取得
    if selected_occupation == "【大分類全体】":
        selected_data = {
            col: major_score(selected_major, col)
            for col in score_columns.values()
        }
        employment = int(major_df["就業者数"].sum())
        occupation_count = len(major_df)
        display_name = selected_major + "（全体）"
    else:
        row = major_df[
            major_df["職業名"] == selected_occupation
        ].iloc[0]

        selected_data = {
            col: row[col]
            for col in score_columns.values()
        }
        employment = int(row["就業者数"])
        occupation_count = 1
        display_name = selected_occupation

    st.divider()

    # 比較対象
    st.subheader("比較対象")

    compare_type = st.radio(
        "比較する対象を選んでください",
        ["全職業の平均（=0）", "別の大分類", "別の職種"],
        horizontal=True
    )

    comparison_data = {}
    comparison_name = "全職業の平均"

    if compare_type == "全職業の平均（=0）":
        comparison_data = all_average
        comparison_name = "全職業の平均"

    elif compare_type == "別の大分類":
        other_major = st.selectbox(
            "比較する大分類",
            [m for m in major_groups if m != selected_major]
        )
        comparison_data = {
            col: major_score(other_major, col)
            for col in score_columns.values()
        }
        comparison_name = other_major

    else:
        other_occupation = st.selectbox(
            "比較する職種",
            sorted(df["職業名"].dropna().unique())
        )
        other_row = df[
            df["職業名"] == other_occupation
        ].iloc[0]

        comparison_data = {
            col: other_row[col]
            for col in score_columns.values()
        }
        comparison_name = other_occupation

    # 基本情報
    st.divider()
    info1, info2, info3 = st.columns(3)

    info1.metric("大分類", selected_major)
    info2.metric("就業者数（合計）", f"{employment:,} 人")
    info3.metric("含まれる職種数", f"{occupation_count}")

    # スコア表
    result = pd.DataFrame({
        display_name: [
            selected_data[col] for col in score_columns.values()
        ],
        comparison_name: [
            comparison_data[col] for col in score_columns.values()
        ]
    }, index=score_names)

    result["差"] = result[display_name] - result[comparison_name]

    # グラフ
    chart_data = pd.DataFrame({
        "タスク指標": score_names,
        "標準化スコア": [
            selected_data[col] for col in score_columns.values()
        ]
    })

    fig = px.bar(
        chart_data,
        x="タスク指標",
        y="標準化スコア",
        title=display_name + "のタスクスコア"
    )
    fig.add_hline(y=0, line_dash="solid", line_color="gray")
    fig.update_layout(
        yaxis_title="標準化スコア",
        xaxis_title="",
        showlegend=False
    )

    left, right = st.columns([3, 2])

    with left:
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("比較表")
        st.dataframe(
            result.round(2),
            use_container_width=True
        )

# -------------------------
# タブ2：全職種一覧
# -------------------------
with tab2:
    st.subheader("全職種のタスクスコア一覧")

    search_word = st.text_input("職種名で検索")

    filter_major = st.selectbox(
        "大分類で絞り込む",
        ["すべて"] + major_groups
    )

    filtered = df.copy()

    if filter_major != "すべて":
        filtered = filtered[
            filtered["大分類"] == filter_major
        ]

    if search_word:
        filtered = filtered[
            filtered["職業名"].str.contains(
                search_word,
                case=False,
                na=False
            )
        ]

    display_df = filtered[
        ["大分類", "職業名", "就業者数"]
        + list(score_columns.values())
    ].rename(columns={
        "加重_非定型分析": "非定型分析",
        "加重_非定型相互": "非定型相互",
        "加重_定型認知": "定型認知",
        "加重_定型手作業": "定型手作業",
        "加重_非定型手作業": "非定型手作業"
    })

    st.write(f"該当する職種数：{len(display_df)}")
    st.dataframe(
        display_df.round(3),
        use_container_width=True,
        hide_index=True
    )
