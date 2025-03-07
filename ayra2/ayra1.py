from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from flask import Flask, request, jsonify, render_template
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
from groq import Groq
import google.generativeai as genai

load_dotenv()

app = Flask(__name__, 
           template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')),
           static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')))

# Initialize credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
GROQ_API_KEY = "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"
GOOGLE_AI_KEY = "AIzaSyCedDzjEnI6hj1f8Nszm-l8z-o5rO7XCxg"

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
groq_client = Groq(api_key='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')
genai.configure(api_key='AIzaSyCedDzjEnI6hj1f8Nszm-l8z-o5rO7XCxg')

# Initialize speech recognition
recognizer = sr.Recognizer()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

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

Current call status: {context.get('call_status', 'N/A')}
Previous interaction context: {context.get('previous_context', 'None')}
'''

def text_to_speech(text, filename="response.mp3"):
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)
    playsound(filename)
    os.remove(filename)  # Clean up the file after playing

def process_ai_response(user_input, business_type, context):
    system_message = get_system_message(business_type, context)
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_input}
    ]
    
    response = groq_client.chat.completions.create(
        messages=messages,
        model="llama3-70b-8192"
    )
    
    return response.choices[0].message.content

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/incoming-call', methods=['POST'])
def handle_incoming_call():
    response = VoiceResponse()
    business_type = request.values.get('business_type', 'general')
    
    # Get business context from database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM call_settings 
        WHERE business_type = %s 
        LIMIT 1
    """, (business_type,))
    settings = cur.fetchone()
    cur.close()
    conn.close()
    
    context = {
        'business_type': business_type,
        'business_name': settings[1] if settings else 'our business',
        'working_hours': settings[4] if settings else 'standard business hours',
        'call_status': 'new_call'
    }
    
    gather = Gather(input='speech', timeout=3, action='/handle-response')
    gather.say(settings[3] if settings else "Welcome to our service. How may I assist you today?")
    response.append(gather)
    
    # Store call details
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO calls (call_sid, phone_number, direction)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (request.values.get('CallSid'),
          request.values.get('From'),
          'inbound'))
    call_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return str(response)

@app.route('/handle-response', methods=['POST'])
def handle_response():
    user_input = request.values.get('SpeechResult')
    call_sid = request.values.get('CallSid')
    business_type = request.values.get('business_type', 'general')
    
    # Get call context
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM calls WHERE call_sid = %s", (call_sid,))
    call_data = cur.fetchone()
    cur.close()
    conn.close()
    
    context = {
        'call_status': 'in_progress',
        'previous_context': call_data[5] if call_data else None
    }
    
    # Process with AI
    ai_response = process_ai_response(user_input, business_type, context)
    
    # Convert AI response to speech
    response = VoiceResponse()
    response.say(ai_response)
    
    # Store interaction
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE calls 
        SET transcription = CONCAT(transcription, %s),
            notes = CONCAT(notes, %s)
        WHERE call_sid = %s
    """, (f"\nUser: {user_input}\nAI: {ai_response}\n",
          f"\nInteraction recorded at {datetime.now()}\n",
          call_sid))
    conn.commit()
    cur.close()
    conn.close()
    
    return str(response)

@app.route('/make-call', methods=['POST'])
def make_outbound_call():
    data = request.json
    phone_number = data.get('phone_number')
    business_type = data.get('purpose', 'general')
    
    call = twilio_client.calls.create(
        url=f'{request.host_url}outbound-call-handler',
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        record=True
    )
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO calls (call_sid, phone_number, direction, category)
        VALUES (%s, %s, %s, %s)
    """, (call.sid, phone_number, 'outbound', business_type))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'status': 'success', 'call_sid': call.sid})

@app.route('/call-history', methods=['GET'])
def get_call_history():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM calls 
        ORDER BY timestamp DESC 
        LIMIT 50
    """)
    calls = cur.fetchall()
    cur.close()
    conn.close()
    
    return jsonify([{
        'timestamp': call[7],
        'direction': call[3],
        'phone_number': call[2],
        'duration': call[6],
        'recording_url': call[4]
    } for call in calls])

if __name__ == "__main__":
    app.run(debug=True, port=5001) 