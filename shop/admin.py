from django.contrib import admin
from .models import SpecialEvents


@admin.register(SpecialEvents)
class SpecialAdmin(admin.ModelAdmin):
    model = SpecialEvents
    filter_horizontal = ('event',)
    search_fields = ('name_special_event_list',)
    autocomplete_fields = ['event']
    list_display = ['name_special_event_list', 'special_events', 'active_list']
