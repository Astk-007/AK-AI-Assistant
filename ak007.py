import os
import time
import urllib.parse
import webbrowser
import subprocess
from pathlib import Path
from datetime import datetime

import speech_recognition as sr
import pyttsx3
import pyautogui
import pyperclip
import ollama


# ============================================================
# AK 3.0 - SMART CONTROL
# MASTER MODE: ON
# ============================================================

ASSISTANT_NAME = "AK"
MODEL_NAME = "qwen2.5:1.5b"

engine = pyttsx3.init()
recognizer = sr.Recognizer()

pyautogui.PAUSE = 0.3
pyautogui.FAILSAFE = True

conversation_history = []
MAX_HISTORY_MESSAGES = 10
current_mode = "voice"

last_youtube_query = ""
pending_whatsapp_message = ""

HOME = Path.home()
KNOWN_FOLDERS = {
    "downloads": HOME / "Downloads",
    "download": HOME / "Downloads",
    "documents": HOME / "Documents",
    "document": HOME / "Documents",
    "desktop": HOME / "Desktop",
    "pictures": HOME / "Pictures",
    "music": HOME / "Music",
    "videos": HOME / "Videos",
}


# ============================================================
# SPEAK AND LISTEN
# ============================================================

def speak(text):
    print(f"\n{ASSISTANT_NAME}: {text}\n")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as error:
        print("Speech error:", error)


def listen():
    try:
        with sr.Microphone() as source:
            print("\nAK is listening, Master...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=20)

        command = recognizer.recognize_google(audio, language="en-IN").strip()
        if command:
            print(f"\nMaster: {command}")
        return command

    except sr.WaitTimeoutError:
        print("No speech detected.")
    except sr.UnknownValueError:
        print("Sorry, I could not understand that.")
    except sr.RequestError:
        speak("Voice recognition needs an internet connection.")
    except Exception as error:
        print("Listening error:", error)
    return ""


# ============================================================
# LOCAL AI BRAIN
# ============================================================

def ask_ai(question):
    global conversation_history

    conversation_history.append({"role": "user", "content": question})
    conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]

    messages = [{
        "role": "system",
        "content": (
            "You are AK, a helpful personal AI assistant. The user is your Master. "
            "Be friendly, practical, and clear. Explain technical topics simply. "
            "Keep spoken answers reasonably concise. Do not claim to have performed "
            "computer actions. If asked to perform an action, explain that you can "
            "only do actions supported by your command handlers."
        )
    }]
    messages.extend(conversation_history)

    try:
        print("\nAK's AI brain is thinking...")
        response = ollama.chat(model=MODEL_NAME, messages=messages)
        answer = response["message"]["content"].strip()
        conversation_history.append({"role": "assistant", "content": answer})
        conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]
        speak(answer)
    except Exception as error:
        print("Ollama error:", error)
        if conversation_history and conversation_history[-1].get("role") == "user":
            conversation_history.pop()
        speak("Master, I could not connect to my AI brain. Please check whether Ollama is running.")


# ============================================================
# MODE SWITCHING
# ============================================================

def detect_mode_switch(command):
    command = command.lower().strip()
    for prefix in ("hey ak ", "ak "):
        if command.startswith(prefix):
            command = command[len(prefix):].strip()
            break

    voice_commands = {
        "switch to voice mode", "switch voice mode", "switch to voice",
        "activate voice mode", "start voice mode", "voice mode",
    }
    typing_commands = {
        "switch to typing mode", "switch to typing mood", "switch to typing",
        "switch to text mode", "activate typing mode", "start typing mode",
        "typing mode", "typing mood", "text mode",
    }
    if command in voice_commands:
        return "voice"
    if command in typing_commands:
        return "typing"
    return None


# ============================================================
# APPLICATIONS AND FOLDERS
# ============================================================

def open_application(app_name):
    applications = {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "file explorer": ["explorer.exe"],
        "task manager": ["taskmgr.exe"],
        "command prompt": ["cmd.exe"],
        "powershell": ["powershell.exe"],
    }

    try:
        if app_name == "vs code":
            subprocess.Popen(["code"])
        elif app_name in applications:
            subprocess.Popen(applications[app_name])
        else:
            speak(f"I do not recognize the application {app_name}, Master.")
            return
        speak(f"Opening {app_name}, Master.")
    except FileNotFoundError:
        speak(f"Master, I could not find {app_name}. Please check whether it is installed.")
    except Exception as error:
        print("Application error:", error)
        speak(f"Sorry, I could not open {app_name}.")


def open_folder(folder_name):
    cleaned = folder_name.strip().strip('"').strip("'")
    if not cleaned:
        speak("Which folder should I open, Master? Say Downloads, Documents, Desktop, or provide a folder path.")
        return

    key = cleaned.lower().replace("my ", "").strip()
    key = key.removesuffix(" folder").strip()
    path = KNOWN_FOLDERS.get(key)

    if path is None:
        # Allow an explicit path only if it already exists.
        candidate = Path(cleaned).expanduser()
        if candidate.exists() and candidate.is_dir():
            path = candidate
        else:
            speak("I could not find that folder. Try Downloads, Documents, Desktop, or give me its full path.")
            return

    if not path.exists():
        speak(f"The {key} folder does not exist at the expected location, Master.")
        return

    try:
        subprocess.Popen(["explorer.exe", str(path)])
        speak(f"Opening {key}, Master.")
    except Exception as error:
        print("Folder error:", error)
        speak("I could not open that folder.")


def search_files(query):
    """Search common user folders and C:\\jarvis without changing or deleting files."""
    query = query.strip().lower()
    if not query:
        speak("Tell me the file name or extension to search for, Master.")
        return

    extension = None
    if query.startswith("files "):
        query = query[6:].strip()
    if query.startswith("file "):
        query = query[5:].strip()
    if query.startswith("named "):
        query = query[6:].strip()

    if query.startswith("with extension "):
        query = query[len("with extension "):].strip()
    if query in {"python", "python files", ".py", "py files"}:
        extension = ".py"
    elif query in {"pdf", "pdfs", "pdf files", ".pdf"}:
        extension = ".pdf"
    elif query in {"word", "word files", "docx files", ".docx"}:
        extension = ".docx"
    elif query in {"excel", "excel files", "xlsx files", ".xlsx"}:
        extension = ".xlsx"
    elif query in {"image", "images", "jpg files", "png files"}:
        extensions = {".jpg", ".jpeg", ".png", ".webp"}
    else:
        extensions = None
        if query.startswith(".") and " " not in query:
            extension = query
        elif query.endswith(" files"):
            possible = query[:-6].strip()
            if possible in {"python", "py"}:
                extension = ".py"
            elif possible in {"pdf"}:
                extension = ".pdf"
            elif possible in {"word", "docx"}:
                extension = ".docx"
            elif possible in {"excel", "xlsx"}:
                extension = ".xlsx"

    if "extensions" not in locals():
        extensions = {extension} if extension else None

    roots = [
        HOME / "Desktop",
        HOME / "Documents",
        HOME / "Downloads",
        Path(r"C:\jarvis"),
    ]
    matches = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for current_root, dirs, files in os.walk(root):
                # Avoid hidden/system folders and common bulky directories.
                dirs[:] = [
                    d for d in dirs
                    if not d.startswith(".")
                    and d.lower() not in {"node_modules", ".git", "__pycache__", ".venv"}
                ]
                for filename in files:
                    file_path = Path(current_root) / filename
                    if extensions:
                        matched = file_path.suffix.lower() in extensions
                    elif extension:
                        matched = file_path.suffix.lower() == extension
                    else:
                        matched = query in filename.lower()
                    if matched:
                        matches.append(file_path)
                        if len(matches) >= 30:
                            break
                if len(matches) >= 30:
                    break
        except (PermissionError, OSError):
            continue
        if len(matches) >= 30:
            break

    if not matches:
        speak("I could not find matching files in Desktop, Documents, Downloads, or C colon backslash jarvis.")
        return

    print("\nFILES FOUND:")
    for index, file_path in enumerate(matches, start=1):
        print(f"{index}. {file_path}")
    speak(f"I found {len(matches)} matching file or files, Master. The results are displayed in the terminal.")


def take_screenshot():
    try:
        folder = HOME / "Pictures" / "AK_Screenshots"
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        destination = folder / f"AK_screenshot_{stamp}.png"
        image = pyautogui.screenshot()
        image.save(destination)
        print(f"Screenshot saved to: {destination}")
        speak("Screenshot captured, Master. I saved it in Pictures, AK Screenshots.")
    except pyautogui.FailSafeException:
        speak("Screenshot action cancelled.")
    except Exception as error:
        print("Screenshot error:", error)
        speak("I could not capture the screenshot.")


# ============================================================
# WEB SEARCH AND TYPING
# ============================================================

def google_search(query):
    if not query.strip():
        speak("What should I search for on Google, Master?")
        return
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote_plus(query))
    speak(f"Searching Google for {query}, Master.")


def youtube_search(query):
    global last_youtube_query
    if not query.strip():
        speak("What should I search for on YouTube, Master?")
        return
    last_youtube_query = query.strip()
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(last_youtube_query)
    webbrowser.open(url)
    speak(f"Searching YouTube for {last_youtube_query}, Master. Choose a video from the results.")


def type_text(text):
    if not text.strip():
        speak("Master, you did not provide any text.")
        return
    speak("Select the window where you want the text typed. I will wait five seconds.")
    time.sleep(5)
    try:
        pyautogui.write(text, interval=0.02)
        speak("Text typed, Master.")
    except pyautogui.FailSafeException:
        speak("Typing cancelled using the mouse failsafe.")
    except Exception as error:
        print("Typing error:", error)
        speak("I could not type the text.")


# ============================================================
# WHATSAPP MESSAGE PREPARATION
# ============================================================

def prepare_whatsapp_message(message):
    global pending_whatsapp_message
    if not message.strip():
        speak("What message should I prepare, Master?")
        return
    try:
        pending_whatsapp_message = message.strip()
        pyperclip.copy(pending_whatsapp_message)
        webbrowser.open("https://web.whatsapp.com")
        print("\nMESSAGE COPIED TO CLIPBOARD:")
        print(pending_whatsapp_message)
        speak(
            "WhatsApp Web is opening and the message is copied, Master. "
            "Select the correct contact, click the message box, and press Control and V. "
            "Review the recipient and message before sending. I have not sent it."
        )
    except Exception as error:
        print("WhatsApp error:", error)
        speak("I could not prepare the WhatsApp message.")


# ============================================================
# COMMAND HANDLER - COMPUTER ACTIONS BEFORE AI
# ============================================================

def process_command(command):
    global current_mode, last_youtube_query

    if not command:
        return True

    original = command.strip()
    low = original.lower().strip()

    # Allow a simple wake-name prefix.
    for prefix in ("hey ak ", "ak "):
        if low.startswith(prefix):
            original = original[len(prefix):].strip()
            low = original.lower()
            break

    # Exit
    if low in {"exit", "quit", "exit ak", "quit ak", "stop ak", "shutdown ak", "goodbye", "goodbye ak"}:
        speak("Goodbye, Master. Plus Ultra!")
        return False

    # Mode switching
    new_mode = detect_mode_switch(low)
    if new_mode:
        if new_mode == current_mode:
            speak(f"{new_mode.title()} mode is already active, Master.")
        else:
            current_mode = new_mode
            speak(f"{new_mode.title()} mode activated, Master.")
        return True

    # Help
    if low in {"help", "show commands", "commands"}:
        print("""
AK 3.0 COMMANDS
---------------
Apps:
  open notepad / calculator / paint / file explorer / task manager
  open cmd / powershell / vs code

Folders:
  open downloads / documents / desktop / pictures / music / videos
  open folder C:\\some\\folder

File search:
  find Python files
  find PDF files
  find file named jarvis.py
  search files for report

Web:
  open YouTube / Google / WhatsApp
  search YouTube for motivation videos
  search for motivation videos on YouTube
  search Google for Python tutorials

Other:
  type Hello Master
  take a screenshot
  prepare message How are you?
  clear conversation
  switch to typing mode / switch to voice mode
  exit

Tip: 'play that' cannot choose a specific video automatically. Select a video from YouTube's results.
""")
        speak("I displayed the command list, Master.")
        return True

    # Clear AI conversation
    if low in {"clear conversation", "clear ai memory", "reset conversation"}:
        conversation_history.clear()
        speak("Conversation history cleared, Master.")
        return True

    # Open common apps
    app_commands = {
        "open notepad": "notepad",
        "open calculator": "calculator",
        "open calc": "calculator",
        "open paint": "paint",
        "open file explorer": "file explorer",
        "open explorer": "file explorer",
        "open task manager": "task manager",
        "open command prompt": "command prompt",
        "open cmd": "command prompt",
        "open powershell": "powershell",
        "open vs code": "vs code",
        "open visual studio code": "vs code",
    }
    if low in app_commands:
        open_application(app_commands[low])
        return True

    # Open common folders, including "open my Downloads folder".
    folder_phrases = ("open folder ", "open my folder ", "open ")
    if low in {"open downloads", "open download", "open downloads folder", "open my downloads"}:
        open_folder("downloads")
        return True
    if low in {"open documents", "open document", "open documents folder", "open my documents"}:
        open_folder("documents")
        return True
    if low in {"open desktop", "open desktop folder", "open my desktop"}:
        open_folder("desktop")
        return True
    if low in {"open pictures", "open pictures folder"}:
        open_folder("pictures")
        return True
    if low in {"open music", "open music folder"}:
        open_folder("music")
        return True
    if low in {"open videos", "open videos folder"}:
        open_folder("videos")
        return True
    if low in {"open folder", "open my folder"}:
        open_folder("")
        return True
    if low.startswith("open folder "):
        open_folder(original[len("open folder "):])
        return True
    if low.startswith("open my folder "):
        open_folder(original[len("open my folder "):])
        return True

    # Websites
    if low in {"open youtube", "youtube"}:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube, Master.")
        return True
    if low in {"open google", "google"}:
        webbrowser.open("https://www.google.com")
        speak("Opening Google, Master.")
        return True
    if low in {"open whatsapp", "open whatsapp web", "whatsapp"}:
        webbrowser.open("https://web.whatsapp.com")
        speak("Opening WhatsApp Web, Master.")
        return True

    # Handle "open YouTube and search [query]" before general YouTube routing.
    if low.startswith("open youtube and search"):
        query = original[len("open youtube and search"):].strip(" :")
        if query:
            youtube_search(query)
        else:
            speak("What should I search for on YouTube, Master?")
        return True

    # Search routing: YouTube has priority if the command mentions YouTube.
    if "youtube" in low and ("search" in low or "find" in low):
        query = original
        for phrase in (
            "search for ", "search youtube for ", "search on youtube for ",
            "search for ", "find ", "youtube search for ",
        ):
            pos = query.lower().find(phrase)
            if pos >= 0:
                query = query[pos + len(phrase):].strip()
                break
        query = query.replace(" on YouTube", "").replace(" on youtube", "").strip()
        if not query or query.lower() in {"on youtube", "youtube"}:
            speak("What should I search for on YouTube, Master?")
        else:
            youtube_search(query)
        return True

    # Explicit YouTube search phrases.
    for prefix in ("search youtube for ", "search on youtube for ", "youtube search for "):
        if low.startswith(prefix):
            youtube_search(original[len(prefix):].strip())
            return True

    # Google searches; generic "search for X on YouTube" is handled above.
    for prefix in ("search google for ", "google search for "):
        if low.startswith(prefix):
            google_search(original[len(prefix):].strip())
            return True
    if low.startswith("search for "):
        query = original[len("search for "):].strip()
        if query:
            google_search(query)
        else:
            speak("What should I search for, Master?")
        return True

    # Find/search local files. Searches only common user folders and C:\jarvis.
    for prefix in ("find file named ", "find a file named ", "find file ", "find ", "search files for "):
        if low.startswith(prefix):
            query = original[len(prefix):].strip()
            search_files(query)
            return True

    # Screenshot
    if low in {"take a screenshot", "take screenshot", "screenshot", "capture screen", "capture a screenshot"}:
        take_screenshot()
        return True

    # "Play that" cannot safely identify/select a particular video in the browser.
    if low in {"play that", "play it", "play the video"}:
        if last_youtube_query:
            speak("Master, YouTube search results for your last search should be open. Please choose the video you want to play.")
        else:
            speak("Master, search YouTube for a topic first, then choose a video from the results.")
        return True

    # Typing text
    if low.startswith("type "):
        type_text(original[5:].strip())
        return True

    # WhatsApp message preparation: never auto-send.
    for prefix in ("prepare whatsapp message ", "prepare message ", "prepare a message ", "write whatsapp message "):
        if low.startswith(prefix):
            prepare_whatsapp_message(original[len(prefix):].strip())
            return True

    # Do not let the AI pretend to send a WhatsApp message.
    if low.startswith("send it to ") or low.startswith("send the message to ") or low.startswith("send message to "):
        speak(
            "Master, I can prepare the message, but this version does not select contacts or send WhatsApp messages automatically. "
            "Please select the intended chat, verify the recipient, paste the message if needed, and send it yourself."
        )
        return True

    # Conversational questions go to Ollama.
    ask_ai(original)
    return True


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    global current_mode

    print("=" * 54)
    print("                 AK AI ASSISTANT 3.0")
    print("                  MASTER MODE: ON")
    print("=" * 54)
    print("AI Model:", MODEL_NAME)
    print("Default mode: VOICE")
    print("Say 'switch to typing mode' to switch.")
    print("Type 'switch to voice mode' to return.")
    print("Say or type 'help' to see commands.")
    print("Say or type 'exit' to close AK.")

    try:
        ollama.list()
        print("\nOllama connection detected.")
    except Exception as error:
        print("\nOllama connection warning:", error)
        print("Check that Ollama is running and the model is installed.")

    speak("AK version 3.0 is online, Master. Smart Control is ready.")

    while True:
        print(f"\n========== {current_mode.upper()} MODE ==========")
        if current_mode == "voice":
            print("Speak a command, Master.")
            command = listen()
            if not command:
                continue
        else:
            try:
                command = input("Master: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInput interrupted.")
                break
            if not command:
                continue

        if not process_command(command):
            break

    print("\nAK has shut down, Master.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAK stopped by Master.")
    except Exception as error:
        print("\nUnexpected error:", error)
        input("Press Enter to close...")
