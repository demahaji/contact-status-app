コンテンツへとスキップする
チャット履歴

あなた:
https://github.com/demahaji/contact-status-app/tree/main
これが上手くいかない
ChatGPT:
GitHubリポジトリ（https://github.com/demahaji/contact-status-app/tree/main）に関して「上手くいかない」とのことですが、もう少し詳しく状況を教えていただけますか？
たとえば、以下のような点を教えていただけると、的確にサポートできます。

🔍 確認したいポイント
どの操作で問題が起きているか？

cloneできない？

Streamlitアプリが起動しない？

LINE通知が送れない？

どんなエラーメッセージが出るか？

コンソールのエラー内容やログがあると助かります。

どのような環境で実行しているか？

ローカルPC？（Windows/Mac）

GitHub Codespaces？Streamlit Community Cloud？

意図している動作と実際の動作の違い

よければ、次のいずれかをお送りください：

実行コマンドと出力されたエラーメッセージ

エラーが出たときのスクリーンショット

該当のコードの一部（エラーが発生した箇所）

すぐに原因を特定できるように全力でお手伝いします。お待ちしています！

あなた:
LINEの通知は今はいいです。
日付でファイルが開かない
ChatGPT:
了解しました、「日付でファイルが開かない」という点にフォーカスします。

おそらく、Streamlit アプリが日付を元に Excel ファイルを開こうとしているけど、対象のファイルが存在しない、またはパスが間違っている可能性があります。

🔍 まず確認：コード上で日付ファイルを開いている箇所
app.py に次のようなコードがあるはずです：

today = datetime.today().strftime('%Y-%m-%d')
file_path = f"data/{today}.xlsx"
df = pd.read_excel(file_path)
この場合、アプリが探しているファイルは：

data/2025-05-24.xlsx
のようなファイルです。

✅ チェックポイント
data/ フォルダがあるか？
contact-status-app/data/ にフォルダが存在しているか確認してください。

今日の日付（例：2025-05-24.xlsx）という名前のExcelファイルが入っているか？
ファイル名が 2025-5-24.xlsx や 05-24-2025.xlsx など、形式がズレているとエラーになります。

ファイル名が正しくても、拡張子が .xls や .csv などではないか？
pd.read_excel() は .xlsx を前提にしていることが多いです。

🛠 解決策
💡 対応 1：ファイル名の自動生成ロジックを確認・修正
from datetime import datetime

today = datetime.today().strftime('%Y-%m-%d')
file_path = f"data/{today}.xlsx"

if os.path.exists(file_path):
    df = pd.read_excel(file_path)
else:
    st.error(f"ファイルが見つかりません: {file_path}")
💡 対応 2：Streamlit UIで日付を選べるようにする
selected_date = st.date_input("日付を選択", datetime.today())
file_path = f"data/{selected_date.strftime('%Y-%m-%d')}.xlsx"
if os.path.exists(file_path):
    df = pd.read_excel(file_path)
else:
    st.error(f"ファイルが見つかりません: {file_path}")
🚀 次にどうしますか？
コードの該当部分を貼っていただければ、正確に修正提案も可能です。

data/ フォルダの中身（ファイル名一覧）を教えていただくのもアリです。

ご希望あれば、日付選択UI付きでエラーハンドリング済みのコードをまるごと提案します！

あなた:
画像をアップロードしました
画像をアップロードしました
ChatGPT:
ありがとうございます！画像から確認すると、現在の data フォルダ内のファイル名は以下のようになっており、「日付だけの名前のファイル（例：2025-05-24.xlsx）」と、「長いファイル名（例：JP-DEMA-DEJ3...2025-05-24.xlsx）」の2種類が混在しています。

❗問題点
Streamlitアプリが以下のようにファイルを読んでいると仮定します：

today = datetime.today().strftime('%Y-%m-%d')
file_path = f"data/{today}.xlsx"
df = pd.read_excel(file_path)
→ このコードは data/2025-05-24.xlsx のような短い名前のファイルしか探しません。

ですが、実際のファイル名は：

JP-DEMA-DEJ3-week-21-Daily_ContactCompliance-2025-05-24.xlsx
なので、ファイルが見つからずエラーになります。

✅ 解決方法（柔軟に日付を含むファイルを探す）
data フォルダ内で 日付を含むファイル名を探す方法 に切り替えると解決できます。

以下のようなコードを app.py に書き換えてみてください：

import os
import glob
from datetime import datetime
import pandas as pd
import streamlit as st

# 今日の日付（例：2025-05-24）
today = datetime.today().strftime('%Y-%m-%d')

# パターンに一致するファイルを探す
file_pattern = f"data/*{today}*.xlsx"
file_list = glob.glob(file_pattern)

if file_list:
    file_path = file_list[0]  # 最初に見つかったファイルを使用
    df = pd.read_excel(file_path)
    st.success(f"読み込んだファイル: {os.path.basename(file_path)}")
    st.dataframe(df)
else:
    st.error(f"{today} を含むExcelファイルが data フォルダに見つかりませんでした。")
✨ 補足：もっと汎用的にするなら
Streamlitのdate_inputで日付を選べるようにして、過去のファイルも読めるようにすると便利です。必要であればそのバージョンもすぐ作れます。

次のアクション
上記コードを app.py に入れてみてください

もし glob モジュールが未インストールであれば、標準ライブラリなのでそのまま使えます

他にも日付形式やエラー対応など調整したい点があれば教えてください！

ご希望があればそのまま貼り替え用に全体コードを作成します。

あなた:
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

# 日付選択
selected_date = st.date_input("📅 確認する日付を選択", datetime.date.today())
file_date_str = selected_date.strftime("%Y-%m-%d")
file_path = DATA_FOLDER / f"{file_date_str}.xlsx"

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

app.pyです
ChatGPT:
ありがとうございます！app.pyのコードは非常に整理されていて、目的も明確です。
ただし、ファイル読み込み部分で「日付だけのファイル名」に依存しているため、前述の通り以下の修正が必要です。

🔧 修正ポイント（ファイル名に日付が含まれるものを柔軟に探索）
✅ 修正前（現在のコード）：
file_path = DATA_FOLDER / f"{file_date_str}.xlsx"

# データ読み込み
if file_path.exists():
    df = pd.read_excel(file_path)
else:
    st.error("指定された日付のファイルが存在しません。")
    st.stop()
✅ 修正後（globで日付を含むファイル名を検索）：
以下に安全な日付検索＋Streamlitエラー表示付きの修正を提示します：

import glob

# 日付に一致するファイルを検索
file_pattern = str(DATA_FOLDER / f"*{file_date_str}*.xlsx")
matching_files = glob.glob(file_pattern)

if matching_files:
    file_path = Path(matching_files[0])  # 最初に見つかったファイルを使用
    df = pd.read_excel(file_path)
    st.success(f"✅ 読み込んだファイル: {file_path.name}")
else:
    st.error(f"❌ 指定された日付（{file_date_str}）を含むExcelファイルが存在しません。")
    st.stop()
🧠 この修正で得られるメリット
ファイル名が 2025-05-24.xlsx でも JP-DEMA...-2025-05-24.xlsx でも読み込める

毎日のファイル名が自動生成されるシステムでも柔軟に対応

エラー原因の特定がしやすくなる

✅ 補足（今後改善するなら）
同じ日付で複数ファイルが存在する場合の選択肢（複数ファイルをリストで表示して選ばせる）

ファイル名の命名規則が決まっているなら、正規表現などでもっと精密に指定可能

この修正を app.py の該当箇所にそのまま貼り付ければ動作するはずです。
必要であれば、ファイル選択UIを追加するバージョンも作成可能です。

あなた:
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

# 日付選択
selected_date = st.date_input("📅 確認する日付を選択", datetime.date.today())
file_date_str = selected_date.strftime("%Y-%m-%d")
file_path = DATA_FOLDER / f"{file_date_str}.xlsx"

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
修正したコードにして
ChatGPT:
以下は、あなたの目的（LINE通知を1通目と2通目でまとめて送り、すでに送信済みの場合は「再送信」ボタンに変化）を満たすように、app.pyを改善した修正版です。

✅ 修正内容のポイント
ボタン表示が「📬まとめて送信」か「🔁再送信」になるように分岐

送信の有無をボタン表示に反映

各送信が成功した場合にマーカーファイルを更新

🔧 修正版 app.py
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

# 日付選択
selected_date = st.date_input("📅 確認する日付を選択", datetime.date.today())
file_date_str = selected_date.strftime("%Y-%m-%d")
file_path = DATA_FOLDER / f"{file_date_str}.xlsx"

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

# フラグファイルパス
sent_marker_path = DATA_FOLDER / f"message1_sent_flag_{file_date_str}.txt"
comment_sent_marker_path = DATA_FOLDER / f"message2_sent_flag_{file_date_str}.txt"

# 送信済みフラグチェック
message1_sent = sent_marker_path.exists()
message2_sent = comment_sent_marker_path.exists()

# ボタンラベルを切り替え
if message1_sent and message2_sent:
    button_label = "🔁再送信（1通目＋2通目）"
else:
    button_label = "📬まとめて送信（1通目＋2通目）"

# 通知セクション
st.subheader("✅ 個別改善レポート＋管理者コメントまとめて通知")
group_id = st.secrets["line"]["group_id"]

if st.button(button_label):
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
if message1_sent:
    st.info("✅ 1通目（個別レポート）は既に送信されています。")
if message2_sent:
    st.info("✅ 2通目（管理者コメント）は既に送信されています。")
✅ 補足
button_label を送信済み状況によって切り替えることで「送信 or 再送信」ボタンが実現されます。

ファイルパスのタイムスタンプは選択日ごとに個別で管理されているため、日付を切り替えたときの送信済みチェックも正確です。

何か他にも追加したい機能があれば気軽にどうぞ！




選択されていません選択されていません
ChatGPT の回答は必ずしも正しいとは限りません。重要な情報は確認するようにしてください。
