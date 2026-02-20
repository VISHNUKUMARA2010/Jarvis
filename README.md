# Jarvis

## Overview
Jarvis is an advanced AI assistant designed to help users automate tasks, answer questions, generate images, perform real-time searches, and interact via both text and voice. It combines multiple AI and automation technologies to provide a seamless, user-friendly experience.

## Features
- **Conversational AI Chatbot:** Engage in natural language conversations for information, assistance, and entertainment.
- **Voice Interaction:** Use speech-to-text and text-to-speech for hands-free operation.
- **Image Generation:** Create images from text prompts using integrated AI models.
- **Automation:** Automate repetitive tasks and workflows.
- **Learning System:** Learns from user interactions to improve responses and suggestions.
- **Real-Time Search Engine:** Fetches up-to-date information from the internet.
- **GUI and Headless Modes:** Run with a graphical interface or in the background.
- **Logging and Data Storage:** Maintains logs and stores user preferences, chat history, and learning data.

## How It Works
1. **Startup:**
   - Launch using `Run_with_GUI.bat` for the graphical interface or `Run_Headless.bat` for background operation.
   - The application initializes all backend modules, loads user data, and prepares the AI models.

2. **User Interaction:**
   - Users can interact via the GUI or through voice commands.
   - The chatbot processes input, generates responses, and can trigger automation or image generation as needed.

3. **Backend Processing:**
   - The backend handles AI model inference, automation scripts, and data management.
   - Real-time search and learning modules enhance the assistant's capabilities.

4. **Data Management:**
   - All interactions, preferences, and learning data are stored in the `Data/` folder for persistent, personalized experiences.

## File Structure
- **Main.py:** Entry point for the application.
- **Backend/:** Core logic for AI, automation, and learning.
- **Frontend/:** GUI components and user interface files.
- **Data/:** Stores chat logs, preferences, and learning memory.
- **config.py, app_paths.py, path_helper.py:** Configuration and path management.
- **Run_with_GUI.bat / Run_Headless.bat:** Scripts to launch the assistant.

## Getting Started
1. Install required dependencies from `Requirements.txt`.
2. Run `Run_with_GUI.bat` or `Run_Headless.bat`.
3. Interact with Jarvis via the GUI or voice.

## Customization
- Add or modify automation scripts in `Backend/Automation.py`.
- Update learning and preferences in the `Data/` folder.
- Adjust configuration in `config.py` as needed.

## Support
For troubleshooting, check the logs in the `logs/` folder or run `view_startup_logs.py`.

## Credits
Developed by the Vishnu Kumar.

---
*This project is inspired by the vision of creating a personal AI assistant like Jarvis from Iron Man, tailored for real-world productivity and automation.*
