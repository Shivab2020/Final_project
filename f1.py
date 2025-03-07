import tkinter as tk
from tkinter import ttk
from groq import Groq
from PIL import Image, ImageGrab
import cv2
import pyperclip
import google.generativeai as genai
import pyttsx3
import speech_recognition as sr

# Initialize TTS with pyttsx3
engine = pyttsx3.init()
def text_to_speech(response_text):
    """
    Convert the AI's response to speech and speak it aloud using female voice.
    """
    try:
        engine.setProperty('voice', 'com.apple.speech.synthesis.voice.karen')
        engine.say(response_text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in Text-to-Speech conversion: {e}")

# Initialize Speech Recognition
recognizer = sr.Recognizer()
mic = sr.Microphone(device_index=None)  # Use default PC microphone

genai.configure(api_key='AIzaSyCedDzjEnI6hj1f8Nszm-l8z-o5rO7XCxg')
web_cam = cv2.VideoCapture(0)
groq_client = Groq(api_key="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")

sys_msg = (
    'You are a multi-modal AI voice assistant. Your user may or may not have attached a photo for context '
    '(either screenshot or a webcam capture). Any photo has already been processed into highly detailed '
    'text prompt that will be attached to their transcribed voice prompt. Generate useful and '
    'factual responses, carefully considering all previous context in your response before '
    'adding new tokens. Do not expect request images, just use the context if added. '
    'Use all of the context of this conversation so your response is relevant. Make '
    'your response clear and concise, avoiding any verbosity.'
)
convo = [{'role': 'system', 'content': sys_msg}]  # Start the conversation context

generation_config = {
    'temperature': 0.7,
    'top_p': 1,
    'top_k': 1,
    'max_output_tokens': 2048
}

def groq_prompt(prompt, img_context):
    if img_context:
        prompt = f'USER PROMPT: {prompt}\n\n IMAGE CONTEXT: {img_context}'
    convo.append({'role': 'user', 'content': prompt})    
    chat_completion = groq_client.chat.completions.create(messages=convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message
    convo.append(response)
    return response.content

def function_call(prompt):
    sys_msg = ('You are an AI function calling model. You will determine whether extracting the users clipboard content, '
               'taking a screenshot, capturing the webcam, or calling no functions is best for a voice assistant to respond '
               'to the users prompt. You will respond with only one selection from this list:("extract clipboard","take screen shot","capture webcam", "None")')
    function_convo = [{'role': 'system', 'content': sys_msg},
                      {'role': 'user', 'content': prompt}]
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message
    return response.content

def take_screenshot():
    path = 'screenshot.jpg'
    screenshot = ImageGrab.grab()
    screenshot.convert('RGB').save(path, quality=15)

def web_cam_capture():
    if not web_cam.isOpened():
        print("Unable to open camera")
        return
    ret, frame = web_cam.read()
    cv2.imwrite('webcam.jpg', frame)

def get_clipboard_text():
    return pyperclip.paste()

def listen_to_input():
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=3)
            user_input = recognizer.recognize_google(audio)
            print(f"User said: {user_input}")
            return user_input.lower()
        except sr.UnknownValueError:
            return "I didn't catch that. Please repeat."
        except sr.WaitTimeoutError:
            return None

def main():
    root = tk.Tk()
    root.title("AI Assistant")
    root.geometry("800x600")

    transcription_area = tk.Text(root, height=20, width=80, wrap='word')
    transcription_area.pack()

    def update_gui(text):
        transcription_area.insert(tk.END, f"{text}\n")
        transcription_area.see(tk.END)

    update_gui("Hi, I am Shiva's AI Ayra. How can I assist you today?")
    text_to_speech("Hi, I am Shiva's AI Ayra. How can I assist you today?")
    
    while True:
        user_input = listen_to_input()
        if user_input:
            update_gui(f"User: {user_input}")
            if "bye" in user_input:
                update_gui("Goodbye!")
                text_to_speech("Goodbye!")
                break
            
            call = function_call(user_input)
            if 'take screen shot' in call:
                take_screenshot()
                visual_context = 'screenshot.jpg'
            elif 'capture webcam' in call:
                web_cam_capture()
                visual_context = 'webcam.jpg'
            elif 'extract clipboard' in call:
                clipboard_text = get_clipboard_text()
                user_input += f"\nCLIPBOARD CONTENT: {clipboard_text}"
                visual_context = None
            else:
                visual_context = None

            response = groq_prompt(user_input, visual_context)
            update_gui(f"Ayra: {response}")  # Display response in GUI before speaking
            text_to_speech(response)

    root.mainloop()

if __name__ == "__main__":
    main()
