$response = Invoke-WebRequest -Uri 'http://192.168.3.129/pt_BR/js/pages/index.js' -UseBasicParsing
$content = $response.Content
if ($content -match 'unlock') {
    Write-Host "Found 'unlock' - showing context:"
    $lines = $content -split "`n"
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match 'unlock') {
            $start = [Math]::Max(0, $i - 3)
            $end = [Math]::Min($lines.Count - 1, $i + 5)
            for ($j = $start; $j -le $end; $j++) {
                Write-Host $lines[$j]
            }
            Write-Host "---"
        }
    }
} else {
    Write-Host "No 'unlock' found in index.js"
}
