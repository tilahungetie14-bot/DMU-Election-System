import csv
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from voting.models import Voter


class Command(BaseCommand):
    help = (
        "Import eligible voters from a CSV with columns: student_id,full_name,department,year (optional: rfid). "
        "Writes a new CSV with one-time passwords to hand out to students."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file")
        parser.add_argument("--out", default="voter_credentials.csv")

    def handle(self, *args, **opts):
        User = get_user_model()
        created = skipped = 0
        try:
            src = open(opts["csv_file"], newline="", encoding="utf-8")
        except OSError as e:
            raise CommandError(str(e))
        with src, open(opts["out"], "w", newline="", encoding="utf-8") as out:
            writer = csv.writer(out)
            writer.writerow(["student_id", "full_name", "password"])
            for row in csv.DictReader(src):
                sid = (row.get("student_id") or "").strip()
                if not sid:
                    continue
                if User.objects.filter(username=sid).exists():
                    skipped += 1
                    continue
                password = secrets.token_urlsafe(6)
                name = (row.get("full_name") or "").strip()
                first, _, last = name.partition(" ")
                user = User.objects.create_user(
                    username=sid, password=password, first_name=first, last_name=last
                )
                year = (row.get("year") or "").strip()
                rfid = "".join((row.get("rfid") or "").split()).upper() or None
                if rfid and Voter.objects.filter(rfid_uid=rfid).exists():
                    rfid = None
                Voter.objects.create(
                    rfid_uid=rfid,
                    user=user,
                    department=(row.get("department") or "").strip(),
                    year=int(year) if year.isdigit() else None,
                )
                writer.writerow([sid, name, password])
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"Created {created} voters, skipped {skipped} existing. Credentials: {opts['out']}"
        ))
        self.stdout.write("Distribute the credentials file securely, then delete it.")
