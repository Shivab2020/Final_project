<?php
header('Content-Type: application/json');
require_once '../config/database.php';

session_start();

class Auth {
    private $db;

    public function __construct($db) {
        $this->db = $db;
    }

    public function register($data) {
        try {
            // Validate input
            if (!filter_var($data['email'], FILTER_VALIDATE_EMAIL)) {
                return ['status' => 'error', 'message' => 'Invalid email format'];
            }

            // Check if email exists
            $stmt = $this->db->prepare("SELECT id FROM users WHERE email = ?");
            $stmt->execute([$data['email']]);
            if ($stmt->fetch()) {
                return ['status' => 'error', 'message' => 'Email already registered'];
            }

            // Hash password
            $password_hash = password_hash($data['password'], PASSWORD_DEFAULT);

            // Insert user
            $stmt = $this->db->prepare(
                "INSERT INTO users (email, password_hash, first_name, last_name, company_name, phone_number) 
                 VALUES (?, ?, ?, ?, ?, ?)"
            );
            $stmt->execute([
                $data['email'],
                $password_hash,
                $data['first_name'] ?? null,
                $data['last_name'] ?? null,
                $data['company_name'] ?? null,
                $data['phone_number'] ?? null
            ]);

            $user_id = $this->db->lastInsertId();

            // Create default user settings
            $stmt = $this->db->prepare(
                "INSERT INTO user_settings (user_id, timezone, notification_preferences) 
                 VALUES (?, 'UTC', '{\"email\":true,\"sms\":false}')"
            );
            $stmt->execute([$user_id]);

            return ['status' => 'success', 'message' => 'Registration successful'];
        } catch (Exception $e) {
            return ['status' => 'error', 'message' => 'Registration failed: ' . $e->getMessage()];
        }
    }

    public function login($email, $password) {
        try {
            $stmt = $this->db->prepare("SELECT id, password_hash FROM users WHERE email = ? AND is_active = TRUE");
            $stmt->execute([$email]);
            $user = $stmt->fetch(PDO::FETCH_ASSOC);

            if ($user && password_verify($password, $user['password_hash'])) {
                // Generate session token
                $token = bin2hex(random_bytes(32));
                $expires = date('Y-m-d H:i:s', strtotime('+24 hours'));

                // Store session
                $stmt = $this->db->prepare(
                    "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)"
                );
                $stmt->execute([$user['id'], $token, $expires]);

                // Update last login
                $stmt = $this->db->prepare("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?");
                $stmt->execute([$user['id']]);

                $_SESSION['user_id'] = $user['id'];
                $_SESSION['token'] = $token;

                return ['status' => 'success', 'token' => $token];
            }

            return ['status' => 'error', 'message' => 'Invalid credentials'];
        } catch (Exception $e) {
            return ['status' => 'error', 'message' => 'Login failed: ' . $e->getMessage()];
        }
    }

    public function logout() {
        try {
            if (isset($_SESSION['token'])) {
                $stmt = $this->db->prepare("DELETE FROM sessions WHERE session_token = ?");
                $stmt->execute([$_SESSION['token']]);
            }

            session_destroy();
            return ['status' => 'success', 'message' => 'Logged out successfully'];
        } catch (Exception $e) {
            return ['status' => 'error', 'message' => 'Logout failed: ' . $e->getMessage()];
        }
    }

    public function validateSession() {
        if (!isset($_SESSION['token'])) {
            return false;
        }

        try {
            $stmt = $this->db->prepare(
                "SELECT user_id FROM sessions 
                 WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP"
            );
            $stmt->execute([$_SESSION['token']]);
            return $stmt->fetch() !== false;
        } catch (Exception $e) {
            return false;
        }
    }
}

// Handle requests
$auth = new Auth((new Database())->connect());

switch ($_SERVER['REQUEST_METHOD']) {
    case 'POST':
        $data = json_decode(file_get_contents('php://input'), true);
        $action = $_GET['action'] ?? '';

        switch ($action) {
            case 'register':
                echo json_encode($auth->register($data));
                break;

            case 'login':
                echo json_encode($auth->login($data['email'], $data['password']));
                break;

            case 'logout':
                echo json_encode($auth->logout());
                break;

            default:
                echo json_encode(['status' => 'error', 'message' => 'Invalid action']);
        }
        break;

    case 'GET':
        if (isset($_GET['validate'])) {
            echo json_encode(['valid' => $auth->validateSession()]);
        } else {
            echo json_encode(['status' => 'error', 'message' => 'Invalid request']);
        }
        break;

    default:
        echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
}
?> 