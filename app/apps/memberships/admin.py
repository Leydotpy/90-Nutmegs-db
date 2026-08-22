from django.contrib import admin

# Register your models here.
from .models import Membership, Plan, Feature, Subscription, Entitlement, AddOn, PlanFeature


class PlanFeatureInline(admin.StackedInline):
    model = PlanFeature
    extra = 0
    can_delete = True

class MembershipInline(admin.StackedInline):
    model = Membership
    extra = 0
    can_delete = True


class FeatureAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'slug', 'is_content_feature')
    class Meta:
        model = Feature


class PlanAdmin(admin.ModelAdmin):
    inlines = [MembershipInline, PlanFeatureInline]
    list_display = ('id', 'name', 'tier', 'price_monthly', 'price_annual')
    list_display_links = ('id', 'name')
    class Meta:
        model = Plan



class SubscriptionAdmin(admin.ModelAdmin):
    class Meta:
        model = Subscription


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    can_delete = True


class MembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan__name', 'user__username', 'customer_id')
    inlines = [SubscriptionInline]
    class Meta:
        model = Membership

class EntitlementAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'content_object', "granted_at", "expires_at", "revoked")
    class Meta:
        model = Entitlement

admin.site.register(Membership, MembershipAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Entitlement, EntitlementAdmin)
admin.site.register(Feature, FeatureAdmin)
admin.site.register(AddOn)