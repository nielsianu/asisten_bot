@echo off
title Push Asisten Bot to GitHub Public Repository
echo =========================================================
echo       ASISTEN BOT - GITHUB AUTOMATIC PUSH SCRIPT
echo =========================================================
echo.

rem Check if git repository exists
if not exist ".git" (
    echo [INFO] Git repository belum diinisialisasi.
    echo [INFO] Menginisialisasi Git repository baru...
    git init
    git branch -M main
    echo.
)

rem Check if remote origin URL exists
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    git remote add origin https://github.com/nielsianu/asisten_bot.git
    echo [SUCCESS] Remote origin set to https://github.com/nielsianu/asisten_bot.git
    echo.
)

rem Prompt for commit message
echo ---------------------------------------------------------
set /p COMMIT_MSG="Masukkan pesan commit (tekan Enter untuk default): "
if "%COMMIT_MSG%"=="" (
    set COMMIT_MSG=Update Asisten Bot codebase
)

echo.
echo [1/3] Menambahkan file ke Git tracking (.env dan credentials.json aman diabaikan)...
git add .

echo [2/3] Membuat Commit: "%COMMIT_MSG%"...
git commit -m "%COMMIT_MSG%"

echo [3/3] Mem-push perubahan ke GitHub (https://github.com/nielsianu/asisten_bot.git)...
git push -u origin main

echo.
echo =========================================================
echo SELESAI! Codebase berhasil di-push ke GitHub.
echo =========================================================
echo.
pause
