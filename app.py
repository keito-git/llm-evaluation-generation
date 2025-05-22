# app.py
import streamlit as st
import pandas as pd
import random
import io
import os
from datetime import datetime

# Streamlit settings
st.set_page_config(page_title="文体年齢評価", layout="wide")
st.title("文体の年齢カテゴリ評価フォーム")

# Load question data
df = pd.read_csv("/streamlit_evaluation_data.csv")
all_categories = [
    "小学校低学年（6–8歳）",
    "小学校高学年（9–12歳）",
    "中学生（13–15歳）",
    "高校生（16–18歳）",
    "若年成人（19–29歳）",
    "中堅社会人（30–44歳）",
    "壮年層（45–64歳）",
    "高齢者（65歳以上）"
]

# Session state for navigation and responses
if "page" not in st.session_state:
    st.session_state.page = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}

# Evaluator ID
if "evaluator_id" not in st.session_state:
    st.session_state.evaluator_id = ""

if st.session_state.page == 0:
    st.header("評価者情報の入力")
    evaluator_id = st.text_input("あなたの評価者IDを入力してください：", value="")
    if st.button("開始") and evaluator_id:
        st.session_state.evaluator_id = evaluator_id
        st.session_state.page += 1
else:
    idx = st.session_state.page - 1
    if idx < len(df):
        row = df.iloc[idx]
        st.subheader(f"質問 {int(row['質問ID'])}: {row['質問文']}")

        used_categories = []
        mappings = {}
        columns = st.columns(2)
        for i, category in enumerate(all_categories):
            col = columns[i % 2]
            with col:
                st.markdown(f"**文{i+1}**: {row[category]}")
                choice = st.selectbox(f"この文に最も近いカテゴリを選んでください：", 
                                     options=[c for c in all_categories if c not in used_categories],
                                     key=f"q{idx}_a{i}")
                mappings[f"文{i+1}"] = {"回答": row[category], "カテゴリ": choice}
                used_categories.append(choice)

        if st.button("次へ"):
            st.session_state.responses[int(row["質問ID"])] = mappings
            st.session_state.page += 1
    else:
        st.success("すべての評価が完了しました。評価結果を保存しました。")

        # 整形してCSVとして出力
        all_rows = []
        for qid, mapping in st.session_state.responses.items():
            for i, (文ID, res) in enumerate(mapping.items(), 1):
                all_rows.append({
                    "評価者ID": st.session_state.evaluator_id,
                    "質問ID": qid,
                    "文番号": i,
                    "文章": res["回答"],
                    "評価カテゴリ": res["カテゴリ"]
                })

        result_df = pd.DataFrame(all_rows)

        # 保存用フォルダとファイル名の作成
        save_dir = "results"
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{save_dir}/evaluation_{st.session_state.evaluator_id}_{timestamp}.csv"
        result_df.to_csv(filename, index=False, encoding="utf-8-sig")

        st.info(f"評価結果はサーバー上に保存されました: {filename}")

        # 任意でDLもできるように
        csv_buffer = io.StringIO()
        result_df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            label="CSVファイルをダウンロード",
            data=csv_buffer.getvalue(),
            file_name=f"評価結果_{st.session_state.evaluator_id}.csv",
            mime="text/csv"
        )

        st.dataframe(result_df)
