<?php
header('Content-Type: application/json');
require_once '../config/database.php';

$database = new Database();
$db = $database->connect();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
    exit;
}

if (!isset($_FILES['file'])) {
    echo json_encode(['status' => 'error', 'message' => 'No file uploaded']);
    exit;
}

$file = $_FILES['file'];
if ($file['error'] !== UPLOAD_ERR_OK) {
    echo json_encode(['status' => 'error', 'message' => 'File upload failed']);
    exit;
}

// Check file type
$fileType = pathinfo($file['name'], PATHINFO_EXTENSION);
if ($fileType !== 'csv') {
    echo json_encode(['status' => 'error', 'message' => 'Only CSV files are allowed']);
    exit;
}

try {
    // Store upload info
    $query = "INSERT INTO bulk_uploads (file_name, status, total_numbers, processed_numbers) 
              VALUES (:file_name, :status, :total_numbers, :processed_numbers)";
    $stmt = $db->prepare($query);
    
    // Read CSV file
    $handle = fopen($file['tmp_name'], 'r');
    $header = fgetcsv($handle);
    $totalRows = 0;
    $numbers = [];
    
    while (($data = fgetcsv($handle)) !== FALSE) {
        $totalRows++;
        $numbers[] = array_combine($header, $data);
    }
    fclose($handle);
    
    $stmt->execute([
        ':file_name' => $file['name'],
        ':status' => 'pending',
        ':total_numbers' => $totalRows,
        ':processed_numbers' => 0
    ]);
    
    $upload_id = $db->lastInsertId();
    
    // Process each number (you might want to do this asynchronously in production)
    foreach ($numbers as $row) {
        $callQuery = "INSERT INTO calls (phone_number, business_type, category, direction, status) 
                     VALUES (:phone_number, :business_type, :category, 'outbound', 'pending')";
        $callStmt = $db->prepare($callQuery);
        $callStmt->execute([
            ':phone_number' => $row['phone_number'],
            ':business_type' => $row['business_type'] ?? 'general',
            ':category' => $row['purpose'] ?? 'general'
        ]);
    }
    
    // Update upload status
    $updateQuery = "UPDATE bulk_uploads SET status = 'completed', processed_numbers = :processed 
                   WHERE id = :id";
    $updateStmt = $db->prepare($updateQuery);
    $updateStmt->execute([
        ':processed' => $totalRows,
        ':id' => $upload_id
    ]);
    
    echo json_encode([
        'status' => 'success',
        'upload_id' => $upload_id,
        'total_processed' => $totalRows
    ]);
    
} catch(Exception $e) {
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
?> 