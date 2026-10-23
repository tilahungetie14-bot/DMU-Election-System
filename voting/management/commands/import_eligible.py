import csv

from django.core.management.base import BaseCommand, CommandError

from voting.models import EligibleStudent


class Command(BaseCommand):
    help = (
        "Load the official list of students allowed to vote from a CSV with columns: "
        "student_id,full_name,department,year (optional: rfid). Students on this list who "
        "register themselves are approved automatically. Existing IDs are updated."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_file")

    def handle(self, *args, **opts):
        try:
            src = open(opts["csv_file"], newline="", encoding="utf-8-sig")
        except OSError as e:
            raise CommandError(str(e))
        created = updated = 0
        with src:
            for row in csv.DictReader(src):
                sid = (row.get("student_id") or "").strip()
                if not sid:
                    continue
                year = (row.get("year") or "").strip()
                _obj, was_created = EligibleStudent.objects.update_or_create(
                    student_id=sid,
                    defaults=dict(
                        full_name=" ".join((row.get("full_name") or "").split()),
                        department=(row.get("department") or "").strip(),
                        year=int(year) if year.isdigit() else None,
                        rfid_uid="".join((row.get("rfid") or "").split()).upper(),
                    ),
                )
                created += was_created
                updated += not was_created
        self.stdout.write(self.style.SUCCESS(f"Eligible list: {created} added, {updated} updated."))
