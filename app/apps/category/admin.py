from django.contrib import admin

from .models import Category


class CategoryAdmin(admin.ModelAdmin):
    readonly_fields = ("id", "slug", "tier", "created_at")

    class Meta:
        model = Category


admin.site.register(Category, CategoryAdmin)
