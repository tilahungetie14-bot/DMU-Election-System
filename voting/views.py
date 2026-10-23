from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import Candidate, Election, Vote, VoteRecord, Voter


def current_election():
    return Election.objects.filter(is_published=True).first()


def can_vote(user):
    """Only authenticated, approved voter profiles may cast ordinary ballots."""
    if not user.is_authenticated or not user.is_active or user.is_staff or user.is_superuser:
        return False
    try:
        return user.voter.is_approved
    except Voter.DoesNotExist:
        return False


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    if not settings.REGISTRATION_OPEN:
        return render(request, "registration/register.html", {"closed": True})

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        first, _sep, last = d["full_name"].partition(" ")
        try:
            with transaction.atomic():
                user = get_user_model().objects.create_user(
                    username=d["student_id"], password=d["password1"],
                    first_name=first, last_name=last,
                )
                Voter.objects.create(
                    user=user, department=d["department"], year=d["year"],
                    rfid_uid=d["rfid"], is_approved=False, registered_at=timezone.now(),
                )
        except IntegrityError:
            form.add_error(None, _("This student ID or RFID card is already registered."))
        else:
            login(request, user)
            messages.success(
                request,
                _("Registration received. You can vote once the election committee approves your account."),
            )
            return redirect("home")
    return render(request, "registration/register.html", {"form": form})


@login_required
def home(request):
    election = current_election()
    voted_ids = set()
    if election:
        voted_ids = set(
            VoteRecord.objects.filter(user=request.user, position__election=election)
            .values_list("position_id", flat=True)
        )
    positions = list(election.positions.all()) if election else []
    remaining = [p for p in positions if p.id not in voted_ids]
    return render(
        request,
        "home.html",
        {
            "election": election,
            "positions": positions,
            "voted_ids": voted_ids,
            "done": bool(positions) and not remaining,
            "pending": not (request.user.is_staff or request.user.is_superuser) and not can_vote(request.user),
        },
    )


@login_required
def ballot(request, election_id):
    election = get_object_or_404(Election, pk=election_id, is_published=True)
    if not can_vote(request.user):
        messages.error(request, _("Your account is waiting for approval and cannot vote yet."))
        return redirect("home")
    if not election.is_open:
        messages.error(request, _("Voting is not open for this election."))
        return redirect("home")
    voted_ids = set(
        VoteRecord.objects.filter(user=request.user, position__election=election)
        .values_list("position_id", flat=True)
    )
    positions = [
        p for p in election.positions.prefetch_related("candidates") if p.id not in voted_ids
    ]
    if not positions:
        return redirect("home")
    return render(request, "ballot.html", {"election": election, "positions": positions})


@login_required
@require_POST
def cast_vote(request, election_id):
    election = get_object_or_404(Election, pk=election_id, is_published=True)
    if not can_vote(request.user):
        messages.error(request, _("Your account is waiting for approval and cannot vote yet."))
        return redirect("home")
    if not election.is_open:
        messages.error(request, _("Voting is closed."))
        return redirect("home")

    cast = 0
    try:
        with transaction.atomic():
            for position in election.positions.all():
                choice = request.POST.get(f"position_{position.id}")
                if choice is None:
                    continue  # not answered, can vote later
                if VoteRecord.objects.filter(user=request.user, position=position).exists():
                    continue
                candidate = None
                if choice != "abstain":
                    candidate = get_object_or_404(Candidate, pk=choice, position=position)
                VoteRecord.objects.create(user=request.user, position=position)
                Vote.objects.create(position=position, candidate=candidate)
                cast += 1
    except IntegrityError:
        messages.error(request, _("You have already voted for one of these positions."))
        return redirect("home")

    if cast:
        messages.success(
            request, _("Your vote was recorded for %(n)d position(s). Thank you!") % {"n": cast}
        )
    else:
        messages.info(request, _("No choices were submitted."))
    return redirect("home")


def results_allowed(request, election):
    if request.user.is_staff:
        return True
    return election.results_public and election.has_ended


@login_required
def results(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    if not results_allowed(request, election):
        messages.error(request, _("Results are not available yet."))
        return redirect("home")

    data = []
    for position in election.positions.all():
        rows = list(
            position.candidates.annotate(total=Count("votes")).order_by("-total", "full_name")
        )
        abstain = Vote.objects.filter(position=position, candidate__isnull=True).count()
        total = sum(r.total for r in rows) + abstain
        for r in rows:
            r.percent = round(100 * r.total / total, 1) if total else 0
        top = rows[0].total if rows else 0
        tied = sum(1 for r in rows if r.total == top) > 1 and top > 0
        data.append(
            {"position": position, "rows": rows, "abstain": abstain, "total": total,
             "top": top, "tied": tied}
        )
    # A voter is counted once in overall turnout, even if they voted for several positions.
    turnout = VoteRecord.objects.filter(position__election=election).values("user_id").distinct().count()
    eligible_voters = Voter.objects.filter(is_approved=True, user__is_active=True).count()
    for item in data:
        item["participation"] = VoteRecord.objects.filter(position=item["position"]).count()
    return render(
        request,
        "results.html",
        {"election": election, "data": data, "turnout": turnout,
         "eligible_voters": eligible_voters,
         "turnout_percent": round(100 * turnout / eligible_voters, 1) if eligible_voters else 0,
         "preview": not election.has_ended},
    )
