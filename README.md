# DMU Student Union Online Voting System

A Django web app for running a Student Union election at Debre Markos University.

## Run it

```bash
pip install django pillow
python manage.py migrate
python manage.py seed_demo        # demo election + admin + 5 demo voters
python manage.py runserver
```

Open http://127.0.0.1:8000/

- The demo command creates demo voters, but does not create an administrator. Create an administrator with `python manage.py createsuperuser`.
- **Demo credentials are insecure and must never be used for a real election.** Delete demo accounts before deployment.
- Demo voters: `DMU/1001` to `DMU/1005`, password `student123` (demo only).

## Run a real election

1. Create the superuser: `python manage.py createsuperuser`
2. In `/admin/` add an **Election** (title, start, end) and its **Positions**, then **Candidates** for each position.
3. Import eligible students from a CSV (`student_id,full_name,department,year`):
   `python manage.py import_voters students.csv --out voter_credentials.csv`
   This creates one account per student with a random password. Hand the passwords out securely, then delete the file.
4. Tick **Is published** on the election. Students can vote between its start and end time.
5. After voting ends, tick **Results public** to show results to everyone. Staff can view live results at any time.

## How it protects the vote

- Login required; each student ID can vote once per position (database-enforced).
- Secret ballot: `Vote` has no link to the voter. `VoteRecord` only stores *that* a student voted for a position, never *for whom*. Ballots are not registered in the admin.
- Votes are saved in a single transaction; candidate must belong to the position.
- Voting is rejected outside the start/end time.
- "Abstain" option for every position.

## Before using it for real

- Set the environment variables `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` (see `DEPLOY.md`); serve over HTTPS if possible.
- Back up `db.sqlite3` (or use PostgreSQL for very large elections).
- Get the election committee to approve the rules (tie-break, eligibility, complaints).

## New in this version

- **Candidate photos:** add them in `/admin/` > Candidates. They show on the ballot and results (a letter avatar is used when there is no photo).
- **English / አማርኛ:** language selector in the top bar; all student pages are translated.
- **Going online:** see `DEPLOY.md` (campus network, PythonAnywhere, VPS) and `run_election_server.bat` for a one-click Windows server.

- **Student registration:** `/register/` (full name, ID, department, year, RFID, password). New accounts are pending until an admin approves them in `/admin/` > Voters. See `DEPLOY.md`.

Run tests: `python manage.py test voting`
