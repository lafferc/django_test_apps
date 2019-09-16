from django.contrib import admin
from member.models import Profile, Organisation, Competition, Ticket
import logging

g_logger = logging.getLogger(__name__)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    readonly_fields = ('used', 'token')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class ParticipantInline(admin.TabularInline):
    model = Competition.participants.through
    extra = 0

def add_tickets(modeladmin, request, queryset):
    g_logger.debug("add_tickets(%r, %r, %r)", modeladmin, request, queryset)
    for comp in queryset:
        for i in range(10):
            Ticket.objects.create(competition=comp)


class CompetitionAdmin(admin.ModelAdmin):
    inlines = ( TicketInline, ParticipantInline)
    actions = [ add_tickets ]
    list_display = ('organisation', 'tournament', 'participant_count')
    fields = ('organisation', 'tournament', 'token_len')

    def participant_count(self, obj):
        return obj.participants.count();

    def get_readonly_fields(self, request, obj):
        return obj and ('organisation', 'tournament') or []

    def get_inline_instances(self, request, obj=None):
        return obj and super(CompetitionAdmin, self).get_inline_instances(request, obj) or []


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'test_features_enabled')

admin.site.register(Profile)
admin.site.register(Organisation)
admin.site.register(Competition, CompetitionAdmin)
