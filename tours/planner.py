"""Trip planner helpers: reference IDs, estimates, WhatsApp messages."""

from __future__ import annotations

import hashlib
import secrets
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings

from .models import PlannerSeasonRate, TripInquiry


def generate_reference_id() -> str:
    return f"FH-{secrets.token_hex(4).upper()}"


def inquiry_fingerprint(*, email: str, phone: str, departure, return_date, place_slugs: list[str]) -> str:
    payload = "|".join(
        [
            (email or "").strip().lower(),
            (phone or "").strip(),
            str(departure),
            str(return_date),
            ",".join(sorted(place_slugs)),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seasonal_multiplier(departure: date | None, return_date: date | None) -> tuple[Decimal, str | None]:
    if not departure:
        return Decimal("1.00"), None
    trip_end = return_date or departure
    seasons = PlannerSeasonRate.objects.filter(is_active=True)
    for season in seasons:
        for start_year in range(departure.year - 1, trip_end.year + 1):
            season_start = date(start_year, season.start_month, season.start_day)
            end_year = start_year if (season.start_month, season.start_day) <= (season.end_month, season.end_day) else start_year + 1
            season_end = date(end_year, season.end_month, season.end_day)
            if season_start <= trip_end and season_end >= departure:
                return season.multiplier, season.name
    return Decimal("1.00"), None


def build_estimate(
    *,
    nights: int,
    travelers: int,
    stay=None,
    transport=None,
    activities=None,
    additional_services=None,
    departure=None,
    return_date=None,
) -> dict:
    """
    Build a transparent estimate from configured catalog amounts only.
    Missing amounts mean the customer should request a personalized quote.
    """
    activities = list(activities or [])
    additional_services = list(additional_services or [])
    missing = []
    lines = []

    if stay:
        if stay.estimate_per_night is None:
            missing.append("accommodation")
        else:
            lines.append(
                {
                    "key": "accommodation",
                    "label": f"{stay.name} × {max(nights, 1)} night{'s' if nights != 1 else ''}",
                    "amount": stay.estimate_per_night * max(nights, 1),
                }
            )

    if transport:
        if transport.estimate_per_day is None:
            missing.append("transportation")
        else:
            trip_days = max(nights + 1, 1)
            lines.append(
                {
                    "key": "transportation",
                    "label": f"{transport.name} × {trip_days} day{'s' if trip_days != 1 else ''}",
                    "amount": transport.estimate_per_day * trip_days,
                }
            )

    activity_total = 0
    priced_activities = 0
    for activity in activities:
        if activity.estimate_amount is None:
            missing.append(f"activity:{activity.slug}")
            continue
        amount = activity.estimate_amount * max(travelers, 1)
        activity_total += amount
        priced_activities += 1
        lines.append(
            {
                "key": f"activity:{activity.slug}",
                "label": f"{activity.name} × {max(travelers, 1)} traveller{'s' if travelers != 1 else ''}",
                "amount": amount,
            }
        )

    for service in additional_services:
        if service.estimate_amount is None:
            missing.append(f"service:{service.slug}")
            continue
        lines.append({
            "key": f"service:{service.slug}",
            "label": service.name,
            "amount": service.estimate_amount,
        })

    if priced_activities and activity_total:
        pass

    multiplier, season_name = seasonal_multiplier(departure, return_date)
    subtotal = 0
    has_priced_line = bool(lines)
    for line in lines:
        subtotal += line["amount"]

    available = has_priced_line and not missing
    total = None
    if available:
        total = int((Decimal(subtotal) * multiplier).quantize(Decimal("1")))

    return {
        "available": available,
        "message": (
            None
            if available
            else "Request a Personalized Quote"
        ),
        "disclaimer": (
            "This is an indicative estimate from configured rates, not a confirmed quotation."
            if available
            else "Final pricing is confirmed by Flavour Holidays after reviewing your itinerary."
        ),
        "nights": nights,
        "travelers": travelers,
        "season": season_name,
        "season_multiplier": str(multiplier) if season_name else None,
        "lines": lines,
        "subtotal": subtotal if has_priced_line else None,
        "total": total,
        "missing_components": missing,
    }


def whatsapp_number() -> str:
    return "".join(ch for ch in getattr(settings, "BUSINESS_WHATSAPP_NUMBER", "") if ch.isdigit())


def build_whatsapp_message(inquiry: TripInquiry) -> str:
    places = ", ".join(inquiry.places.order_by("tripinquiryplace__sort_order").values_list("name", flat=True)) or "Not specified"
    activities = ", ".join(inquiry.activities.values_list("name", flat=True)) or "None selected"
    services = ", ".join(inquiry.additional_services.values_list("name", flat=True)) or "None selected"
    stay = inquiry.stay_option.name if inquiry.stay_option else "Not specified"
    transport = inquiry.transport_option.name if inquiry.transport_option else "Not specified"
    budget = inquiry.budget_band.label if inquiry.budget_band else "Not specified"
    scope = inquiry.get_budget_scope_display()
    return (
        f"Hello Flavour Holidays, I submitted a custom trip enquiry.\n"
        f"Name: {inquiry.name}\n"
        f"Reference: {inquiry.reference_id}\n"
        f"Destinations: {places}\n"
        f"Travel dates: {inquiry.departure_date} to {inquiry.return_date}\n"
        f"Travellers: {inquiry.adults} adults, {inquiry.children} children, {inquiry.infants} infants\n"
        f"Stay: {stay}\n"
        f"Transport: {transport}\n"
        f"Activities: {activities}\n"
        f"Additional services: {services}\n"
        f"Budget: {budget} ({scope})"
    )


def whatsapp_url(inquiry: TripInquiry) -> str | None:
    number = whatsapp_number()
    if not number:
        return None
    from urllib.parse import quote
    return f"https://wa.me/{number}?text={quote(build_whatsapp_message(inquiry))}"


def parse_iso_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not value:
        return None
    return date.fromisoformat(str(value))
