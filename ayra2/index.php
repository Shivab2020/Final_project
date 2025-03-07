<?php
session_start();
require_once 'config/database.php';

// Authentication middleware
function requireAuth() {
    if (!isset($_SESSION['user_id'])) {
        header('Location: /login');
        exit;
    }

    // Validate session
    $db = (new Database())->connect();
    $stmt = $db->prepare(
        "SELECT user_id FROM sessions 
         WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP"
    );
    $stmt->execute([$_SESSION['token']]);
    
    if (!$stmt->fetch()) {
        session_destroy();
        header('Location: /login');
        exit;
    }
}

// Get the request path
$request = $_SERVER['REQUEST_URI'];
$path = parse_url($request, PHP_URL_PATH);

// Basic routing
switch ($path) {
    case '/':
        require 'templates/index.html';
        break;
        
    case '/login':
        if (isset($_SESSION['user_id'])) {
            header('Location: /dashboard');
            exit;
        }
        require 'templates/login.html';
        break;
        
    case '/signup':
        if (isset($_SESSION['user_id'])) {
            header('Location: /dashboard');
            exit;
        }
        require 'templates/signup.html';
        break;
        
    case '/dashboard':
        requireAuth();
        require 'templates/dashboard.html';
        break;
        
    case '/logout':
        session_destroy();
        header('Location: /login');
        break;
        
    default:
        http_response_code(404);
        require 'templates/404.html';
        break;
}
?> 