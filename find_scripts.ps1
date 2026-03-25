$response = Invoke-WebRequest -Uri 'http://192.168.3.129/pt_BR/html/index.html' -UseBasicParsing
$content = $response.Content
$scriptMatches = [regex]::Matches($content, 'src="([^"]+\.js[^"]*)"')
foreach ($match in $scriptMatches) {
    Write-Host $match.Groups[1].Value
}
