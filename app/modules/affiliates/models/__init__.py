"""Affiliate Models"""
from app.modules.affiliates.models.affiliate_partner_model import AffiliatePartner
from app.modules.affiliates.models.affiliate_agreement_model import AffiliateAgreement
from app.modules.affiliates.models.affiliate_earning_model import AffiliateEarningEvent, AffiliatePayout

__all__ = [
    "AffiliatePartner",
    "AffiliateAgreement",
    "AffiliateEarningEvent",
    "AffiliatePayout",
]
