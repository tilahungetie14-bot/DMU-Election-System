# DMU Election System — Security Update Notes

This update focuses on voter eligibility, vote-record privacy, election data integrity, and turnout reporting.

## Changes made

1. **Voter eligibility:** ordinary voting now requires an active, authenticated account with an approved `Voter` profile. Accounts without a profile and staff/superuser accounts cannot cast ordinary ballots.
2. **Ballot privacy:** removed the exact `cast_at` timestamp from `VoteRecord` to reduce correlation between the participation record and the anonymous ballot. `Vote` still has no voter foreign key. This is a privacy improvement, not a cryptographic anonymity guarantee.
3. **Data retention:** changed key election, position, candidate, voter, and participation relationships to `PROTECT` so ORM deletion cannot casually cascade through election history. Admin deletion is disabled for elections, positions, and candidates; key fields are locked once participation records exist while results publication remains configurable. Voter profiles cannot be deleted through the admin, and profiles with participation history are read-only.
4. **Turnout:** overall turnout counts distinct participants across all positions, and each position displays its own participation count. The percentage denominator is the number of active, approved voter profiles in the database.
5. **Demo administrator:** the demo seeding command no longer creates a hard-coded `admin/admin12345` administrator. Create an administrator yourself with `python manage.py createsuperuser`.
6. **Tests:** added regression tests for users without voter profiles, staff ballot restriction, timestamp removal, and overall turnout.

## Apply the update safely

1. Stop the running Django server.
2. Back up your existing database file (`db.sqlite3` or the path set in `DJANGO_DB_PATH`).
3. In the project directory, activate your virtual environment and install dependencies:
   `python -m pip install -r requirements.txt`
4. Apply the migration:
   `python manage.py migrate`
5. Run checks and tests:
   `python manage.py check`
   `python manage.py test voting`
6. Create an admin account if needed:
   `python manage.py createsuperuser`

The new migration removes `VoteRecord.cast_at`; its existing values will be dropped when the migration runs. Back up first. The ZIP does not include your live database, so existing student accounts and ballots are not bundled in this project archive.

## Important limitations before a real election

- This is a practical Django application, not a certified election system. Do a formal threat review and independent security test before using it for a binding election.
- The app does not cryptographically prove ballot anonymity or prevent a privileged database operator from correlating records through other means.
- Turnout denominator currently means all active, approved `Voter` profiles. If eligibility differs by election (e.g., program/year-specific rules), add an explicit election-specific eligibility list before use.
- Configure a strong `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, correct `DJANGO_ALLOWED_HOSTS`, HTTPS, protected backups, and least-privilege database access for deployment.

## Test execution status

Python syntax compilation was checked during packaging. Django tests could not be executed in the packaging environment because Django was not installed and package installation was blocked by unavailable network access. Run the checks above on the target computer after installing the project's requirements.
