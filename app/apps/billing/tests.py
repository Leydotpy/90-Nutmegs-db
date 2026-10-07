import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone

from apps.billing.models import Bankcard, Source, SourceType, Transaction
from apps.memberships.models import Entitlement, Membership, Plan, Subscription
from apps.memberships.policies import AccessAction, AccessPolicy, AccessReason
from apps.posts.podcasts.models import Episode, Podcast


class BillingFixtureMixin:
    def setUp(self):
        self.user = get_user_model().objects.create(
            username="billing-listener",
            clerk_user_id="clerk_billing_listener",
        )
        self.plan = Plan.objects.create(name="Billing fixture", tier=Plan.Level.FAN)
        self.entitlement = Entitlement.objects.create(
            user=self.user,
            content_type=ContentType.objects.get_for_model(self.plan),
            object_id=str(self.plan.pk),
        )
        self.source_type = SourceType.objects.create(name="Provider token")
        self.source = Source.objects.create(
            order=self.entitlement,
            source_type=self.source_type,
            reference="provider-source-1",
        )


class TransactionStateTests(BillingFixtureMixin, TestCase):
    def create_transaction(self, *, status=Transaction.Status.PENDING):
        return Transaction.objects.create(
            source=self.source,
            amount=Decimal("12.50"),
            reference="provider-payment-1",
            status=status,
        )

    def test_pending_transaction_completes_once_and_preserves_timestamp(self):
        completed_at = timezone.now().replace(microsecond=0)
        payment = self.create_transaction()

        result = payment.mark_completed(completed_at=completed_at)
        result.mark_completed(completed_at=completed_at + datetime.timedelta(days=1))
        payment.refresh_from_db()

        self.assertIs(result, payment)
        self.assertEqual(payment.status, Transaction.Status.COMPLETED)
        self.assertEqual(payment.completed_at, completed_at)

    def test_only_completed_transaction_can_be_refunded(self):
        pending = self.create_transaction()

        with self.assertRaisesRegex(ValueError, "Cannot refund"):
            pending.mark_refunded()

        pending.refresh_from_db()
        self.assertEqual(pending.status, Transaction.Status.PENDING)

    def test_completed_transaction_refund_is_idempotent_and_terminal(self):
        payment = self.create_transaction()
        payment.mark_completed()

        result = payment.mark_refunded()
        result.mark_refunded()

        self.assertIs(result, payment)
        self.assertEqual(payment.status, Transaction.Status.REFUNDED)
        with self.assertRaisesRegex(ValueError, "Cannot complete"):
            payment.mark_completed()

    def test_stale_pending_instance_cannot_overwrite_refunded_terminal_row(self):
        payment = self.create_transaction()
        stale_pending = Transaction.objects.get(pk=payment.pk)
        payment.mark_completed()
        payment.mark_refunded()

        with self.assertRaisesRegex(ValueError, "Cannot complete"):
            stale_pending.mark_completed()

        payment.refresh_from_db()
        self.assertEqual(payment.status, Transaction.Status.REFUNDED)
        self.assertEqual(stale_pending.status, Transaction.Status.REFUNDED)


class SourceLedgerTests(BillingFixtureMixin, TestCase):
    def test_allocate_debit_and_refund_keep_ledger_totals_coherent(self):
        authorisation = self.source.allocate(Decimal("100.00"), reference="auth-1")
        debit = self.source.debit(Decimal("40.00"), reference="debit-1")
        refund = self.source.refund(Decimal("15.00"), reference="refund-1")
        self.source.refresh_from_db()

        self.assertEqual(self.source.amount_allocated, Decimal("100.00"))
        self.assertEqual(self.source.amount_debited, Decimal("40.00"))
        self.assertEqual(self.source.amount_refunded, Decimal("15.00"))
        self.assertEqual(self.source.balance, Decimal("75.00"))
        self.assertEqual(self.source.amount_available_for_refund, Decimal("25.00"))
        self.assertEqual(
            [authorisation.txn_type, debit.txn_type, refund.txn_type],
            [Transaction.AUTHORISE, Transaction.DEBIT, Transaction.REFUND],
        )
        self.assertTrue(
            all(
                item.status == Transaction.Status.PENDING for item in (authorisation, debit, refund)
            )
        )

    def test_impossible_amounts_do_not_mutate_source_or_create_transactions(self):
        self.source.allocate(Decimal("20.00"))
        initial_count = self.source.transactions.count()

        with self.assertRaisesRegex(ValueError, "greater than zero"):
            self.source.debit(Decimal("0.00"))
        with self.assertRaisesRegex(ValueError, "available balance"):
            self.source.debit(Decimal("20.01"))
        with self.assertRaisesRegex(ValueError, "available for refund"):
            self.source.refund(Decimal("0.01"))

        self.source.refresh_from_db()
        self.assertEqual(self.source.amount_debited, Decimal("0.00"))
        self.assertEqual(self.source.amount_refunded, Decimal("0.00"))
        self.assertEqual(self.source.transactions.count(), initial_count)

    def test_deferred_transaction_is_created_only_once(self):
        deferred_source = Source(
            order=self.entitlement,
            source_type=self.source_type,
            reference="deferred-source",
        )
        deferred_source.create_deferred_transaction(
            Transaction.AUTHORISE,
            Decimal("8.00"),
            reference="deferred-auth",
        )

        deferred_source.save()
        deferred_source.save()

        transaction_row = deferred_source.transactions.get()
        self.assertEqual(transaction_row.status, Transaction.Status.PENDING)


class BankcardStorageTests(BillingFixtureMixin, TestCase):
    def test_saved_bankcard_retains_only_obfuscated_number_and_no_cvv(self):
        card = Bankcard(
            user=self.user,
            name="Test Listener",
            number="4111111111111111",
            expiry_date=datetime.date.today() + datetime.timedelta(days=365),
            ccv="123",
        )

        card.save()
        stored = Bankcard.objects.get(pk=card.pk)

        self.assertEqual(stored.number, "XXXX-XXXX-XXXX-1111")
        self.assertIsNone(stored.ccv)


class SubscriptionCancellationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username="cancel-listener",
            clerk_user_id="clerk_cancel_listener",
        )
        self.plan = Plan.objects.create(
            name="Cancellation fixture",
            tier=Plan.Level.FAN,
        )
        self.membership = Membership.objects.create(user=self.user, plan=self.plan)

    def create_subscription(self, *, auto_renew, end_date=None):
        return Subscription.objects.create(
            membership=self.membership,
            subscription_id="provider-subscription-1",
            status=Subscription.Status.ACTIVE,
            auto_renew=auto_renew,
            end_date=end_date,
        )

    def test_canceling_renewal_persists_paid_through_end(self):
        subscription = self.create_subscription(auto_renew=True)
        paid_through = timezone.now() + datetime.timedelta(days=20)

        result = subscription.cancel(when=paid_through)
        subscription.refresh_from_db()

        self.assertIs(result, subscription)
        self.assertFalse(subscription.auto_renew)
        self.assertEqual(subscription.status, Subscription.Status.CANCELED)
        self.assertEqual(subscription.end_date, paid_through)
        self.assertTrue(subscription.is_active())
        self.assertTrue(
            Subscription.objects.active_for_user(self.user).filter(pk=subscription.pk).exists()
        )

    def test_cancel_at_period_end_is_idempotent(self):
        subscription = self.create_subscription(auto_renew=True)
        paid_through = timezone.now() + datetime.timedelta(days=20)

        subscription.cancel(when=paid_through)
        # Reload to prove the retry distinction is durable, not instance-local.
        subscription = Subscription.objects.get(pk=subscription.pk)
        subscription.cancel(when=paid_through)
        subscription.refresh_from_db()

        self.assertFalse(subscription.auto_renew)
        self.assertEqual(subscription.status, Subscription.Status.CANCELED)
        self.assertEqual(subscription.end_date, paid_through)

    def test_fixed_term_subscription_cancels_immediately(self):
        natural_end = timezone.now() + datetime.timedelta(days=20)
        subscription = self.create_subscription(
            auto_renew=False,
            end_date=natural_end,
        )
        canceled_at = timezone.now().replace(microsecond=0)

        subscription.cancel(when=canceled_at)
        subscription.refresh_from_db()

        self.assertEqual(subscription.status, Subscription.Status.CANCELED)
        self.assertEqual(subscription.end_date, canceled_at)
        self.assertNotEqual(subscription.end_date, natural_end)
        self.assertFalse(subscription.is_active())
        self.assertFalse(
            Subscription.objects.active_for_user(self.user).filter(pk=subscription.pk).exists()
        )

    def test_stale_active_instance_cannot_resurrect_expired_subscription(self):
        now = timezone.now().replace(microsecond=0)
        subscription = self.create_subscription(auto_renew=True)
        stale_active = Subscription.objects.get(pk=subscription.pk)
        expired_at = now - datetime.timedelta(seconds=1)
        Subscription.objects.filter(pk=subscription.pk).update(
            status=Subscription.Status.EXPIRED,
            active=False,
            auto_renew=False,
            end_date=expired_at,
        )

        stale_active.cancel(when=now + datetime.timedelta(days=20))

        subscription.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.Status.EXPIRED)
        self.assertEqual(subscription.end_date, expired_at)
        self.assertEqual(stale_active.status, Subscription.Status.EXPIRED)
        self.assertEqual(stale_active.end_date, expired_at)
        self.assertFalse(stale_active.active)
        self.assertFalse(stale_active.is_active())

        podcast = Podcast.objects.create(
            title="Expired access fixture",
            status=Podcast.PublicationStatus.PUBLISHED,
            published_at=now - datetime.timedelta(days=1),
        )
        premium_episode = Episode.objects.create(
            podcast=podcast,
            title="Expired premium episode",
            exclusive=True,
            public_release_date=now - datetime.timedelta(days=1),
            status=Episode.PublicationStatus.PUBLISHED,
            visibility=Episode.Visibility.PLAN,
            premium_available_at=now - datetime.timedelta(days=1),
            required_plan=self.plan,
        )
        decision = AccessPolicy().evaluate(
            user=self.user,
            resource=premium_episode,
            action=AccessAction.STREAM,
            now=now,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, AccessReason.EXPIRED)
