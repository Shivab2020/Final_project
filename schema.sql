CREATE TABLE calls (
    id SERIAL PRIMARY KEY,
    call_sid VARCHAR(255),
    phone_number VARCHAR(20),
    direction VARCHAR(10),
    recording_url TEXT,
    transcription TEXT,
    call_duration INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50),
    notes TEXT
);

CREATE TABLE call_settings (
    id SERIAL PRIMARY KEY,
    business_name VARCHAR(255),
    business_type VARCHAR(50),
    greeting_message TEXT,
    working_hours TEXT,
    special_instructions TEXT
); 