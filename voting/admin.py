from django.contrib import admin

from .models import Candidate, Election, Position, Vote, VoteRecord, Voter


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1
    can_delete = False

    def has_add_permission(self, request, obj=None):
        if obj and VoteRecord.objects.filter(position__election=obj).exists():
            return False
        return super().has_add_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj and VoteRecord.objects.filter(position__election=obj).exists():
            return ("name", "order")
        return ()


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ("title", "start", "end", "is_published", "results_public")
    inlines = [PositionInline]

    def has_delete_permission(self, request, obj=None):
        # Elections should be archived, not deleted through the admin UI.
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and VoteRecord.objects.filter(position__election=obj).exists():
            return ("title", "start", "end", "is_published")
        return ()


class CandidateInline(admin.StackedInline):
    model = Candidate
    extra = 1
    can_delete = False

    def has_add_permission(self, request, obj=None):
        if obj and Vote.objects.filter(position=obj).exists():
            return False
        return super().has_add_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj and Vote.objects.filter(position=obj).exists():
            return ("full_name", "department", "year", "manifesto", "photo")
        return ()


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name", "election", "order")
    list_filter = ("election",)
    inlines = [CandidateInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and VoteRecord.objects.filter(position=obj).exists():
            return ("name", "election", "order")
        return ()


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name", "position", "department", "year")
    list_filter = ("position__election", "position")
    search_fields = ("full_name",)

    def has_delete_permission(self, request, obj=None):
        # Prevent accidental loss of candidate/vote history via the admin.
        return False


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "department", "year", "rfid_uid", "is_approved", "registered_at")
    list_filter = ("is_approved", "department", "year")
    search_fields = ("user__username", "user__first_name", "user__last_name", "department", "rfid_uid")
    actions = ["approve_selected", "unapprove_selected"]

    def has_delete_permission(self, request, obj=None):
        # Keep the eligibility denominator and voter-account history stable.
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and VoteRecord.objects.filter(user=obj.user).exists():
            return ("user", "department", "year", "rfid_uid", "is_approved", "registered_at")
        return ("registered_at",)

    @admin.display(description="Full name")
    def full_name(self, obj):
        return obj.user.get_full_name()

    @admin.action(description="Approve selected students (they can vote)")
    def approve_selected(self, request, queryset):
        eligible = queryset.filter(user__voterecord__isnull=True).distinct()
        n = eligible.update(is_approved=True)
        skipped = queryset.count() - n
        self.message_user(request, f"{n} student(s) approved; {skipped} with participation history unchanged.")

    @admin.action(description="Unapprove selected students (block voting)")
    def unapprove_selected(self, request, queryset):
        eligible = queryset.filter(user__voterecord__isnull=True).distinct()
        n = eligible.update(is_approved=False)
        skipped = queryset.count() - n
        self.message_user(request, f"{n} student(s) unapproved; {skipped} with participation history unchanged.")


# Audit-only views: who voted (not for whom) and raw counts. Read-only on purpose.
class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(VoteRecord)
class VoteRecordAdmin(ReadOnlyAdmin):
    list_display = ("user", "position")
    list_filter = ("position__election", "position")


# Ballots are intentionally NOT registered in admin so individual votes can't be browsed or edited.
