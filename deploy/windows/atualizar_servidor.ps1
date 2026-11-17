# ══════════════════════════════════════════════════════
#  Escritural Web — atualizar o servidor com um build novo
#  1. Na máquina de desenvolvimento: deploy\windows\build_exe.bat
#  2. Copie a pasta deploy\windows\dist inteira para o servidor (ex.: C:\Sistemas\dist)
#  3. No servidor:  powershell -ExecutionPolicy Bypass -File C:\Sistemas\dist\atualizar_servidor.ps1
#
#  Mantém: data\ (banco), .env, logs\, nssm\, instalar_servico.ps1 e static\uploads\ (anexos).
#  Antes de trocar, copia a pasta atual inteira para <pasta>_antes_<data>.
# ══════════════════════════════════════════════════════
param(
    [string]$AppDir  = 'C:\Sistemas\Escritural_web',
    [string]$Servico = 'Sisplan-Escritural_Web',   # nome ou nome de exibição (services.msc)
    [int]$Porta      = 8000
)
$ErrorActionPreference = 'Stop'

$Novo = Join-Path $PSScriptRoot 'EscrituralWeb'
$Manter = @('data', '.env', 'logs', 'nssm', 'nssm.exe', 'instalar_servico.ps1', 'static')

if (-not (Test-Path (Join-Path $Novo 'EscrituralWeb.exe')))   { throw "Build não encontrado em $Novo" }
if (-not (Test-Path (Join-Path $AppDir 'EscrituralWeb.exe'))) { throw "EscrituralWeb.exe não encontrado em $AppDir" }

$svc = Get-Service -Name $Servico -ErrorAction SilentlyContinue
if (-not $svc) { $svc = Get-Service -DisplayName $Servico -ErrorAction SilentlyContinue }
if (-not $svc) { throw "Serviço '$Servico' não encontrado. Veja o nome em services.msc e rode de novo com -Servico 'nome'" }
$Servico = $svc.Name

Write-Host ">>> Parando o serviço '$Servico'..."
Stop-Service $Servico
(Get-Service $Servico).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
Start-Sleep -Seconds 2   # o .exe solta os arquivos alguns instantes depois

$Copia = "{0}_antes_{1}" -f $AppDir, (Get-Date -Format 'yyyyMMdd_HHmm')
Write-Host ">>> Copiando a versão atual para $Copia ..."
Copy-Item $AppDir $Copia -Recurse

Write-Host '>>> Removendo a versão antiga (mantendo banco, .env, logs e anexos)...'
Get-ChildItem $AppDir -Force | Where-Object { $Manter -notcontains $_.Name } | Remove-Item -Recurse -Force
Get-ChildItem (Join-Path $AppDir 'static') -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne 'uploads' } | Remove-Item -Recurse -Force

Write-Host '>>> Copiando a versão nova...'
Copy-Item (Join-Path $Novo '*') $AppDir -Recurse -Force

Write-Host '>>> Iniciando o serviço...'
Start-Service $Servico
Start-Sleep -Seconds 5
try {
    $r = Invoke-WebRequest "http://localhost:$Porta/login" -UseBasicParsing -TimeoutSec 20
    Write-Host "OK: sistema respondendo (HTTP $($r.StatusCode)) em http://$env:COMPUTERNAME`:$Porta"
} catch {
    Write-Warning "O sistema não respondeu em http://localhost:$Porta. Veja $AppDir\logs\servico.log"
    Write-Warning "Para voltar à versão anterior: pare o serviço, apague $AppDir e renomeie $Copia para $AppDir."
}
