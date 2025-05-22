from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import time
import os
import glob

# --- ログイン情報（GitHub Secrets から渡される） ---
EMAIL = os.environ.get("CCDAY_EMAIL")
PASSWORD = os.environ.get("CCDAY_PASSWORD")
if not EMAIL or not PASSWORD:
    raise ValueError("環境変数 CCDAY_EMAIL または CCDAY_PASSWORD が設定されていません。")

# --- 保存先ディレクトリの設定 ---
DOWNLOAD_DIR = os.path.abspath("data")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Chrome起動オプション ---
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "safebrowsing.disable_download_protection": True,
}
chrome_options.add_experimental_option("prefs", prefs)

# --- WebDriver起動 ---
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)
wait = WebDriverWait(driver, 20)

# --- 日付に基づくファイル名の構築 ---
today = datetime.date.today()
target_date = today  # 前日データが必要なら today - datetime.timedelta(days=1)
year, week_number, _ = target_date.isocalendar()
date_str = target_date.strftime("%Y-%m-%d")

# --- レポートページURLを生成 ---
report_url = (
    f"https://logistics.amazon.co.jp/performance?"
    f"pageId=dsp_supp_reports&navMenuVariant=external&station=DEJ3"
    f"&companyId=114cd7d4-070f-421f-b41e-550a248ec5c7"
    f"&tabId=safety-dsp-weekly-tab&timeFrame=Weekly&to={year}-W{week_number}"
)

# --- ログインページへ ---
driver.get(report_url)
time.sleep(3)

# --- メール入力 & 認証 ---
email_input = wait.until(EC.presence_of_element_located((By.ID, "ap_email")))
email_input.send_keys(EMAIL)
email_input.send_keys(Keys.RETURN)
time.sleep(3)

password_input = wait.until(EC.presence_of_element_located((By.ID, "ap_password")))
password_input.send_keys(PASSWORD)
password_input.send_keys(Keys.RETURN)
time.sleep(5)

print("✅ ログイン完了")

# --- ★ ここで再度レポートページを開き直し ★ ---
driver.get(report_url)
time.sleep(3)
print("🔄 レポートページをリロードしました")

# --- ダウンロードリンク検出 & 実行 ---
try:
    links = driver.find_elements(By.TAG_NAME, "a")
    print(f"🔍 検出されたリンク数: {len(links)}")
    download_found = False

    for idx, link in enumerate(links):
        href = link.get_attribute("href") or ""
        text = link.text or ""
        # ログ出力（確認用）
        print(f"[{idx}] href: {href}")
        if ("Daily_ContactCompliance" in href and date_str in href) or \
           ("Daily_ContactCompliance" in text and date_str in text):
            print(f"✅ 該当ファイルリンクを発見: {href or text}")
            driver.execute_script("arguments[0].click();", link)
            print("📥 ダウンロードを開始しました。")
            download_found = True
            break

    if not download_found:
        raise Exception(f"リンクが見つかりませんでした: キー ワード = Daily_ContactCompliance-{date_str}.xlsx")

    # --- ダウンロード完了を待機（最大30秒） ---
    for i in range(30):
        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"*Daily_ContactCompliance*{date_str}*.xlsx"))
        if files:
            print(f"✅ ファイルが保存されました: {files[0]}")
            download_found = True
            break
        time.sleep(1)

    if not download_found:
        raise Exception("⚠️ 30秒待ってもファイルが見つかりませんでした。")

except Exception as e:
    print("⚠️ ダウンロード処理中にエラーが発生しました。")
    print(e)

finally:
    driver.quit()
