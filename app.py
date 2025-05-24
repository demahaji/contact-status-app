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

# 日付選択（配送日を選択）
selected_date = st.date_input("📅 確認する日付を選択", datetime.date.today())

# ファイルの日付は配送日の翌日（アップロード日）
upload_date = selected_date + datetime.timedelta(days=1)
upload_date_str = upload_date.strftime("%Y-%m-%d")

# ファイル検索
file_path = None
for file in DATA_FOLDER.glob(f"*{upload_date_str}.xlsx"):
    file_path = file
    break

# データ読み込み
if file_path is None:
    st.error("指定された日付のファイルが存在しません。")
    st.stop()
else:
    df = pd.read_excel(file_path)

# 未対応データ抽出
no_contact_df = df[df["contact_status"] == "no_contact"]

# impact列が存在する場合のみ抽出
if "impact" in df.columns and "driver_name" in df.columns:
    impact_drivers = df[df["impact"] == "high"]["driver_name"].unique()
else:
    impact_drivers = []

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

# メッセージ生成関数
def generate_message(no_contact_df: pd.DataFrame, selected_date: datetime.date) -> str:
    date_str = selected_date.strftime("%-m月%-d日")
    message_lines = [f"📢【未対応ドライバー連絡】{date_str}時点\n"]
    grouped = no_contact_df.groupby("driver_name")
    for name, group in grouped:
        count = len(group)
        message_lines.append(f"🚨 {name} さん（未対応 {count} 件）")
    message_lines.append("\nご対応のほど、よろしくお願いします。")
    return "\n".join(message_lines)

# LINE送信関数
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

# 送信フラグファイル（アップロード日をベースに保存）
sent_marker_path = DATA_FOLDER / f"message1_sent_flag_{upload_date_str}.txt"
comment_sent_marker_path = DATA_FOLDER / f"message2_sent_flag_{upload_date_str}.txt"

# 送信状況判定
message1_sent = sent_marker_path.exists()
message2_sent = comment_sent_marker_path.exists()

# ボタンラベル切り替え
button_label = "🔁再送信（1通目＋2通目）" if message1_sent and message2_sent else "📬まとめて送信（1通目＋2通目）"

# 通知セクション
st.subheader("✅ 個別改善レポート＋管理者コメントまとめて通知")
group_id = st.secrets["line"]["group_id"]

if st.button(button_label):
    # 1通目：個別レポート
    if no_contact_df.empty:
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
if message1_sent:
    st.info("✅ 1通目（個別レポート）は既に送信されています。")
if message2_sent:
    st.info("✅ 2通目（管理者コメント）は既に送信されています。")
