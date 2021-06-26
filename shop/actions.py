def active_list_of_special_events(modeladmin, request, queryset):
    queryset.update(active_list=True)
    active_list_of_special_events.short_decription = "Active list of special events"


def deactive_list_of_special_events(modeladmin, request, queryset):
    queryset.update(active_list=False)
    deactive_list_of_special_events.short_decription = "Deactive list of special events"
