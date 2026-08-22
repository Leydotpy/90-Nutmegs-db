from django.contrib import admin

from .models import Package, Packaging, License, Device


class PackageAdmin(admin.ModelAdmin):

    list_display = ("id", "created_by__username", "episode__title", "storage_key", "encrypted_dek", "created_at")
    list_filter = ("episode__title", "storage_key", "created_at")

    class Meta:
        model = Package

    def get_readonly_fields(self, request, obj=None):
        return obj._meta.get_fields()


class LicenseAdmin(admin.ModelAdmin):
    list_display = ("user__username", "device__id", "issued_at", "expires_at")

    def get_readonly_fields(self, request, obj=None):
        return obj._meta.get_fields()

    class Meta:
        model = License


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "user__username", "device_type", "device_id", "platform")

    class Meta:
        model = Device

    def get_readonly_fields(self, request, obj=None):
        return obj._meta.get_fields()


class PackagingAdmin(admin.ModelAdmin):

    class Meta:
        model = Packaging

    def get_readonly_fields(self, request, obj=None):
        return obj._meta.get_fields()


admin.site.register(Package, PackageAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Packaging, PackagingAdmin)