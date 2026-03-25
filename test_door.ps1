$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$cookie = New-Object System.Net.Cookie('session', 'oHOtB1Ao5eB/L4KhKKru/JdG', '/', '192.168.3.129')
$session.Cookies.Add($cookie)
Invoke-WebRequest -Uri 'http://192.168.3.129/execute_actions.fcgi' -Method POST -ContentType 'application/json' -Body '{"actions":[{"action":"unlock","parameters":"id=0,timeout=5"}]}' -WebSession $session -UseBasicParsing
