from django.contrib import admin
from .models import SpecialEvents


@admin.register(SpecialEvents)
class FavoriteAdmin(admin.ModelAdmin):
    model = SpecialEvents
    filter_horizontal = ('event',)
    search_fields = ('event',)
    autocomplete_fields = ['event']
    # list_display = ['event', ]
