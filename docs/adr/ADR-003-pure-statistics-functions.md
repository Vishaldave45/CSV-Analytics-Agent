# ADR-003: Pure Functions for Statistical Computation

## Status
Accepted

## Context
Computing column statistics (numeric, categorical, datetime) requires high reliability, state-free logic, and easy unit testing.

## Decision
Implement statistical computations as pure, stateless functions in `profiler/statistics.py` and rule checks in `insights/rules.py`.

## Consequences
* Eliminates class state, side effects, and memory leaks.
* Enables straightforward 100% unit test coverage.
* Decouples mathematical metric computation from dataset orchestrators.
