import os
import sys
import socket
import time
import threading
import signal
import traceback

# A --windowed exe has no console (stdout/stderr are None), which makes Streamlit's
# server crash on startup. Send all output to a log file instead.
LOG_PATH = os.path.join(os.path.expanduser("~"), "AediPueblo_log.txt")
if sys.stdout is None or sys.stderr is None or getattr(sys, "frozen", False):
    _log = open(LOG_PATH, "w", buffering=1, encoding="utf-8")
    sys.stdout = _log
    sys.stderr = _log

PORT = 8765

# In a packaged exe, Streamlit wrongly thinks it is a developer install and looks for its
# frontend on localhost:3000. These must be set BEFORE streamlit is imported.
os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
os.environ["STREAMLIT_SERVER_PORT"] = "8765"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)


def run_server():
    try:
        import streamlit.web.cli as stcli
        signal.signal = lambda *a, **k: None  # Streamlit can't register signals off the main thread
        # Same way Streamlit's own command line starts an app. The developmentMode flag is
        # the documented fix for packaged exes jumping to localhost:3000.
        sys.argv = [
            "streamlit", "run", os.path.join(BASE, "app.py"),
            "--global.developmentMode=false",
            f"--server.port={PORT}",
            "--server.address=127.0.0.1",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--client.toolbarMode=minimal",
            # Force the app's own light look. Without this, Streamlit follows Windows dark
            # mode and draws pale text on the app's light sidebar, making it unreadable.
            "--theme.base=light",
            "--theme.primaryColor=#2F7A6E",
            "--theme.backgroundColor=#FBFCFA",
            "--theme.secondaryBackgroundColor=#F1F6F3",
            "--theme.textColor=#173E3A",
            "--server.enableXsrfProtection=false",
        ]
        stcli.main()
    except SystemExit:
        pass
    except Exception:
        traceback.print_exc()


threading.Thread(target=run_server, daemon=True).start()

# Wait up to ~60 seconds for the server to start (a packaged exe starts slowly)
for _ in range(120):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", PORT))
        s.close()
        break
    except Exception:
        time.sleep(0.5)

try:
    import webview
    webview.create_window("AediPueblo", f"http://127.0.0.1:{PORT}", width=1280, height=820)
    webview.start()
except Exception:
    # Fallback: open in the default browser if the native window fails
    import webbrowser
    traceback.print_exc()
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    input("Press Enter to quit...")

os._exit(0)