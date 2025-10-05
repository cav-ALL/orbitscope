<?php
// openai-proxy.php
header('Content-Type: application/json');
$apiKey = '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'; // Your OpenAI API key

$data = file_get_contents('php://input');
$ch = curl_init('https://api.openai.com/v1/chat/completions');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Authorization: Bearer ' . $apiKey
]);
$response = curl_exec($ch);
http_response_code(curl_getinfo($ch, CURLINFO_HTTP_CODE));
echo $response;
curl_close($ch);
?>