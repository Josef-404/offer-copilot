"""Data models shared by the database layer and the optimizer."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Service:
    """A service a company sells, as stored in the `services` table."""

    id: int
    name: str
    unit_price: Decimal


@dataclass(frozen=True)
class Candidate:
    """A service the customer is interested in, with how much the customer values it.

    `value` is the priority of the service for this customer (higher = more important).
    Later it will come from the LLM extraction; for now it is entered by hand.
    """

    service: Service
    value: int


@dataclass(frozen=True)
class Customer:
    """A customer of a company, as stored in the `customers` table."""

    id: int
    company_name: str
    contact_name: str | None


@dataclass(frozen=True)
class OfferSummary:
    """One offer with its total, calculated in SQL."""

    id: int
    status: str
    created_at: datetime
    created_by_email: str
    total: Decimal


@dataclass(frozen=True)
class OfferItem:
    """One line of an offer, with the price that was valid when the offer was created."""

    service_name: str
    quantity: Decimal
    unit_price: Decimal
