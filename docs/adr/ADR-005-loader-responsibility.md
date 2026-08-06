# ADR-005: Boundary and Responsibilities of CSV Data Loader

## Status
Accepted

## Context
A key design decision in data pipeline architecture is determining whether the initial data loader should automatically coerce data types (e.g. parsing date strings, cleaning currency symbols, standardizing boolean strings, or inferring semantic types) or restrict its scope strictly to format reading and validation.

## Decision
The CSV Data Loader (`CSVLoader` and `CSVValidator`) exclusively reads and validates CSV files for structural integrity, encoding, and schema parsing. Domain-specific data coercion and semantic type casting belong to a separate, downstream preprocessing stage.

## Consequences
* **Cleaner Architecture**: Preserves Single Responsibility Principle (SRP) for file ingestion.
* **No Silent Data Modification**: Ingests raw data accurately without unpredictable implicit mutations.
* **Predictable Pipeline Behavior**: Prevents premature type parsing failures during ingestion.
* **Easier Testing**: Ingestion tests verify structural parsing without coupling to data cleaning logic.
