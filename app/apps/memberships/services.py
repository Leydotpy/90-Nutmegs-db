from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

from .models import Entitlement, Plan, Subscription
from apps.billing.models import Transaction


def _create_entitlement(user, content_obj, *, purchase=None, subscription=None, expires_at=None, notes=None):
    ct = ContentType.objects.get_for_model(type(content_obj))
    ent = Entitlement.objects.create(
        user=user,
        content_type=ct,
        object_id=str(getattr(content_obj, "id", getattr(content_obj, "pk"))),
        granted_by_purchase=purchase,
        granted_by_subscription=subscription,
        expires_at=expires_at,
        notes=notes or "",
    )
    return ent

# 1) Single-episode purchase flow (used in webhook handler)
def grant_single_episode_purchase(user, episode, purchase: Transaction):
    """
    Called after payment success. Creates purchase (if not already) and grants entitlement.
    """
    with transaction.atomic():
        if purchase.status != "completed":
            purchase.mark_completed()
        ent = _create_entitlement(user, episode, purchase=purchase)
    return ent

# 2) Temporary promo access (e.g., 7-day Pro access)
def grant_temporary_promo_plan_like_entitlement(user, plan_like_slug, days=7, purchase=None, notes=None):
    """
    Grants an entitlement that mimics plan access by creating a synthetic entitlement object
    that points at the Plan model (or another sentinel object). Two patterns:
      A) If you want entitlement to grant plan-like behavior, point to Plan object via ContentType.
      B) Or store plan slug in notes and check for it in has_access fallback.
    """
    plan_ct = ContentType.objects.get_for_model(Plan)
    plan = Plan.objects.get(slug=plan_like_slug)
    expires_at = timezone.now() + timedelta(days=days)
    ent = Entitlement.objects.create(
        user=user,
        content_type=plan_ct,
        object_id=str(plan.id),
        granted_by_purchase=purchase,
        expires_at=expires_at,
        notes=notes or f"Promo {plan_like_slug} for {days}d"
    )
    return ent

# 3) Event ticket grant
# def grant_event_ticket(user, event: LiveEvent, purchase=None, via_subscription: Subscription = None):
#     """
#     Create EventTicket and entitlement (optional depending on flow).
#     """
#     # create EventTicket (unique_together prevents duplicates)
#     ticket, created = EventTicket.objects.get_or_create(user=user, event=event, defaults={
#         "via_subscription": via_subscription
#     })
#     # create entitlement pointing at event if you want general access checks to use entitlements.
#     ent = _create_entitlement(user, event, purchase=purchase, subscription=via_subscription)
#     return ticket, ent

# 4) Coaching session / small-group video call access
def grant_coaching_session_access(user, session_obj, purchase=None, expires_at=None):
    """
    session_obj could be a Meeting/Event resource. Grant entitlement for that meeting.
    """
    return _create_entitlement(user, session_obj, purchase=purchase, expires_at=expires_at, notes="coaching_session")

# 5) Gifted annual subscription
def grant_gifted_subscription_entitlement(user, plan_slug, length_days=365, purchased_by=None, notes=None):
    """
    Instead of creating a Subscription object for the recipient, you can create a plan-targeting entitlement
    that `has_access` recognizes as giving plan permissions for the TTL.
    """
    plan = Plan.objects.get(slug=plan_slug)
    expires_at = timezone.now() + timedelta(days=length_days)
    ent = Entitlement.objects.create(
        user=user,
        content_type=ContentType.objects.get_for_model(Plan),
        object_id=str(plan.id),
        expires_at=expires_at,
        notes=(notes or "") + (f" Gifted by purchase {purchased_by.id}" if purchased_by else "")
    )
    return ent

# 6) Merch voucher redemption (grant entitlement that is later checked at checkout)
def redeem_merch_voucher_for_user(user, voucher_obj, purchase=None):
    """
    Voucher object could be a Merchandise or Voucher model; we create an entitlement granting the
    voucher (coupon) to the user, which you can check at checkout.
    """
    return _create_entitlement(user, voucher_obj, purchase=purchase, notes="merch voucher redemption")

# 7) Revoke entitlement / refund flow
def refund_purchase_and_revoke_entitlements(purchase: Transaction, reason: str = "Refunded"):
    """
    Marks the purchase refunded and revokes all entitlements created by the purchase.
    """
    with transaction.atomic():
        purchase.mark_refunded()
        ents = Entitlement.objects.filter(granted_by_purchase=purchase, revoked=False)
        for e in ents:
            e.revoke(reason=reason)
    return ents

# 8) Admin grant or revoke helpers
def admin_grant_entitlement(user, content_obj, admin_user, expires_at=None, notes=None):
    ent = _create_entitlement(user, content_obj, notes=(notes or "") + f" (granted by admin={admin_user.pk})", expires_at=expires_at)
    return ent

def admin_revoke_entitlement(entitlement: Entitlement, admin_user, reason=None):
    reason_note = f"Revoked by admin={admin_user.pk}" + (f": {reason}" if reason else "")
    entitlement.revoke(reason=reason_note)
    return entitlement
