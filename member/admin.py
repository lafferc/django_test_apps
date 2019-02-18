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


def add_tickets(modeladmin, request, queryset):
    g_logger.debug("add_tickets(%r, %r, %r)", modeladmin, request, queryset)
    for comp in queryset:
        for i in range(10):
            Ticket.objects.create(competition=comp)


class CompetitionAdmin(admin.ModelAdmin):
    inlines = ( TicketInline, )
    actions = [ add_tickets ]
    list_display = ('organisation', 'tournament', 'participant_count')

    def participant_count(self, obj):
        return obj.participants.count();

admin.site.register(Profile)
admin.site.register(Organisation)
admin.site.register(Competition, CompetitionAdmin)
