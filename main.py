"""Offer Copilot command-line app.

Usage (after `export $(grep -v '^#' .env | xargs)`):
    .venv/bin/python main.py services
    .venv/bin/python main.py customers
    .venv/bin/python main.py add-note 1 2026-11-20 "Wants an AI setup and a workshop, budget 5000"
    .venv/bin/python main.py create-offer 1 --budget 5000 --want "AI setup=10" --want "Workshop=5"
    .venv/bin/python main.py offers 1
    .venv/bin/python main.py show-offer 1
    .venv/bin/python main.py set-status 1 sent
    .venv/bin/python main.py compare --budget 5000 --want "AI setup=10" --want "Workshop=5"

There is no login yet, so the app works for company 1 and the seeded test user.
"""

import argparse
import time
from datetime import date
from decimal import Decimal

import psycopg

import db
from knapsack import brute_force, repeated_hill_climbing, util
from models import Candidate, Service

COMPANY_ID: int = 1
CURRENT_USER_EMAIL: str = "test@example.com"
HILL_CLIMBING_RESTARTS: int = 10


def parse_wants(wants: list[str]) -> dict[str, int]:
    """Turn ["AI setup=10", "Workshop=5"] into {"AI setup": 10, "Workshop": 5}."""
    priorities: dict[str, int] = {}
    for want in wants:
        name, separator, value = want.rpartition("=")
        if separator == "" or not value.strip().isdigit():
            raise ValueError(f"Expected 'Service name=priority', got {want!r}")
        priorities[name.strip()] = int(value)
    return priorities


def build_candidates(services: list[Service], priorities: dict[str, int]) -> list[Candidate]:
    """Pair every wanted service with its priority; raise if a wanted service does not exist."""
    known_names: set[str] = {service.name for service in services}
    unknown_names: set[str] = set(priorities) - known_names
    if unknown_names:
        raise ValueError(f"Unknown services: {sorted(unknown_names)}. See: main.py services")
    return [Candidate(service=service, value=priorities[service.name]) for service in services if service.name in priorities]


def selected_services(candidates: list[Candidate], selection: list[bool]) -> list[Service]:
    """Return the services whose bit is True in the selection."""
    return [candidate.service for candidate, chosen in zip(candidates, selection) if chosen]


def show_services(connection: psycopg.Connection) -> None:
    for service in db.load_services(connection, COMPANY_ID):
        print(f"{service.id:>3}  {service.name:<22} {service.unit_price:>10} EUR")


def show_customers(connection: psycopg.Connection) -> None:
    for customer in db.load_customers(connection, COMPANY_ID):
        print(f"{customer.id:>3}  {customer.company_name:<28} {customer.contact_name or ''}")


def add_note(connection: psycopg.Connection, customer_id: int, call_date: date, notes: str) -> None:
    note_id: int = db.add_discovery_note(connection, customer_id, call_date, notes)
    print(f"Saved discovery note #{note_id}")


def create_offer(connection: psycopg.Connection, customer_id: int, budget: Decimal, wants: list[str]) -> None:
    candidates: list[Candidate] = build_candidates(db.load_services(connection, COMPANY_ID), parse_wants(wants))
    selection: list[bool] = brute_force(candidates, budget)
    user_id: int = db.find_user_id(connection, CURRENT_USER_EMAIL)
    offer_id: int = db.save_offer(connection, customer_id, user_id, selected_services(candidates, selection))
    print(f"Saved offer #{offer_id} with value {util(candidates, selection, budget)}")
    show_offer(connection, offer_id)


def show_offers(connection: psycopg.Connection, customer_id: int) -> None:
    for offer in db.list_offers(connection, customer_id):
        print(f"#{offer.id:<4} {offer.status:<9} {offer.created_at:%Y-%m-%d %H:%M}  {offer.total:>10} EUR  by {offer.created_by_email}")


def show_offer(connection: psycopg.Connection, offer_id: int) -> None:
    for item in db.load_offer_items(connection, offer_id):
        print(f"  {item.service_name:<22} {item.quantity:>5} x {item.unit_price:>10} EUR")
    print(f"  {'Total (calculated in SQL)':<38} {db.offer_total(connection, offer_id):>10} EUR")


def set_status(connection: psycopg.Connection, offer_id: int, status: str) -> None:
    db.set_offer_status(connection, offer_id, status)
    print(f"Offer #{offer_id} is now {status}")


def compare(connection: psycopg.Connection, budget: Decimal, wants: list[str]) -> None:
    """SE_14: compare the exact brute force result with repeated hill climbing."""
    candidates: list[Candidate] = build_candidates(db.load_services(connection, COMPANY_ID), parse_wants(wants))
    print(f"{len(candidates)} services, budget {budget} EUR, {2 ** len(candidates)} combinations")
    for label, run in (
        ("Brute force", lambda: brute_force(candidates, budget)),
        ("Hill climbing", lambda: repeated_hill_climbing(candidates, budget, HILL_CLIMBING_RESTARTS)),
    ):
        start: float = time.perf_counter()
        selection: list[bool] = run()
        milliseconds: float = (time.perf_counter() - start) * 1000
        names: list[str] = [service.name for service in selected_services(candidates, selection)]
        print(f"{label:<14} value {util(candidates, selection, budget):>3} in {milliseconds:8.2f} ms  {names}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offer Copilot")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("services", help="list services and prices")
    commands.add_parser("customers", help="list customers")

    note = commands.add_parser("add-note", help="store discovery notes of a sales call")
    note.add_argument("customer_id", type=int)
    note.add_argument("call_date", type=date.fromisoformat)
    note.add_argument("notes")

    create = commands.add_parser("create-offer", help="build and save the best offer within budget")
    create.add_argument("customer_id", type=int)
    create.add_argument("--budget", type=Decimal, required=True)
    create.add_argument("--want", action="append", required=True, help='"Service name=priority"')

    comparison = commands.add_parser("compare", help="compare brute force and hill climbing (SE_14)")
    comparison.add_argument("--budget", type=Decimal, required=True)
    comparison.add_argument("--want", action="append", required=True, help='"Service name=priority"')

    offers = commands.add_parser("offers", help="list offers of a customer with totals")
    offers.add_argument("customer_id", type=int)

    offer = commands.add_parser("show-offer", help="show the items of an offer")
    offer.add_argument("offer_id", type=int)

    status = commands.add_parser("set-status", help="change the status of an offer")
    status.add_argument("offer_id", type=int)
    status.add_argument("status", choices=["draft", "sent", "accepted", "rejected"])
    return parser


def main() -> None:
    args = build_parser().parse_args()
    with db.connect() as connection:
        match args.command:
            case "services":
                show_services(connection)
            case "customers":
                show_customers(connection)
            case "add-note":
                add_note(connection, args.customer_id, args.call_date, args.notes)
            case "create-offer":
                create_offer(connection, args.customer_id, args.budget, args.want)
            case "offers":
                show_offers(connection, args.customer_id)
            case "show-offer":
                show_offer(connection, args.offer_id)
            case "set-status":
                set_status(connection, args.offer_id, args.status)
            case "compare":
                compare(connection, args.budget, args.want)


if __name__ == "__main__":
    main()
