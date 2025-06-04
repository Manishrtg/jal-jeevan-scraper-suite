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
import requests

# Disable warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Setup Chrome
chrome_options = Options()
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-popup-blocking")

# Set download preferences with more options
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

def is_block_clickable(block_element):
    try:
        # Check multiple conditions to ensure block is truly clickable
        if (block_element.get_attribute('disabled') == 'disabled' or 
            not block_element.is_enabled() or 
            'disabled' in block_element.get_attribute('class') or 
            not block_element.is_displayed()):
            return False
        return True
    except:
        return False

# Initialize driver and open website
print("Starting browser...")
driver = webdriver.Chrome(options=chrome_options)
driver.get("https://sbm.gov.in/sbmphase2/Secure/Entry/UserMenu.aspx")

try:
    wait = WebDriverWait(driver, 20)  # Increased wait time
    
    # Wait for preloader to disappear
    print("Waiting for page to load...")
    time.sleep(3)  # Initial wait for page load
    
    # Click on initial menu item
    print("Opening main menu...")
    menu_element = wait.until(EC.presence_of_element_located((By.ID, "RptrPhaseIIMISreport_ctl09_lnkbtn_PageLinkHeader")))
    # Scroll into view and click using JavaScript
    driver.execute_script("arguments[0].scrollIntoView(true);", menu_element)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", menu_element)
    time.sleep(3)

    # Get state number from user
    state_number = int(input("\nEnter the state row number (1 for first state, 2 for second state, etc.): "))
    state_number_str = str(state_number).zfill(2)

    # Click on state
    print("\nSelecting state...")
    state_id = f"ctl00_ContentPlaceHolder1_Rpt_State_ctl{state_number_str}_lkn_statename"
    state_element = wait.until(EC.presence_of_element_located((By.ID, state_id)))
    state_name = state_element.text
    print(f"Found state: {state_name}")
    driver.execute_script("arguments[0].click();", state_element)
    time.sleep(3)



# Create data directory
  
    script_dir = os.getcwd()


    # Create data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    state_dir = os.path.join(script_dir, "data", state_name)
    os.makedirs(state_dir, exist_ok=True)

    # Process districts
    district_number = 1
    while True:
        try:
            district_id = f"ctl00_ContentPlaceHolder1_Rpt_District_ctl{str(district_number).zfill(2)}_lnk_DistrictName"
            try:
                district_element = wait.until(EC.presence_of_element_located((By.ID, district_id)))
            except TimeoutException:
                print("No more districts found")
                break

            district_name = district_element.text
            print(f"\nProcessing district: {district_name}")
            driver.execute_script("arguments[0].click();", district_element)
            time.sleep(3)

            # Process blocks in district
            block_number = 1
            blocks_found = False
            while True:
                try:
                    block_id = f"ctl00_ContentPlaceHolder1_Rpt_Block_ctl{str(block_number).zfill(2)}_lnk_BlockName"
                    
                    # First check if block element exists
                    try:
                        block_element = driver.find_element(By.ID, block_id)
                    except:
                        print("No more blocks found")
                        break

                    # Check if block is disabled
                    disabled = block_element.get_attribute('disabled')
                    if disabled == 'true' or disabled == 'disabled':
                        print(f"Block {block_number} is disabled, skipping...")
                        block_number += 1
                        continue
                        
                    blocks_found = True
                    block_name = block_element.text
                    print(f"Processing block: {block_name}")
                    driver.execute_script("arguments[0].click();", block_element)
                    time.sleep(3)

                    # Download Excel file with retries
                    max_download_attempts = 3
                    for attempt in range(max_download_attempts):
                        try:
                            print(f"Downloading Excel file (attempt {attempt + 1}/{max_download_attempts})...")
                            excel_btn = wait.until(EC.element_to_be_clickable((By.NAME, "ctl00$ContentPlaceHolder1$btnExcel")))
                            driver.execute_script("arguments[0].click();", excel_btn)
                            
                            # Wait for file download with timeout
                            print("Waiting for download to complete...")
                            download_timeout = time.time() + 45  # Increased timeout to 45 seconds
                            file_downloaded = False
                            latest_file = None
                            
                            while time.time() < download_timeout and not file_downloaded:
                                try:
                                    # Get list of .xls files in downloads directory
                                    xls_files = [f for f in os.listdir(downloads_dir) if f.endswith('.xls')]
                                    if xls_files:
                                        latest_file = max([os.path.join(downloads_dir, f) for f in xls_files], 
                                                       key=os.path.getctime)
                                        # Check if file is fully downloaded
                                        if not latest_file.endswith('.crdownload'):
                                            # Verify file is not empty and is accessible
                                            if os.path.getsize(latest_file) > 0:
                                                file_downloaded = True
                                                break
                                except Exception as e:
                                    print(f"Waiting for download... {str(e)}")
                                time.sleep(1)
                            
                            if file_downloaded:
                                break
                            else:
                                print(f"Download attempt {attempt + 1} failed, retrying...")
                                time.sleep(2)  # Wait before retry
                        
                        except Exception as e:
                            print(f"Error during download attempt {attempt + 1}: {str(e)}")
                            if attempt < max_download_attempts - 1:
                                time.sleep(2)  # Wait before retry
                                continue
                    
                    if not file_downloaded:
                        print("All download attempts failed!")
                        # Go back to district page if download failed
                        back_button = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_lnk_back")))
                        driver.execute_script("arguments[0].click();", back_button)
                        time.sleep(3)
                        block_number += 1
                        continue
                        
                    # Move the downloaded file
                    new_filename = os.path.join(state_dir, f"{district_name}_{block_name}.xls")
                    try:
                        # Wait for file to be released by the system
                        for _ in range(5):  # Try 5 times
                            try:
                                shutil.move(latest_file, new_filename)
                                print(f"Saved file: {new_filename}")
                                break
                            except PermissionError:
                                time.sleep(1)
                            except Exception as e:
                                print(f"Error moving file: {str(e)}")
                                time.sleep(1)
                    except Exception as e:
                        print(f"Failed to move file: {str(e)}")

                    # Go back to district page
                    back_button = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_lnk_back")))
                    driver.execute_script("arguments[0].click();", back_button)
                    time.sleep(3)
                    block_number += 1

                except Exception as e:
                    print(f"Error processing block: {str(e)}")
                    # Try to go back to district page if there was an error
                    try:
                        back_button = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_lnk_back")))
                        driver.execute_script("arguments[0].click();", back_button)
                        time.sleep(3)
                    except:
                        pass
                    break

            # Always go back to state page after processing blocks
            try:
                back_button = wait.until(EC.element_to_be_clickable((By.ID, "ctl00_ContentPlaceHolder1_lnk_back")))
                driver.execute_script("arguments[0].click();", back_button)
                time.sleep(3)
            except Exception as e:
                print(f"Error going back to state page: {str(e)}")
                
            district_number += 1

        except Exception as e:
            print(f"Error processing district: {str(e)}")
            break

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    print("\nClosing browser...")
    driver.quit()
