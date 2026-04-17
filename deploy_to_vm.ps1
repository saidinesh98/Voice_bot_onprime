# deploy_to_vm.ps1
# Automates the transfer and startup of Aura AI on your VM

$VM_IP = "172.20.100.68"
$VM_USER = "administrator"
$VM_PATH = "/home/administrator/Voice bot/onprime/aura-ai"

Write-Host "📦 Packaging Aura AI for VM Migration..." -ForegroundColor Cyan

# 1. Create a zip of the current folder (excluding large venv and node_modules)
$ExcludeList = @("venv", "node_modules", ".git", ".next", "dist", "*.zip")
Compress-Archive -Path ".*", "*" -DestinationPath "aura-ai-deploy.zip" -Force -Exclude $ExcludeList

Write-Host "🚀 Sending to VM: $VM_IP..." -ForegroundColor Yellow

# 2. Secure Copy (scp) the zip to the VM
scp aura-ai-deploy.zip "${VM_USER}@${VM_IP}:${VM_PATH}"

Write-Host "✅ Transfer Complete!" -ForegroundColor Green

Write-Host "`nNext Steps on the VM:" -ForegroundColor Cyan
Write-Host "1. ssh ${VM_USER}@${VM_IP}"
Write-Host "2. cd '${VM_PATH}'"
Write-Host "3. unzip aura-ai-deploy.zip"
Write-Host "4. docker-compose up --build -d"
