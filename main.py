import webview
import requests
import threading
import os, sys, shutil, re, time, zipfile
from pathlib import Path
from datetime import datetime, timedelta

BROWSER_BINARIES = ["chromium", "chromium-headless-shell", "winldd"]
PLATFORM = "win64"
INSTALL_DIR = (
    Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    / "ms-playwright"
)
CACHE_FILE = Path(os.getenv("LOCALAPPDATA")) / "ms-playwright" / "browsers_cache.json"
CACHE_EXPIRY_DAYS = 7


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_local_browser_revisions():
    install_dir = INSTALL_DIR
    revisions = {}

    if not install_dir.exists():
        return revisions

    for item in install_dir.iterdir():
        if item.is_dir():
            match = re.match(
                r"^(chromium|chromium[_-]headless[_-]shell|winldd)[-_]?(\d+)",
                item.name,
                re.IGNORECASE,
            )
            if match:
                browser, revision = match.groups()
                browser_key = browser.replace("-", "_").lower()
                revisions[browser_key] = revision
    return revisions


class Logger:
    def __init__(self, stream_callback=None):
        if not os.path.exists("logs"):
            os.makedirs("logs")

        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file_path = os.path.join("logs", f"{today}.log")
        self.log_file = open(self.log_file_path, "a", encoding="utf-8")

        # Optional: callback to stream to GUI
        self.stream_callback = stream_callback

    def write(self, text):
        if text.strip():  # avoid logging empty lines
            if not text.endswith("\n"):
                text += "\n"
            self.log_file.write(text)
            self.log_file.flush()
            if self.stream_callback:
                self.stream_callback(
                    text.strip()
                )  # Still stream without newline to GUI

    def flush(self):
        self.log_file.flush()

    def close(self):
        self.log_file.close()


class CombinedStream:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, message):
        for stream in self.streams:
            stream.write(message)

    def flush(self):
        for stream in self.streams:
            if hasattr(stream, "flush"):
                stream.flush()


class GuiStream:
    def __init__(self, stream_func):
        self.stream_func = stream_func
        self.buffer = ""

    def write(self, message):
        self.buffer += message
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line.strip():
                self.stream_func(line.strip())

    def flush(self):
        if self.buffer.strip():
            self.stream_func(self.buffer.strip())
        self.buffer = ""


class API:
    def __init__(self, window):
        self.window = window
        self.vpn_verified = False
        self.printed_fail = False

    def stream(self, msg):
        for c in msg:
            self.window.evaluate_js(f"window.streamChar({repr(c)})")
            time.sleep(0.01)
        self.window.evaluate_js("window.streamChar('__NEWLINE__')")

    def check_browser_installation(self):
        self.window.evaluate_js(
            "window.updateStatus('Checking browser installation...')"
        )

        revisions = self.fetch_browser_revisions()
        local_revisions = get_local_browser_revisions()

        missing_or_outdated = []

        INSTALL_DIR.mkdir(parents=True, exist_ok=True)

        for browser, latest_rev in revisions.items():
            local_rev = local_revisions.get(browser)
            if local_rev != latest_rev:
                # If outdated or missing
                missing_or_outdated.append(browser)

                # Delete old version folder (only that one)
                old_folder = (
                    INSTALL_DIR / f"{browser}-{local_rev}" if local_rev else None
                )
                if old_folder and old_folder.exists():
                    try:
                        shutil.rmtree(old_folder)
                        self.stream(f"🧹 Deleted old version: {old_folder.name}")
                    except Exception as e:
                        self.stream(f"❌ Failed to delete {old_folder.name}: {e}")

        if not missing_or_outdated:
            self.window.evaluate_js(
                "window.updateStatus('All browsers already installed.')"
            )
            time.sleep(1.5)
            return

        # 🔄 Updating browsers
        self.window.evaluate_js("window.updateStatus('Updating browsers...')")

        for browser in missing_or_outdated:
            revision = revisions[browser]
            url = self.build_download_url(browser, revision)
            zip_path = INSTALL_DIR / f"{browser}-{PLATFORM}.zip"

            self.window.evaluate_js(f"window.updateStatus('Downloading {browser}...')")
            self.download_with_progress(url, zip_path)

            extract_to = INSTALL_DIR / f"{browser}-{revision}"
            try:
                self.extract_zip(zip_path, extract_to)
                os.remove(zip_path)
            except Exception as e:
                self.stream(f"❌ Extraction failed for {browser}: {e}")
                continue
            if not extract_to.exists() or not any(extract_to.iterdir()):
                self.stream(f"❌ Extraction folder is empty: {extract_to}")
                continue
        time.sleep(1)

        self.window.evaluate_js("window.clearProgress()")
        self.window.evaluate_js("window.clearBrowserStatus()")
        self.window.evaluate_js("window.updateStatus('Checking VPN...')")
        self.window.evaluate_js("window.startVpnStatus()")

    def fetch_browser_revisions(self):
        url = "https://raw.githubusercontent.com/microsoft/playwright/main/packages/playwright-core/browsers.json"

        def parse_revisions(data):
            revisions = {}
            for item in data["browsers"]:
                name = item["name"].lower()
                if name not in BROWSER_BINARIES:
                    continue
                revision = item.get("revision")
                overrides = item.get("revisionOverrides", {})
                if PLATFORM in overrides:
                    revision = overrides[PLATFORM]
                if revision:
                    key = name.replace("-", "_")  # normalize
                    revisions[key] = revision
            return revisions

        try:
            import json

            def is_cache_valid():
                if not CACHE_FILE.exists():
                    return False
                modified_time = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
                return datetime.now() - modified_time < timedelta(
                    days=CACHE_EXPIRY_DAYS
                )

            # 🧠 Use cached file if recent
            if is_cache_valid():
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return parse_revisions(data)

            # 🌐 Fetch from GitHub
            self.stream("🌐 Fetching latest browser revisions...")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # 💾 Cache the file
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return parse_revisions(data)

        except Exception as e:
            self.stream(f"❌ Failed to fetch browser revisions: {e}")
            return {}

    def build_download_url(self, browser, revision):
        if browser == "chromium_headless_shell":
            return f"https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/{revision}/chromium-headless-shell-win64.zip"
        else:
            return f"https://cdn.playwright.dev/dbazure/download/playwright/builds/{browser}/{revision}/{browser}-win64.zip"

    def download_with_progress(self, url, path):
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True) as r:
            if r.status_code != 200:
                raise Exception(f"Failed to download: {r.status_code} {r.reason}")
            content_type = r.headers.get("Content-Type", "")
            if not content_type.startswith("application/") or "html" in content_type:
                raise Exception(f"Invalid or unexpected content type: {content_type}")

            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()

            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        elapsed = time.time() - start_time
                        speed = downloaded / elapsed if elapsed > 0 else 0

                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        speed_mb = speed / (1024 * 1024)

                        self.window.evaluate_js(
                            f"window.updateProgress('{downloaded_mb:.2f}', '{total_mb:.2f}', '{speed_mb:.2f}')"
                        )
        time.sleep(0.3)

    def extract_zip(self, zip_path, extract_to):
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)
        except zipfile.BadZipFile:
            raise

    def vpn_check_loop(self):
        self.window.evaluate_js("window.clearBrowserStatus()")  # ✅ Hide browser status
        self.window.evaluate_js("window.startVpnStatus()")  # ✅ Start VPN dots

        while True:
            try:
                country = (
                    requests.get("http://ip-api.com/json", timeout=5)
                    .json()
                    .get("country", "Unknown")
                )
            except Exception:
                if not self.printed_fail:
                    self.window.evaluate_js("window.vpnFail()")
                    self.printed_fail = True
                time.sleep(5)
                continue

            if country != "United States":
                if not self.printed_fail:
                    self.window.evaluate_js("window.vpnFail()")
                    self.printed_fail = True
                time.sleep(5)
                continue
            else:
                self.vpn_verified = True
                self.window.evaluate_js("window.vpnSuccess()")
                time.sleep(1)
                break


def check_for_update(current_version="v1.1"):
    try:
        res = requests.get(
            "https://api.github.com/repos/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/releases/latest",
            timeout=10,
        )
        if res.status_code == 200:
            latest_version = res.json()["tag_name"]
            return latest_version != current_version, latest_version
    except Exception as e:
        print(f"⚠ Failed to check for updates: {e}")
    return False, None  # Fail-safe: assume no update


def start_gui():
    re_path = resource_path("Animation/Animation.html")
    html_path = os.path.abspath(re_path)
    window = webview.create_window(
        "FL Foreclosure County Scraper v1.1",
        url=f"file://{html_path}",
        width=1100,
        height=700,
    )
    api = API(window)

    # Logger instance, stream_callback sends logs to GUI
    logger = Logger()  # now GUI handled separately
    gui_stream = GuiStream(api.stream)

    # Combine both into one stream
    combined = CombinedStream(logger, gui_stream)

    sys.stdout = combined
    sys.stderr = combined

    def run_checks():
        from datetime import timedelta

        yesterday = datetime.now() - timedelta(days=1)
        AUCTION_DATE = yesterday.strftime("%m/%d/%Y")
        api.check_browser_installation()
        api.vpn_check_loop()

        # ✅ VERSION CHECK HERE
        is_outdated, latest = check_for_update("v1.1")
        if is_outdated:
            api.stream(
                f"🚨 New version available: {latest} Please upgrade to continue.\n"
            )
            return  # ⛔ stop here — don't run scrapers

        # Proceed only if VPN is okay and version is current
        if api.vpn_verified:
            api.stream("👋 Welcome to FL Foreclosure County Scraper...\n\n")
            api.stream(f"=== Start Scraping {AUCTION_DATE} ===")

            from Scraper import Calendar_scraper, Scraper
            from Merger import Auction_merger

            try:
                Calendar_scraper.main()
                Scraper.main()
                Auction_merger.main()
            except Exception as e:
                api.stream(f"❌ Error: {str(e)}")

    threading.Thread(target=run_checks, daemon=True).start()
    webview.start(gui="edgechromium" if os.name == "nt" else None)


try:
    import win32com.client
except ImportError:
    win32com = None  # Don't break the GUI if module isn't available

import os
import sys
import win32com.client


def create_start_menu_shortcut():
    exe_path = sys.executable  # ✅ This is your .exe when using PyInstaller
    shortcut_name = "FL Foreclosure Scraper.lnk"

    start_menu = os.path.join(
        os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs"
    )

    shortcut_path = os.path.join(start_menu, shortcut_name)

    if not os.path.exists(shortcut_path):
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.IconLocation = exe_path  # ✅ Automatically uses the .exe's icon
            shortcut.save()
            print("Shortcut created.")
        except Exception as e:
            print(f"Failed to create shortcut: {e}")
    else:
        print("Shortcut already exists.")


if __name__ == "__main__":
    create_start_menu_shortcut()  # 🔁 Call this once on startup
    start_gui()
