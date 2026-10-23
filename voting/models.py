
from django.conf import settings
from django.db import models
from django.utils import timezone


class Election(models.Model):
    title = models.CharField(
        max_length=200,
        default="DMU Student Union Election",
    )
    start = models.DateTimeField()
    end = models.DateTimeField()

    is_published = models.BooleanField(
        default=False,
        help_text="Tick to open this election to voters.",
    )
    results_public = models.BooleanField(
        default=False,
        help_text="Show results to everyone (after voting has ended).",
    )

    class Meta:
        ordering = ["-start"]

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return (
            self.is_published
            and self.start <= timezone.now() <= self.end
        )

    @property
    def has_ended(self):
        return timezone.now() > self.end


class Position(models.Model):
    election = models.ForeignKey(
        Election,
        on_delete=models.PROTECT,
        related_name="positions",
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        unique_together = ("election", "name")

    def __str__(self):
        return f"{self.name} ({self.election})"


class Candidate(models.Model):
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="candidates",
    )
    full_name = models.CharField(max_length=150)
    department = models.CharField(max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    manifesto = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to="candidates/",
        blank=True,
    )

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} - {self.position.name}"


class Voter(models.Model):
    """Extra information about a student account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    department = models.CharField(max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)

    rfid_uid = models.CharField(
        "RFID card number",
        max_length=64,
        unique=True,
        null=True,
        blank=True,
    )

    is_approved = models.BooleanField(
        default=True,
        help_text=(
            "Students must be approved by an admin "
            "before they can vote."
        ),
    )

    is_rejected = models.BooleanField(
        default=False,
        help_text=(
            "Rejected by the committee. The student cannot vote "
            "and sees the reason."
        ),
    )
    review_note = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Reason (shown to the student)",
    )
    reviewed_at = models.DateTimeField(
        blank=True,
        editable=False,
        null=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    registered_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    def __str__(self):
        return self.user.username


class EligibleStudent(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    department = models.CharField(max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
    )
    rfid_uid = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="RFID card number",
    )

    class Meta:
        ordering = ["student_id"]

    def __str__(self):
        return self.student_id


class ReviewLog(models.Model):
    ACTION_CHOICES = [
        ("approve", "Approved"),
        ("auto_approve", "Auto-approved (eligible list)"),
        ("unapprove", "Unapproved"),
        ("reject", "Rejected"),
    ]

    student_id = models.CharField(max_length=150)
    student_name = models.CharField(max_length=300, blank=True)
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )
    reason = models.CharField(max_length=300, blank=True)
    by_username = models.CharField(max_length=150, blank=True)
    at = models.DateTimeField(auto_now_add=True)
    by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["-at", "-id"]

    def __str__(self):
        return f"{self.student_id} - {self.action}"


class VoteRecord(models.Model):
    """
    Records that a student voted for a position,
    without recording whom they selected.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
    )

    class Meta:
        unique_together = ("user", "position")


class Vote(models.Model):
    """
    Anonymous ballot with no direct link to the voter.

    candidate=None means the voter abstained.
    """

    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="votes",
    )
    candidate = models.ForeignKey(
        Candidate,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="votes",
    )
