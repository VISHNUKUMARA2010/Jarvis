# Import required libraries
from AppOpener import close, open as appopen  # Import functions to open and close apps.
from webbrowser import open as webopen  # Import web browser functionality.
# pywhatkit is lazy-imported to avoid its internet check at import time.
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML content.
from rich import print  # Import rich for styled console output.
from groq import Groq  # Import Groq for AI chat functionalities.
import webbrowser  # Import webbrowser for opening URLs.
import subprocess  # Import subprocess for interacting with system processes.
import requests  # Import requests for making HTTP requests.
import keyboard  # Import keyboard for keyboard-related actions.
import asyncio  # Import asyncio for asynchronous programming.
import datetime  # Import datetime for timestamps.
import os  # Import os for operating system functionalities.

# Import TextToSpeech for verbal acknowledgments
from Backend.TextToSpeech import TextToSpeech
import config  # Import centralized configuration

# Load configuration from config.py
GroqAPIKey = config.GROQ_API_KEY
Username = config.USERNAME

# Define CSS Classes for parsing specific elements in HTML content.
classes = ["zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSD YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "O5uR6d LTKOO", "vlzY6d", "webanswers-webanswers__table__webanswers-table", "dDoNo ikb4Bb gsrt", "sxLaOe",
           "LWKfke", "VQF4g", "qv3Wpe", "Kno-rdesc", "SPZz6b"]

# Define a user-agent for making web requests.
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36"

# Initialize the Groq client with the API key.
client = Groq(api_key=GroqAPIKey)

# Initialize professional responses for user interactions.
professional_responses = [
    "your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need - don't hesitate to ask.",
]

# List to store chatbot messages.
messages = []

# System message to provide context to the chatbot.
systemChatBot = [{"role": "system", "content": f"You are a professional content writer assistant. Write well-formatted, professional content including letters (sick leave, resignation, job applications), emails, code, essays, poems, stories, etc. For letters, ALWAYS include proper formatting:\n\nFor formal letters format:\nDate: [Current Date]\n[Your Name]\n[Your Address]\n[City, State, ZIP]\n\nTo,\n[Recipient Name/Title]\n[Organization]\n[Address]\n\nSubject: [Brief Subject]\n\nDear Sir/Madam,\n\n[Body paragraphs with proper spacing]\n\nYours sincerely,\n[Your Name]\n\nFor emails, include Subject, Dear [Name], body, and signature. Make all content ready to use, properly formatted, and professional. Use clear paragraphs and appropriate spacing."}]

# Function to perform a Google search.
def GoogleSearch(Topic):
    from pywhatkit import search  # Lazy import to avoid startup internet check.
    search(Topic)  #Use pywhatkit's search function to perform a Google search.
    return True  # Indicate success.

# Function to generate content using AI and save it to a file.
def Content(Topic):
    """
    Generates professional content (letters, emails, code, etc.) using AI
    and opens it in Notepad for editing.
    
    Examples:
    - "sick leave letter" -> Creates a professional sick leave application
    - "resignation letter" -> Creates a formal resignation letter  
    - "job application" -> Creates a job application letter
    - "email to boss" -> Creates a professional email
    """

    # Nested function to open a file in notepad.
    def OpenNotepad(file):
        default_text_editor = 'notepad.exe'  # Default text editor.
        subprocess.Popen([default_text_editor, file])  # Open the file in Notepad.

    # Nested function to generate content using the AI chatbot.
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})  # Add the user's prompt to messages.

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Use the versatile model for high-quality content generation.
            messages=systemChatBot + messages,  # Include system instructions and chat history.
            max_tokens=2048,  # Limit the maximum tokens in the response.
            temperature=0.7,  # Adjust response randomness.
            top_p=1,  # Use nucleus sampling for response diversity.
            stream=True,  # Enable streaming responses.
            stop=None  # Allow the model to determine stopping conditions.
        )
        
        Answer = ""  # Initialize an empty string for the response.

        # Process streamed responses chunks.
        for chunk in completion:
            if chunk.choices[0].delta.content:  # Check for content in the current chunk.
                Answer += chunk.choices[0].delta.content  # Append the content to the answer.

        Answer = Answer.replace("</s>", "")  # Remove unwanted tokens from the response.
        messages.append({"role": "assistant", "content": Answer})  # Add the AI's response to messages.
        return Answer
    
    # Generate appropriate filename based on content type
    filename_base = Topic.lower().replace(' ', '_')
    
    # Add descriptive prefix for common letter types
    if 'letter' in Topic.lower():
        if 'sick' in Topic.lower() or 'leave' in Topic.lower():
            filename_base = 'sick_leave_letter'
        elif 'resign' in Topic.lower():
            filename_base = 'resignation_letter'
        elif 'job' in Topic.lower() or 'application' in Topic.lower():
            filename_base = 'job_application_letter'
    
    # Add timestamp to make filename unique
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_base}_{timestamp}.txt"

    print(f"[INFO] Generating content for: {Topic}")
    ContentByAI = ContentWriterAI(f"Write a professional {Topic}")  # Generate content using AI.

    # Save the generated content to a text file.
    filepath = rf"Data\{filename}"
    with open(filepath, "w" , encoding="utf-8") as file:
        file.write(ContentByAI)  # Write the content to the file.
        file.close()

    print(f"[SUCCESS] Content saved to: {filepath}")
    OpenNotepad(filepath)  # Open the file in Notepad.
    return True  # Indicate success.

# Function to search for topic on Youtube.
def YouTubeSearch(Topic):
    URL4Search = f"https://www.youtube.com/results?search_query={Topic}"  # Construct the YouTube search URL.
    webbrowser.open(URL4Search)  # Open the search URL in a web browser.
    return True  # Indicate success.

# Function to skip YouTube ads.
def SkipYouTubeAds():
    try:
        import pyautogui
        import time
        
        print("[INFO] Attempting to skip YouTube ads...")
        
        # Method 1: Try to find and click the Skip Ad button using image recognition or coordinates
        # First, give focus to the browser window by clicking in center of screen
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(0.3)
        
        # Method 2: Use Tab navigation to reach Skip button
        # YouTube skip button is usually a few tabs away
        for _ in range(5):
            keyboard.press_and_release('tab')
            time.sleep(0.1)
        
        keyboard.press_and_release('enter')
        time.sleep(0.2)
        
        # Method 3: Try Shift+Tab if forward didn't work
        for _ in range(3):
            keyboard.press_and_release('shift+tab')
            time.sleep(0.1)
        
        keyboard.press_and_release('enter')
        
        print("[SUCCESS] YouTube ad skip command executed")
        return True
        
    except ImportError:
        # If pyautogui is not installed, use keyboard only method
        print("[INFO] Using keyboard-only method to skip ads...")
        try:
            # Tab through elements to find skip button
            for _ in range(8):
                keyboard.press_and_release('tab')
            keyboard.press_and_release('enter')
            print("[SUCCESS] YouTube ad skip attempted with keyboard")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to skip ads with keyboard: {e}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to skip YouTube ads: {e}")
        return False

# Function to play a video on YouTube.
def PlayYouTube(query):
    from pywhatkit import playonyt  # Lazy import to avoid startup internet check.
    playonyt(query)  # Use pywhatkit's playonyt function to play the video.
    return True  # Indicate success.

# Function to open an application or a relevant webpage.
def OpenApp(app, sess=requests.session()):

    print(f"[DEBUG] Attempting to open app: '{app}'")  # Debug: Show which app is being opened
    
    # Check if input is a URL or website
    app_lower = app.lower()
    if any(x in app_lower for x in ['http://', 'https://', 'www.', '.com', '.org', '.net', '.io', '.ai']):
        # It's a website URL
        try:
            url = app if app.startswith('http') else f'https://{app}'
            print(f"[INFO] Opening website: {url}")
            webbrowser.open(url)
            print(f"[SUCCESS] Website '{app}' opened successfully!")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to open website: {e}")
            return False
    
    # Try using AppOpener first for applications
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)  # Attempt to open the app.
        print(f"[SUCCESS] App '{app}' opened successfully with AppOpener!")  # Debug: Confirm success
        return True  # Indicate success.
    
    except Exception as e:
        print(f"[ERROR] AppOpener failed for '{app}': {e}")  # Debug: Show the error
        
        # Try Windows 'start' command as second attempt
        try:
            print(f"[FALLBACK 1] Trying Windows 'start' command for '{app}'...")
            subprocess.Popen(['cmd', '/c', 'start', app], shell=False)
            print(f"[SUCCESS] App '{app}' opened with Windows 'start' command!")
            return True
        except Exception as e2:
            print(f"[ERROR] Windows 'start' command failed: {e2}")
            print(f"[FALLBACK 2] Searching Google for '{app}' and opening first link...")  # Debug: Fallback mode
        # Nested function to extract links from HTML content.
        def extract_links(html):
            if html is None:
                return []
            soup = BeautifulSoup(html, 'html.parser')  # Parse the HTML content.
            links = soup.find_all('a', {'jsname': 'UWckNb'})  # Find relevant links.
            return [link.get('href') for link in links]  # Return the links.
        
        # Nested function to perform a Google search and retrieve HTML.
        def search_google(query):
            url = f"https://www.google.com/search?q={query}"  # Construct the Google search URL.
            headers = {"User-Agent": useragent}  # Use the predefined user-agent.
            response = sess.get(url, headers=headers)  # Perform the GET request.

            if response.status_code == 200:
                return response.text  # Return the HTML content.
            else:
                print("Failed to retrieve search results.")  # Print an error message.
                return None

        html = search_google(app)  # Perform the Google search.

        if html:
            link = extract_links(html)[0]  # Extract the first link from the search results.
            print(f"[FALLBACK] Opening link: {link}")  # Debug: Show the link being opened
            webopen(link)  # Open the link in a web browser.
        else:
            print(f"[ERROR] Could not find any link for '{app}'")  # Debug: No link found

        return True  # Indicate success.
        
# Function to close an application.
def CloseApp(app):
    # Don't close browsers that might be used for speech recognition
    browser_keywords = ["chrome", "edge", "firefox", "browser"]
    app_lower = app.lower()
    
    if any(browser in app_lower for browser in browser_keywords):
        print(f"[INFO] Skipping close for browser '{app}' - needed for speech recognition")
        return True  # Return success but don't close
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)  # Attempt to close the app.
            return True  # Indicate success.
        except:
            return False # Indicate failure.
        
# Function to execute system-level commands.
def System(command):

    # Nested function to mute the system volume.
    def mute():
        keyboard.press_and_release("volume mute")  # Simulate the mute key press.

    # Nested function to unmute the system volume.
    def unmute():
        keyboard.press_and_release("volume mute")  # Simulate the unmute key press.

    # Nested function to increase the system volume.
    def volume_up():
        keyboard.press_and_release("volume up")  # Simulate the volume up key press.

    # Nested function to decrease the system volume.
    def volume_down():
        keyboard.press_and_release("volume down")  # Simulate the volume down key press.

    # Nested function to shutdown the PC.
    def shutdown():
        subprocess.run(['shutdown', '/s', '/t', '0'], shell=False)  # Shutdown immediately.

    # Nested function to restart the PC.
    def restart():
        subprocess.run(['shutdown', '/r', '/t', '0'], shell=False)  # Restart immediately.

    # Nested function to lock the PC.
    def lock():
        subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], shell=False)  # Lock the PC.

    # Nested function to put the PC to sleep.
    def sleep_pc():
        subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0', '1', '0'], shell=False)  # Sleep mode.

    # Nested function to hibernate the PC.
    def hibernate():
        subprocess.run(['shutdown', '/h'], shell=False)  # Hibernate the PC.

    # Nested function to log off the current user.
    def logoff():
        subprocess.run(['shutdown', '/l'], shell=False)  # Log off.

    # Execute the appropriate command.
    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()
    elif command == "shutdown":
        shutdown()
    elif command == "restart":
        restart()
    elif command == "lock":
        lock()
    elif command == "sleep":
        sleep_pc()
    elif command == "hibernate":
        hibernate()
    elif command in ["log off", "logoff"]:
        logoff()
    else:
        print(f"[WARNING] Unknown system command: '{command}'")

    return True  # Indicate success.
    
# Asynchronous Function to translate and execute user command.
async def TranslateAndExecute(commands: list[str]):

    funcs = []  # List to store asynchronous tasks.

    for command in commands:

        if command.startswith("open "):  # Handel "open" commands.

            if "open it" in command:  # Ignore "open it" commands.
                print(f"[SKIP] Ignoring command: '{command}'")  # Debug: Show skipped command
                pass

            elif "open file" == command:  # Ignore "open file" commands.
                print(f"[SKIP] Ignoring command: '{command}'")  # Debug: Show skipped command
                pass

            else:
                app_name = command.removeprefix("open ").strip()
                acknowledgment = f"Ok sir, I will open {app_name}."
                print(f"[AUTOMATION] Processing open command: '{command}'")  # Debug: Show command being processed
                TextToSpeech(acknowledgment)  # Speak acknowledgment
                fun = asyncio.to_thread(OpenApp, app_name)  # Schedule app opening.
                funcs.append(fun)

        elif command.startswith("general "):  # Placeholder for general commands.
            pass

        elif command.startswith("realtime "):  # Placeholder for real-time commands.
            pass

        elif command.startswith("close "):  # Handle "close" commands.
            app_name = command.removeprefix("close ").strip()
            acknowledgment = f"Ok sir, closing {app_name}."
            TextToSpeech(acknowledgment)  # Speak acknowledgment
            fun = asyncio.to_thread(CloseApp, app_name)  # Schedule app closing.
            funcs.append(fun)

        elif command.startswith("play "):  # Handel "play" commands.
            video_query = command.removeprefix("play ").strip()
            acknowledgment = f"Ok sir, playing {video_query} on YouTube."
            TextToSpeech(acknowledgment)  # Speak acknowledgment
            fun = asyncio.to_thread(PlayYouTube, video_query)  # Schedule YouTube playback.
            funcs.append(fun)

        elif command.startswith("content "):  # Handel "content" commands.
            content_request = command.removeprefix("content ").strip()
            acknowledgment = f"Ok sir, I'll write {content_request} for you."
            TextToSpeech(acknowledgment)  # Speak acknowledgment
            fun = asyncio.to_thread(Content, content_request)  # Schedule content creation.
            funcs.append(fun)

        elif command.startswith("google search "):  # Handle "google search" commands.
            search_query = command.removeprefix("google search ").strip()
            acknowledgment = f"Ok sir, searching Google for {search_query}."
            TextToSpeech(acknowledgment)  # Speak acknowledgment
            fun = asyncio.to_thread(GoogleSearch, search_query)  # Schedule Google search.
            funcs.append(fun)

        elif command.startswith("youtube search "): # Handle "youtube search" commands.
            search_query = command.removeprefix("youtube search ").strip()
            acknowledgment = f"Ok sir, searching YouTube for {search_query}."
            TextToSpeech(acknowledgment)  # Speak acknowledgment
            fun = asyncio.to_thread(YouTubeSearch, search_query)  # Schedule YouTube search.
            funcs.append(fun)

        elif command.startswith("system "):  # Handel system commands.
            system_action = command.removeprefix("system ").strip()
            # Custom acknowledgments for different system actions
            if system_action in ["shutdown", "restart"]:
                acknowledgment = f"Ok sir, I will {system_action} the computer now."
            elif system_action == "lock":
                acknowledgment = f"Ok sir, locking your computer."
            elif system_action in ["sleep", "hibernate"]:
                acknowledgment = f"Ok sir, putting the computer to {system_action} mode."
            elif "volume" in system_action:
                acknowledgment = f"Ok sir, adjusting volume."
            elif system_action in ["mute", "unmute"]:
                acknowledgment = f"Ok sir, I'll {system_action} the system."
            elif "log" in system_action:
                acknowledgment = f"Ok sir, logging off."
            else:
                acknowledgment = f"Ok sir, executing {system_action} command."
            
            TextToSpeech(acknowledgment)  # Speak acknowledgment
            fun = asyncio.to_thread(System, system_action)  # Schedule system command.
            funcs.append(fun)

        elif command == "skip ads":  # Handle "skip ads" command.
            acknowledgment = f"Ok sir, I'll skip the ads for you."
            TextToSpeech(acknowledgment)  # Speak acknowledgment
            fun = asyncio.to_thread(SkipYouTubeAds)  # Schedule YouTube ad skipping.
            funcs.append(fun)

        else:
            print(f"No Function Found. For {command}")  # Print an error for unrecognized commands.

    results = await asyncio.gather(*funcs)  # Execute all tasks concurrently.

    for result in results:  # Process the results.
        if isinstance(result, str):
            yield result
        else:
            yield result

# Asynchronous function to automate command execution.
async def Automation(commands: list[str]):

    async for result in TranslateAndExecute(commands):  # Translate and execute commands.
        pass

    return True  # Indicate success.
