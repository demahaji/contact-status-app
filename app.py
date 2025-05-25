import streamlit as st
import pandas as pd
import datetime
import requests
from pathlib import Path

# 定数定義
DATA_FOLDER = Path("data")
FREE_COMMENT_FILE = DATA_FOLDER / "free_comment.txt"
CHANNEL_ACCESS_TOKEN = st.secrets["line"]["channel_access_token"]

# タイトル
st.title("Contact状況可視化アプリ📊")

# 日付付きファイルから候補を自動抽出
import re

def get_available_dates():
    pattern = r"(\d{4}-\d{2}-\d{2})\.xlsx"
    dates = []
    for f in DATA_FOLDER.glob("*.xlsx"):
        match = re.search(pattern, f.name)
        if match:
            dates.append(match.group(1))
    return sorted(dates, reverse=True)

# ファイルのある日付から選択
available_dates = get_available_dates()

if not available_dates:
    st.error("📂 dataフォルダに日付付きのファイルが存在しません。")
    st.stop()

selected_date_str = st.selectbox("📅 確認する日付を選択", available_dates)
file_path = DATA_FOLDER / f"{selected_date_str}.xlsx"
selected_date = datetime.datetime.strptime(selected_date_str, "%Y-%m-%d").date()


# データ読み込み
if file_path.exists():
    df = pd.read_excel(file_path)
else:
    st.error("指定された日付のファイルが存在しません。")
    st.stop()

# 未対応データ抽出
no_contact_df = df[df["contact_status"] == "no_contact"]
impact_drivers = df[df["impact"] == "high"]["driver_name"].unique()

# 表示
st.subheader("📌 未対応ドライバー一覧")
if no_contact_df.empty:
    st.success("未対応のドライバーはいません。")
else:
    st.dataframe(no_contact_df[["driver_name", "detail"]])

st.subheader("🚀 改善インパクトの高いドライバー")
if len(impact_drivers) > 0:
    st.write("、".join(impact_drivers))
else:
    st.write("該当者なし")

# 管理者コメント入力
st.subheader("📝 管理者コメント入力")
if FREE_COMMENT_FILE.exists():
    default_comment = FREE_COMMENT_FILE.read_text(encoding="utf-8")
else:
    default_comment = ""
free_comment = st.text_area("改善のポイントや励ましコメントなど", value=default_comment, height=150)
FREE_COMMENT_FILE.write_text(free_comment, encoding="utf-8")

# メッセージ生成関数（1通目）
def generate_message(no_contact_df: pd.DataFrame, selected_date: datetime.date) -> str:
    date_str = selected_date.strftime("%-m月%-d日")
    message_lines = [f"📢【未対応ドライバー連絡】{date_str}時点\n"]

    grouped = no_contact_df.groupby("driver_name")
    for name, group in grouped:
        count = len(group)
        message_lines.append(f"🚨 {name} さん（未対応 {count} 件）")

    message_lines.append("\nご対応のほど、よろしくお願いします。")
    return "\n".join(message_lines)

# LINE送信関数（Messaging API 使用）
def send_line_message(to: str, message: str, token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": to,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", json=payload, headers=headers)
    return response.status_code, response.text

# フラグファイルパス
sent_marker_path = DATA_FOLDER / f"message1_sent_flag_{file_date_str}.txt"
comment_sent_marker_path = DATA_FOLDER / f"message2_sent_flag_{file_date_str}.txt"

# まとめて送信ボタン
st.subheader("✅ 個別改善レポート＋管理者コメントまとめて通知")
group_id = st.secrets["line"]["group_id"]

if st.button("📬まとめて送信（1通目＋2通目）"):
    # 1通目：個別レポート
    if len(no_contact_df) == 0:
        st.warning("未対応のドライバーがいません。1通目の送信はスキップされます。")
    else:
        message1 = generate_message(no_contact_df, selected_date)
        status1, text1 = send_line_message(group_id, message1, CHANNEL_ACCESS_TOKEN)
        if status1 == 200:
            st.success("✅ 1通目（個別レポート）を送信しました。")
            sent_marker_path.touch()
        else:
            st.error(f"❌ 1通目の送信失敗: {text1}")

    # 2通目：管理者コメント
    if not free_comment.strip():
        st.warning("管理者コメントが入力されていません。2通目はスキップされます。")
    else:
        comment_message = f"🚨【管理者コメント】さらなる改善に向けて\n\n{free_comment.strip()}"
        status2, text2 = send_line_message(group_id, comment_message, CHANNEL_ACCESS_TOKEN)
        if status2 == 200:
            st.success("✅ 2通目（管理者コメント）を送信しました。")
            comment_sent_marker_path.touch()
        else:
            st.error(f"❌ 2通目の送信失敗: {text2}")

# 送信状況表示
if sent_marker_path.exists():
    st.info("✅ 1通目（個別レポート）は既に送信されています。")
if comment_sent_marker_path.exists():
    st.info("✅ 2通目（管理者コメント）は既に送信されています。")
