# Jal Jeevan Mission Scraper Suite

An automated Python suite to extract multiple datasets from the [Jal Jeevan Mission](https://ejalshakti.gov.in/JJM/JJMReports/Physical/JJMRep_VillageWiseFHTCCoverage.aspx) portal. This tool supports concurrent scraping of state-wise, district-wise, and scheme-level progress reports.

---

## 🚀 Features

- ✅ State-wise Village FHTC Coverage Report
- ✅ District-wise Physical Progress Reports
- ✅ Scheme-wise Status Reports
- 🧠 Modular script structure for easy extensibility
- 🔁 Parallelized downloads using Python multiprocessing
- 📁 Auto-organized folders for report categories

---

## 📂 Available Scrapers

| Report Type                       | Script Name                     | Output Folder          |
|----------------------------------|----------------------------------|------------------------|
| State-wise Village FHTC          | `statewise_fhtc_scraper.py`     | `data/2025-26/FHTC/`   |
| District-wise Physical Progress  | `districtwise_progress_scraper.py` | `data/2025-26/DistrictProgress/` |
| Scheme-wise Status               | `scheme_status_scraper.py`      | `data/2025-26/SchemeStatus/`     |

---

## 🛠️ Setup Instructions

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/jal-jeevan-scraper-suite-2025.git
    cd jal-jeevan-scraper-suite
    ```

2. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```

3. Run a specific scraper:
    ```bash
    python src/statewise_fhtc_scraper.py
    ```

---

## 📦 requirements.txt

```text
selenium
