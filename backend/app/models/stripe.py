"""
Stripe API models.

This module defines minimal Pydantic models for Stripe webhook handling.
Payment and subscription management are handled through Stripe's hosted solutions.
"""

# Note: This file is kept minimal as most Stripe interactions
# are handled through Stripe's hosted solutions (Pricing Table, Customer Portal).
# Only webhook processing requires custom models, which use standard dict responses.
