from django.contrib import admin
from member.models import Profile, Organisation, Competition, Ticket

class TicketInline(admin.TabularInline):
    model = Ticket
    readonly_fields = ('used', 'token')


class CompetitionAdmin(admin.ModelAdmin):
    inlines = ( TicketInline, )


admin.site.register(Profile)
admin.site.register(Organisation)
admin.site.register(Competition, CompetitionAdmin)
admin.site.register(Ticket)
