$response = Invoke-WebRequest -Uri 'http://192.168.3.129/pt_BR/js/pages/index.js' -UseBasicParsing
$content = $response.Content
$patterns = @('execute', 'action', 'door', 'abrir', 'open')
foreach ($pattern in $patterns) {
    if ($content -match $pattern) {
        Write-Host "`n=== Found '$pattern' ==="
        $lines = $content -split "`n"
        $count = 0
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match $pattern) {
                $start = [Math]::Max(0, $i - 2)
                $end = [Math]::Min($lines.Count - 1, $i + 3)
                for ($j = $start; $j -le $end; $j++) {
                    Write-Host $lines[$j]
                }
                Write-Host "---"
                $count++
                if ($count -ge 5) { break }
            }
        }
    }
}
