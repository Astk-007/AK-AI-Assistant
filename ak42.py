import os
import time
import urllib.parse
import webbrowser
import subprocess
import ctypes
from ctypes import wintypes
from pathlib import Path
from datetime import datetime

import speech_recognition as sr
import pyttsx3
import pyautogui
import pyperclip
import ollama


# ============================================================
# AK 4.0 - ADVANCED COMPUTER INTELLIGENCE
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


def close_application(app_name):
    """
    Ask Windows to close visible windows belonging to the requested application.
    This sends WM_CLOSE (a normal close request), rather than force-killing it.
    Unsaved-work dialogs are therefore allowed to appear.
    """
    process_names = {
        "notepad": {"notepad.exe"},
        "calculator": {"calculator.exe", "calculatorapp.exe"},
        "paint": {"mspaint.exe"},
        "file explorer": {"explorer.exe"},
        "task manager": {"taskmgr.exe"},
        "command prompt": {"cmd.exe"},
        "cmd": {"cmd.exe"},
        "powershell": {"powershell.exe", "pwsh.exe"},
        "vs code": {"code.exe"},
        "visual studio code": {"code.exe"},
        "chrome": {"chrome.exe"},
        "google chrome": {"chrome.exe"},
        "edge": {"msedge.exe"},
        "microsoft edge": {"msedge.exe"},
        "firefox": {"firefox.exe"},
    }

    targets = process_names.get(app_name.lower().strip())
    if not targets:
        speak(f"I do not have a close rule for {app_name}, Master.")
        return

    if os.name != "nt":
        speak("Application closing is supported on Windows, Master.")
        return

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    EnumWindows = user32.EnumWindows
    EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
    EnumWindows.restype = wintypes.BOOL

    IsWindowVisible = user32.IsWindowVisible
    IsWindowVisible.argtypes = [wintypes.HWND]
    IsWindowVisible.restype = wintypes.BOOL

    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetWindowTextLengthW.argtypes = [wintypes.HWND]
    GetWindowTextLengthW.restype = ctypes.c_int

    GetWindowTextW = user32.GetWindowTextW
    GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    GetWindowTextW.restype = ctypes.c_int

    GetWindowThreadProcessId = user32.GetWindowThreadProcessId
    GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    GetWindowThreadProcessId.restype = wintypes.DWORD

    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    OpenProcess.restype = wintypes.HANDLE

    QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
    QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD)
    ]
    QueryFullProcessImageNameW.restype = wintypes.BOOL

    CloseHandle = kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype = wintypes.BOOL

    SendMessageTimeoutW = user32.SendMessageTimeoutW
    SendMessageTimeoutW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)
    ]
    SendMessageTimeoutW.restype = wintypes.LPARAM

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    WM_CLOSE = 0x0010
    SMTO_ABORTIFHUNG = 0x0002

    windows_to_close = []
    # Protect the terminal that launched AK (for example, the PowerShell
    # window where Master is running this script).
    protected_parent_pid = os.getppid()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def enum_callback(hwnd, lparam):
        if not IsWindowVisible(hwnd):
            return True

        title_length = GetWindowTextLengthW(hwnd)
        if title_length <= 0:
            return True

        title_buffer = ctypes.create_unicode_buffer(title_length + 1)
        GetWindowTextW(hwnd, title_buffer, title_length + 1)
        window_title = title_buffer.value.strip()

        # Avoid treating the Windows desktop shell as a File Explorer window.
        if not window_title or window_title.lower() == "program manager":
            return True

        pid = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value or pid.value == protected_parent_pid:
            return True

        handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return True

        try:
            image_buffer = ctypes.create_unicode_buffer(1024)
            image_size = wintypes.DWORD(len(image_buffer))
            if QueryFullProcessImageNameW(handle, 0, image_buffer, ctypes.byref(image_size)):
                exe_name = Path(image_buffer.value).name.lower()
                if exe_name in targets:
                    windows_to_close.append((hwnd, window_title))
        finally:
            CloseHandle(handle)

        return True

    try:
        EnumWindows(enum_callback, 0)
        if not windows_to_close:
            speak(f"I could not find an open {app_name} window, Master.")
            return

        closed_count = 0
        for hwnd, title in windows_to_close:
            result = ctypes.c_size_t()
            sent = SendMessageTimeoutW(
                hwnd, WM_CLOSE, 0, 0, SMTO_ABORTIFHUNG, 2000,
                ctypes.byref(result)
            )
            if sent:
                closed_count += 1

        if closed_count:
            speak(
                f"I sent a normal close request to {closed_count} "
                f"{app_name} window or windows, Master. Save any changes if asked."
            )
        else:
            speak(f"Windows did not respond to the close request for {app_name}, Master.")
    except Exception as error:
        print("Application closing error:", error)
        speak(f"I could not close {app_name}, Master.")



# ============================================================
# WINDOWS SYSTEM CONTROLS - AK 4.2
# ============================================================

def get_volume():
    """Read the current Windows master volume (0-100) using pycaw."""
    from pycaw.pycaw import AudioUtilities
    speakers = AudioUtilities.GetSpeakers()

    # Newer pycaw versions expose EndpointVolume directly on AudioDevice.
    endpoint = getattr(speakers, "EndpointVolume", None)
    if endpoint is not None:
        return round(endpoint.GetMasterVolumeLevelScalar() * 100)

    # Compatibility path for older pycaw versions.
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import IAudioEndpointVolume
    interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    endpoint = cast(interface, POINTER(IAudioEndpointVolume))
    return round(endpoint.GetMasterVolumeLevelScalar() * 100)


def set_volume(level):
    """Set Windows master volume to a percentage (0-100)."""
    try:
        level = max(0, min(100, int(level)))
    except (TypeError, ValueError):
        speak("Tell me a volume from zero to one hundred, Master.")
        return

    try:
        from pycaw.pycaw import AudioUtilities
        speakers = AudioUtilities.GetSpeakers()

        # Current pycaw API: AudioDevice.EndpointVolume
        endpoint = getattr(speakers, "EndpointVolume", None)
        if endpoint is not None:
            endpoint.SetMasterVolumeLevelScalar(level / 100.0, None)
        else:
            # Compatibility path for older pycaw releases.
            from ctypes import POINTER, cast
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import IAudioEndpointVolume
            interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            endpoint = cast(interface, POINTER(IAudioEndpointVolume))
            endpoint.SetMasterVolumeLevelScalar(level / 100.0, None)

        speak(f"Volume set to {level} percent, Master.")
    except ImportError:
        speak("Exact volume setting needs pycaw and comtypes. Install them with pip install pycaw comtypes, Master.")
    except Exception as error:
        print("Volume control error:", repr(error))
        speak("I could not change the volume. Check the Windows audio device and permissions.")


def change_volume(direction):
    try:
        if direction == "up":
            pyautogui.press("volumeup", presses=5, interval=0.05)
            speak("Volume increased, Master.")
        elif direction == "down":
            pyautogui.press("volumedown", presses=5, interval=0.05)
            speak("Volume decreased, Master.")
        elif direction == "mute":
            pyautogui.press("volumemute")
            speak("Mute toggled, Master.")
    except Exception as error:
        print("Volume key error:", error)
        speak("I could not control the volume.")


def set_brightness(level):
    try:
        level = max(0, min(100, int(level)))
    except (TypeError, ValueError):
        speak("Tell me a brightness level from zero to one hundred, Master.")
        return
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        speak(f"Brightness set to {level} percent, Master.")
    except ImportError:
        speak("Brightness control needs the optional screen-brightness-control package. Install it with pip install screen-brightness-control.")
    except Exception as error:
        print("Brightness control error:", error)
        speak("I could not change brightness. This display may not support software brightness control.")


def open_windows_setting(setting):
    pages = {
        "wifi": "ms-settings:network-wifi",
        "bluetooth": "ms-settings:bluetooth",
        "sound": "ms-settings:sound",
        "display": "ms-settings:display",
    }
    uri = pages.get(setting)
    if not uri:
        speak("That Windows settings page is not supported.")
        return
    try:
        os.startfile(uri)
        speak(f"Opening {setting} settings, Master. You can finish the change there.")
    except Exception as error:
        print("Settings error:", error)
        speak(f"I could not open {setting} settings.")


def lock_computer():
    if os.name != "nt":
        speak("Locking is supported on Windows only.")
        return
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception as error:
        print("Lock error:", error)
        speak("I could not lock the computer.")


def show_running_apps():
    """Display visible-window application names without terminating anything."""
    if os.name != "nt":
        speak("Listing running apps is supported on Windows only.")
        return
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        results = []
        EnumWindows = user32.EnumWindows
        EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
        EnumWindows.restype = wintypes.BOOL
        IsWindowVisible = user32.IsWindowVisible
        IsWindowVisible.argtypes = [wintypes.HWND]
        IsWindowVisible.restype = wintypes.BOOL
        GetWindowTextLengthW = user32.GetWindowTextLengthW
        GetWindowTextLengthW.argtypes = [wintypes.HWND]
        GetWindowTextLengthW.restype = ctypes.c_int
        GetWindowTextW = user32.GetWindowTextW
        GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        GetWindowTextW.restype = ctypes.c_int
        GetWindowThreadProcessId = user32.GetWindowThreadProcessId
        GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        GetWindowThreadProcessId.restype = wintypes.DWORD
        OpenProcess = kernel32.OpenProcess
        OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        OpenProcess.restype = wintypes.HANDLE
        QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW
        QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        QueryFullProcessImageNameW.restype = wintypes.BOOL
        CloseHandle = kernel32.CloseHandle
        CloseHandle.argtypes = [wintypes.HANDLE]
        CloseHandle.restype = wintypes.BOOL
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def callback(hwnd, _):
            if not IsWindowVisible(hwnd):
                return True
            length = GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            title = ctypes.create_unicode_buffer(length + 1)
            GetWindowTextW(hwnd, title, length + 1)
            name = title.value.strip()
            if not name or name.lower() == "program manager":
                return True
            pid = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
            exe = "Unknown"
            if handle:
                try:
                    pathbuf = ctypes.create_unicode_buffer(1024)
                    size = wintypes.DWORD(len(pathbuf))
                    if QueryFullProcessImageNameW(handle, 0, pathbuf, ctypes.byref(size)):
                        exe = Path(pathbuf.value).name
                finally:
                    CloseHandle(handle)
            results.append((exe, name))
            return True

        EnumWindows(callback, 0)
        if not results:
            speak("I could not find any visible application windows, Master.")
            return
        print("\nVISIBLE RUNNING APPLICATIONS:")
        for index, (exe, title) in enumerate(results, 1):
            print(f"{index}. {exe} — {title}")
        speak(f"I found {len(results)} visible application windows. Their names are displayed in the terminal, Master.")
    except Exception as error:
        print("Running apps error:", error)
        speak("I could not list running applications.")

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
AK 4.2 COMMANDS
---------------
Apps:
  open notepad / calculator / paint / file explorer / task manager
  open cmd / powershell / vs code / chrome

Close apps:
  close notepad / calculator / paint / file explorer
  close task manager / cmd / powershell / vs code / chrome / edge

Windows controls:
  increase volume / decrease volume / mute
  set volume to 50
  increase brightness / decrease brightness
  set brightness to 70
  open Wi-Fi settings / open Bluetooth settings
  turn on Wi-Fi / turn off Wi-Fi
  turn on Bluetooth / turn off Bluetooth
  lock computer
  show running apps

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

    # Windows system controls
    if low in {"volume", "current volume", "what is the volume", "check volume"}:
        try:
            current = get_volume()
            speak(f"Your current volume is {current} percent, Master.")
        except Exception as error:
            print("Volume reading error:", repr(error))
            speak("I could not read the current volume, Master. Try volume up or volume down.")
        return True
    if low in {"increase volume", "volume up", "turn volume up"}:
        change_volume("up")
        return True
    if low in {"decrease volume", "volume down", "turn volume down"}:
        change_volume("down")
        return True
    if low in {"mute", "mute volume", "unmute", "toggle mute"}:
        change_volume("mute")
        return True
    if low.startswith("set volume to ") or low.startswith("volume to "):
        value = low.split(" to ", 1)[1].replace("percent", "").replace("%", "").strip()
        if value.isdigit():
            set_volume(int(value))
        else:
            speak("Give me a number from zero to one hundred, Master.")
        return True
    if low.startswith("set brightness to ") or low.startswith("brightness to "):
        value = low.split(" to ", 1)[1].replace("percent", "").replace("%", "").strip()
        if value.isdigit():
            set_brightness(int(value))
        else:
            speak("Give me a brightness number from zero to one hundred, Master.")
        return True
    if low in {"increase brightness", "brightness up", "make screen brighter"}:
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness()
            current = current[0] if isinstance(current, list) else current
            set_brightness(min(100, int(current) + 10))
        except ImportError:
            speak("Install screen-brightness-control to use brightness commands, Master.")
        except Exception as error:
            print("Brightness error:", error)
            speak("I could not read or increase brightness.")
        return True
    if low in {"decrease brightness", "brightness down", "make screen dimmer"}:
        try:
            import screen_brightness_control as sbc
            current = sbc.get_brightness()
            current = current[0] if isinstance(current, list) else current
            set_brightness(max(0, int(current) - 10))
        except ImportError:
            speak("Install screen-brightness-control to use brightness commands, Master.")
        except Exception as error:
            print("Brightness error:", error)
            speak("I could not read or decrease brightness.")
        return True
    if low in {"open wifi settings", "wifi settings", "show wifi settings", "open wi-fi settings"}:
        open_windows_setting("wifi")
        return True
    if low in {"open bluetooth settings", "bluetooth settings", "show bluetooth settings"}:
        open_windows_setting("bluetooth")
        return True
    if low in {"turn on wifi", "enable wifi", "turn off wifi", "disable wifi", "turn on wi-fi", "turn off wi-fi"}:
        speak("I am opening Wi-Fi settings, Master. Please switch Wi-Fi there. This avoids changing the wrong network adapter.")
        open_windows_setting("wifi")
        return True
    if low in {"turn on bluetooth", "enable bluetooth", "turn off bluetooth", "disable bluetooth"}:
        speak("I am opening Bluetooth settings, Master. Please switch Bluetooth there.")
        open_windows_setting("bluetooth")
        return True
    if low in {"lock computer", "lock my computer", "lock laptop", "lock my laptop", "lock pc"}:
        speak("Locking your computer, Master.")
        lock_computer()
        return True
    if low in {"show running apps", "list running apps", "what apps are running", "which apps are open", "show open applications"}:
        show_running_apps()
        return True

    # Close a specifically named application (normal Windows close request).
    close_aliases = {
        "close notepad": "notepad",
        "close calculator": "calculator",
        "close calc": "calculator",
        "close paint": "paint",
        "close file explorer": "file explorer",
        "close explorer": "file explorer",
        "close task manager": "task manager",
        "close command prompt": "command prompt",
        "close cmd": "cmd",
        "close powershell": "powershell",
        "close vs code": "vs code",
        "close visual studio code": "visual studio code",
        "close chrome": "chrome",
        "close google chrome": "google chrome",
        "close edge": "edge",
        "close microsoft edge": "microsoft edge",
        "close firefox": "firefox",
    }
    if low in close_aliases:
        close_application(close_aliases[low])
        return True

    if low in {"open chrome", "open google chrome"}:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", "chrome"])
            speak("Opening Chrome, Master.")
        except Exception as error:
            print("Chrome launch error:", error)
            speak("I could not open Chrome. Check that it is installed.")
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
    print("                 AK AI ASSISTANT 4.1")
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

    speak("AK version 4.1 is online, Master. Advanced Computer Intelligence and Windows controls are ready.")

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
