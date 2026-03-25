$response = Invoke-WebRequest -Uri 'http://192.168.3.129/pt_BR/js/main.js' -UseBasicParsing
$content = $response.Content
# Search for login, session, authenticate
$patterns = @('login', 'session', 'authenticate', 'password')
foreach ($pattern in $patterns) {
    if ($content -match $pattern) {
        Write-Host "`n=== Found '$pattern' ==="
        $lines = $content -split "`n"
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match $pattern) {
                $start = [Math]::Max(0, $i - 2)
                $end = [Math]::Min($lines.Count - 1, $i + 3)
                for ($j = $start; $j -le $end; $j++) {
                    Write-Host $lines[$j]
                }
                Write-Host "---"
            }
        }
    }
}
