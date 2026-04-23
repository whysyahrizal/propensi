$ErrorActionPreference = "SilentlyContinue"

# Kill anything listening on port 8000 first.
$pids = Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique
if ($pids) {
    foreach ($pid in $pids) {
        Stop-Process -Id $pid -Force
        Write-Host "Killed PID $pid on port 8000"
    }
} else {
    Write-Host "No listener on port 8000"
}

$ErrorActionPreference = "Continue"

Write-Host "Starting Django server on 127.0.0.1:8000"
python manage.py runserver 127.0.0.1:8000
