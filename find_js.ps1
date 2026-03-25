$endpoints = @(
    '/js/app.js',
    '/js/login.js',
    '/static/js/app.js',
    '/assets/js/app.js',
    '/js/idface.js',
    '/js/main.js'
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "http://192.168.3.129$endpoint" -UseBasicParsing -ErrorAction Stop
        Write-Host "Found: $endpoint - Size: $($response.Content.Length)"
    } catch {
        Write-Host "Not found: $endpoint"
    }
}
