from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("voting", "0002_voter_rfid_approval"),
    ]

    operations = [
        # Remove the exact ballot-participation timestamp to reduce correlation
        # between a voter's participation record and their anonymous ballot.
        migrations.RemoveField(model_name="voterecord", name="cast_at"),
        migrations.AlterField(
            model_name="position", name="election",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="positions", to="voting.election"),
        ),
        migrations.AlterField(
            model_name="candidate", name="position",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="candidates", to="voting.position"),
        ),
        migrations.AlterField(
            model_name="voter", name="user",
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="voterecord", name="user",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="voterecord", name="position",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="voting.position"),
        ),
        migrations.AlterField(
            model_name="vote", name="position",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="votes", to="voting.position"),
        ),
        migrations.AlterField(
            model_name="vote", name="candidate",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="votes", to="voting.candidate"),
        ),
    ]
