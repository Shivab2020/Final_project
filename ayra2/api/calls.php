<?php
header('Content-Type: application/json');
require_once '../config/database.php';

$database = new Database();
$db = $database->connect();

// Get the request method
$method = $_SERVER['REQUEST_METHOD'];

switch($method) {
    case 'GET':
        // Get all calls
        try {
            $query = "SELECT * FROM calls ORDER BY created_at DESC";
            $stmt = $db->prepare($query);
            $stmt->execute();
            $calls = $stmt->fetchAll(PDO::FETCH_ASSOC);
            echo json_encode(['status' => 'success', 'data' => $calls]);
        } catch(PDOException $e) {
            echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
        }
        break;

    case 'POST':
        // Make a new call
        $data = json_decode(file_get_contents('php://input'), true);
        
        if (isset($data['phone_number']) && isset($data['business_type'])) {
            try {
                // Initialize Twilio client
                $twilio = new Client(getenv('TWILIO_ACCOUNT_SID'), getenv('TWILIO_AUTH_TOKEN'));
                
                // Make the call using Twilio
                $call = $twilio->calls->create(
                    $data['phone_number'],
                    getenv('TWILIO_PHONE_NUMBER'),
                    [
                        'url' => 'http://' . $_SERVER['HTTP_HOST'] . '/outbound-call-handler.php',
                        'record' => true
                    ]
                );

                // Store call in database
                $query = "INSERT INTO calls (call_sid, phone_number, direction, category, business_type) 
                         VALUES (:call_sid, :phone_number, :direction, :category, :business_type)";
                $stmt = $db->prepare($query);
                $stmt->execute([
                    ':call_sid' => $call->sid,
                    ':phone_number' => $data['phone_number'],
                    ':direction' => 'outbound',
                    ':category' => $data['purpose'] ?? 'general',
                    ':business_type' => $data['business_type']
                ]);

                $call_id = $db->lastInsertId();
                echo json_encode(['status' => 'success', 'call_sid' => $call->sid, 'call_id' => $call_id]);
            } catch(Exception $e) {
                echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
            }
        } else {
            echo json_encode(['status' => 'error', 'message' => 'Missing required fields']);
        }
        break;

    default:
        echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
        break;
}
?> 