# Putting the election online

Right now `runserver` only works on your own computer. Pick ONE of the options below.

| Option | Who can vote | Cost | Difficulty |
|---|---|---|---|
| **A. Campus network (LAN)** | Anyone on the same Wi-Fi/network as your server computer | Free | Easy |
| **B. Cloud hosting (PythonAnywhere)** | Anyone with the link, from anywhere | Free/low cost | Medium |
| **C. Linux server / VPS** | Anyone with the link | Paid server | Harder |

Recommended for a first real election: **A** if students will vote in a campus lab or on campus Wi-Fi,
**B** if they must vote from home or phone data.

---

## Settings (environment variables)

The app reads its settings from environment variables, so you never edit code.

| Variable | Meaning | Example |
|---|---|---|
| `DJANGO_DEBUG` | `0` for a real election (default `1` = development) | `0` |
| `DJANGO_SECRET_KEY` | Long random private text. **Required when DEBUG=0** | (generate below) |
| `DJANGO_ALLOWED_HOSTS` | Addresses the site may be opened with, comma separated | `192.168.1.20,vote.dmu.edu.et` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Full site address(es) with `http://` or `https://` | `https://vote.dmu.edu.et` |
| `DJANGO_REGISTRATION_OPEN` | `0` closes the student registration page (default `1`) | `1` |
| `DJANGO_HTTPS` | `1` once the site uses HTTPS (secure cookies) | `1` |
| `DJANGO_DB_PATH` | Where the SQLite file lives (optional) | `D:\election\db.sqlite3` |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` | Use PostgreSQL instead of SQLite (optional) | |

Generate a secret key:

```
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## Option A: Campus network (Windows computer)

1. Choose one computer to be the server. It must stay on, awake, and connected for the whole voting period. Use a wired connection if you can.
2. Install Python, then in the project folder: `python -m pip install -r requirements.txt`
3. Find the computer's address: open Command Prompt, run `ipconfig`, and note the **IPv4 Address** (for example `192.168.1.20`).
4. Open `run_election_server.bat` in Notepad and change:
   - `DJANGO_SECRET_KEY` to your generated key
   - every `192.168.1.20` to your IPv4 address
5. Create the admin (once): in the project folder run `python manage.py createsuperuser`
   (set the same environment variables first, or just run it once before step 6; it uses the same database file).
6. Allow the port through Windows Firewall: Windows Security > Firewall > Advanced settings > Inbound Rules > New Rule > Port > TCP `8000` > Allow > name it "DMU Election".
7. Double-click `run_election_server.bat`. Keep the window open.
8. On another phone/computer on the same network, open `http://192.168.1.20:8000/`.

Stop sleep: Settings > System > Power > set "Sleep" to **Never** while voting.

## Option B: PythonAnywhere (works from anywhere)

1. Create an account at pythonanywhere.com and open a **Bash console**.
2. Upload the project (Files tab > upload the zip, then `unzip dmu_election_system.zip`).
3. Create a virtualenv and install:
   ```
   mkvirtualenv election --python=python3.12
   cd ~/dmu_election_system
   pip install -r requirements.txt
   ```
4. **Web** tab > Add a new web app > **Manual configuration** > same Python version.
5. On the Web tab set:
   - Source code and working directory: `/home/YOURNAME/dmu_election_system`
   - Virtualenv: `/home/YOURNAME/.virtualenvs/election`
   - Click the WSGI configuration file link and replace its contents with:
     ```python
     import os, sys
     sys.path.insert(0, "/home/YOURNAME/dmu_election_system")
     os.environ["DJANGO_DEBUG"] = "0"
     os.environ["DJANGO_SECRET_KEY"] = "PASTE-YOUR-GENERATED-KEY"
     os.environ["DJANGO_ALLOWED_HOSTS"] = "YOURNAME.pythonanywhere.com"
     os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"] = "https://YOURNAME.pythonanywhere.com"
     os.environ["DJANGO_HTTPS"] = "1"
     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```
   - Static files table: URL `/static/` -> `/home/YOURNAME/dmu_election_system/staticfiles`
6. In the Bash console (same virtualenv; export the same variables first, e.g. `export DJANGO_DEBUG=0 DJANGO_SECRET_KEY=...`):
   ```
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
7. Click **Reload**. Your site is at `https://YOURNAME.pythonanywhere.com`. HTTPS is included.

## Option C: Linux VPS (outline)

Ubuntu server + `gunicorn` behind `nginx` with a Let's Encrypt certificate, PostgreSQL for the database,
and the environment variables above in a systemd service file. Ask and I will write the exact files.

---

## Before opening voting (checklist)

- [ ] `DJANGO_DEBUG=0` and a private `DJANGO_SECRET_KEY` are set
- [ ] Demo admin and demo voters (`DMU/1001`...) are deleted; your own admin exists with a strong password
- [ ] Demo election deleted or edited into the real one; candidates and photos added
- [ ] Voters imported with `import_voters`; each student has received their password privately; `voter_credentials.csv` deleted afterwards
- [ ] Start/end times correct (shown in Addis Ababa time)
- [ ] **Is published** ticked; **Results public** NOT ticked until voting ends
- [ ] Rehearsed with a separate TEST election (not the real one: votes cannot be removed afterwards), then delete the test election
- [ ] Database file backed up (copy `db.sqlite3` now, during voting, and after voting)
- [ ] Election committee has agreed the tie-break and complaint rules

## During and after voting

- Do not restart or move the server computer unnecessarily. Voting is saved instantly in `db.sqlite3`.
- Staff (admin accounts) can watch live results; students cannot until you tick **Results public** after the end time.
- After voting ends: copy `db.sqlite3` to a safe place as the official record, then publish results.

## Candidate photos

In `/admin/`: **Candidates** > open a candidate > **Photo** > choose a file > Save. Use a square, clear photo under 1 MB.
Uploaded photos are stored in the `media/` folder. Back it up together with `db.sqlite3`.

## Language

Students switch between English and አማርኛ with the selector in the top bar. The choice is remembered on their device.
Candidate names, positions and manifestos are shown exactly as you type them in the admin, so type them in the language you want shown.

## Student registration and approval

Students who are not in your imported list can register themselves at `/register/` (link on the sign-in page):
full name, student ID, department, year, RFID card number and a password they choose.

- A new registration is **pending**: the student can sign in but cannot vote until you approve them.
- Approve in `/admin/` > **Voters**: filter **Is approved = No**, check the students (compare with the student list / ID card and RFID), then choose the action **"Approve selected students"** > Go.
- Imported students (`import_voters`) are approved automatically. The CSV may include an optional `rfid` column.
- The student ID and the RFID card number must each be unique.
- Close registration when you have all the students: set `DJANGO_REGISTRATION_OPEN=0` and restart the server (or add it to `run_election_server.bat`).
- Approve everyone **before** voting starts, and check the Voters list for suspicious entries (same person, wrong department, fake names).
