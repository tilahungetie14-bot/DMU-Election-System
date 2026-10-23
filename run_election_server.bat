@echo off
REM ============================================================
REM  Start the DMU election server so other devices on the same
REM  network (campus Wi-Fi / LAN) can open it.
REM  1. Edit the two values below (SECRET KEY and HOST).
REM  2. Double-click this file. Keep the window open during voting.
REM ============================================================

REM Make up a long random text (50+ characters) and keep it private:
set DJANGO_SECRET_KEY=CHANGE-ME-to-a-long-random-text-1234567890-abcdefghijklmnopqrstuvwxyz

REM The computer's IP address on the network (run "ipconfig", look for IPv4), e.g. 192.168.1.20
REM Also add your domain name here if you have one, separated by commas.
set DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.20
set DJANGO_CSRF_TRUSTED_ORIGINS=http://192.168.1.20:8000

REM Student self-registration page: 1 = open, 0 = closed
set DJANGO_REGISTRATION_OPEN=1

set DJANGO_DEBUG=0

cd /d "%~dp0"
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
echo.
echo Server starting. Students open:  http://192.168.1.20:8000/
echo.
python -m waitress --listen=0.0.0.0:8000 config.wsgi:application
pause
