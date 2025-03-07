import subprocess
import sys
import os

def install_dependencies():
    print("Installing dependencies...")
    
    # First upgrade pip
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install wheel first to help with binary packages
    subprocess.check_call([sys.executable, "-m", "pip", "install", "wheel"])
    
    try:
        # Install PyAudio using pipwin on Windows
        if os.name == 'nt':  # Windows
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"])
            subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio"])
        
        # Install the rest of the requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("\nAll dependencies installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"\nError installing dependencies: {e}")
        print("\nTrying alternative installation method for problematic packages...")
        
        # Install packages one by one to identify and handle problematic ones
        with open('requirements.txt') as f:
            requirements = f.read().splitlines()
        
        for requirement in requirements:
            try:
                if 'opencv-python' in requirement:
                    # Try alternative opencv-python version if specified one fails
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python"])
                    except:
                        print("Trying alternative opencv-python version...")
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python==4.8.0.76"])
                elif 'pyaudio' in requirement.lower():
                    # Skip PyAudio as it's already handled above for Windows
                    continue
                else:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to install {requirement}: {e}")

def setup_database():
    print("\nSetting up database...")
    try:
        import mysql.connector
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Get database credentials from environment variables or use defaults
        host = os.getenv('DB_HOST', 'localhost')
        user = os.getenv('DB_USER', 'root')
        password = os.getenv('DB_PASSWORD', '')
        
        # Create database and tables
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS callcenter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # Switch to the database
        cursor.execute("USE callcenter")
        
        # Read and execute schema.sql
        with open('schema.sql', 'r') as f:
            schema = f.read()
            statements = schema.split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        print("Please ensure MySQL is installed and running, and the credentials are correct in .env file")

def main():
    print("Starting setup process...")
    
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Install dependencies
    install_dependencies()
    
    # Setup database
    setup_database()
    
    print("\nSetup completed!")
    print("\nNext steps:")
    print("1. Update your .env file with your credentials")
    print("2. Configure your web server (Apache/Nginx)")
    print("3. Start the application")

if __name__ == "__main__":
    main() 