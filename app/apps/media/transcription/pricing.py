from decimal import Decimal

# keep these in settings or external pricing service in real infra
OPENAI_PRICE_PER_MINUTE = Decimal('0.006')
GOOGLE_PRICE_PER_MINUTE = Decimal('0.004')

def estimate_cost(provider: str, duration_seconds: int) -> Decimal:
    minutes = Decimal(duration_seconds) / Decimal(60)
    if provider == 'openai':
        return (minutes * OPENAI_PRICE_PER_MINUTE).quantize(Decimal('0.0001'))
    if provider == 'google':
        return (minutes * GOOGLE_PRICE_PER_MINUTE).quantize(Decimal('0.0001'))
    raise ValueError('Unknown provider')

def charge_user_quota(user, duration_seconds: int):
    # simplistic: decrement quota; raise if insufficient
    quota = user.usertranscriptionquota
    plan_minutes = quota.plan.get_transcription_quota()
    used = quota.used_seconds
    if used + duration_seconds > plan_minutes * 60:
        return False
    quota.used_seconds = used + duration_seconds
    quota.save(update_fields=['used_seconds'])
    return True