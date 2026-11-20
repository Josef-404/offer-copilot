"""Knapsack optimizer: choose the services with the highest total value within the customer's budget.

Function signatures prepared with AI assistance (Claude); the algorithms are written by me without AI (SE_14 requirement).

A solution is a list of booleans, one per candidate: True = the service goes into the offer.
"""

from decimal import Decimal

from models import Candidate

from itertools import product


def util(candidates: list[Candidate], selection: list[bool], budget: Decimal) -> int:
    """Total value of the selected services, or -1 if the selection exceeds the budget."""
    price = Decimal ("0")
    value = 0
    for candidate, chosen in zip(candidates, selection):
        if chosen:
            price = price + candidate.service.unit_price
            value += candidate.value
    if price > budget:
        return -1
    else:
        return value
            


def brute_force(candidates: list[Candidate], budget: Decimal) -> list[bool]:
    """Try every combination (grid search with step 1) and return the best one."""
    best_value = -1
    best_selection = [False] * len(candidates)
    for selection in product([False, True], repeat=len(candidates)):
        score = util(candidates, selection, budget)
        if score > best_value:
            best_value = score
            best_selection = list(selection)
    return best_selection
