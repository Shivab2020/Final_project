# AI Call Center Assistant

An intelligent call center solution powered by AI that can handle calls for hospitals, colleges, and restaurants. The system supports both inbound and outbound calls, with features like bulk calling and call analytics.

## Features

- AI-powered conversation handling
- Support for multiple business types (hospitals, colleges, restaurants)
- Inbound and outbound call handling
- Bulk call processing via CSV upload
- Call recording and transcription
- Real-time analytics dashboard
- Call history tracking
- HIPAA-compliant for medical contexts

## Prerequisites

- PHP 7.4+
- MySQL 5.7+
- Twilio Account
- Groq API Account
- Web server (Apache/Nginx)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-call-center
```

2. Create MySQL database:
```sql
CREATE DATABASE callcenter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Import the schema:
```bash
mysql -u your_username -p callcenter < schema.sql
```

4. Copy the example environment file and update with your credentials:
```bash
cp .env.example .env
```

5. Update the `.env` file with your:
   - MySQL database credentials
   - Twilio credentials
   - Groq API key
   - Application settings

6. Configure your web server:
   - Point the document root to the project's public directory
   - Ensure PHP has write permissions for uploads
   - Configure SSL if needed

7. Install PHP dependencies:
```bash
composer install
```

## Directory Structure

```
.
├── api/                # PHP API endpoints
│   ├── calls.php      # Call management
│   └── upload.php     # Bulk upload handling
├── config/            # Configuration files
│   └── database.php   # Database connection
├── js/               # JavaScript files
│   └── dashboard.js  # Dashboard functionality
├── public/           # Public assets
├── templates/        # HTML templates
├── schema.sql       # Database schema
└── .env.example     # Environment template
```

## Usage

### Dashboard

The dashboard provides:
- Call statistics
- Interface for making outbound calls
- CSV upload for bulk calling
- Call history view

### Making Calls

1. Single Call:
   - Enter phone number
   - Select business type
   - Enter call purpose
   - Click "Make Call"

2. Bulk Calls:
   - Prepare a CSV file with columns: phone_number, business_type, purpose
   - Upload via the bulk upload interface

### Business Types

1. Hospital
   - Appointment scheduling
   - Emergency triage
   - Insurance queries
   - HIPAA-compliant interactions

2. College
   - Admissions information
   - Course inquiries
   - Campus tour scheduling
   - Financial aid information

3. Restaurant
   - Reservations
   - Take-out orders
   - Menu information
   - Catering requests

## API Endpoints

### Calls API
- GET `/api/calls.php`: Get all calls
- POST `/api/calls.php`: Make a new call

### Upload API
- POST `/api/upload.php`: Upload and process CSV file

## Security

- All medical data handling is HIPAA-compliant
- Call recordings are encrypted
- Database connections use SSL
- Environment variables for sensitive data
- Prepared statements for all database queries

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 