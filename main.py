# main.py
import pyttsx3

import speech_recognition as sr

from agents import file_manager

from agents import web_app_manager

from agents import calendar_manager

import datetime

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

def process_command(command: str):
        intent = recognize_intent(command)
        try:  
            if intent == "file_manage":
                if "list" in command:
                    result = file_manager.list_files(".")
                elif "create" in command and "folder" in command:
                    result = file_manager.create_folder("test_folder")
                elif "move" in command:
                    result = file_manager.move_file("test.txt", "test_folder/test.txt")
                else:
                    result = "File management command not recognized."
    
                print("Assistant:", result)
                speak(result)
                feedback = input("Did this work correctly? (yes/no): ").strip().lower()
                if feedback in ["yes", "y"]:
                    log_feedback(command, "success")
                else:
                    log_feedback(command, "failure")

                return
            response = f"Recognized intent: {intent}"
            print(f"Assistant: {response}")
            speak(response)

            if intent == "web_search" or intent == "launch_app":
                if "search for" in command or "google" in command:
                    query = command.replace("search for", "").replace("google", "").strip()
                    feedback = f"Searching for {query}..."
                    print(f"Assistant: {feedback}")
                    speak(feedback)
                    result = web_app_manager.search_google(query)
                elif intent == "web_search":
                    feedback = f"Searching for {command}..."
                    print(f"Assistant: {feedback}")
                    speak(feedback)
                    result = web_app_manager.search_google(command)
                elif "open" in command:
                    if ".com" in command or ".org" in command or ".net" in command:
                        site = command.replace("open", "").strip()
                        feedback = f"Opening website {site}..."
                        print(f"Assistant: {feedback}")
                        speak(feedback)
                        result = web_app_manager.open_website(site)
                    else:
                        app = command.replace("open", "").replace("run", "").strip()
                        feedback = f"Opening application {app}..."
                        print(f"Assistant: {feedback}")
                        speak(feedback)
                        result = web_app_manager.open_application(app)
                else:
                    result = "Web/App command not recognized."

                print("Assistant:", result)
                speak(result)
                feedback = input("Did this work correctly? (yes/no): ").strip().lower()
                if feedback in ["yes", "y"]:
                    log_feedback(command, "success")
                else:
                    log_feedback(command, "failure")

                return

            if intent == "calendar_event":
                summary, start_time, duration_hours = calendar_manager.parse_command(command)
                if summary and start_time:
                    result = calendar_manager.create_event(summary, start_time, duration_hours)
                else:
                    result = "Sorry, I couldn't understand the date/time."
                
                print("Assistant:", result)
                speak(result)
                feedback = input("Did this work correctly? (yes/no): ").strip().lower()
                if feedback in ["yes", "y"]:
                    log_feedback(command, "success")
                else:
                    log_feedback(command, "failure")

                return
            if intent == "calendar_list":
                events = calendar_manager.list_upcoming_events()
                result = "\n".join(events)
                print("Assistant:\n", result)
                speak("Here are your upcoming events.")
                feedback = input("Did this work correctly? (yes/no): ").strip().lower()
                if feedback in ["yes", "y"]:    
                    log_feedback(command, "success")
                else:
                    log_feedback(command, "failure")
                return

            # In main.py
            if intent == "rag_query":
                result = rag.answer_query(command) # Revert back to this
                print("Assistant:", result)
                speak(result)
                feedback = input("Did this work correctly? (yes/no): ").strip().lower()
                if feedback in ["yes", "y"]:
                    log_feedback(command, "success")
                else:
                    log_feedback(command, "failure")

                return


            if intent == "workflow_trigger":
                speak("Triggering workflow.")
                if ":" in command:
                    actual_cmd = command.split(":", 1)[1].strip()
                else:
                    actual_cmd = "dir"  # default

                result = trigger_n8n(actual_cmd)
                print("Assistant:", result)
                speak("Workflow executed")
                return


            if intent == "email_send":
                try:
                    sender_email = "pratham.r.108@gmail.com"
                    password = "lshp zhca cyzm yocd"  # use Gmail App Password, not normal password

                    # --- Extract recipient ---
                    recipient_email = None
                    for name in CONTACTS:
                        if f"to {name}" in command.lower():
                            recipient_email = CONTACTS[name]
                            break
                    if not recipient_email:
                        return "I couldn't find the recipient in your contacts."

                    # --- Extract subject ---
                    subject = "General Email"
                    if "about" in command:
                        subject = command.split("about", 1)[1].split("saying")[0].strip().title()

                    # --- Extract body ---
                    body = "Hello!"
                    if "saying" in command:
                        body = command.split("saying", 1)[1].strip()
                    else:
                        body = command.replace("send email", "").strip()

                    return email_manager.send_email(sender_email, password, recipient_email, subject, body)

                except Exception as e:
                    return f"Error handling email: {e}"

            
            elif intent == "exit":
                return "Goodbye! 👋"

            else:
                return "Sorry, I don't understand that command."
            
            
        except Exception as e:
            # Log error details to file
            with open("error.log", "a", encoding="utf-8") as f:
                f.write(f"[ERROR] Command: {command}\nIntent: {intent}\nError: {str(e)}\n\n")
            return "Something went wrong, please try again."


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
