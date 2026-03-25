$session = "sOExEzwPQ8ObKBt286cM8J43"
$userId = "981233218003"
$filePath = "C:\Users\Paulo Junior\AGAAPPS\IDFaceSistema\backend\uploads\photos\1313_1774404947.jpg"
$url = "http://192.168.3.129/user_set_image.fcgi?session=$session&user_id=$userId&match=0"

Invoke-WebRequest -Uri $url -Method POST -InFile $filePath -ContentType "image/jpeg"
