import speech_recognition as sr
import webbrowser
import pyttsx3  # Not strictly used, but kept for context
import musicLibrary
import requests
from openai import OpenAI
from gtts import gTTS
import pygame
import os

# --- Configuration ---
# IMPORTANT: Replace these with your actual keys
newsapi = "<Your Key Here>"
openai_api_key = "<Your Key Here>"

# Initialize Recognizer only once
recognizer = sr.Recognizer()
engine = pyttsx3.init()


def speak_old(text):
    # This function is redundant, but maintained to avoid changing your script structure
    engine.say(text)
    engine.runAndWait()


def speak(text):
    if not text:
        return

    tts = gTTS(text, lang='en')
    temp_file = 'temp.mp3'
    tts.save(temp_file)

    # Initialize Pygame mixer
    pygame.mixer.init()

    # Load the MP3 file
    pygame.mixer.music.load(temp_file)

    # Play the MP3 file
    pygame.mixer.music.play()

    # Keep the program running until the music stops playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # Clean up
    pygame.mixer.music.unload()
    os.remove(temp_file)


def aiProcess(command):
    # Use the local variable for the API key here
    client = OpenAI(api_key=openai_api_key)

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a virtual assistant named Jarvis skilled in general tasks like Alexa and Google Cloud. Give short, concise responses please"},
                {"role": "user", "content": command}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "Sorry, I couldn't connect to the AI service right now."


def processCommand(c):
    c_lower = c.lower()

    if "open google" in c_lower:
        webbrowser.open("https://google.com")
        speak("Opening Google.")
    elif "open facebook" in c_lower:
        webbrowser.open("https://facebook.com")
        speak("Opening Facebook.")
    elif "open youtube" in c_lower:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube.")
    elif "open linkedin" in c_lower:
        webbrowser.open("https://linkedin.com")
        speak("Opening LinkedIn.")

    # --- MUSIC PLAY COMMAND FIX ---
    elif c_lower.startswith("play") or ("jarvis" in c_lower and "play" in c_lower):
        # 1. Remove common command words to isolate the song name
        # We strip the full "jarvis" and "play" words from the command, then clean up spaces
        command_phrase = c_lower.replace("jarvis", "").replace("play", "").strip()

        # 2. Look up the resulting phrase in the music dictionary
        if command_phrase in musicLibrary.music:
            link = musicLibrary.music[command_phrase]
            webbrowser.open(link)
            speak(f"Playing {command_phrase}.")
        else:
            # 3. If the direct lookup fails, inform the user
            speak(f"Sorry, I don't have a song called {command_phrase} in the library. Try saying stealth or march.")

    elif "news" in c_lower:
        speak("Fetching today's top headlines.")
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}")
            if r.status_code == 200:
                data = r.json()
                articles = data.get('articles', [])

                # Speak only the top 3 headlines
                speak(f"Here are the top {min(3, len(articles))} headlines:")
                for i, article in enumerate(articles):
                    if i < 3:
                        speak(article['title'])
                    else:
                        break
            else:
                speak("I'm having trouble connecting to the news service.")
        except Exception as e:
            print(f"News API Request Error: {e}")
            speak("I encountered an error while trying to get the news.")

    else:
        # Let OpenAI handle the request
        output = aiProcess(c)
        speak(output)


if __name__ == "__main__":
    speak("Initializing Jarvis....")

    # Set default Recognizer properties for better detection
    recognizer.pause_threshold = 0.8
    recognizer.energy_threshold = 500  # Set a reliable noise threshold

    while True:
        print("recognizing...")
        try:
            with sr.Microphone() as source:
                # 1. Ambient noise adjustment for wake word
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

                print("Listening for wake word 'Jarvis'...")
                # 2. More generous timeout for wake word
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=2)

                word = recognizer.recognize_google(audio)

                # --- WAKE WORD DETECTED ---
                if word.lower() == "jarvis":
                    speak("Ya")

                    with sr.Microphone() as source:
                        # 3. Ambient noise adjustment for command
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        print("Jarvis Active. Waiting for command...")

                        # 4. Generous timeout for command
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                        command = recognizer.recognize_google(audio)
                        print(f"Jarvis heard command: {command}")

                        # Process the recognized command
                        processCommand(command)

        # --- EXCEPTION HANDLING ---
        except sr.WaitTimeoutError:
            pass  # Keep silent if no wake word detected
        except sr.UnknownValueError:
            print("Error: Could not understand audio.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
