import pygame  # Import pygame library for handling audio playback.
import random  # Import random library for generating random choices.
import asyncio  # Import asyncio for asynchronous operations.
import edge_tts  # Import edge_tts for text-to-speech functionality.
import os  # Import os for file path handling 
import config  # Import configuration file with hardcoded settings
import app_paths  # Import for correct file paths

# Load configuration from config.py
AssistantVoice = config.ASSISTANT_VOICE

# Asynchronous function to convert text to an audio file
async def TextToAudioFile(text) -> None:
    file_path = app_paths.get_data_path("speech.mp3")  # Define the path where the speech file will be saved 

    # Try to remove existing file with retry logic
    if os.path.exists(file_path):  # Check if the file already exists
        for attempt in range(3):  # Try up to 3 times
            try:
                os.remove(file_path)  # If it exists, remove it to avoid overwriting errors
                break
            except PermissionError:
                if attempt < 2:  # If not last attempt
                    await asyncio.sleep(0.1)  # Wait a bit and retry
                else:
                    pass  # On last attempt, let it create a new file anyway

    # Create the communicator object to generate speech with retry logic for network issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+25%')
            await communicate.save(r'Data\speech.mp3')  # Save the generated speech as an MP3 file
            break  # Success, exit retry loop
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[TTS] Connection attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(1)  # Wait before retry
            else:
                raise  # Re-raise the exception if all retries failed

# Function to manage Text-To-Speech (TTS) functionality
def TTS(Text, func=lambda r=None: True):
    mixer_initialized = False  # Track if mixer was initialized
    max_attempts = 2  # Try twice before giving up
    
    for attempt in range(max_attempts):
        try:
            # Convert text to an audio file asynchronously
            asyncio.run(TextToAudioFile(Text))

            # Initialize pygame mixer for audio playback
            pygame.mixer.init()
            mixer_initialized = True  # Mark as initialized

            # Load the generated speech file into pygame mixer
            pygame.mixer.music.load(r'Data\speech.mp3')
            pygame.mixer.music.play()  # Play the audio

            # Loop until the audio is done playing or the function stops 
            while pygame.mixer.music.get_busy():
                if func() == False:  # Check if the external function returns False
                    break
                pygame.time.Clock().tick(20)  # Increase tick rate for more responsive playback

            return True  # Return True if the audio played successfully
        
        except Exception as e:  # Handle any exceptions during the process
            print(f"Error in TTS (attempt {attempt + 1}/{max_attempts}): {e}")  # Print the error message
            if attempt == max_attempts - 1:
                print(f"[TTS] Failed to generate speech after {max_attempts} attempts. Check your internet connection.")
                return False  # Return False if all attempts failed

        finally:
            try:
                # Only cleanup if mixer was initialized
                if mixer_initialized and pygame.mixer.get_init():
                    pygame.mixer.music.stop()  # Stop the audio playback
                    pygame.mixer.quit()  # Quit the pygame mixer
                # Call the provided function with False to signal the end of TTS
                func(False)

            except Exception as e:  # Handle any exceptions during cleanup
                # Only print error if it's not about mixer not being initialized
                if "mixer not initialized" not in str(e).lower():
                    print(f"Error in finally block: {e}")

# Function to manage Text-To-Speech with additional response for long text
def TextToSpeech(Text, func=lambda r=None: True):
    Data = str(Text).split(".")  # Split the text by periods into a list of sentences

    # List of predefined responses for cases where the text is too long 
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]

    # If the text is very long (more than 4 sentences and 250 characters), add a response message 
    if len(Data) > 4 and len(Text) > 250:
        TTS("".join(Text.split(".")[0:2]) + ". " + random.choice(responses), func)

        # Otherwise, just play the whole text 
    else:
        TTS(Text, func)

# Main execution loop
if __name__ == "__main__":

    while True:
        # Prompt user for input and pass it to TextToSpeech function
        TextToSpeech(input("Enter the text:"))
