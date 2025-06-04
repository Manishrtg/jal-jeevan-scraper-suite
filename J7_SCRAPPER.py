from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import time
import warnings
import shutil

# Disable warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-popup-blocking")

# Set download preferences
downloads_dir = os.path.expanduser("~/Downloads")
chrome_options.add_experimental_option('prefs', {
    "download.default_directory": downloads_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
    "safebrowsing.disable_download_protection": True,
    "profile.default_content_setting_values.automatic_downloads": 1
})

def is_district_page(driver):
    try:
        headers = driver.find_elements(By.TAG_NAME, "th")
        for header in headers:
            if "District Name" in header.text:
                return True
        return False
    except:
        return False

def wait_for_overlay_to_disappear(driver):
    try:
        # Adjust the overlay selector based on your page's specific structure
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading-overlay")))  # Replace with actual overlay class or ID
    except TimeoutException:
        print("Overlay did not disappear in time.")

# Initialize driver and open website
print("Starting browser...")
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://ejalshakti.gov.in/JJM/JJMReports/Physical/JJMRep_VillageWiseFHTCCoverage.aspx")

try:
    wait = WebDriverWait(driver, 20)  # Increased wait time to 30 seconds

    print("Waiting for state list to load...")
    wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@id, 'CPHPage_rpt_lnkStateName_')]")))

    state_elements = driver.find_elements(By.XPATH, "//a[contains(@id, 'CPHPage_rpt_lnkStateName_')]")
    print(f"Found {len(state_elements)} states.")

    state_number = int(input("Enter the state row number (e.g., 1 for first state): "))
    if state_number < 1 or state_number > len(state_elements):
        print("Invalid state number entered.")
    else:
        state_element = state_elements[state_number - 1]
        state_name = state_element.text.strip()
        print(f"\nClicking on state: {state_name}")
        driver.execute_script("arguments[0].click();", state_element)
        time.sleep(3)

    # Create data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    state_dir = os.path.join(script_dir, "dataset_J7_", state_name)
    os.makedirs(state_dir, exist_ok=True)

    # Process districts
    district_number = 0
    while True:
        district_id = f"CPHPage_rpt_lnkdistrictname_{district_number}"
        
        # DEBUGGING: Print the district ID to verify it's correct
        print(f"District ID: {district_id}")

        try:
            # Wait for district element to be present
            district_element = wait.until(EC.presence_of_element_located((By.ID, district_id)))
            
            # Wait for the district to be clickable
            district_element = wait.until(EC.element_to_be_clickable((By.ID, district_id)))

            district_name = district_element.text
            print(f"\nProcessing district: {district_name}")

            # Click the district element
            driver.execute_script("arguments[0].click();", district_element)
            time.sleep(3)

            # Download Excel file with retries
            max_download_attempts = 3
            file_downloaded = False
            latest_file = None

            for attempt in range(max_download_attempts):
                try:
                    print(f"Downloading Excel file (attempt {attempt + 1}/{max_download_attempts})...")
                    # Fix: Locate the download button by ID instead of NAME
                    excel_btn = wait.until(EC.element_to_be_clickable((By.ID, "convertEXCEL")))  # Change NAME to ID
                    driver.execute_script("arguments[0].click();", excel_btn)  # Trigger JavaScript postback

                    # Wait for the page to process the download (postback)
                    print("Waiting for download to complete...")
                    download_timeout = time.time() + 45  # 45 seconds timeout

                    while time.time() < download_timeout:
                        try:
                            xls_files = [f for f in os.listdir(downloads_dir) if f.endswith('.xls')]
                            if xls_files:
                                latest_file = max([os.path.join(downloads_dir, f) for f in xls_files], key=os.path.getctime)
                                if not latest_file.endswith('.crdownload') and os.path.getsize(latest_file) > 0:
                                    file_downloaded = True
                                    break
                        except Exception as e:
                            print(f"Waiting for download... {str(e)}")
                        time.sleep(1)

                    if file_downloaded:
                        break
                    else:
                        print(f"Download attempt {attempt + 1} failed, retrying...")
                        time.sleep(2)
                except Exception as e:
                    print(f"Error during download attempt {attempt + 1}: {str(e)}")
                    if attempt < max_download_attempts - 1:
                        time.sleep(2)
                        continue

            if not file_downloaded:
                print("All download attempts failed!")
                # Go back to district page if download failed
                driver.back()

                time.sleep(3)
                district_number += 1
                continue

            # Move the downloaded file
            new_filename = os.path.join(state_dir, f"{district_name}.xls")
            for _ in range(5):
                try:
                    shutil.move(latest_file, new_filename)
                    print(f"Saved file: {new_filename}")
                    break
                except PermissionError:
                    time.sleep(1)
                except Exception as e:
                    print(f"Error moving file: {str(e)}")
                    time.sleep(1)

        except TimeoutException:
            print(f"No more districts or failed to find district with ID {district_id}.")
            break
        except Exception as e:
            print(f"Error processing district '{district_name}': {str(e)}")
            # Try to go back to district list page if error
            try:
                driver.back()

                time.sleep(3)
            except:
                pass
            break
        
        # Always go back to state page after processing district
        try:
            driver.back()
            time.sleep(3)
        except Exception as e:
            print(f"Error going back to state page: {str(e)}")

        district_number += 1

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    print("\nClosing browser...")
    driver.quit()
