# 🏛️ Florida Foreclosure Auction Scraper

A lightweight, high-performance tool for extracting foreclosure auction data from 36 Florida counties. Designed for real estate investors, analysts, and professionals who need accurate third-party bidder data without the overhead.

> **🎯 Investment Focus:**  
> **Targets third-party foreclosure purchases only—filters out bank repossessions to surface real investment opportunities.**

---

## 📸 Preview When Checking Vpn.

![WhatsApp Image 2025-12-01 at 14 58 00_97250333](https://github.com/user-attachments/assets/8bd6b627-bc50-4010-a4d4-67045d7d92db)


---
---

## 📸 Preview After Checking Vpn and started Scraping.

![Screenshot 2025-06-03 223228](https://github.com/user-attachments/assets/a1932699-fb46-4364-9f74-dd671a0cc437)

---

## ✨ Features

### ⚡ **Performance**
- **Single Executable**: No Python, no dependencies, no setup
- **4-5× Faster**: Lightweight cURL engine replaces heavy browser automation
- **36 Counties**: Simultaneous multi-county scraping
- **Smart Filtering**: Auto-removes timeshares and bank repossessions

### 🔒 **Reliability** 
- **VPN Detection**: Validates US-based IP before execution
- **Auto-Updates**: Built-in version checker with notifications
- **Chrome Fingerprinting**: Uses `curl_cffi` with TLS/JA3 impersonation for undetected requests
- **Error Recovery**: Automatic retries with comprehensive logging

### 📊 **Output**
- **Excel Reports**: Clean, formatted spreadsheets with dual-sheet structure
- **Address Intelligence**: Auto-extracts city, state, ZIP from property addresses
- **Deduplication**: Removes duplicate entries automatically
- **Live Progress**: Real-time terminal output in GUI

### 🧹 **Automation**
- **Calendar Scanner**: Checks 5 months ahead for upcoming auctions
- **Date Logic**: Handles month-end edge cases automatically
- **Auction Classification**: Distinguishes Foreclosure vs Tax Deed sales

---

## 📍 County Coverage (36 Total)

**Metro Areas:**
- **South Florida**: Miami-Dade, Broward, Palm Beach
- **Central Florida**: Orange, Seminole, Volusia
- **Tampa Bay**: Hillsborough, Pinellas, Pasco
- **Jacksonville**: Duval, Clay, St. Johns

**Full List:**
```
Alachua, Bay, Broward, Charlotte, Citrus, Clay, Duval, Escambia, 
Flagler, Gilchrist, Gulf, Hillsborough, Indian River, Jackson, 
Lee, Leon, Manatee, Marion, Martin, Miami-Dade, Nassau, Okeechobee,
Orange, Palm Beach, Pasco, Pinellas, Polk, Putnam, Santa Rosa, 
Sarasota, Seminole, St. Johns, St. Lucie, Volusia, Walton, Washington
```

> 📄 **See**: [`db/url.py`](db/url.py) for complete URL configuration

---

## 🚀 Quick Start

### **Windows (Recommended)**

**Requirements:**
- Windows 10/11 (64-bit)
- US-based VPN (for county site access)
- Internet connection

**Run:**
1. Download `.exe` from [Releases](https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/releases)
2. Double-click—it handles everything:
   - ✅ VPN verification
   - 🌐 Multi-county scraping
   - 📊 Excel generation

### **Developer Setup**

```bash
git clone https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper.git
cd US-FL-County-Foreclosure-Sale-Scraper
pip install -r requirements.txt
python main.py
```

**Dependencies:**
- `curl_cffi` – Chrome-impersonated HTTP requests
- `pandas` – Data processing
- `openpyxl` – Excel generation
- `pywebview` – GUI framework
- `pytz` – Timezone handling

---

## 🛠️ Workflow

```
🔍 VPN Check → 📅 Calendar Scan → 🕸️ Data Scrape → 📑 Excel Export
```

**Automatic Steps:**
1. **Location Validation**: Confirms US IP address.
2. **Auction Discovery**: Scans calendars for recent/upcoming sales.
3. **Data Collection**: Extracts property details via fingerprinted requests.
4. **Report Generation**: Merges data into formatted Excel file.

**Output Location:**  
`FL Foreclosure Final Report/` directory

---

## 📊 Excel Structure

### **Sheet 1: Foreclosure Data**
| Field | Description | Example |
|-------|-------------|---------|
| County | County name | MIAMI-DADE |
| Auction Sold | Sale status | Yes |
| Case # | Court case ID | 2024-CA-001234 |
| Parcel ID | Tax parcel number | 30-3210-001-0120 |
| Property Address | Cleaned address | 123 MAIN ST |
| City | Parsed city | MIAMI |
| State | Always FL | FL |
| Zip | ZIP code | 33101 |
| Final Judgment Amount | Court-ordered amount | $450,000.00 |
| Amount | Sale price | $300,000.00 |
| Sold To | Buyer classification | 3rd Party Bidder |
| Auction Type | Sale category | FORECLOSURE |

### **Sheet 2: Upcoming Auctions**
- County availability status
- Next scheduled auction dates
- Auction type (Foreclosure/Tax Deed)

---

## 🔧 Architecture

### **Core Files**

**`main.py`**  
- WebView GUI with typewriter animation
- VPN/update verification
- Process orchestration

**`db/base_url.py`**  
- County auction URLs
- Calendar endpoints

**`make_excel.py`**  
- Data merging logic
- Excel formatting/export

### **Technology Stack**
- **curl_cffi**: Chrome TLS fingerprinting (replaces Playwright)
- **Pywebview**: HTML/CSS-based GUI
- **Pandas**: Data manipulation
- **OpenPyXL**: Excel styling

---

## ⚙️ Automation Logic

### **Calendar Intelligence**
- **Day 1**: Checks prior month's last day
- **Other Days**: Checks previous day
- **Forward Scan**: Searches 5 months ahead for next auction

### **Error Handling**
- Automatic retry on network failures
- Graceful degradation for missing data
- UTF-8 safe logging (EXE-compatible)

### **Resource Management**
- In-memory data processing
- Temp file auto-deletion
- No browser binaries required

---

## 🤝 Contributing

### **Setup**
```bash
git clone https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper.git
cd US-FL-County-Foreclosure-Sale-Scraper
pip install -r requirements.txt
python make_excel.py
```

### **Project Structure**
```
├── main.py              # Entry point
├── db/                  # County configs
├── Utils/               # Helper functions
├── Animation/           # GUI assets
└── tests/               # pytest suite
```

### **PR Guidelines**
1. Fork & create feature branch
2. Add tests for new functionality
3. Ensure pytest passes
4. Submit PR with clear description

---

## 💻 System Requirements

**Minimum:**
- Windows 10 (64-bit)
- 2GB RAM
- 500MB storage
- Stable internet

**Recommended:**
- Multi-core CPU
- 4GB+ RAM
- SSD storage
- US-based VPN

---

## ⚖️ Legal

**Important:**
- Accesses **public auction records only**
- For legitimate real estate research
- Users responsible for ToS compliance
- No PII collection

---

## 📞 Support

**Issues:**  
[GitHub Issues](https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/issues)

**Community:**
- ⭐ Star if useful
- 🐛 Report bugs
- 💡 Suggest features

---

## 📝 Changelog
### **v1.3** (Current)
- 🛠️🐛 Bug Fix.
- 🗓️ Fixed upcoming calendar parser.
- 📊 Improved Excel output (better message, better Sheet2).
- 🧪 removed pytest.

### **v1.2**
- 🚀 Removed Playwright—4-5× faster execution
- 🌐 Added `curl_cffi` with Chrome fingerprinting
- ⚡ Rewrote scraper engine (multi-page, filtering)
- 🗓️ Fixed calendar parser (`.CALDAYBOX`/`.CALBOX`)
- 💻 Enhanced GUI (typewriter animation, emoji rendering)
- 📊 Improved Excel output (auto-sizing, Sheet2)
- 📦 Fixed PyInstaller UTF-8 issues
- 🧪 Added pytest suite with 36-county coverage

### **v1.1**
- Initial release

---

## 📄 License

MIT License – see [LICENSE](LICENSE)

---

**🏠 Built for Florida real estate investors**

*Updated: March 2026*
