# DMU Student Union Online Voting System

A Django-based web application for managing Student Union elections at **Debre Markos University (DMU)**. The system supports student registration, administrator approval, secure voting, candidate management, and election results.

## Features

- **Student registration and approval:** Students register with their details and wait for administrator approval.
- **Secure authentication:** Login is required before voting.
- **Election management:** Administrators manage elections, positions, and candidates.
- **One vote per position:** Database constraints help prevent duplicate voting.
- **Secret ballot design:** Vote records are separated from voter identity records.
- **Candidate photos:** Display candidate photos on ballot and results pages.
- **Election scheduling:** Voting is restricted to the configured election period.
- **Results management:** Administrators control when results become public.
- **English and Amharic:** Language selector for supported student pages.
- **RFID field support:** Student registration includes an RFID field.
- **Automated tests:** Run the Django app's voting tests.

## Technology Stack

- Python
- Django
- SQLite
- HTML and CSS
- Pillow for image handling

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/tilahungetie14-bot/DMU-Election-System.git
cd DMU-Election-System
```

### 2. Install dependencies

```bash
python -m venv .venv
```

On Windows:

```cmd
.venv\Scripts\activate
```

Then install the project dependencies:

```bash
pip install -r requirements.txt
```

### 3. Prepare the database

```bash
python manage.py migrate
```

### 4. Create an administrator account

```bash
python manage.py createsuperuser
```

### 5. Optional: Create demo data

```bash
python manage.py seed_demo
```

**Demo warning:** Demo accounts and passwords are for local testing only. Never use demo credentials for a real election. Remove demo accounts before deployment.

### 6. Start the development server

```bash
python manage.py runserver
```

Open the application at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

The Django administration panel is available at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

## Running an Election

1. Create an administrator account.
2. Open `/admin/` and configure an election, its positions, and candidates.
3. Register eligible students or import voter records using the project's management command.
4. Approve student accounts where required.
5. Publish the election and configure its start and end times.
6. Allow eligible students to vote during the election period.
7. After voting ends, make results public when appropriate.

See `DEPLOY.md` for additional deployment and voter-import instructions.

## Vote Protection

The project includes several safeguards:

- Authentication is required to access voting.
- Database constraints help prevent duplicate votes for a position.
- Votes are submitted within a database transaction.
- Candidates must belong to the relevant position.
- Voting is restricted by the election's start and end times.
- An abstain option is available for each position.
- The design separates ballot records from voter identity records.

These safeguards are implemented in the application; they should not be interpreted as a guarantee of security for a high-stakes real election without independent security review and testing.

## Run Tests

```bash
python manage.py test voting
```

## Configuration and Deployment

Before deploying:

- Set `DJANGO_DEBUG=0`.
- Set a strong, secret `DJANGO_SECRET_KEY`.
- Configure `DJANGO_ALLOWED_HOSTS` for the deployment host.
- Use HTTPS in production.
- Review access controls, voter-data handling, backups, and deployment settings.

Read `DEPLOY.md` for more information.

## Project Structure

```text
DMU-Election-System/
├── config/
├── locale/
├── templates/
├── voting/
├── manage.py
├── requirements.txt
├── README.md
├── DEPLOY.md
└── .gitignore
```

## Project Purpose

This project demonstrates the development of a university election web application using Django, with an emphasis on election administration, voter eligibility, ballot privacy, and transparent result management.

---

**Developed as a university software project for Debre Markos University.**