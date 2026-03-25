$response = Invoke-WebRequest -Uri 'http://192.168.3.129/login.fcgi' -Method POST -ContentType 'application/x-www-form-urlencoded' -Body 'login=admin&password=123456' -SessionVariable ws -UseBasicParsing
Write-Host "Status:" $response.StatusCode
Write-Host "Response:" $response.Content
Write-Host "Session cookie:"
$ws.Cookies.GetCookies("http://192.168.3.129") | Format-Table
