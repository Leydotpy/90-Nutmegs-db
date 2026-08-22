from django.contrib import admin
from apps.persons.models import Player, Staff, Fitness, Injury, InjuryType


class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "age", "slug", "code")
    list_filter = ("code", "age")
    search_fields = ("name", "code")

    class Meta:
        model = Player
        fields = ("team", "name", "age", "code")


class StaffAdmin(admin.ModelAdmin):
    list_filter = ("code", "slug", "job")
    list_display = ("name", "age", "job", "slug", "code")

    class Meta:
        model = Staff
        fields = ("name", "age", "code", "job")


admin.site.register(Player, PlayerAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Fitness)
admin.site.register(Injury)
admin.site.register(InjuryType)