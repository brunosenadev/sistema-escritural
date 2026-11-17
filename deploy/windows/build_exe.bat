@echo off
rem ══════════════════════════════════════════════════════
rem  Gera o EscrituralWeb.exe (servidor Windows) em deploy\windows\dist\EscrituralWeb
rem  Rodar na raiz do projeto ou com dois cliques; usa o Python do .venv.
rem  Atualizar o servidor: deploy\windows\atualizar_servidor.ps1 (instruções no topo dele)
rem ══════════════════════════════════════════════════════
setlocal
cd /d "%~dp0\..\.."

if not exist .venv\Scripts\python.exe (
  echo .venv nao encontrado. Crie com: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
  exit /b 1
)
.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt pyinstaller || exit /b 1

rem static\uploads guarda arquivos enviados no servidor: nunca vai no build
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --console ^
  --name EscrituralWeb ^
  --contents-directory . ^
  --paths "%CD%" ^
  --add-data "%CD%\templates;templates" ^
  --add-data "%CD%\static;static" ^
  --distpath deploy\windows\dist ^
  --workpath deploy\windows\build ^
  --specpath deploy\windows\build ^
  deploy\windows\escritural_web.py || exit /b 1

if exist deploy\windows\dist\EscrituralWeb\static\uploads rmdir /s /q deploy\windows\dist\EscrituralWeb\static\uploads
copy /y deploy\windows\atualizar_servidor.ps1 deploy\windows\dist\ >nul
echo.
echo Pronto: copie a pasta deploy\windows\dist para o servidor e rode atualizar_servidor.ps1 nela
endlocal
