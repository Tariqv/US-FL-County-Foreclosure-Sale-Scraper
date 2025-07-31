# 🏛️ FL Foreclosure Auction Scraper

A powerful, automated tool for scraping and analyzing foreclosure auction data from 36 Florida counties. Built for real estate professionals, investors, and data analysts who need reliable, up-to-date foreclosure information across the state.

> **🎯 Key Focus:**  
> **This tool specifically targets _third-party foreclosure sales_ (3rd Party Bidders) from county auction websites, filtering out bank repossessions for investment opportunities.**

---

## 📸 Application Preview

![Screenshot 2025-06-03 223228](https://github.com/user-attachments/assets/a1932699-fb46-4364-9f74-dd671a0cc437)


---

## ✨ Key Features

### 🚀 **Core Functionality**
- **One-Click Executable**: No Python installation required—download and run instantly
- **Multi-County Coverage**: Scrapes 36 Florida counties simultaneously
- **Smart Filtering**: Only captures properties sold to third-party bidders (investment opportunities)
- **Automated Scheduling**: Intelligent date handling for daily auction monitoring

### 🛡️ **Security & Reliability** 
- **VPN Location Verification**: Ensures US-based access before scraping
- **Automatic Updates**: Built-in version checking with update notifications
- **Browser Automation**: Uses Playwright for robust, headless browser control
- **Error Handling**: Comprehensive error recovery and logging system

### 📊 **Data Processing**
- **Excel Export**: Clean, formatted Excel files with merged county data
- **Address Parsing**: Automatic extraction of state, city, ZIP, and clean addresses  
- **Data Deduplication**: Removes duplicate entries and filters timeshares
- **Real-time Progress**: Live terminal output embedded in GUI

### 🧹 **Smart Management**
- **Automatic Cleanup**: Removes temporary files and folders after processing
- **Calendar Integration**: Checks auction availability across multiple months
- **Auction Type Detection**: Identifies Foreclosure vs Tax Deed sales
- **Resource Optimization**: CPU-only operation, no GPU required

---

## 📍 Supported Florida Counties (36 Total)

The scraper covers all major Florida markets:

**Major Metropolitan Areas:**
- Miami-Dade, Broward, Palm Beach (South Florida)
- Orange, Seminole, Volusia (Central Florida) 
- Hillsborough, Pinellas, Pasco (Tampa Bay)
- Duval, Clay, St. Johns (Jacksonville)

**Complete County List:**
```
Alachua, Bay, Broward, Charlotte, Citrus, Clay, Duval, Escambia, 
Flagler, Gilchrist, Gulf, Hillsborough, Indian River, Jackson, 
Lee, Leon, Manatee, Marion, Martin, Miami-Dade, Nassau, Okaloosa, 
Orange, Palm Beach, Pasco, Pinellas, Polk, Putnam, Santa Rosa, 
Sarasota, Seminole, St. Johns, St. Lucie, Volusia, Walton, Washington
```

> 📋 **Up-to-date URLs**: See [`database/url.py`](database/url.py) for the complete list with auction site URLs.

---

## 📦 Installation & Setup

### 🖥️ **Windows (Recommended)**

**Prerequisites:**
- Windows 10/11
- US-based VPN connection (required for access)
- Active internet connection

**Installation:**
1. Download the latest `.exe` from [Releases](https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/releases)
2. Double-click to run—**no installation needed**
3. The app will automatically:
   - Download required browser components
   - Verify your US location
   - Begin scraping process

### 🐍 **Python Development Setup**

For developers who want to modify the code:

```bash
# Clone repository
git clone https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper.git
cd US-FL-County-Foreclosure-Sale-Scraper

# Install dependencies  
pip install -r requirements.txt

# Run application
python main.py
```

**Required Python Packages:**
- `playwright` - Browser automation
- `pandas` - Data processing
- `openpyxl` - Excel file handling
- `pywebview` - GUI framework
- `requests` - HTTP requests
- `pytz` - Timezone handling

---

## 🛠️ How to Use

### **Simple 3-Step Process:**

1. **🚀 Launch**: Double-click the executable
2. **⏳ Wait**: App automatically verifies location and downloads browsers
3. **📊 Collect**: Results are saved as Excel files in `FL Foreclosure Final Report/`

### **What Happens Automatically:**

```
🔍 VPN Check → 🌐 Browser Setup → 📅 Calendar Scan → 🕸️ Data Scraping → 📑 Excel Export
```

- **Location Verification**: Confirms US-based IP address
- **Auction Availability**: Checks each county's calendar for recent auctions  
- **Data Extraction**: Scrapes detailed property information
- **File Organization**: Creates organized Excel reports with merged data
- **Cleanup**: Removes temporary files automatically

---

## 📊 Output Data Structure

### **Main Sheet (Foreclosure Data):**
| Column | Description | Example |
|--------|-------------|---------|
| County | Florida county name | MIAMI-DADE |
| Auction Sold | Sale status | Yes/No |
| Case # | Court case number | 2024-CA-001234 |
| Parcel ID | Property identifier | 30-3210-001-0120 |
| Property Address | Clean address | 123 MAIN ST |
| City | Extracted city | MIAMI |
| State | Always FL | FL |
| Zip | ZIP code | 33101 |
| Final Judgment Amount | Court judgment | $450,000.00 |
| Amount | Sale price | $300,000.00 |
| Sold To | Buyer type | 3rd Party Bidder |
| Auction Type | Sale category | FORECLOSURE |

### **Secondary Sheet (Availability Report):**
- County-by-county auction availability
- Upcoming auction dates
- Auction type identification (Foreclosure/Tax Deed)

---

## 🔧 Technical Architecture

### **Core Components:**

**`main.py`** - GUI and orchestration
- WebView-based interface with real-time updates
- Browser management and installation  
- VPN verification and update checking

**`Scraper/Scraper.py`** - Data extraction engine
- Playwright-based web automation
- Multi-page navigation and parsing
- Calendar integration for date validation

**`Merger/Auction_merger.py`** - Data processing
- Address parsing and normalization
- County data merging and deduplication
- Excel formatting and export

**`database/url.py`** - County configuration
- Auction site URLs for all 36 counties
- Calendar URLs for availability checking

### **Key Technologies:**
- **Playwright**: Headless browser automation
- **Pywebview & Html , css , html**: Cross-platform GUI framework  
- **Pandas**: Data manipulation and analysis
- **OpenPyXL**: Excel file generation with formatting

---

## 🔄 Automation Features

### **Date Intelligence:**
- **Day 1 of Month**: Checks last day of previous month
- **Other Days**: Checks previous day's auctions
- **Multi-month Scanning**: Searches forward for upcoming auctions

### **Error Recovery:**
- Automatic retry on connection failures
- Graceful handling of missing data
- Comprehensive logging system

### **Resource Management:**
- Temporary folder cleanup
- Browser process management  
- Memory-efficient data processing

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### **Development Setup:**
```bash
git clone https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper.git
cd US-FL-County-Foreclosure-Sale-Scraper
pip install -r requirements.txt
```

### **Code Structure:**
- `main.py` - Application entry point and GUI
- `Scraper/` - Web scraping logic
- `Merger/` - Data processing and export
- `database/` - County URLs and configuration
- `Animation/` - GUI assets and styling

### **Contribution Guidelines:**
- Fork the repository
- Create a feature branch (`git checkout -b feature/new-feature`)
- Make your changes with clear commit messages
- Test thoroughly across multiple counties
- Submit a pull request with detailed description

---

## 📋 System Requirements

### **Minimum Requirements:**
- **OS**: Windows 10 (64-bit) or later
- **RAM**: 4GB (8GB recommended for large datasets)
- **Storage**: 2GB free space (for browser and data files)
- **Network**: Stable broadband internet connection
- **Browser**: Google Chrome (automatically managed)

### **Recommended Setup:**
- **CPU**: Multi-core processor for faster scraping
- **RAM**: 8GB+ for handling large county datasets
- **SSD**: For faster file I/O operations
- **VPN**: US-based VPN service if running from outside US

---

## 🔒 Legal & Compliance

### **Important Notes:**
- This tool accesses **publicly available** auction data
- Designed for legitimate real estate research and investment
- Users are responsible for complying with website terms of service
- Recommended to use responsibly with appropriate delays between requests

### **Data Usage:**
- All scraped data is from public county records
- No personal information or protected data is collected
- Tool focuses only on property auction information

---

## 📞 Support & Community

### **Getting Help:**
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/discussions)
- 📧 **Direct Contact**: Open an issue for support questions

### **Community:**
- Star ⭐ the repository if you find it useful
- Share your success stories and use cases
- Contribute county additions or improvements

---

## 📈 Version History

- **v1.1** (Current) - Enhanced GUI, automatic updates, improved error handling
- **v1.0** - Initial release with core scraping functionality

---

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

---

**Made with ❤️ for the Florida real estate community**

*Last updated: January 2025*
