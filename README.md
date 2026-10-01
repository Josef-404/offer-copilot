# Offer Copilot

Turns discovery-call notes into a ready-to-send offer draft.

## Problem
Small businesses spend hours writing offers after every sales call.
In a discovery call, a decision-maker named offer creation as one of
their biggest time sinks.

## Solution
1. Paste the notes from a discovery call.
2. An LLM extracts the customer's needs and picks matching services.
3. The offer is calculated from the database and exported as a draft.

## Core idea
The LLM extracts and selects. It never calculates prices.
Services and prices live in a relational database, totals are computed
in SQL. No hallucinated prices, every number is traceable.

## Status
Work in progress: database schema.
