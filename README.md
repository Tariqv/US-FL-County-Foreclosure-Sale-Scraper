# 🏛️ FL Foreclosure Auction Scraper

A fast, user-friendly tool for scraping and merging foreclosure auction data from multiple counties in Florida. This project is designed for real estate professionals, data analysts, and anyone needing up-to-date foreclosure auction data across the state.

> **Note:**  
> **This tool specifically scrapes only _third-party foreclosure sales_ (3rd Party Sale) from county auction sites.**

---

## 📸 Preview

![Screenshot 2025-06-03 223228](https://github.com/user-attachments/assets/e0e58a34-c642-47c2-a7de-200d1179fb01)

---

## ✨ Features

- ✅ **One-Click Executable**: No setup or Python installation required—just download and run.
- 🏛 **Multi-County Coverage**: Automatically scrapes foreclosure auction data from multiple Florida counties.
- 🔎 **3rd Party Sale Focus**: Only scrapes auctions where a property was sold to a third party (not the plaintiff or bank).
- 🚀 **High-Speed Scraping**: Utilizes multithreading for fast data collection.
- 🧠 **Smart Data Handling**: Includes filters and de-duplication to ensure clean, accurate results.
- 🌎 **VPN Location Check**: Verifies US location before scraping; includes automatic retry countdown if not connected from the US.
- 🖥️ **Live Terminal Output in GUI**: Real-time status and logs are embedded directly in the graphical interface.
- 🔒 **Selenium WebDriver Integration**: Robust browser automation for reliable data extraction.
- 📅 **Auction Calendar Awareness**: Identifies and targets current and upcoming auction dates automatically.
- 📑 **Automatic Excel Export & Merge**: Saves results as Excel files, merging data across counties for easy analysis.
- 🧹 **Automatic Cleanup**: Temporary folders and files are removed after each run to keep your workspace tidy.
- 🔔 **Update Checker**: Notifies if a newer version is available.
- ❌ **No GPU Required**: Fully optimized for CPU-only PCs; runs on standard hardware.

---
## 📍 Supported Florida Counties

This scraper currently supports foreclosure auction data from the following counties:

- Alachua
- Bay
- Broward
- Charlotte
- Citrus
- Clay
- Duval
- Escambia
- Flagler
- Gilchrist
- Gulf
- Hillsborough
- Indian River
- Jackson
- Lee
- Leon
- Manatee
- Marion
- Martin
- Miami-Dade
- Nassau
- Okaloosa
- Orange
- Palm Beach
- Pasco
- Pinellas
- Polk
- Putnam
- Santa Rosa
- Sarasota
- Seminole
- St. Johns
- St. Lucie
- Volusia
- Walton
- Washington

> To view the most up-to-date list and their URLs, see [`database/url.py`](https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/blob/main/database/url.py).

---

## 📦 Installation

- 📦 **Chrome Browser Needed**

### 🖥️ Windows (EXE)

1. Download the latest `.exe` file from the [Releases section](https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/releases).
2. Run it by double-clicking – **no installation required**.

### 🐍 Python (Manual)

1. Clone the repository:
    ```bash
    git clone https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper.git
    cd US-FL-County-Foreclosure-Sale-Scraper
    ```
2. Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the app:
    ```bash
    python main.py
    ```

---

## 🛠️ Usage

```bash
1. Launch the application.
2. Wait for the VPN detection to confirm US location.
3. Scraping begins automatically – just watch the animated terminal.
```

- Results are merged and saved as Excel files.
- Live progress is displayed in the GUI.
- Folders created for each auction date are auto-cleaned up after processing.

---

## 🧩 How It Works

- **VPN Check**: App automatically checks your location (must be US-based for access).
- **Calendar Scraper**: Gathers upcoming auction dates and checks if auctions are available for each county.
- **Main Scraper**: Collects detailed foreclosure property data from each county’s auction website, focusing _only_ on 3rd party sales.
- **Merger**: Combines all results into a single, well-formatted Excel file.
- **Automation**: Designed for minimal user input — just start and let it run.

---

## 💻 Developer Notes

- Written in Python 3.8+ with PySide6 (for GUI) and Selenium (for web scraping).
- Supports modular development — scraper logic, calendar logic, and data merging are in separate modules.
- Easily extendable to more counties or additional auction data fields.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📬 Contact

For questions, suggestions, or support, open an issue or reach out via GitHub.
