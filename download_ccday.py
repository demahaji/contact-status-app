from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import time
import os

# --- ログイン情報（GitHub Secrets から渡される） ---
EMAIL = os.environ.get("CCDAY_EMAIL")
PASSWORD = os.environ.get("CCDAY_PASSWORD")

if not EMAIL or not PASSWORD:
    raise ValueError("環境変数 CCDAY_EMAIL または CCDAY_PASSWORD が設定されていません。")

# --- ChromeDriverのパス ---
driver_path = r"C:\WebDriver\chromedriver.exe"

# --- Chrome起動オプション ---
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
prefs = {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "safebrowsing.disable_download_protection": True,
}
chrome_options.add_experimental_option("prefs", prefs)

# --- WebDriver起動 ---
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
wait = WebDriverWait(driver, 20)

# --- 日付に基づく週番号とファイル名部分の生成 ---
today = datetime.date.today()
target_date = today  # または today - datetime.timedelta(days=1)
year, week_number, _ = target_date.isocalendar()
week_str = f"week-{week_number}"
date_str = target_date.strftime("%Y-%m-%d")
expected_filename_part = f"JP-DEMA-DEJ3-{week_str}-Daily_ContactCompliance-{date_str}.xlsx"

# --- Amazon レポートURLを生成 ---
report_url = f'https://logistics.amazon.co.jp/performance?pageId=dsp_supp_reports&navMenuVariant=external&station=DEJ3&companyId=114cd7d4-070f-421f-b41e-550a248ec5c7&tabId=safety-dsp-weekly-tab&timeFrame=Weekly&to={year}-W{week_number}'

# --- ログインページへ遷移 ---
driver.get(report_url)
time.sleep(3)

# --- メールアドレス入力 ---
email_input = wait.until(EC.presence_of_element_located((By.ID, "ap_email")))
email_input.send_keys(EMAIL)
email_input.send_keys(Keys.RETURN)
time.sleep(3)

# --- パスワード入力 ---
password_input = wait.until(EC.presence_of_element_located((By.ID, "ap_password")))
password_input.send_keys(PASSWORD)
password_input.send_keys(Keys.RETURN)
time.sleep(5)

print("✅ ログイン完了、レポートページが開かれたはずです。")

# --- ダウンロードリンクの検出 ---
try:
    links = driver.find_elements(By.TAG_NAME, "a")
    download_found = False

    for link in links:
        href = link.get_attribute("href")
        if href and expected_filename_part in href:
            print(f"✅ 該当ファイルリンクを発見: {href}")
            driver.execute_script("arguments[0].click();", link)
            print("📥 ダウンロードを開始しました。")
            download_found = True
            break

    if not download_found:
        raise Exception(f"リンクが見つかりませんでした: キーワード = {expected_filename_part}")

except Exception as e:
    print("⚠️ ダウンロード処理中にエラーが発生しました。")
    print(e)
