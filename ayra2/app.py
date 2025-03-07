from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, session
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
from dotenv import load_dotenv
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import json
from groq import Groq
import speech_recognition as sr
from gtts import gTTS
import tempfile
from functools import wraps
import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
from werkzeug.security import generate_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
GROQ_API_KEY = os.getenv('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')

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'callcenter')
}

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
groq_client = Groq(api_key='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')

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_business_context(business_type):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM business_contexts 
        WHERE business_type = %s 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (business_type,))
    context = cur.fetchone()
    cur.close()
    conn.close()
    return dict(zip(['id', 'business_type', 'business_name', 'working_hours', 'special_instructions'], context))

def get_system_message(business_type, context):
    templates = {
        'hospital': '''You are an AI medical call center assistant. Your role is to:
1. Schedule medical appointments
2. Handle emergency triage (direct to 911 if immediate emergency)
3. Answer basic medical facility questions
4. Collect patient information with HIPAA compliance
5. Provide directions and working hours
6. Handle insurance-related queries

Current hospital context:
- Hospital name: {business_name}
- Working hours: {working_hours}
- Special instructions: {special_instructions}

Remember:
- Maintain strict HIPAA compliance
- Be empathetic and professional
- Collect accurate patient information
- Never provide medical advice
- Direct emergencies to 911
''',
        'college': '''You are an AI college admissions and information assistant. Your role is to:
1. Provide information about programs and courses
2. Handle admission inquiries
3. Schedule campus tours
4. Answer questions about application deadlines
5. Provide information about financial aid
6. Direct specific department inquiries appropriately

Current college context:
- Institution name: {business_name}
- Working hours: {working_hours}
- Special instructions: {special_instructions}

Remember:
- Be informative and encouraging
- Collect accurate prospect information
- Provide clear application instructions
- Maintain professional tone
''',
        'restaurant': '''You are an AI restaurant assistant. Your role is to:
1. Take reservations
2. Handle takeout orders
3. Answer menu questions
4. Provide business hours and location info
5. Handle special dietary requests
6. Process catering inquiries

Current restaurant context:
- Restaurant name: {business_name}
- Working hours: {working_hours}
- Special instructions: {special_instructions}

Remember:
- Be friendly and professional
- Confirm all order details
- Note special dietary requirements
- Handle peak hour policies
'''
    }
    
    return templates.get(business_type, '').format(**context)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Validate session token
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT user_id FROM sessions WHERE session_token = %s AND expires_at > NOW()",
                (session.get('token'),)
            )
            valid_session = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not valid_session:
                session.clear()
                return redirect(url_for('login'))
                
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, password_hash FROM users WHERE email = %s AND is_active = TRUE", (email,))
            user = cursor.fetchone()
            
            if user and verify_password(password, user['password_hash']):
                # Generate session token
                token = secrets.token_hex(32)
                expires = datetime.now() + timedelta(days=1)
                
                # Store session
                cursor.execute(
                    "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)",
                    (user['id'], token, expires)
                )
                conn.commit()
                
                session['user_id'] = user['id']
                session['token'] = token
                
                cursor.close()
                conn.close()
                return jsonify({'status': 'success', 'token': token})
            
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Invalid credentials'})
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Basic validation
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'})
        
        try:
            cursor = mysql.connector.connect(**db_config).cursor()
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Email already registered'})
            
            # Hash the password
            password_hash = generate_password_hash(password)
            
            # Insert new user
            cursor.execute(
                'INSERT INTO users (email, password_hash, created_at) VALUES (%s, %s, NOW())',
                (email, password_hash)
            )
            mysql.connector.connect(**db_config).commit()
            
            # Get the new user's ID
            user_id = cursor.lastrowid
            
            # Create session
            session['user_id'] = user_id
            session['email'] = email
            
            return jsonify({'success': True})
            
        except Exception as e:
            print(f"Error during signup: {str(e)}")
            return jsonify({'success': False, 'message': 'An error occurred during signup'})
        finally:
            cursor.close()

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        
        # Get user's calls
        cursor.execute("""
            SELECT * FROM calls 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (session['user_id'],))
        calls = cursor.fetchall()
        
        # Get user's settings
        cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (session['user_id'],))
        settings = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html', calls=calls, settings=settings)
    
    return render_template('dashboard.html', calls=[], settings={})

@app.route('/logout')
def logout():
    if 'token' in session:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_token = %s", (session['token'],))
            conn.commit()
            cursor.close()
            conn.close()
    
    session.clear()
    return redirect(url_for('login'))

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash):
    return hashlib.sha256(password.encode()).hexdigest() == hash

@app.route('/api/calls', methods=['GET'])
def get_calls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM calls ORDER BY created_at DESC")
    calls = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(calls)

@app.route('/api/make-call', methods=['POST'])
def make_outbound_call():
    data = request.json
    phone_number = data.get('phone_number')
    business_type = data.get('business_type')
    purpose = data.get('purpose')
    
    # Get business context
    context = get_business_context(business_type)
    
    # Create call
    call = client.calls.create(
        url=f'{request.host_url}outbound-call-handler',
        to=phone_number,
        from_=TWILIO_PHONE_NUMBER,
        record=True
    )
    
    # Store call details
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO calls (call_sid, phone_number, direction, category, business_type)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """, (call.sid, phone_number, 'outbound', purpose, business_type))
    call_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'status': 'success', 'call_sid': call.sid, 'call_id': call_id})

@app.route('/api/upload-numbers', methods=['POST'])
def upload_numbers():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV'}), 400
        
    # Save the file and process
    df = pd.read_csv(file)
    
    # Store upload info
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO bulk_uploads (file_name, status, total_numbers, processed_numbers)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """, (file.filename, 'pending', len(df), 0))
    upload_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    # Process numbers (you might want to do this asynchronously)
    for _, row in df.iterrows():
        make_outbound_call(row['phone_number'], row.get('purpose', 'general'))
        
    return jsonify({'status': 'success', 'upload_id': upload_id})

@app.route('/incoming-call', methods=['POST'])
def handle_incoming_call():
    response = VoiceResponse()
    gather = Gather(input='speech dtmf', timeout=3, num_digits=1)
    gather.say("Welcome to our service. For hospitals, press 1. For colleges, press 2. For restaurants, press 3.")
    response.append(gather)
    
    # Store call details
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

@app.route('/handle-user-input', methods=['POST'])
def handle_user_input():
    digit_pressed = request.values.get('Digits', None)
    speech_result = request.values.get('SpeechResult', None)
    
    business_types = {
        '1': 'hospital',
        '2': 'college',
        '3': 'restaurant'
    }
    
    business_type = business_types.get(digit_pressed, 'general')
    context = get_business_context(business_type)
    
    response = VoiceResponse()
    gather = Gather(input='speech', timeout=3)
    gather.say(f"Welcome to {context['business_name']}. How may I assist you today?")
    response.append(gather)
    
    return str(response)

if __name__ == '__main__':
    app.run(debug=True) 