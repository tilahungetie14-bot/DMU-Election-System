from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from voting.models import Candidate, Election, Position, Voter


class Command(BaseCommand):
    help = "Create a demo election, candidates and 5 demo voters (demo credentials only)."

    def handle(self, *args, **opts):
        User = get_user_model()
        for i in range(1, 6):
            sid = f"DMU/{1000 + i}"
            if not User.objects.filter(username=sid).exists():
                u = User.objects.create_user(sid, password="student123", first_name=f"Student{i}")
                Voter.objects.create(user=u, department="Computer Science", year=3)

        now = timezone.now()
        election, _ = Election.objects.get_or_create(
            title="DMU Student Union Election (Demo)",
            defaults=dict(start=now - timedelta(hours=1), end=now + timedelta(days=2),
                          is_published=True),
        )
        spec = {
            "President": [("Abebe Kebede", "Law"), ("Selam Tesfaye", "Pharmacy")],
            "Vice President": [("Dawit Alemu", "Engineering"), ("Hana Bekele", "Health Science")],
            "General Secretary": [("Yonas Mulu", "Computer Science"), ("Meron Haile", "Business")],
        }
        for order, (pos_name, cands) in enumerate(spec.items()):
            pos, _ = Position.objects.get_or_create(election=election, name=pos_name,
                                                    defaults={"order": order})
            for name, dept in cands:
                Candidate.objects.get_or_create(
                    position=pos, full_name=name,
                    defaults={"department": dept, "year": 3,
                              "manifesto": "Better services, fair representation and an open union."},
                )
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Create an administrator separately with: python manage.py createsuperuser")
        self.stdout.write(self.style.WARNING(
            "Demo voters DMU/1001..DMU/1005 use password student123. Do not use demo accounts for a real election."
        ))
