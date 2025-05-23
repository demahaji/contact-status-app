import streamlit as st
import pandas as pd
import datetime
from pathlib import Path
import unicodedata
import requests
import json


# Secrets から安全にトークンを取得
CHANNEL_ACCESS_TOKEN = st.secrets["line"]["channel_access_token"]

# ==== LINE Messaging API 通知関数 ====
def send_line_message(to_id: str, message_text: str, access_token: str):
    """
    LINE Messaging APIで指定のユーザーやグループにメッセージを送信
    :param to_id: 送信先の userId または groupId
    :param message_text: 送信するテキスト
    :param access_token: チャネルアクセストークン（Messaging API用）
    """
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "to": to_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.status_code, response.text

# ページ全体をワイドに表示
st.set_page_config(layout="wide")

# ==== 設定 ====
DATA_FOLDER = Path("data")  # 保存先フォルダ
MAPPING_FILE = Path("driver_mapping.csv")

# ==== タイトル ====
st.markdown("# 📞 Contact Status 監視アプリ")

# ==== 日付選択 ====
selected_date = st.date_input("対象日を選択", datetime.date.today() - datetime.timedelta(days=1))
st.write(f"選択日: {selected_date.strftime('%Y/%m/%d')}")

# ==== ファイル探索 ====
upload_date = selected_date + datetime.timedelta(days=1)
file_date_str = upload_date.strftime("%Y-%m-%d")
file_path = None
file_name = f"(見つからず): {file_date_str}.xlsx"

for file in DATA_FOLDER.glob("*.xlsx"):
    if file_date_str in file.name:
        file_path = file
        file_name = file.name
        break

if file_path is None or not file_path.exists():
    st.warning(f"⚠️ ファイルが見つかりません: {file_date_str}.xlsx")
    st.stop()

st.success(f"✅ ファイル: {file_name} を読み込みました")

# ==== メイン処理 ====
try:
    df = pd.read_excel(file_path)

    for col in ["枦電有無", "テキスト送付有無", "お客様発信有無"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    if "transporter_id" not in df.columns or "contact_status" not in df.columns:
        st.error("❌ 必須のカラム（transporter_id / contact_status）が見つかりません")
        st.stop()

    # ==== マッピング処理 ====
    if MAPPING_FILE.exists():
        mapping_df = pd.read_csv(MAPPING_FILE)
        mapping_df["transporter_id"] = mapping_df["transporter_id"].apply(lambda x: unicodedata.normalize("NFKC", str(x)).strip())
        mapping_df["driver_name"] = mapping_df["driver_name"].apply(lambda x: str(x).strip())
        mapping_dict = dict(zip(mapping_df["transporter_id"], mapping_df["driver_name"]))
        df["transporter_id"] = df["transporter_id"].apply(lambda x: unicodedata.normalize("NFKC", str(x)).strip())
        df["driver_name"] = df["transporter_id"].map(mapping_dict).fillna(df["transporter_id"])
    else:
        st.warning("⚠️ マッピングファイルが読み込めませんでした。IDをそのまま使用します。")
        df["driver_name"] = df["transporter_id"]

    # ==== 未対応の抽出 ====
    no_contact_df = df[df["contact_status"] == "no_contact"]

    # ==== 件数集計 ====
    summary = no_contact_df["driver_name"].value_counts().reset_index()
    summary.columns = ["driver_name", "no_contact_count"]

    # ==== 表示 ====
    st.markdown("## 🔔 未対応のドライバー")
    for _, row in summary.iterrows():
        name = row["driver_name"]
        count = row["no_contact_count"]
        with st.expander(f"🚨 {name}（未対応: {count} 件）"):
            exclude_cols = ["Company", "event_week", "delivery_station_code", "provider_company_short_code", "provider_type", "枦電有無", "テキスト送付有無"]
            display_cols = [col for col in no_contact_df.columns if col not in exclude_cols]
            st.dataframe(no_contact_df[no_contact_df["driver_name"] == name][display_cols], use_container_width=True)

    with st.expander("📊 全体の未対応件数（ドライバー別）"):
        st.dataframe(summary, use_container_width=True)

    # ==== 📆 過去7日間の対応実績 ====
    st.markdown("## 📆 過去7日間の対応実績")
    summary_data = []

    for i in range(7):
        target_day = selected_date - datetime.timedelta(days=i)
        upload_day = target_day + datetime.timedelta(days=1)
        fname = upload_day.strftime("%Y-%m-%d")
        fpath = None
        for f in DATA_FOLDER.glob(f"*{fname}*.xlsx"):
            fpath = f
            break

        if fpath and fpath.exists():
            try:
                day_df = pd.read_excel(fpath)
                if "contact_status" in day_df.columns:
                    total = day_df["contact_status"].isin(["both_call_and_textcall_only", "text_only", "call_only", "no_contact"]).sum()
                    no_contact = (day_df["contact_status"] == "no_contact").sum()
                    done = total - no_contact
                    rate = f"{round(done / total * 100)}%" if total > 0 else "0%"
                    summary_data.append({
                        "日付": target_day.strftime("%Y-%m-%d"),
                        "実施率": rate,
                        "必要件数": f"{total}件",
                        "未対応件数": f"{no_contact}件"
                    })
                else:
                    raise ValueError("contact_status カラムが見つかりません")
            except:
                summary_data.append({"日付": target_day.strftime("%Y-%m-%d"), "実施率": "N/A", "必要件数": "N/A", "未対応件数": "N/A"})
        else:
            summary_data.append({"日付": target_day.strftime("%Y-%m-%d"), "実施率": "N/A", "必要件数": "N/A", "未対応件数": "N/A"})

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)

    # ==== 🚨 過去7日間の実施率95%未満のドライバー ====
    st.markdown("## 🚨 過去7日間の実施率95%未満のドライバー（改善インパクト）")

    driver_records = {}
    total_all = 0
    total_all_done = 0
    total_all_no_contact = 0

    for i in range(7):
        target_day = selected_date - datetime.timedelta(days=i)
        upload_day = target_day + datetime.timedelta(days=1)
        fname = upload_day.strftime("%Y-%m-%d")
        fpath = None
        for f in DATA_FOLDER.glob(f"*{fname}*.xlsx"):
            fpath = f
            break

        if fpath and fpath.exists():
            try:
                day_df = pd.read_excel(fpath)
                if "contact_status" in day_df.columns and "transporter_id" in day_df.columns:
                    if MAPPING_FILE.exists():
                        mapping_df = pd.read_csv(MAPPING_FILE)
                        mapping_df["transporter_id"] = mapping_df["transporter_id"].apply(lambda x: unicodedata.normalize("NFKC", str(x)).strip())
                        mapping_df["driver_name"] = mapping_df["driver_name"].apply(lambda x: str(x).strip())
                        mapping_dict = dict(zip(mapping_df["transporter_id"], mapping_df["driver_name"]))
                        day_df["transporter_id"] = day_df["transporter_id"].apply(lambda x: unicodedata.normalize("NFKC", str(x)).strip())
                        day_df["driver_name"] = day_df["transporter_id"].map(mapping_dict).fillna(day_df["transporter_id"])
                    else:
                        day_df["driver_name"] = day_df["transporter_id"]

                    for driver, group in day_df.groupby("driver_name"):
                        total = group["contact_status"].isin(["both_call_and_textcall_only", "text_only", "call_only", "no_contact"]).sum()
                        no_contact = (group["contact_status"] == "no_contact").sum()
                        done = total - no_contact
                        if driver not in driver_records:
                            driver_records[driver] = {"done": 0, "total": 0, "no_contact": 0}
                        driver_records[driver]["done"] += done
                        driver_records[driver]["total"] += total
                        driver_records[driver]["no_contact"] += no_contact
                        total_all += total
                        total_all_done += done
                        total_all_no_contact += no_contact
            except:
                continue

    under_95_df = []
    for driver, record in driver_records.items():
        total = record["total"]
        done = record["done"]
        no_contact = record["no_contact"]
        rate = (done / total) * 100 if total > 0 else 0

        if rate < 95 and total_all > 0:
            improved_total_done = total_all_done + no_contact
            improved_rate = improved_total_done / total_all * 100
            current_rate = total_all_done / total_all * 100
            improvement = improved_rate - current_rate

            under_95_df.append({
                "ドライバー名": driver,
                "実施率": f"{rate:.1f}%",
                "未対応件数": no_contact,
                "改善インパクト（%）": f"{improvement:.1f}%"
            })

    if under_95_df:
        result_df = pd.DataFrame(under_95_df).sort_values("改善インパクト（%）", ascending=False)
        result_df["未対応件数"] = result_df["未対応件数"].astype(str) + " 件"
        st.dataframe(result_df, use_container_width=True)

        total_no_contact = result_df["未対応件数"].str.replace(" 件", "").astype(int).sum()
        st.markdown(f"**🔢 未対応件数の合計：{total_no_contact}件**")

        # ==== 通知メッセージ生成 ====
        today_str = selected_date.strftime("%-m月%-d日")
        current_rate = total_all_done / total_all * 100 if total_all > 0 else 0
        improved_rate = (total_all_done + total_all_no_contact) / total_all * 100 if total_all > 0 else 0

        message_lines = [
            f"🚀【対応状況のご連絡】{today_str}時点",
            "",
            "日々のご対応、本当にありがとうございます！",
            "以下の方々のアクションで、さらに組織全体の実施率が向上します✨",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━"
        ]

        for _, row in result_df.iterrows():
            name = row["ドライバー名"]
            no_contact = row["未対応件数"]
            improvement = row["改善インパクト（%）"]
            try:
                new_rate = current_rate + float(improvement.replace("%", ""))
            except:
                new_rate = current_rate

            message_lines.append(f"🌟 {name}（未対応 {no_contact}）")
            message_lines.append(f"📈 対応で実施率 +{improvement} UP！")
            message_lines.append(f"➡ 改善後：{new_rate:.1f}%")
            message_lines.append("")

        message_lines.append("━━━━━━━━━━━━━━━━━━━━━━")
        message_lines.append(f"\n✅ 現在の組織実施率：{current_rate:.1f}%")
        message_lines.append(f"🎯 全員が対応すると：{improved_rate:.1f}% に！")
        message_lines.append("")
        message_lines.append("💡 あなたの行動が、チーム全体を引き上げます！")
        message_lines.append("引き続きよろしくお願いします💪✨")

        notify_message = "\n".join(message_lines)
        st.markdown("## ✉️ 通知メッセージ（プレビュー）")
        st.code(notify_message)

    else:
        st.success("🎉 実施率95%以上のドライバーのみでした。")

except Exception as e:
    st.error("❌ データの読み込み中にエラーが発生しました。")
    st.code(str(e))
    st.stop()

    st.stop()
    
 # ==== 📣 Freeコメント通知（管理者コメント） ====
st.markdown("## 🗒️ 管理者Freeコメント通知")

# コメント入力欄
free_comment = st.text_area("📬 コメントを入力してください（ドライバーへのメッセージ）", height=150)

# 保存先ファイル（コメント送信済みフラグ）
flag_file_path = DATA_FOLDER / f"comment_sent_flag_{file_date_str}.txt"

# 送信済みかどうか確認
if flag_file_path.exists():
    sent = True
    button_label = "🔁 再送信"
else:
    sent = False
    button_label = "📤 送信"

# 通知送信処理
if st.button(button_label):
    if not free_comment.strip():
        st.warning("⚠️ コメントを入力してください。")
    else:
        comment_message = f"🚨【管理者コメント】さらなる改善に向けて\n\n{free_comment.strip()}"

        # Messaging APIで送信（グループIDやユーザーIDを指定）
        group_id = st.secrets["line"]["group_id"]  # ★ここにgroupIdを設定
        status, text = send_line_message(group_id, comment_message, CHANNEL_ACCESS_TOKEN)

        if status == 200:
            st.success("✅ 通知を送信しました！")
            flag_file_path.write_text("sent")
        else:
            st.error(f"❌ 通知送信に失敗しました。ステータスコード: {status} - {text}")

st.markdown("---")
st.subheader("✅ 個別改善レポート＋管理者コメントまとめて通知")

if st.button("📬まとめて送信（1通目＋2通目）"):
    if len(no_contact_df) == 0:
        st.warning("未対応のドライバーがいません。1通目の送信はスキップされます。")
    else:
        # 1通目メッセージ送信
        message1 = generate_message(no_contact_df, selected_date)
        status1 = send_line_message(message1)
        if status1 == 200:
            st.success("✅ 1通目（個別レポート）を送信しました。")
            sent_marker_path.touch()
        else:
            st.error("❌ 1通目（個別レポート）の送信に失敗しました。")

    if not free_comment.strip():
        st.warning("管理者コメントが入力されていません。2通目はスキップされます。")
    else:
        # 2通目メッセージ送信
        comment_message = f"🚨【管理者コメント】さらなる改善に向けて\n\n{free_comment.strip()}"
        status2 = send_line_message(comment_message)
        if status2 == 200:
            st.success("✅ 2通目（管理者コメント）を送信しました。")
            comment_sent_marker_path.touch()
        else:
            st.error("❌ 2通目（管理者コメント）の送信に失敗しました。")

