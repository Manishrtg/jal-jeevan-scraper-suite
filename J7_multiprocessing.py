from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import time
import warnings
import shutil

# Disable warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# === Setup paths ===
downloads_dir = os.path.expanduser("~/Downloads")
dataset_dir = os.path.join(os.getcwd(), "j8_dataset_2024-25")
os.makedirs(dataset_dir, exist_ok=True)

# === Setup Chrome options ===
chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--start-maximized")
chrome_options.add_experimental_option('prefs', {
    "download.default_directory": downloads_dir,
    "download.prompt_for_download": False,
    "directory_upgrade": True,
    "safebrowsing.enabled": True
})

# === Wait for download ===
def wait_for_download(download_dir, timeout=60):
    end_time = time.time() + timeout
    while time.time() < end_time:
        files = [f for f in os.listdir(download_dir) if f.endswith('.xls') and not f.endswith('.crdownload')]
        if files:
            latest = max([os.path.join(download_dir, f) for f in files], key=os.path.getctime)
            if os.path.getsize(latest) > 0:
                return latest
        time.sleep(1)
    return None

# === Launch Chrome ===
print("Launching Chrome browser...")
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 20)

driver.get("https://ejalshakti.gov.in/JJM/JJMReports/Physical/JJMRep_HarGharJalVillage.aspx")
time.sleep(5)

try:
    wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@id, 'CPHPage_rpt_lnkName_')]")))
    state_links = driver.find_elements(By.XPATH, "//a[contains(@id, 'CPHPage_rpt_lnkName_')]")
    num_states = len(state_links)
    print(f"Found {num_states} states")

    for index in range(24, num_states):
        print(f"\nProcessing state {index + 1}/{num_states}")

        # Re-fetch due to DOM refresh after going back
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@id, 'CPHPage_rpt_lnkName_')]")))
        state_links = driver.find_elements(By.XPATH, "//a[contains(@id, 'CPHPage_rpt_lnkName_')]")
        state_element = state_links[index]
        state_name = state_element.text.strip().replace("/", "_").replace("\\", "_")

        print(f"Clicking on state: {state_name}")
        driver.execute_script("arguments[0].click();", state_element)
        time.sleep(5)

        # === Select year ===
        try:
            year_dropdown = wait.until(EC.presence_of_element_located((By.ID, "CPHPage_ddFinyear")))
            select_year = Select(year_dropdown)

            target_year = "2024-2025"
            print(f"Selecting year: {target_year}")
            select_year.select_by_value(target_year)
            time.sleep(3)
        except Exception as e:
            print(f"❌ Error selecting year: {e}")
            continue

        # === Click 'Show' button ===
        try:
            show_button = wait.until(EC.element_to_be_clickable((By.ID, "CPHPage_btnShow")))
            driver.execute_script("arguments[0].click();", show_button)
            print("Clicked 'Show' button. Waiting for data to load...")
            time.sleep(10)  # Wait for data to load
        except Exception as e:
            print(f"❌ Error clicking 'Show' button: {e}")
            continue

        # === Click Excel download button ===
        try:
            excel_button = wait.until(EC.element_to_be_clickable((By.ID, "convertEXCEL")))
            driver.execute_script("arguments[0].click();", excel_button)
            print("Download started. Waiting for Excel file...")

            downloaded_file = wait_for_download(downloads_dir)
            if downloaded_file:
                new_path = os.path.join(dataset_dir, f"{state_name}.xls")
                if os.path.exists(new_path):
                    timestamp = int(time.time())
                    new_path = os.path.join(dataset_dir, f"{state_name}_{timestamp}.xls")
                shutil.move(downloaded_file, new_path)
                print(f"✅ Saved to: {new_path}")
            else:
                print("❌ Download failed or timed out.")
        except Exception as e:
            print(f"❌ Error downloading Excel for state '{state_name}': {e}")

        # === Go back to state list ===
        try:
            driver.get("https://ejalshakti.gov.in/JJM/JJMReports/Physical/JJMRep_HarGharJalVillage.aspx")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Error reloading state list page: {e}")
            break

except Exception as e:
    print(f"\n⚠️ Unhandled error occurred: {e}")

print("\n✅ All states processed. Closing browser...")
driver.quit()
