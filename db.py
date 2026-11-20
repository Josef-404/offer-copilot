"""Data layer: all SQL of Offer Copilot lives here.

Security: every query is parameterized (%s placeholders), user input is never
concatenated into SQL. The app connects as the least-privilege role offer_copilot_app.
"""

import os
from datetime import date
from decimal import Decimal

import psycopg

from models import Customer, OfferItem, OfferSummary, Service


def connect() -> psycopg.Connection:
    """Open a connection using DATABASE_URL from the environment (see .env.example)."""
    database_url: str | None = os.environ.get("DATABASE_URL")
    if database_url is None:
        raise RuntimeError("DATABASE_URL is not set. Run: export $(grep -v '^#' .env | xargs)")
    # autocommit: each `with connection.transaction()` block is its own real transaction
    return psycopg.connect(database_url, autocommit=True)


def load_services(connection: psycopg.Connection, company_id: int) -> list[Service]:
    """Return all services of one company (tenant isolation via company_id)."""
    rows = connection.execute(
        "SELECT id, name, unit_price FROM services WHERE company_id = %s ORDER BY id",
        (company_id,),
    ).fetchall()
    return [Service(id=row[0], name=row[1], unit_price=row[2]) for row in rows]


def save_offer(
    connection: psycopg.Connection,
    customer_id: int,
    created_by: int,
    services: list[Service],
) -> int:
    """Save an offer and its items in ONE transaction and return the new offer id.

    Either the offer and all its items are stored, or nothing is (atomicity).
    Prices are copied into offer_items, so later price changes do not alter sent offers.
    """
    with connection.transaction():
        offer_id: int = connection.execute(
            "INSERT INTO offers (customer_id, created_by) VALUES (%s, %s) RETURNING id",
            (customer_id, created_by),
        ).fetchone()[0]
        for service in services:
            connection.execute(
                "INSERT INTO offer_items (offer_id, service_id, quantity, unit_price) "
                "VALUES (%s, %s, %s, %s)",
                (offer_id, service.id, Decimal("1"), service.unit_price),
            )
    return offer_id


def offer_total(connection: psycopg.Connection, offer_id: int) -> Decimal:
    """Return the total of an offer, calculated in SQL from the stored items."""
    return connection.execute(
        "SELECT COALESCE(SUM(quantity * unit_price), 0)::NUMERIC(12,2) FROM offer_items WHERE offer_id = %s",
        (offer_id,),
    ).fetchone()[0]


def find_user_id(connection: psycopg.Connection, email: str) -> int:
    """Return the id of the user with this email, or raise LookupError if there is none."""
    row = connection.execute("SELECT id FROM users WHERE email = %s", (email,)).fetchone()
    if row is None:
        raise LookupError(f"No user with email {email!r}. Did you run seed.sql?")
    return row[0]


def load_customers(connection: psycopg.Connection, company_id: int) -> list[Customer]:
    """Return all customers of one company."""
    rows = connection.execute(
        "SELECT id, company_name, contact_name FROM customers WHERE company_id = %s ORDER BY id",
        (company_id,),
    ).fetchall()
    return [Customer(id=row[0], company_name=row[1], contact_name=row[2]) for row in rows]


def add_discovery_note(connection: psycopg.Connection, customer_id: int, call_date: date, notes: str) -> int:
    """Store the notes of a sales call and return the new note id."""
    return connection.execute(
        "INSERT INTO discovery_notes (customer_id, call_date, notes) VALUES (%s, %s, %s) RETURNING id",
        (customer_id, call_date, notes),
    ).fetchone()[0]


def list_offers(connection: psycopg.Connection, customer_id: int) -> list[OfferSummary]:
    """Return all offers of a customer with creator and total (JOIN + GROUP BY in SQL)."""
    rows = connection.execute(
        "SELECT o.id, o.status, o.created_at, u.email, "
        "       COALESCE(SUM(i.quantity * i.unit_price), 0)::NUMERIC(12,2) "
        "FROM offers o "
        "JOIN users u ON u.id = o.created_by "
        "LEFT JOIN offer_items i ON i.offer_id = o.id "
        "WHERE o.customer_id = %s "
        "GROUP BY o.id, u.email "
        "ORDER BY o.id",
        (customer_id,),
    ).fetchall()
    return [
        OfferSummary(id=row[0], status=row[1], created_at=row[2], created_by_email=row[3], total=row[4])
        for row in rows
    ]


def load_offer_items(connection: psycopg.Connection, offer_id: int) -> list[OfferItem]:
    """Return the lines of an offer (n:m: offers ↔ services via offer_items)."""
    rows = connection.execute(
        "SELECT s.name, i.quantity, i.unit_price "
        "FROM offer_items i JOIN services s ON s.id = i.service_id "
        "WHERE i.offer_id = %s ORDER BY i.id",
        (offer_id,),
    ).fetchall()
    return [OfferItem(service_name=row[0], quantity=row[1], unit_price=row[2]) for row in rows]


def set_offer_status(connection: psycopg.Connection, offer_id: int, status: str) -> None:
    """Change the status of an offer; the CHECK constraint rejects unknown statuses."""
    updated = connection.execute(
        "UPDATE offers SET status = %s WHERE id = %s", (status, offer_id)
    ).rowcount
    if updated == 0:
        raise LookupError(f"No offer with id {offer_id}")
