# start_keycloak.ps1
$KeycloakPath = "C:\Users\Dinesh\OneDrive\Documents\keycloak-26.5.4\bin"
Write-Host "🚀 Starting Keycloak in Development Mode..." -ForegroundColor Cyan
Set-Location $KeycloakPath
.\kc.bat start-dev --spi-theme-static-max-age=-1 --spi-theme-cache-themes=false --spi-theme-cache-templates=false
