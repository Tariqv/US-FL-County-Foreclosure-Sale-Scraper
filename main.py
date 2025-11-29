import webview
import threading
import os
import sys
import time
import json
from datetime import datetime
import win32com.client
from utils import SESSION, get_auction_date
from make_excel import main
requests = SESSION()

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class Logger:
    def __init__(self, stream_callback=None):
        if not os.path.exists("logs"):
            os.makedirs("logs")

        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file_path = os.path.join("logs", f"{today}.log")
        self.log_file = open(self.log_file_path, "a", encoding="utf-8")

        self.stream_callback = stream_callback

    def write(self, text):
        if text.strip():
            if not text.endswith("\n"):
                text += "\n"
            self.log_file.write(text)
            self.log_file.flush()
            if self.stream_callback:
                self.stream_callback(
                    text.strip()
                )

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
        self.stream_func(message)

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
        self.window.evaluate_js(f"window.enqueueText({json.dumps(msg)})")

    def vpn_check_loop(self):
        self.window.evaluate_js("window.startVpnStatus()")

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


def check_for_update(current_version="v1.2"):
    try:
        res = requests.get(
            "https://api.github.com/repos/Tariqv/US-FL-County-Foreclosure-Sale-Scraper/releases/latest",
            timeout=10,
        )
        if res.status_code == 200:
            latest_version = res.json()["tag_name"]
            return latest_version != current_version, latest_version
    except Exception:
        pass
    return False, None

def start_gui():
    re_path = resource_path("Animation/Animation.html")
    html_path = os.path.abspath(re_path)
    window = webview.create_window(
        "FL Foreclosure County Scraper v1.2",
        url=f"file://{html_path}",
        width=1100,
        height=700,
    )
    api = API(window)
    logger = Logger()
    gui_stream = GuiStream(api.stream)
    combined = CombinedStream(logger, gui_stream)

    sys.stdout = combined
    sys.stderr = combined

    def run_checks():

        api.vpn_check_loop()
        is_outdated, latest = check_for_update("v1.2")
        if is_outdated:
            api.stream(
                f"🚨 New version available: {latest} Please upgrade to continue.\n"
            )
            return

        if api.vpn_verified:
            api.stream("👋 Welcome to FL Foreclosure County Scraper...\n")
            api.stream(f"=== Start Scraping {get_auction_date()} ===\n")
            try:
                main()
            except Exception as e:
                api.stream(f"❌ Error in main(): {str(e)}")

    threading.Thread(target=run_checks, daemon=True).start()
    webview.start(gui="edgechromium" if os.name == "nt" else None)

def create_start_menu_shortcut():
    exe_path = sys.executable
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
            shortcut.IconLocation = exe_path
            shortcut.save()
        except Exception:
            pass
    else:
        pass

if __name__ == "__main__":
    create_start_menu_shortcut()
    start_gui()
