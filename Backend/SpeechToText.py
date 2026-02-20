from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import os
import mtranslate as mt 
from time import sleep
import config  # Import configuration file with hardcoded settings
import app_paths  # Import for correct file paths

# Load configuration from config.py
InputLanguage = config.INPUT_LANGUAGE

# Define the HTML code for the speech recognition interface.
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            recognition.stop();
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

# Replace the language setting in the HTML code with the input language from the environment variables.
HtmlCode = str(HtmlCode).replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# Write the modified HTML code to a file in Frontend/Files (better for browser access)
voice_html_path = app_paths.get_frontend_files_path("Voice.html")
with open(voice_html_path, "w") as f:
    f.write(HtmlCode)

# Generate the file path for the HTML file.
Link = f"file:///{voice_html_path.replace(os.sep, '/')}"

def initialize_browser():
    """
    Initialize a WebDriver with automatic fallback across multiple browsers.
    Tries Chrome -> Edge -> Firefox in order.
    Returns (driver, browser_name) or (None, None) if all fail.
    """
    
    # Try Chrome first
    try:
        print("[INFO] Attempting to initialize Chrome WebDriver...")
        chrome_options = ChromeOptions()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        driver = webdriver.Chrome(options=chrome_options)
        print("[INFO] ✓ Chrome WebDriver initialized successfully!")
        return driver, "Chrome"
    except Exception as e:
        print(f"[WARNING] Chrome not available: {e}")
    
    # Try Edge as fallback (pre-installed on Windows 10/11)
    try:
        print("[INFO] Attempting to initialize Edge WebDriver...")
        edge_options = EdgeOptions()
        edge_options.add_argument("--use-fake-ui-for-media-stream")
        edge_options.add_argument("--headless=new")
        edge_options.add_argument("--log-level=3")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Edge(options=edge_options)
        print("[INFO] ✓ Edge WebDriver initialized successfully!")
        return driver, "Edge"
    except Exception as e:
        print(f"[WARNING] Edge not available: {e}")
    
    # Try Firefox as final fallback
    try:
        print("[INFO] Attempting to initialize Firefox WebDriver...")
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        firefox_options.set_preference("media.navigator.permission.disabled", True)
        firefox_options.set_preference("permissions.default.microphone", 1)
        
        driver = webdriver.Firefox(options=firefox_options)
        print("[INFO] ✓ Firefox WebDriver initialized successfully!")
        return driver, "Firefox"
    except Exception as e:
        print(f"[WARNING] Firefox not available: {e}")
    
    # All browsers failed
    print("[ERROR] ================================================")
    print("[ERROR] Could not initialize any browser!")
    print("[ERROR] Tried: Chrome, Edge, Firefox")
    print("[ERROR] Please install at least one of these browsers:")
    print("[ERROR]   - Google Chrome (recommended)")
    print("[ERROR]   - Microsoft Edge (pre-installed on Windows)")
    print("[ERROR]   - Mozilla Firefox")
    print("[ERROR] ================================================")
    return None, None

# Initialize the WebDriver with automatic browser detection
driver = None
browser_name = None
try:
    print("[INFO] Initializing WebDriver for speech recognition...")
    driver, browser_name = initialize_browser()
    if driver:
        print(f"[INFO] ✓ Speech recognition is ready using {browser_name}!")
    else:
        print("[ERROR] ✗ Speech recognition will not work - no compatible browser found.")
except Exception as e:
    print(f"[ERROR] ✗ Failed to initialize WebDriver: {e}")
    print("[ERROR] ✗ Speech recognition will not work.")
    driver = None
    browser_name = None

# Define the path for temporary files.
TempDirPath = app_paths.FRONTEND_FILES_DIR

# Function to set the assistant's status by writing it to a file.
def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, 'Status.data'), "w", encoding='utf-8') as file:
        file.write(Status)

# Function to modify a query to ensue proper punctuation and formatting.
def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["who", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "how's", "can you"]

    # Check if the query is a question and add a question mark is needed.
    if any(word + "" in new_query for word in question_words):
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        # Add a period if the query is not a question.
        if query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()
    
# Function to translate text into English using the mtranslate library.
def UniversalTranalator(Text):
        english_translation = mt.translate(Text, "en", "auto")
        return english_translation.capitalize()
    
# Function to perforam speech recognition using the webdriver.
def SpeechRecognition():
    from datetime import datetime
    
    # Check if driver is initialized
    if driver is None:
        print("[ERROR] WebDriver not available. Cannot perform speech recognition.")
        print("[ERROR] Jarvis cannot listen without a compatible browser. Please install Chrome, Edge, or Firefox and restart.")
        return "error: speech recognition unavailable"
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] ========== STARTING SPEECH RECOGNITION ==========")
    
    # First, listen for wake word "Jarvis"
    try:
        print(f"[{timestamp}] Step 1: Loading speech recognition page...")
        print(f"[{timestamp}] URL: {Link}")
        driver.get(Link)
        print(f"[{timestamp}] Step 2: Starting microphone...")
        driver.find_element(by=By.ID, value="start").click()
        SetAssistantStatus("Waiting for wake word... Say 'Jarvis'")
        print(f"[{timestamp}] [OK] Microphone is ON - Listening for wake word 'Jarvis'")
        print(f"[{timestamp}] >> SPEAK NOW: Say 'Jarvis' clearly into your microphone!")
    except Exception as e:
        print(f"[ERROR] Failed to start speech recognition: {e}")
        print(f"[ERROR] Voice.html path: {Link}")
        return "error: failed to start recognition"

    wake_word_detected = False
    check_count = 0  # Counter to track attempts
    last_heartbeat = 0
    
    # Wake word detection loop
    while not wake_word_detected:
        try:
            Text = driver.find_element(by=By.ID, value="output").text
            
            if Text:
                check_count += 1
                # Check if wake word is present
                text_lower = Text.lower().strip()
                
                # More flexible wake word matching
                if "jarvis" in text_lower or "jarvis" in text_lower.replace(" ", ""):
                    wake_word_detected = True
                    driver.find_element(by=By.ID, value="end").click()
                    SetAssistantStatus("Wake word detected! Listening for command...")
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] *** WAKE WORD DETECTED: '{Text}' ***")
                    print(f"[{timestamp}] Now listening for your command...")
                    sleep(0.5)
                else:
                    # Show what was heard for debugging
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Heard: '{Text}' (not 'Jarvis', resetting...)")
                    # Reset if wrong word detected
                    driver.find_element(by=By.ID, value="end").click()
                    sleep(0.3)
                    driver.find_element(by=By.ID, value="start").click()
                    print(f"[{timestamp}] >> Listening again... Say 'Jarvis'")
            else:
                # Heartbeat message every 30 checks to show it's still listening
                check_count += 1
                if check_count % 30 == 0:
                    last_heartbeat = check_count
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Still listening... (microphone active, say 'Jarvis')")
                    
        except Exception as e:
            sleep(0.1)  # Slightly longer sleep to avoid excessive CPU usage
    
    # Now listen for the actual command
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] ========== LISTENING FOR COMMAND ==========")
    driver.get(Link)
    driver.find_element(by=By.ID, value="start").click()
    SetAssistantStatus("Listening...")
    print(f"[{timestamp}] >> Speak your command now!")

    while True:
        try:
            # Get the recognized text from the HTML output element.
            Text = driver.find_element(by=By.ID, value="output").text

            if Text:
                # Stop recognition by clicking the stop button.
                driver.find_element(by=By.ID, value="end").click()
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] [OK] Command recognized: '{Text}'")

                # If the input language is English, return the modified query.
                if InputLanguage.lower() == "en" or "en" in InputLanguage.lower():
                    SetAssistantStatus("")
                    result = QueryModifier(Text)
                    print(f"[{timestamp}] [OK] Returning command: '{result}'")
                    print(f"[{timestamp}] =================================================\n")
                    return result
                else:
                    # If the input language is not English, translate the text and return it.
                    SetAssistantStatus("Translating...")
                    print(f"[{timestamp}] Translating to English...")
                    result = QueryModifier(UniversalTranalator(Text))
                    print(f"[{timestamp}] [OK] Translated: '{result}'")
                    print(f"[{timestamp}] =================================================\n")
                    return result
                    
        except Exception as e:
            sleep(0.05)

# Main execution block.
if __name__ == "__main__":
    while True:
        # Continuously perform speech recognition and print the recognized text.
        Text = SpeechRecognition()
        print(Text)
