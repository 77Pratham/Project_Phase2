# agents/web_app_manager.py
import webbrowser
import os
import subprocess
import sys

def open_website(url):
    try:
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opening website: {url}"
    except Exception as e:
        return f"Error: {e}"

def open_application(app_name):
    try:
        if sys.platform.startswith("win"):
            os.system(f"start {app_name}")
        elif sys.platform.startswith("darwin"):  # macOS
            subprocess.call(["open", "-a", app_name])
        else:  # Linux
            subprocess.call([app_name])
        return f"Opening application: {app_name}"
    except Exception as e:
        return f"Error: {e}"

def search_google(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"Searching Google for: {query}"
    except Exception as e:
        return f"Error: {e}"
