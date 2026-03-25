try {
    $response = Invoke-WebRequest -Uri 'http://192.168.3.129/js/app.js' -UseBasicParsing -ErrorAction Stop
    Write-Host "Status:" $response.StatusCode
    Write-Host "Content Length:" $response.Content.Length
    Write-Host "First 500 chars:" $response.Content.Substring(0, [Math]::Min(500, $response.Content.Length))
} catch {
    Write-Host "Error:" $_.Exception.Message
    Write-Host "Response:" $_.Exception.Response.StatusCode
}
