# ========== PARSE COMMAND-LINE ARGUMENTS FIRST ==========
# This MUST happen before importing Frontend.GUI to prevent PyQt5 initialization
import argparse
import sys

parser = argparse.ArgumentParser(description='Jarvis AI Assistant')
parser.add_argument('--headless', action='store_true', 
                   help='Run in headless mode (no GUI, voice only) for auto-startup')
parser.add_argument('--background', action='store_true',
                   help='Alias for --headless')
parser.add_argument('--gif-only', action='store_true',
                   help='Show only GIF animation, no chat interface')
args = parser.parse_args()

# Set mode flags BEFORE any other imports
headless_mode = args.headless or args.background
gif_only_mode = args.gif_only

# ========== SETUP APP PATHS BEFORE ANYTHING ELSE ==========
# This MUST be imported before backend modules to set up correct file paths
import app_paths

# ========== CONDITIONAL GUI IMPORT ==========
# Only import GUI if NOT in headless mode to prevent PyQt5 initialization
if not headless_mode:
    from Frontend.GUI import (
        GraphicalUserIntersace,
        GifOnlyInterface,
        SetAssistantStatus,
        ShowTextToScreen,
        TempDirectoryPath,
        SetMicrophoneStatus,
        AnswerModifier,
        QueryModifier,
        GetMicrophoneStatus,
        GetAssistantStatus
    )

# ========== BACKEND IMPORTS (always needed) ==========
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from Backend.AutoDeleteChat import delete_old_messages
import config
from asyncio import run
from time import sleep
import subprocess
import threading
import datetime
import random
import json
import os
import speech_recognition as sr

# Global variables for interruption handling
is_speaking = False  # Flag to track if Jarvis is currently speaking
should_interrupt = False  # Flag to signal interruption request
current_query = ""  # Store the current query being processed
task_paused = False  # Flag to indicate if task is paused for interruption

# Load configuration from config.py
Username = config.USERNAME
Assistantname = config.ASSISTANT_NAME
DefaultMessage = f'''{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username} : I am doing well. How may i help you?'''
subprocesses = []
Function = ["open", "close", "play", "system", "content", "google search", "youtube search", "skip ads"]

# ========== HEADLESS MODE UTILITY FUNCTIONS ==========
# These provide alternatives to GUI utility functions when running without GUI

TempDirPathHeadless = app_paths.FRONTEND_FILES_DIR

def HeadlessTempDirectoryPath(Filename):
    """Get path to temp file in headless mode"""
    return os.path.join(TempDirPathHeadless, Filename)

def HeadlessAnswerModifier(Answer):
    """Remove empty lines from answer (headless version)"""
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def HeadlessQueryModifier(Query):
    """Add proper punctuation to query (headless version)"""
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = [
        "how", "what", "who", "where", "when", "why",
        "which", "whom", "can you", "what's", "where's", "how's",
    ]
    
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    
    return new_query.capitalize()

# ========== HEADLESS MODE STATUS FUNCTIONS ==========
# These functions provide console-only alternatives when GUI is disabled

headless_status = "Initializing..."
headless_mic_status = "False"

def HeadlessSetAssistantStatus(status):
    """Set assistant status in headless mode (console only)"""
    global headless_status
    headless_status = status
    print(f"[STATUS] {status}")

def HeadlessShowTextToScreen(text):
    """Show text in headless mode (console only)"""
    print(f"[CHAT] {text}")

def HeadlessGetMicrophoneStatus():
    """Get microphone status in headless mode"""
    global headless_mic_status
    return headless_mic_status

def HeadlessSetMicrophoneStatus(status):
    """Set microphone status in headless mode"""
    global headless_mic_status
    headless_mic_status = status

def HeadlessGetAssistantStatus():
    """Get assistant status in headless mode"""
    global headless_status
    return headless_status

# Wrapper functions that switch between GUI and headless mode
def SetAssistantStatusWrapper(status):
    if headless_mode:
        HeadlessSetAssistantStatus(status)
    else:
        SetAssistantStatus(status)

def ShowTextToScreenWrapper(text):
    if headless_mode:
        HeadlessShowTextToScreen(text)
    else:
        ShowTextToScreen(text)

def GetMicrophoneStatusWrapper():
    if headless_mode:
        return HeadlessGetMicrophoneStatus()
    else:
        return GetMicrophoneStatus()

def SetMicrophoneStatusWrapper(status):
    if headless_mode:
        HeadlessSetMicrophoneStatus(status)
    else:
        SetMicrophoneStatus(status)

def GetAssistantStatusWrapper():
    if headless_mode:
        return HeadlessGetAssistantStatus()
    else:
        return GetAssistantStatus()

# Wrapper functions for utility functions
def TempDirectoryPathWrapper(Filename):
    """Get temp file path (works in both GUI and headless mode)"""
    if headless_mode:
        return HeadlessTempDirectoryPath(Filename)
    else:
        return TempDirectoryPath(Filename)

def AnswerModifierWrapper(Answer):
    """Modify answer text (works in both GUI and headless mode)"""
    if headless_mode:
        return HeadlessAnswerModifier(Answer)
    else:
        return AnswerModifier(Answer)

def QueryModifierWrapper(Query):
    """Modify query text (works in both GUI and headless mode)"""
    if headless_mode:
        return HeadlessQueryModifier(Query)
    else:
        return QueryModifier(Query)

# ========== END HEADLESS MODE FUNCTIONS ==========

def GetRandomGreeting():
    """Generate a random greeting based on time of day."""
    current_time = datetime.datetime.now()
    hour = current_time.hour
    
    # Time-based greetings
    if 5 <= hour < 12:
        time_greetings = [
            "Good morning sir",
            "Good morning sir, how are you today",
            "Morning sir, hope you're doing well",
            "Good morning sir, nice to see you",
            "Hello sir, good morning"
        ]
    elif 12 <= hour < 17:
        time_greetings = [
            "Good afternoon sir",
            "Good afternoon sir, how are you",
            "Afternoon sir, how's your day going",
            "Hello sir, good afternoon",
            "Good afternoon sir, nice to see you"
        ]
    elif 17 <= hour < 21:
        time_greetings = [
            "Good evening sir",
            "Good evening sir, how are you",
            "Evening sir, hope you had a great day",
            "Hello sir, good evening",
            "Good evening sir, nice to see you"
        ]
    else:
        time_greetings = [
            "Hello sir",
            "Hey there sir",
            "Hello sir, how are you",
            "Hi sir, nice to see you",
            "Hello sir, hope you're doing well"
        ]
    
    # General friendly greetings
    general_greetings = [
        "Hello sir",
        "Hi sir",
        "Hey sir",
        "Hello sir, how are you doing",
        "Hi sir, how can I help you today",
        "Hey there sir",
        "Hello sir, ready to assist you",
        "Hi sir, what can I do for you",
        "Hello sir, at your service",
        "Hey sir, I'm here to help"
    ]
    
    # Combine both lists and choose randomly
    all_greetings = time_greetings + general_greetings
    return random.choice(all_greetings)

def ShowDefaultChatIfNoChats():
      chatlog_path = r'Data\ChatLog.json'
      
      # Ensure the file exists before trying to read it
      if not os.path.exists(chatlog_path):
            print(f"[INFO] ChatLog.json not found, creating it...")
            with open(chatlog_path, 'w', encoding='utf-8') as f:
                  json.dump([], f)
      
      try:
            File = open(chatlog_path, "r", encoding='utf-8')
            chat_content = File.read()
            File.close()
            
            if len(chat_content)<5:
                  with open(TempDirectoryPathWrapper('Database.data'), "w", encoding='utf-8') as file:
                        file.write("")

                  with open(TempDirectoryPathWrapper('Responses.data'), 'w', encoding='utf-8') as file:
                        file.write("")  # Keep it empty instead of showing default message
      except Exception as e:
            print(f"[ERROR] Error in ShowDefaultChatIfNoChats: {e}")

def ReadChatLogJson():
      chatlog_path = r'Data\ChatLog.json'
      try:
            # Ensure file exists before reading
            if not os.path.exists(chatlog_path):
                  print(f"[INFO] ChatLog.json not found, creating empty log...")
                  with open(chatlog_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                  return []
            
            with open(chatlog_path, 'r', encoding='utf-8') as file:
                  chatlog_data = json.load(file)
            return chatlog_data
      except json.JSONDecodeError:
            print(f"[WARNING] ChatLog.json is corrupted, resetting...")
            with open(chatlog_path, 'w', encoding='utf-8') as f:
                  json.dump([], f)
            return []
      except Exception as e:
            print(f"[ERROR] Error reading ChatLog.json: {e}")
            return []

def ChatLogIntegration():
      if headless_mode:
            # Skip GUI integration in headless mode
            return
      json_data = ReadChatLogJson()
      formatted_chatlog = ""
      for entry in json_data:
            if entry['role'] == 'user':
                  formatted_chatlog += f"{Username} : {entry['content']}\n"
            elif entry["role"] == "assistant":
                  formatted_chatlog += f"{Assistantname} : {entry['content']}\n"

      with open(TempDirectoryPathWrapper('Database.data'), "w", encoding='utf-8') as file:
            file.write(AnswerModifierWrapper(formatted_chatlog))

def ShowChatsOnGUI():
      if headless_mode:
            # Skip GUI update in headless mode
            return
      File = open(TempDirectoryPathWrapper('Database.data'), "r", encoding='utf-8')
      Data = File.read()
      if len(str(Data))>0:
            lines = Data.split("\n")
            result = '\n'.join(lines)
            File.close()
            File = open(TempDirectoryPathWrapper('Responses.data'), "w", encoding='utf-8')
            File.write(result)
            File.close()

def InitialExecution():
      SetMicrophoneStatusWrapper("False")
      if not headless_mode:
            ShowTextToScreenWrapper("")
      delete_old_messages()  # Check and delete old messages if auto-delete is enabled
      if not headless_mode:
            ShowDefaultChatIfNoChats()
            ChatLogIntegration()
            ShowChatsOnGUI()
      else:
            # In headless mode, just ensure chat log exists
            chatlog_path = r'Data\ChatLog.json'
            if not os.path.exists(chatlog_path):
                  with open(chatlog_path, 'w') as f:
                        json.dump([], f)

InitialExecution()

# Callback function for TTS to check if it should stop due to interruption
def tts_check_interrupt(signal=None):
    """Callback for TTS to check interruption status.
    Args:
        signal: Optional signal from TTS (False = cleanup, None/True = check status)
    Returns:
        bool: False to stop TTS, True to continue
    """
    global should_interrupt, is_speaking
    
    # If signal is False, it's a cleanup call from finally block
    if signal is False:
        return True
    
    # Check for interruption request
    if should_interrupt:
        print("[INFO] TTS interrupted by user")
        should_interrupt = False
        return False
    return True

# Background thread to monitor for wake word during execution (optional enhancement)
def WakeWordMonitor():
    """
    Monitors for wake word 'Jarvis' during task execution.
    If detected while Jarvis is speaking, sets interruption flag.
    """
    global should_interrupt, is_speaking
    
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    print("[INFO] Wake word monitor started")
    
    while True:
        try:
            if is_speaking:  # Only monitor when Jarvis is speaking
                with microphone as source:
                    # Listen with shorter timeout for responsiveness
                    audio = recognizer.listen(source, timeout=0.5, phrase_time_limit=2)
                
                try:
                    # Recognize speech
                    text = recognizer.recognize_google(audio).lower()
                    
                    # Check for wake word
                    if "jarvis" in text or Assistantname.lower() in text:
                        print(f"[INFO] Wake word detected during speech: {text}")
                        should_interrupt = True
                        sleep(0.1)
                
                except sr.UnknownValueError:
                    pass  # Speech not understood, continue monitoring
                except sr.RequestError:
                    pass  # API error, continue monitoring
            else:
                sleep(0.1)  # Sleep when not speaking to save resources
        
        except Exception as e:
            if is_speaking:  # Only log errors during active monitoring
                print(f"[WARNING] Wake word monitor error: {e}")
            sleep(0.1)

def MainExecution():

      global is_speaking, should_interrupt, current_query, task_paused

      TaskExecution = False
      ImageExecution = False
      ImageGenerationQuery = ""

      SetAssistantStatusWrapper("Listening... ")
      Query = SpeechRecognition()
      current_query = Query  # Store current query
      ShowTextToScreenWrapper(f"{Username} : {Query}")
      SetAssistantStatusWrapper("Thinking... ")
      Decision = FirstLayerDMM(Query)

      print("")
      print(f"Decision : {Decision}")
      print("")

      G = any([i for i in Decision if i.startswith("general")])
      R = any([i for i in Decision if i.startswith("realtime")])

      Mearged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
      )

      for queries in Decision:
            if "generate " in queries:
                  ImageGenerationQuery = str(queries)
                  ImageExecution = True

      for queries in Decision:
            if TaskExecution == False:
                  if any(queries.startswith(func) for func in Function):
                        print(f"[DEBUG] Executing automation with commands: {Decision}")
                        run(Automation(list(Decision)))
                        TaskExecution = True
                        print("[DEBUG] Automation completed")

      if ImageExecution == True:

            with open(r"Frontend\Files\ImageGeneration.data", "w") as file:
                  file.write(f"{ImageGenerationQuery},True")

            try:
                  p1 = subprocess.Popen(['python', r'Backend\ImageGeneration.py'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE, shell=False)
                  subprocesses.append(p1)

            except Exception as e:
                  print(f"Error starting ImageGeneration.py: {e}")

      # Handle realtime search queries
      if G and R or R:
            SetAssistantStatusWrapper("Searching... ")
            Answer = RealtimeSearchEngine(QueryModifierWrapper(Mearged_query))
            ShowTextToScreenWrapper(f"{Assistantname} : {Answer}")
            SetAssistantStatusWrapper("Answering... ")
            is_speaking = True
            TextToSpeech(Answer, tts_check_interrupt)
            is_speaking = False
            return True
      
      # If automation tasks were executed, provide confirmation
      if TaskExecution:
            Answer = "Done."
            ShowTextToScreenWrapper(f"{Assistantname} : {Answer}")
            SetAssistantStatusWrapper("Task Completed")
            is_speaking = True
            TextToSpeech(Answer, tts_check_interrupt)
            is_speaking = False
            return True
      
      # Handle general queries and other commands
      ResponseGiven = False
      for Queries in Decision:

            if "general" in Queries:
                  SetAssistantStatusWrapper("Thinking... ")
                  QueryFinal = Queries.replace("general ", "")
                  Answer = ChatBot(QueryModifierWrapper(QueryFinal))
                  ShowTextToScreenWrapper(f"{Assistantname} : {Answer}")
                  SetAssistantStatusWrapper("Answering... ")
                  is_speaking = True
                  TextToSpeech(Answer, tts_check_interrupt)
                  is_speaking = False
                  ResponseGiven = True
                  return True

            elif "realtime" in Queries:
                  SetAssistantStatusWrapper("Searching... ")
                  QueryFinal = Queries.replace("realtime ", "")
                  Answer = RealtimeSearchEngine(QueryModifierWrapper(QueryFinal))
                  ShowTextToScreenWrapper(f"{Assistantname} : {Answer}")
                  SetAssistantStatusWrapper("Answering... ")
                  is_speaking = True
                  TextToSpeech(Answer, tts_check_interrupt)
                  is_speaking = False
                  ResponseGiven = True
                  return True
            
            elif "exit" in Queries:
                  QueryFinal = "Okay, Bye!"
                  Answer = ChatBot(QueryModifierWrapper(QueryFinal))
                  ShowTextToScreenWrapper(f"{Assistantname} : {Answer}")
                  SetAssistantStatusWrapper("Answering... ")
                  is_speaking = True
                  TextToSpeech(Answer, tts_check_interrupt)
                  is_speaking = False
                  SetAssistantStatusWrapper("Answering... ")
                  os._exit(1)
      
      # If Decision was empty or no valid action was found
      if not ResponseGiven:
            print(f"Warning: No valid action found for Decision: {Decision}")
            Answer = ChatBot(Query)
            ShowTextToScreenWrapper(f"{Assistantname} : {Answer}")
            SetAssistantStatusWrapper("Answering... ")
            is_speaking = True
            TextToSpeech(Answer, tts_check_interrupt)
            is_speaking = False
            return True

def FirstThread():
    global is_speaking, should_interrupt, task_paused
    
    # Greet the user when program starts
    sleep(1)  # Wait for GUI to initialize
    greeting = GetRandomGreeting()
    SetAssistantStatusWrapper("Greeting...")
    is_speaking = True
    TextToSpeech(greeting, tts_check_interrupt)
    is_speaking = False
    SetAssistantStatusWrapper("Available... ")

    while True:

        CurrentStatus = GetMicrophoneStatusWrapper()

        if CurrentStatus == "True":
            MainExecution()

        else:
            AIStatus = GetAssistantStatusWrapper()

            if "Available ... " in AIStatus:
                sleep(0.05)

            else:
                 SetAssistantStatusWrapper("Available... ")

def SecondThread():
    """Start GUI - either full GUI or GIF-only based on mode"""
    if gif_only_mode:
        GifOnlyInterface()
    else:
        GraphicalUserIntersace()

if __name__ == "__main__":
     # Arguments were already parsed at the top of the file
     # headless_mode and gif_only_mode are already set
     
     if headless_mode:
         print("=" * 70)
         print("JARVIS AI - HEADLESS MODE")
         print("Running in background with voice interface only")
         print("No GUI will be displayed")
         print("=" * 70)
         print()
         
         # Initialize without GUI
         HeadlessSetMicrophoneStatus("True")  # Enable mic by default in headless mode
         InitialExecution()
         
         # Start the main thread
         thread2 = threading.Thread(target=FirstThread, daemon=False)  # Non-daemon to keep process alive
         thread2.start()
         
         # Start the wake word monitor thread
         try:
             wake_word_thread = threading.Thread(target=WakeWordMonitor, daemon=False)
             wake_word_thread.start()
             print("[INFO] Wake word monitor enabled - you can interrupt Jarvis by saying 'Jarvis' during responses")
         except Exception as e:
             print(f"[WARNING] Wake word monitor disabled: {e}")
             print("[INFO] You can still use Jarvis normally, interruption feature unavailable")
         
         print("\n[INFO] Jarvis is now running in background mode")
         print("[INFO] Press Ctrl+C to stop\n")
         
         # Keep the main thread alive (no GUI to block on)
         try:
             thread2.join()
         except KeyboardInterrupt:
             print("\n[INFO] Shutting down Jarvis...")
             os._exit(0)
     
     elif gif_only_mode:
         # GIF-only mode: Show GIF animation without full chat interface
         print("=" * 70)
         print("JARVIS AI - GIF-ONLY MODE")
         print("Showing GIF animation with voice interface")
         print("=" * 70)
         print()
         
         InitialExecution()
         # Enable microphone so Jarvis starts listening
         SetMicrophoneStatusWrapper("True")
         
         # Start the main thread (daemon so it won't block GUI shutdown)
         thread2 = threading.Thread(target=FirstThread, daemon=True)
         thread2.start()
         
         # Start the wake word monitor thread
         try:
             wake_word_thread = threading.Thread(target=WakeWordMonitor, daemon=True)
             wake_word_thread.start()
             print("[INFO] Wake word monitor enabled")
         except Exception as e:
             print(f"[WARNING] Wake word monitor disabled: {e}")
         
         # Start the GIF GUI (this will block and keep the program running)
         SecondThread()
     
     else:
         # Normal mode with full GUI
         print("=" * 70)
         print("JARVIS AI - GUI MODE")
         print("Starting with graphical user interface")
         print("=" * 70)
         print()
         
         InitialExecution()
         # Enable microphone so Jarvis starts listening (GUI has mic button to control this)
         SetMicrophoneStatusWrapper("True")
         
         # Start the main thread
         thread2 = threading.Thread(target=FirstThread, daemon=True)
         thread2.start()
         
         # Start the wake word monitor thread
         try:
             wake_word_thread = threading.Thread(target=WakeWordMonitor, daemon=True)
             wake_word_thread.start()
             print("[INFO] Wake word monitor enabled - you can interrupt Jarvis by saying 'Jarvis' during responses")
         except Exception as e:
             print(f"[WARNING] Wake word monitor disabled: {e}")
             print("[INFO] You can still use Jarvis normally, interruption feature unavailable")
         
         # Start the GUI thread (this will block and keep the program running)
         SecondThread()
