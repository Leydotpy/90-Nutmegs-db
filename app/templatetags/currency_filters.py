from decimal import Decimal as D
from decimal import InvalidOperation

from babel.numbers import format_currency
from django import template
from django.conf import settings
from django.utils.translation import get_language, to_locale

register = template.Library()


@register.filter(name='currency')
def currency(value, currency_=None):
    """
    Format decimal value as currency
    """
    if currency_ is None:
        currency_ = settings.DEFAULT_CURRENCY

    try:
        value = D(value)
    except (TypeError, InvalidOperation):
        return ""
    # Using Babel's currency formatting
    # http://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_currency
    STORE_CURRENCY_FORMAT = getattr(settings, 'STORE_CURRENCY_FORMAT', None)
    kwargs = {
        'currency': currency_,
        'locale': to_locale(get_language() or settings.LANGUAGE_CODE)
    }
    if isinstance(STORE_CURRENCY_FORMAT, dict):
        kwargs.update(STORE_CURRENCY_FORMAT.get(currency, {}))
    else:
        kwargs['format'] = STORE_CURRENCY_FORMAT
    return format_currency(value, **kwargs)
