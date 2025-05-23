import streamlit as st
import pandas as pd
import random
import io
import os
from datetime import datetime
import requests
import base64

# Streamlit settings
st.set_page_config(page_title="文体年齢評価", layout="wide")
st.title("文体の年齢カテゴリ評価フォーム")

# Load question data
df = pd.read_csv("streamlit_evaluation_data.csv")
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
if "evaluator_id" not in st.session_state:
    st.session_state.evaluator_id = ""

if st.session_state.page == 0:
    st.header("評価者情報の入力")
    evaluator_id = st.text_input("あなたの年齢を入力してください：", value="")
    if st.button("開始") and evaluator_id:
        st.session_state.evaluator_id = evaluator_id
        st.session_state.page += 1
else:
    idx = st.session_state.page - 1
    if idx < len(df):
        row = df.iloc[idx]
        st.subheader(f"質問 {int(row['質問ID'])}: {row['質問文']}")

        # 一度だけランダム化された文と選択肢を保存
        if f"shuffled_entries_{idx}" not in st.session_state:
            entries = [(cat, row[cat]) for cat in all_categories]
            random.shuffle(entries)
            st.session_state[f"shuffled_entries_{idx}"] = entries
        else:
            entries = st.session_state[f"shuffled_entries_{idx}"]

        mappings = {}
        columns = st.columns(2)
        for i, (category, answer) in enumerate(entries):
            col = columns[i % 2]
            with col:
                st.markdown(f"**文{i+1}**: {answer}")

                # カテゴリ選択肢も固定しておく
                key_opt = f"options_{idx}_{i}"
                if key_opt not in st.session_state:
                    st.session_state[key_opt] = random.sample(all_categories, len(all_categories))
                options = ["選択する"] + st.session_state[key_opt]

                choice = st.selectbox(
                    f"この文に最も近いカテゴリを選んでください：",
                    options=options,
                    key=f"q{idx}_a{i}"
                )
                mappings[f"文{i+1}"] = {"回答": answer, "カテゴリ": choice, "正解カテゴリ": category}

        if st.button("次へ"):
            st.session_state.responses[int(row["質問ID"])] = mappings
            st.session_state.page += 1
    else:
        st.success("すべての評価が完了しました。評価結果を保存しました。")

        all_rows = []
        for qid, mapping in st.session_state.responses.items():
            for i, (文ID, res) in enumerate(mapping.items(), 1):
                all_rows.append({
                    "評価者ID": st.session_state.evaluator_id,
                    "質問ID": qid,
                    "文番号": i,
                    "文章": res["回答"],
                    "評価カテゴリ": res["カテゴリ"],
                    "正解カテゴリ": res["正解カテゴリ"]
                })

        result_df = pd.DataFrame(all_rows)

        save_dir = "results"
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_{st.session_state.evaluator_id}_{timestamp}.csv"
        filepath = os.path.join(save_dir, filename)
        result_df.to_csv(filepath, index=False, encoding="utf-8-sig")

        st.info(f"評価結果はサーバー上に保存されました: {filepath}")

        csv_buffer = io.StringIO()
        result_df.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            label="CSVファイルをダウンロード",
            data=csv_buffer.getvalue(),
            file_name=filename,
            mime="text/csv"
        )

        GAS_URL = "https://script.google.com/macros/s/AKfycbxUzmEUtAmolKUeiyh-KOSvD5sGuSuJEiDDCIzOSRdy5iwzCgOxiJcEPCHIDahC0Mat/exec"
        try:
            b64_csv = base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("utf-8")
            response = requests.post(GAS_URL, data={"file": b64_csv, "filename": filename})
            if response.status_code == 200:
                st.success("Google Driveへの自動保存に成功しました！")
            else:
                st.warning(f"Google Driveへの保存に失敗しました（{response.status_code}）")
        except Exception as e:
            st.error(f"保存送信時にエラーが発生しました：{e}")

        st.dataframe(result_df)
