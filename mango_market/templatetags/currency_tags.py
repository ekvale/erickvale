"""
Template tags for currency conversion.
"""
from django import template
from ..utils import tzs_to_usd

register = template.Library()


@register.filter
def to_usd(tzs_amount):
    """Convert TZS to USD for display."""
    if tzs_amount is None:
        return None
    return tzs_to_usd(tzs_amount)


@register.filter
def currency_display(tzs_amount, show_both=True):
    """Display amount in both TZS and USD."""
    if tzs_amount is None or tzs_amount == '':
        return "N/A"
    
    try:
        tzs_value = float(tzs_amount)
        if tzs_value == 0:
            return "0 TZS ($0.00 USD)"
        usd_value = tzs_to_usd(tzs_value)
        
        if show_both:
            return f"{tzs_value:,.0f} TZS (${usd_value:,.2f} USD)"
        else:
            return f"{tzs_value:,.0f} TZS"
    except (ValueError, TypeError):
        return "N/A"
