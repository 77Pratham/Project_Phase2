# main.py
import pyttsx3

from slot_extractor import extract_datetime
import speech_recognition as sr

from agents import file_manager

from agents import web_app_manager

from agents import calendar_manager 

from contacts_manager import ContactsManager
contacts = ContactsManager("contacts.csv")

import datetime

import difflib

import whisper
import sounddevice as sd
import numpy as np
import tempfile
import scipy.io.wavfile
import os

import json

CONTACTS = {
    "siddharth": "siddharthjayachandran2004@gmail.com",
    "shreya": "kulalshreya1204@gmail.com",
    "pratham": "pratham.r.prathamr8055@gmail.com"
}


from agents import email_manager

from rag_engine import RAGEngine
   # load existing FAISS index if available

rag = RAGEngine()
if not os.path.exists("faiss_index.pkl"):
    print("No FAISS index found. Building one now...")
    rag.build_index()
else:
    rag.load_index()


engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="whisper")

def listen_command():
    print("Listening... Speak now.")
    fs = 22050  # Higher sample rate for better quality
    duration = 8  # More time to speak
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    print("Recording complete.")

    # Normalize audio
    audio = audio / np.max(np.abs(audio))

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        scipy.io.wavfile.write(tmpfile.name, fs, audio)
        model = whisper.load_model("small")  # Use "small" or "base" for better accuracy
        result = model.transcribe(tmpfile.name, language="en")
        command = result["text"]
        print(f"You said: {command}")
        return command.lower()

def main():
    print("Hello! I am your AI Assistant. Type 'exit' to quit.\n")

    while True:
        choice = input("Type 'v' for voice, or just type your command: ").strip().lower()

        if choice == "v":
            command = listen_command()
        else:
            command = choice

        # If command is empty, skip
        if not command:
            continue

        result = process_command(command)
        print("Assistant:", result)
        speak(result)

        if result == "Goodbye! 👋":
            break

from intent_classifier import predict_intent
#from slot_extractor import extract_recipient, extract_subject_body, extract_datetime
from datetime import datetime

SESSION = {}  # keep context for multi-step tasks

from template_manager import TemplateManager

templates = TemplateManager("templates")

def process_command(command: str):
    global SESSION

    intent = recognize_intent(command)
    print(f"[DEBUG] Recognized intent: {intent}")
    try:
                # --- Step 1: Handle active session ---
        if "calendar" in SESSION:
            session = SESSION["calendar"]
            dt, duration = extract_datetime(command)
            if dt:
                subject = session.get("subject", "General Event")
                result = calendar_manager.create_event(subject, dt, duration_hours=duration)
                SESSION.pop("calendar", None)
                return f"Event created: {subject} at {dt.strftime('%Y-%m-%d %H:%M')} for {duration}h"
            else:
                return "Sorry, I still couldn't understand the date/time."

        label, conf = predict_intent(command)
        if conf > 0.75:
            intent = label
        else:
            intent = recognize_intent(command) 

        if intent == "file_manage":
            if "list" in command:
                result = file_manager.list_files(".")
            elif "create" in command and "folder" in command:
                result = file_manager.create_folder("test_folder")
            elif "move" in command:
                result = file_manager.move_file("test.txt", "test_folder/test.txt")
            else:
                result = "File management command not recognized."
            return result

        if intent == "web_search" or intent == "launch_app":
            if "search for" in command or "google" in command:
                query = command.replace("search for", "").replace("google", "").strip()
                return web_app_manager.search_google(query)
            elif "open" in command:
                if ".com" in command or ".org" in command or ".net" in command:
                    site = command.replace("open", "").strip()
                    return web_app_manager.open_website(site)
                else:
                    app = command.replace("open", "").replace("run", "").strip()
                    return web_app_manager.open_application(app)
            else:
                return "Web/App command not recognized."

        if intent == "calendar_event":
            session = SESSION.get("calendar", {})
            dt = extract_datetime(command) or session.get("datetime")
            subject, _ = extract_subject_body(command)
            subject = subject or session.get("subject") or "General Event"

            if not dt:
                SESSION["calendar"] = {"subject": subject}
                return "When should I schedule the event?"
            
            # auto-fill with context from RAG
            ctx = rag.get_context(subject)
            attendees = []
            if ctx and isinstance(ctx, str):
                attendees = [email for email in extract_emails_from_text(ctx)]
            
            result = calendar_manager.create_event(subject, dt, duration_hours=1, attendees=attendees)
            SESSION.pop("calendar", None)
            return f"Event created: {result}"

        if intent == "calendar_list":
            events = calendar_manager.list_upcoming_events()
            return "\n".join(events)

        if intent == "rag_query":
            return rag.answer_query(command)

        if intent == "workflow_trigger":
            if ":" in command:
                actual_cmd = command.split(":", 1)[1].strip()
            else:
                actual_cmd = "dir"
            return trigger_n8n(actual_cmd)

        if intent == "workflow":
            return trigger_n8n(command)

        if intent == "email_send":
# --- Extract recipients ---
            recipient = []

            # Match individual by name
            for name in contacts.df['name']:
                if name.lower() in command.lower():
                    email = contacts.get_email(name)
                    if email:
                        recipient.append(email)

            # Match groups by group_name (CSE_A, CSE_B, etc.)
            for group in contacts.df['group_name'].dropna().unique():
                if group.lower() in command.lower():
                    recipient.extend(contacts.get_group_emails(group))

            # Match all students
            if "all students" in command.lower():
                recipient.extend(contacts.get_all_students())

            # Match all staff
            if "all staff" in command.lower() or "faculty" in command.lower():
                recipient.extend(contacts.get_all_staff())

            # Remove duplicates
            recipient = list(set(recipient))

            if not recipient:
                return "I couldn't find any recipients in contacts.csv."


            # Fill placeholders (could use NLP or rules to parse date/time/context)
            dt, duration = extract_datetime(command)
            formatted_email = templates.fill_template(
                template_name,
                date=dt.strftime("%Y-%m-%d") if dt else "TBD",
                time=dt.strftime("%I:%M %p") if dt else "TBD",
                subject=subject or "Meeting",
                location="Conference Room",
                extra=body or "No extra agenda"
            )

            sender_email = "pratham.r.108@gmail.com"
            password = "lshp zhca cyzm yocd"
            return email_manager.send_email(sender_email, password, recipient, subject or "Meeting", formatted_email)
             # fallback rules

        if intent == "exit":
            return "Goodbye! 👋"

        return "Sorry, I don't understand that command."

    except Exception as e:
        with open("error.log", "a", encoding="utf-8") as f:
            f.write(f"[ERROR] Command: {command}\nIntent: {intent}\nError: {str(e)}\n\n")
        return "Something went wrong, please try again."


def extract_emails_from_text(text):
    import re
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)



import re

def recognize_intent(command: str):
    command = command.lower().strip()

    # Keyword sets for each intent
    web_keywords = {"search for", "google", "weather", "news", "who is", "what is", "define", "find", "look up"}
    app_keywords = {"open", "run", "launch", "start"}
    file_keywords = {"file", "folder", "directory", "list files", "create folder", "move file", "delete file", "rename file"}
    calendar_keywords = {"schedule", "meeting", "event", "remind", "reminder", "appointment", "calendar"}
    exit_keywords = {"exit", "quit", "goodbye", "bye", "close"}
    workflow_keywords = {"workflow", "trigger", "n8n", "automate"}
    email_keywords = {"send email", "mail", "email"}
    # Check for exit intent
    if any(word in command for word in exit_keywords):
        return "exit"

    # Calendar event intent
    if any(word in command for word in calendar_keywords):
        if "show" in command or "list" in command or "what's" in command:
            return "calendar_list"
        return "calendar_event"

    # File management intent
    if any(word in command for word in file_keywords):
        return "file_manage"

    # App launch intent
    if any(word in command for word in app_keywords):
        # Avoid false positives for web search (e.g., "open weather")
        if re.search(r"\b(open|run|launch|start)\b\s+\w+\.(com|org|net|io|gov)", command):
            return "web_search"
        return "launch_app"

    # Web search intent
    if any(word in command for word in web_keywords):
        return "web_search"

    # Fallback: Use regex for common question patterns
    if re.match(r"(who|what|when|where|how)\b", command):
        return "web_search"
    
    if "rag" in command or "kb" in command or "tell" in command:
        return "rag_query"
    
    if any(word in command for word in workflow_keywords):
        if ":" in command or "n8n" in command:
            return "workflow_trigger"
        return "workflow"
    
    if any(word in command for word in email_keywords):
        return "email_send"

    return "unknown"

def log_feedback(command, status):
    log_file = "log.json"
    logs = []

    # Load existing logs
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Add new entry
    logs.append({"command": command, "status": status})

    # Save back
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4)

import requests

def trigger_n8n(command):
    try:
        url = "http://localhost:5678/webhook/assistant"
        response = requests.post(url, json={"command": command})
        if response.status_code == 200:
            return response.text
        else:
            return f"Error: {response.status_code} {response.text}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    main()
