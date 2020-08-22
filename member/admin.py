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

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):

        field = super(ParticipantInline, self).formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'participant':
            if request._obj_ is not None:
                field.queryset = field.queryset.filter(tournament=request._obj_.tournament)
            else:
                field.queryset = field.queryset.none()

        return field


def add_tickets(modeladmin, request, queryset):
    g_logger.debug("add_tickets(%r, %r, %r)", modeladmin, request, queryset)
    for comp in queryset:
        for i in range(10):
            Ticket.objects.create(competition=comp)


class CompetitionAdmin(admin.ModelAdmin):
    inlines = (TicketInline, ParticipantInline)
    actions = [add_tickets]
    list_display = ('organisation', 'tournament', 'participant_count')
    fields = ('organisation', 'tournament', 'token_len')

    def participant_count(self, obj):
        return obj.participants.count()

    def get_readonly_fields(self, request, obj):
        return obj and ('organisation', 'tournament') or []

    def get_inline_instances(self, request, obj=None):
        return obj and super(CompetitionAdmin, self).get_inline_instances(request, obj) or []

    def get_form(self, request, obj=None, **kwargs):
        # save obj reference for future processing in Inline
        request._obj_ = obj
        return super(CompetitionAdmin, self).get_form(request, obj, **kwargs)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'test_features_enabled')


admin.site.register(Profile)
admin.site.register(Organisation)
admin.site.register(Competition, CompetitionAdmin)
