$response = Invoke-WebRequest -Uri 'http://192.168.3.129/pt_BR/js/main.js' -UseBasicParsing
$content = $response.Content
# Search for challenge, login, session
if ($content -match 'challenge') {
    Write-Host "Found 'challenge' - showing context:"
    $lines = $content -split "`n"
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match 'challenge') {
            $start = [Math]::Max(0, $i - 3)
            $end = [Math]::Min($lines.Count - 1, $i + 5)
            for ($j = $start; $j -le $end; $j++) {
                Write-Host $lines[$j]
            }
            Write-Host "---"
        }
    }
} else {
    Write-Host "No 'challenge' found in main.js"
    Write-Host "First 2000 chars:"
    Write-Host $content.Substring(0, [Math]::Min(2000, $content.Length))
}
