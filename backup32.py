import tkinter as tk
from tkinter import ttk, font
import pyttsx3
import speech_recognition as sr
from groq import Groq
import threading
import datetime
import sqlite3
import time

class VoiceAssistant:
    def __init__(self):
        self.setup_voice()
        self.setup_db()
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.groq_client = Groq(api_key="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")
        self.is_in_call = False
        self.last_response = ""
        self.setup_gui()
        self.greet()

    def setup_voice(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "female" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)

    def setup_db(self):
        self.conn = sqlite3.connect('assistant.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                            (id INTEGER PRIMARY KEY, date TEXT, time TEXT, 
                             description TEXT, completed BOOLEAN)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS appointments
                            (id INTEGER PRIMARY KEY, date TEXT, time TEXT, 
                             person TEXT, purpose TEXT)''')
        self.conn.commit()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("AI Call Assistant")
        self.root.geometry("1200x800")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Call button
        ttk.Button(main_frame, text="📞 Start Call", command=self.start_call,
                  style='Large.TButton').pack(pady=20)
        
        # Transcript area
        self.transcript = tk.Text(main_frame, height=30, font=('Arial', 12))
        self.transcript.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Info panels
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        
        # Reminders panel
        self.reminders_text = tk.Text(info_frame, height=10, width=40)
        self.reminders_text.pack(side=tk.LEFT, padx=5)
        
        # Appointments panel
        self.appointments_text = tk.Text(info_frame, height=10, width=40)
        self.appointments_text.pack(side=tk.RIGHT, padx=5)

    def speak(self, text):
        self.last_response = text
        self.engine.say(text)
        self.engine.runAndWait()

    def repeat_last_response(self):
        while self.is_in_call:
            if self.last_response:
                time.sleep(10)
                self.speak(self.last_response)

    def greet(self):
        self.speak("Hello! I'm your AI assistant. Press the call button to start.")

    def start_call(self):
        if not self.is_in_call:
            self.is_in_call = True
            self.speak("Starting call. How may I help you today?")
            threading.Thread(target=self.handle_call).start()
            threading.Thread(target=self.repeat_last_response).start()

    def handle_call(self):
        while self.is_in_call:
            try:
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio)
                    
                    if "bye" in text.lower():
                        self.speak("Thank you for calling. Goodbye!")
                        self.is_in_call = False
                        break
                    
                    if "reminder" in text.lower():
                        self.handle_reminder(text)
                    elif "appointment" in text.lower():
                        self.handle_appointment(text)
                    else:
                        response = self.process_input(text)
                        self.update_transcript(text, response)
                        self.speak(response)
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Error: {e}")

    def handle_reminder(self, text):
        response = self.process_input(f"Extract date, time and reminder details from: {text}")
        # Simple parsing for demo - could be enhanced
        self.cursor.execute('''INSERT INTO reminders (date, time, description, completed)
                            VALUES (?, ?, ?, ?)''', 
                            (datetime.datetime.now().date().isoformat(),
                             datetime.datetime.now().time().isoformat(),
                             text, False))
        self.conn.commit()
        self.speak(f"I've added your reminder: {text}")
        self.update_reminders_display()

    def handle_appointment(self, text):
        self.cursor.execute('''INSERT INTO appointments (date, time, person, purpose)
                            VALUES (?, ?, ?, ?)''',
                            (datetime.datetime.now().date().isoformat(),
                             datetime.datetime.now().time().isoformat(),
                             "Unknown", text))
        self.conn.commit()
        self.speak(f"I've scheduled your appointment: {text}")
        self.update_appointments_display()

    def update_reminders_display(self):
        self.reminders_text.delete(1.0, tk.END)
        self.cursor.execute("SELECT * FROM reminders WHERE completed = 0")
        for reminder in self.cursor.fetchall():
            self.reminders_text.insert(tk.END, f"{reminder[1]}: {reminder[3]}\n")

    def update_appointments_display(self):
        self.appointments_text.delete(1.0, tk.END)
        self.cursor.execute("SELECT * FROM appointments")
        for apt in self.cursor.fetchall():
            self.appointments_text.insert(tk.END, f"{apt[1]} - {apt[4]}\n")

    def process_input(self, text):
        messages = [
            {"role": "system", "content": "You are a professional call assistant. Handle reminders and appointments."},
            {"role": "user", "content": text}
        ]
        response = self.groq_client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192"
        )
        return response.choices[0].message.content

    def update_transcript(self, user_text, assistant_response):
        self.transcript.insert(tk.END, f"User: {user_text}\nAssistant: {assistant_response}\n\n")
        self.transcript.see(tk.END)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()