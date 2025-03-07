from groq import Groq
from PIL import Image, ImageGrab
import cv2
import pyperclip
import google.generativeai as genai
import pyaudio
import speech_recognition as sr  # Importing speech recognition
from gtts import gTTS  # Import Google Text-to-Speech (gTTS)
import os
import time
from playsound import playsound

# Initialize Speech Recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

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
safety_settings = [
    {
        'category': 'HARM_CATEGORY_HARASSMENT',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_HATE_SPEECH',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        'threshold': 'BLOCK_NONE'
    },
    {
        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
        'threshold': 'BLOCK_NONE'
    }
]

model = genai.GenerativeModel('gemini-1.5-flash-latest',
                            generation_config=generation_config,
                            safety_settings=safety_settings)

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
              'taking a screenshot, capturing the webcam or calling no functions is best for a voice assistant to respond '
              'to the users prompt. The webcam can be assumed to be a normal laptop webcam facing the user. You will '
              'respond with only one selection from this list:("extract clipboard","take screen shot","capture webcam", "None") \n '
              'Do not respond with anything but the most logical selection from that list With no explanations, Format the '
              'function call name exactly as I listed.')

    function_convo = [{'role': 'system', 'content': sys_msg},
                     {'role': 'user', 'content': prompt}]
    chat_completion = groq_client.chat.completions.create(messages=function_convo, model='llama3-70b-8192')
    response = chat_completion.choices[0].message
    return response.content

def take_screenshot():
    path = 'screenshot.jpg'
    screenshot = ImageGrab.grab()
    rgb_screenshot = screenshot.convert('RGB')
    rgb_screenshot.save(path, quality=15)

def web_cam_capture():
    if not web_cam.isOpened():
        print("Unable to open camera")
        exit()

    path = 'webcam.jpg'
    ret, frame = web_cam.read()
    cv2.imwrite(path, frame)

def get_clipboard_text():
    clipboard_content = pyperclip.paste()
    if isinstance(clipboard_content, str):
        return clipboard_content
    else:
        print('No clipboard')
        return None

def vision_prompt(prompt, photo_path):
    img = Image.open(photo_path)
    prompt = (
        'You are the vision analysis AI that provides semantic meaning from images to provide context '
        'to send to another AI that will create a response to the user. Do not respond as an AI assistant '
        'to the user. Instead take the user prompt input and try to extract all meaning from the photo '
        'relevant to the user prompt, then create or generate as much objective data about the image from the photo. '
        f'Assistant, who will respond to user.\n USER: {prompt} '
    )
    response = model.generate_content([prompt, img])
    return response.text

def text_to_speech(response_text):
    """
    Convert the AI's response to speech and speak it aloud using Google Text-to-Speech (gTTS).
    """
    try:
        tts = gTTS(text=response_text, lang='en', slow=False, tld='com.au')  # Using Australian English which is faster
        tts.save("response.mp3")
        playsound("response.mp3")  # Directly play the MP3 file without opening the media player
    except Exception as e:
        print(f"Error in Text-to-Speech conversion: {e}")

def listen_to_input():
    """
    Listens for a voice command after the assistant greets the user with 'hi.'
    Keeps listening after a short pause.
    """
    with mic as source:
        print("Listening for user input...")
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust for ambient noise with 1 second duration
        audio = recognizer.listen(source, timeout=5)  # Increased timeout for listening
    try:
        user_input = recognizer.recognize_google(audio)  # Recognize speech using Google's API
        print(f"User said: {user_input}")
        return user_input
    except sr.UnknownValueError:
        print("Sorry, I could not understand what you said.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

def main():
    # Greet the user first
    text_to_speech("Hi, I am Shiva's AI Ayra. How can I assist you today?")
    
    while True:
        user_input = listen_to_input()  # Listen for user's input after greeting
        if user_input:
            prompt = user_input
            call = function_call(prompt)

            if 'take screen shot' in call:
                print('Taking screenshot')
                take_screenshot()
                visual_context = vision_prompt(prompt=prompt, photo_path='screenshot.jpg')
            elif 'capture webcam' in call:
                print('Capturing webcam')
                web_cam_capture()
                visual_context = vision_prompt(prompt=prompt, photo_path='webcam.jpg')
            elif 'extract clipboard' in call:
                print('Extracting clipboard')
                paste = get_clipboard_text()
                prompt = f'{prompt}\n\n CLIPBOARD CONTENT: {paste}'
                visual_context = None
            else:
                visual_context = None
                
            response = groq_prompt(prompt=prompt, img_context=visual_context)
            print(f"AI: {response}")
            text_to_speech(response)

# Initialize Flask
app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

# Modified system message template
def get_system_message(business_type, context):
    return f'''You are an AI call center assistant for a {business_type}. 
Current context: {context}
Business hours: {context.get('working_hours', 'N/A')}
Special instructions: {context.get('special_instructions', 'N/A')}

Your role is to:
1. Maintain a professional and courteous tone
2. Handle {business_type}-specific inquiries
3. Follow conversation flow based on caller responses
4. Collect relevant information
5. Provide accurate information about {context.get('business_name', 'our business')}
6. Handle scheduling and inquiries appropriately

Remember to:
- Stay within the scope of your role
- Be clear and concise
- Ask for clarification when needed
- Follow up on important details
- Maintain HIPAA compliance for medical contexts
- Document important information

Current call status: {{call_status}}
Previous interaction context: {{previous_context}}
'''

# Call handling routes
@app.route('/incoming-call', methods=['POST'])
def handle_incoming_call():
    response = VoiceResponse()
    gather = Gather(input='speech dtmf', timeout=3, num_digits=1)
    gather.say("Welcome to our service. How may I assist you today?")
    response.append(gather)
    
    # Store call details in database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO calls (call_sid, phone_number, direction)
        VALUES (%s, %s, %s)
        """, (request.values.get('CallSid'),
              request.values.get('From'),
              'inbound'))
    conn.commit()
    cur.close()
    conn.close()
    
    return str(response)

@app.route('/make-call', methods=['POST'])
def make_outbound_call():
    data = request.json
    phone_number = data.get('phone_number')
    purpose = data.get('purpose')
    
    call = client.calls.create(
        url=f'{request.host_url}outbound-call-handler',
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER
    )
    
    # Store call details
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO calls (call_sid, phone_number, direction, category)
        VALUES (%s, %s, %s, %s)
        """, (call.sid, phone_number, 'outbound', purpose))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'status': 'success', 'call_sid': call.sid})

# Call recording and transcription
@app.route('/call-recording', methods=['POST'])
def handle_recording():
    recording_url = request.values.get('RecordingUrl')
    call_sid = request.values.get('CallSid')
    
    # Store recording URL
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE calls 
        SET recording_url = %s
        WHERE call_sid = %s
        """, (recording_url, call_sid))
    conn.commit()
    cur.close()
    conn.close()
    
    # Transcribe recording using existing speech recognition
    transcription = transcribe_audio(recording_url)
    store_transcription(call_sid, transcription)
    
    return jsonify({'status': 'success'})

def transcribe_audio(audio_url):
    # Use existing speech recognition code
    recognizer = sr.Recognizer()
    # Download and process audio file
    # Return transcription
    pass

def store_transcription(call_sid, transcription):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE calls 
        SET transcription = %s
        WHERE call_sid = %s
        """, (transcription, call_sid))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True)
