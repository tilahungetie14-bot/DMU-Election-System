from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Candidate, Election, Position, Vote, VoteRecord, Voter


class ElectionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.u1 = User.objects.create_user("S1", password="pw")
        self.u2 = User.objects.create_user("S2", password="pw")
        self.staff = User.objects.create_user("boss", password="pw", is_staff=True)
        Voter.objects.create(user=self.u1, is_approved=True)
        Voter.objects.create(user=self.u2, is_approved=True)
        now = timezone.now()
        self.e = Election.objects.create(
            title="T", start=now - timedelta(hours=1), end=now + timedelta(hours=1),
            is_published=True,
        )
        self.pres = Position.objects.create(election=self.e, name="President")
        self.vp = Position.objects.create(election=self.e, name="VP", order=1)
        self.a = Candidate.objects.create(position=self.pres, full_name="A")
        self.b = Candidate.objects.create(position=self.pres, full_name="B")
        self.c = Candidate.objects.create(position=self.vp, full_name="C")

    def cast(self, data):
        return self.client.post(reverse("cast_vote", args=[self.e.id]), data, follow=True)

    def test_login_required(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login/", r.url)

    def test_vote_recorded_once(self):
        self.client.login(username="S1", password="pw")
        self.cast({f"position_{self.pres.id}": self.a.id, f"position_{self.vp.id}": "abstain"})
        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(VoteRecord.objects.filter(user=self.u1).count(), 2)
        # second attempt (even for a different candidate) is ignored
        self.cast({f"position_{self.pres.id}": self.b.id})
        self.assertEqual(Vote.objects.filter(position=self.pres).count(), 1)
        self.assertEqual(self.a.votes.count(), 1)
        self.assertEqual(self.b.votes.count(), 0)

    def test_candidate_from_other_position_rejected(self):
        self.client.login(username="S1", password="pw")
        r = self.client.post(
            reverse("cast_vote", args=[self.e.id]), {f"position_{self.pres.id}": self.c.id}
        )
        self.assertEqual(r.status_code, 404)
        self.assertEqual(Vote.objects.count(), 0)
        self.assertEqual(VoteRecord.objects.count(), 0)

    def test_closed_election_blocks_voting(self):
        self.e.end = timezone.now() - timedelta(minutes=1)
        self.e.save()
        self.client.login(username="S1", password="pw")
        self.cast({f"position_{self.pres.id}": self.a.id})
        self.assertEqual(Vote.objects.count(), 0)

    def test_ballot_has_no_voter_link_or_precise_timestamp(self):
        field_names = {f.name for f in Vote._meta.get_fields()}
        self.assertNotIn("user", field_names)
        self.assertNotIn("cast_at", {f.name for f in VoteRecord._meta.get_fields()})

    def test_account_without_voter_profile_cannot_vote(self):
        outsider = get_user_model().objects.create_user("outsider", password="pw")
        self.client.login(username="outsider", password="pw")
        self.cast({f"position_{self.pres.id}": self.a.id})
        self.assertEqual(Vote.objects.count(), 0)

    def test_staff_cannot_cast_ordinary_ballot(self):
        self.client.login(username="boss", password="pw")
        self.cast({f"position_{self.pres.id}": self.a.id})
        self.assertEqual(Vote.objects.count(), 0)

    def test_results_hidden_from_students_until_end(self):
        self.client.login(username="S1", password="pw")
        r = self.client.get(reverse("results", args=[self.e.id]))
        self.assertEqual(r.status_code, 302)
        self.client.logout()
        self.client.login(username="boss", password="pw")
        r = self.client.get(reverse("results", args=[self.e.id]))
        self.assertEqual(r.status_code, 200)

    def test_results_counts(self):
        for name, cand in (("S1", self.a), ("S2", self.a)):
            self.client.login(username=name, password="pw")
            self.cast({f"position_{self.pres.id}": cand.id})
            self.client.logout()
        self.client.login(username="boss", password="pw")
        r = self.client.get(reverse("results", args=[self.e.id]))
        row = r.context["data"][0]["rows"][0]
        self.assertEqual((row.full_name, row.total, row.percent), ("A", 2, 100.0))
        self.assertEqual(r.context["turnout"], 2)
        self.assertEqual(r.context["eligible_voters"], 2)


class LanguageAndPhotoTests(ElectionTests):
    def test_amharic_pages_render(self):
        self.client.login(username="S1", password="pw")
        self.client.post(reverse("set_language"), {"language": "am", "next": "/"})
        r = self.client.get(reverse("ballot", args=[self.e.id]), HTTP_ACCEPT_LANGUAGE="am")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "ድምጸ ተአቅቦ")  # "Abstain"
        self.assertContains(r, "ድምጼን ላክ")  # "Submit my vote"
        r = self.client.get(reverse("home"))
        self.assertContains(r, "ገና ድምጽ አልሰጡም")

    def test_amharic_results_and_plural(self):
        self.client.login(username="S1", password="pw")
        self.cast({f"position_{self.pres.id}": self.a.id})
        self.client.logout()
        self.client.login(username="boss", password="pw")
        self.client.post(reverse("set_language"), {"language": "am", "next": "/"})
        r = self.client.get(reverse("results", args=[self.e.id]))
        self.assertContains(r, "1 ድምጽ")
        self.assertContains(r, "width: 100.0%")

    def test_english_default_and_switcher(self):
        self.client.login(username="S1", password="pw")
        r = self.client.get(reverse("home"))
        self.assertContains(r, "Go to ballot")
        self.assertContains(r, 'name="language"')

    def test_photo_shown_when_uploaded(self):
        import io, tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (20, 20), "green").save(buf, "PNG")
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            self.a.photo = SimpleUploadedFile("a.png", buf.getvalue(), "image/png")
            self.a.save()
            self.client.login(username="S1", password="pw")
            r = self.client.get(reverse("ballot", args=[self.e.id]))
            self.assertContains(r, "/media/candidates/")
            self.assertContains(r, 'class="photo ph"')  # candidate B has no photo: initial letter


class RegistrationTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.e = Election.objects.create(
            title="T", start=now - timedelta(hours=1), end=now + timedelta(hours=1),
            is_published=True,
        )
        self.pos = Position.objects.create(election=self.e, name="President")
        self.cand = Candidate.objects.create(position=self.pos, full_name="A")
        self.url = reverse("register")
        self.data = {
            "full_name": "Abebe Kebede Alemu", "student_id": "DMU/2001",
            "department": "Pharmacy", "year": "3", "rfid": "04 A3 B2 1C",
            "password1": "Vote-Secure-77", "password2": "Vote-Secure-77", "website": "",
        }

    def test_login_page_links_to_register(self):
        self.assertContains(self.client.get(reverse("login")), self.url)

    def test_register_creates_pending_voter_and_logs_in(self):
        r = self.client.post(self.url, self.data, follow=True)
        self.assertEqual(r.status_code, 200)
        u = get_user_model().objects.get(username="DMU/2001")
        v = u.voter
        self.assertEqual((u.first_name, u.last_name), ("Abebe", "Kebede Alemu"))
        self.assertEqual((v.department, v.year, v.rfid_uid, v.is_approved), ("Pharmacy", 3, "04A3B21C", False))
        self.assertContains(r, "waiting for approval")
        self.assertTrue(u.check_password("Vote-Secure-77"))

    def test_pending_cannot_vote_until_approved(self):
        self.client.post(self.url, self.data)
        cast = reverse("cast_vote", args=[self.e.id])
        self.client.post(cast, {f"position_{self.pos.id}": self.cand.id})
        self.assertEqual(Vote.objects.count(), 0)
        r = self.client.get(reverse("ballot", args=[self.e.id]))
        self.assertEqual(r.status_code, 302)
        v = get_user_model().objects.get(username="DMU/2001").voter
        v.is_approved = True
        v.save()
        self.client.post(cast, {f"position_{self.pos.id}": self.cand.id})
        self.assertEqual(Vote.objects.count(), 1)

    def test_duplicate_id_rfid_and_case(self):
        self.client.post(self.url, self.data)
        self.client.logout()
        for change in ({"rfid": "04a3b21c"}, {"student_id": "dmu/2001", "rfid": "FFFF"}):
            bad = dict(self.data, **change)
            r = self.client.post(self.url, bad)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(get_user_model().objects.count(), 1)

    def test_validation_errors(self):
        cases = [
            {"password2": "different"},
            {"password1": "12345678", "password2": "12345678"},
            {"full_name": "Abebe"},
            {"student_id": "bad id!"},
            {"year": "9"},
            {"rfid": "  "},
            {"website": "http://spam"},
        ]
        for change in cases:
            r = self.client.post(self.url, dict(self.data, **change))
            self.assertEqual(r.status_code, 200, change)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_registration_can_be_closed(self):
        from django.test import override_settings
        with override_settings(REGISTRATION_OPEN=False):
            r = self.client.post(self.url, self.data)
            self.assertContains(r, "Registration is closed")
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_imported_voters_stay_approved(self):
        u = get_user_model().objects.create_user("X1", password="pw")
        from .models import Voter
        self.assertTrue(Voter.objects.create(user=u).is_approved)

    def test_amharic_register_page(self):
        self.client.post(reverse("set_language"), {"language": "am", "next": "/"})
        self.assertContains(self.client.get(self.url), "የተማሪ ምዝገባ")
