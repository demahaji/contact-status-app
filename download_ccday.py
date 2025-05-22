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

# --- ログイン情報 ---
EMAIL = os.environ.get("CCDAY_EMAIL")
PASSWORD = os.environ.get("CCDAY_PASSWORD")

if not EMAIL or not PASSWORD:
    raise ValueError("環境変数 CCDAY_EMAIL または CCDAY_PASSWORD が設定されていません。")

# --- ダウンロード保存先 ---
DOWNLOAD_DIR = os.path.abspath("data")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- Chromeオプション ---
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

# --- 日付設定（例：今日の前日） ---
today = datetime.date.today()
target_date = today - datetime.timedelta(days=1)
year, week_number, _ = target_date.isocalendar()
date_str = target_date.strftime("%Y-%m-%d")

# --- レポートページのURL生成 ---
report_url = (
    f"https://logistics.amazon.co.jp/performance?pageId=dsp_supp_reports"
    f"&navMenuVariant=external&station=DEJ3&companyId=114cd7d4-070f-421f-b41e-550a248ec5c7"
    f"&tabId=safety-dsp-weekly-tab&timeFrame=Weekly&to={year}-W{week_number}"
)

try:
    driver.get(report_url)
    time.sleep(3)

    # --- ログイン ---
    email_input = wait.until(EC.presence_of_element_located((By.ID, "ap_email")))
    email_input.send_keys(EMAIL)
    email_input.send_keys(Keys.RETURN)
    time.sleep(2)

    password_input = wait.until(EC.presence_of_element_located((By.ID, "ap_password")))
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    # --- 2段階認証が表示される場合の対応 ---
try:
    mfa_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "auth-mfa-otpcode"))
    )
    print("🔐 2段階認証コードの入力待ちです（手動で入力してください）")
    
    # ユーザーが入力するまで待機（30秒まで）
    for i in range(30):
        if mfa_input.get_attribute("value"):
            print("✅ 2段階認証コードが入力されました")
            mfa_input.send_keys(Keys.RETURN)
            break
        time.sleep(1)
    else:
        raise Exception("⚠️ 2段階認証コードの入力が確認できませんでした")
except:
    print("🔓 2段階認証画面は表示されませんでした")
    time.sleep(5)

    print("✅ ログイン完了、レポートページが開かれたはずです。")

    # --- innerText でリンク要素を探す ---
    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), 'Daily_ContactCompliance')]")))
    elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Daily_ContactCompliance')]")
    print(f"🔍 'Daily_ContactCompliance' を含む要素数: {len(elements)}")

    download_found = False

    for idx, el in enumerate(elements):
        text = el.text.strip()
        print(f"[{idx}] text: {text}")
        if date_str in text:
            print(f"✅ 対象ファイル名を検出: {text}")
            try:
                driver.execute_script("arguments[0].click();", el)
                print("📥 ダウンロードを開始しました")
                download_found = True
                break
            except Exception as click_e:
                print(f"⚠️ クリック失敗: {click_e}")
                try:
                    el.send_keys(Keys.CONTROL, Keys.RETURN)
                    print("📥 別ウィンドウで開くよう試行しました")
                    download_found = True
                    break
                except Exception as ctrl_e:
                    print(f"⚠️ CTRL+クリックも失敗: {ctrl_e}")

    if not download_found:
        raise Exception(f"リンクが見つかりませんでした: キーワード = Daily_ContactCompliance-{date_str}.xlsx")

    # --- ダウンロード完了を最大30秒待機 ---
    for i in range(30):
        downloaded_files = glob.glob(os.path.join(DOWNLOAD_DIR, f"*Daily_ContactCompliance*{date_str}*.xlsx"))
        if downloaded_files:
            print(f"✅ ファイルが保存されました: {downloaded_files[0]}")
            break
        time.sleep(1)
    else:
        raise Exception("⚠️ 30秒待ってもファイルが見つかりませんでした。")

except Exception as e:
    print("⚠️ ダウンロード処理中にエラーが発生しました。")
    print(f"Message: {repr(e)}")

finally:
    driver.quit()
