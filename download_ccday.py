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
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

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
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 20)

# --- ダウンロード対象の日付を取得（＝当日） ---
today = datetime.date.today()
date_str = today.strftime("%Y-%m-%d")
expected_filename_part = f"Daily_ContactCompliance-{date_str}.xlsx"

# --- レポートページのURL生成 ---
year, week_number, _ = today.isocalendar()
report_url = (
    f"https://logistics.amazon.co.jp/performance?pageId=dsp_supp_reports"
    f"&navMenuVariant=external&station=DEJ3&companyId=114cd7d4-070f-421f-b41e-550a248ec5c7"
    f"&tabId=safety-dsp-weekly-tab&timeFrame=Weekly&to={year}-W{week_number}"
)

driver.get(report_url)
time.sleep(3)

# --- ログイン処理 ---
email_input = wait.until(EC.presence_of_element_located((By.ID, "ap_email")))
email_input.send_keys(EMAIL)
email_input.send_keys(Keys.RETURN)
time.sleep(3)

password_input = wait.until(EC.presence_of_element_located((By.ID, "ap_password")))
password_input.send_keys(PASSWORD)
password_input.send_keys(Keys.RETURN)
time.sleep(5)

print("✅ ログイン完了、レポートページが開かれたはずです。")

# --- ダウンロードリンク検出 & 実行 ---
try:
    links = driver.find_elements(By.TAG_NAME, "a")
    download_found = False

    for link in links:
        href = link.get_attribute("href")
        text = link.text
        if (href and expected_filename_part in href) or (expected_filename_part in text):
            print(f"✅ 該当ファイルリンクを発見: {href or text}")
            driver.execute_script("arguments[0].click();", link)
            print("📥 ダウンロードを開始しました。")
            download_found = True
            break

    if not download_found:
        raise Exception(f"リンクが見つかりませんでした: キーワード = {expected_filename_part}")

    # --- ダウンロード完了を待機（最大30秒） ---
    download_success = False
    for i in range(30):
        downloaded_files = glob.glob(os.path.join(DOWNLOAD_DIR, f"*{date_str}.xlsx"))
        if downloaded_files:
            downloaded_path = downloaded_files[0]
            print(f"✅ ファイルが保存されました: {downloaded_path}")
            download_success = True
            break
        time.sleep(1)

    if not download_success:
        raise Exception("⚠️ 30秒待ってもファイルが見つかりませんでした。")

except Exception as e:
    print("⚠️ ダウンロード処理中にエラーが発生しました。")
    print(e)

finally:
    driver.quit()
