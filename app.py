import streamlit as st
import pandas as pd
import datetime
import os
from pathlib import Path
import unicodedata

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

# ==== アップロード日からファイル名を探索 ====
upload_date = selected_date + datetime.timedelta(days=1)
file_date_str = upload_date.strftime("%Y-%m-%d")

file_path = None
file_name = f"(見つからず): {file_date_str}.xlsx"

for file in DATA_FOLDER.glob("*.xlsx"):
    if file_date_str in file.name:
        file_path = file
        file_name = file.name
        break

# ==== データ読み込み ====
if file_path and file_path.exists():
    st.success(f"✅ ファイル: {file_name} を読み込みました")
    try:
        df = pd.read_excel(file_path)

        # contact関連カラムを文字列に統一
        for col in ["架電有無", "テキスト送付有無", "お客様発信有無"]:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # 必須カラム確認
        if "transporter_id" not in df.columns or "contact_status" not in df.columns:
            st.error("❌ 必須のカラム（transporter_id / contact_status）が見つかりません")
        else:
            # ==== ドライバー名マッピング ====
            if MAPPING_FILE.exists():
                mapping_df = pd.read_csv(MAPPING_FILE)
                mapping_df["transporter_id"] = mapping_df["transporter_id"].apply(
                    lambda x: unicodedata.normalize("NFKC", str(x)).strip()
                )
                mapping_df["driver_name"] = mapping_df["driver_name"].apply(lambda x: str(x).strip())
                mapping_dict = dict(zip(mapping_df["transporter_id"], mapping_df["driver_name"]))

                df["transporter_id"] = df["transporter_id"].apply(
                    lambda x: unicodedata.normalize("NFKC", str(x)).strip()
                )
                df["driver_name"] = df["transporter_id"].map(mapping_dict).fillna(df["transporter_id"])
            else:
                st.warning("⚠️ マッピングファイルが読み込めませんでした。IDをそのまま使用します。")
                df["driver_name"] = df["transporter_id"]

            # ==== 未対応の抽出 ====
            no_contact_df = df[df["contact_status"] == "no_contact"]

            # ==== ドライバーごとの件数集計 ====
            summary = no_contact_df["driver_name"].value_counts().reset_index()
            summary.columns = ["driver_name", "no_contact_count"]

            # ==== 表示 ====
            st.markdown("## 🔔 未対応のドライバー（クリックで展開）")

            for _, row in summary.iterrows():
                name = row["driver_name"]
                count = row["no_contact_count"]
                with st.expander(f"🚨 {name}（未対応: {count} 件）"):
                    exclude_cols = [
                        "Company", "event_week", "delivery_station_code",
                        "provider_company_short_code", "provider_type",
                        "架電有無", "テキスト送付有無"
                    ]
                    display_cols = [col for col in no_contact_df.columns if col not in exclude_cols]
                    st.dataframe(no_contact_df[no_contact_df["driver_name"] == name][display_cols], use_container_width=True)

            # ==== 全体の件数 ====
            with st.expander("📊 全体の未対応件数（ドライバー別）"):
                st.dataframe(summary, use_container_width=True)

            # ==== 7日間の対応率集計表示 ====
            st.markdown("## 📆 過去7日間の対応実績")

            days_range = [selected_date - datetime.timedelta(days=i) for i in range(6, -1, -1)]
            summary_data = []

            for day in days_range:
                upload_day = day + datetime.timedelta(days=1)
                file_name_day = upload_day.strftime("%Y-%m-%d")

                matched_file = None
                for file in DATA_FOLDER.glob("*.xlsx"):
                    if file_name_day in file.name:
                        matched_file = file
                        break

                if matched_file and matched_file.exists():
                    try:
                        tmp_df = pd.read_excel(matched_file)
                        if "contact_status" in tmp_df.columns:
                            contact_counts = tmp_df["contact_status"].value_counts()

                            needed = sum(contact_counts.get(status, 0) for status in [
                                "both_call_and_text", "call_only", "text_only", "no_contact"
                            ])
                            no_contact = contact_counts.get("no_contact", 0)
                            done = needed - no_contact
                            rate = (done / needed * 100) if needed > 0 else 0.0

                            summary_data.append({
                                "日付": day.strftime("%Y-%m-%d"),
                                "実施率": f"{rate:.1f}%",
                                "必要件数": needed,
                                "未対応件数": no_contact
                            })
                        else:
                            summary_data.append({
                                "日付": day.strftime("%Y-%m-%d"),
                                "実施率": "N/A",
                                "必要件数": "N/A",
                                "未対応件数": "N/A"
                            })
                    except Exception as e:
                        summary_data.append({
                            "日付": day.strftime("%Y-%m-%d"),
                            "実施率": "エラー",
                            "必要件数": "-",
                            "未対応件数": "-"
                        })
                else:
                    summary_data.append({
                        "日付": day.strftime("%Y-%m-%d"),
                        "実施率": "未収集",
                        "必要件数": "-",
                        "未対応件数": "-"
                    })

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

    except Exception as e:
        st.error("❌ データの読み込み中にエラーが発生しました。")
        st.code(str(e))

else:
    st.warning(f"⚠️ ファイルが見つかりません: {file_name}")
