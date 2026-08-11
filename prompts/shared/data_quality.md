# Data Quality & Preprocessing Guidelines

1. **Type Awareness**: Verify data types (numeric, datetime, categorical) before triggering mathematical operations.
2. **Missing Values**: Detect and handle `NaN`/null values gracefully (e.g. using `.dropna()` or explicit null filtering) before computing aggregates.
3. **Coercion & Normalization**: Account for deterministic preprocessing (currency symbols `$`, percentage strings `%`, date formatting) applied during dataset loading.
4. **Transformations**: Any data transformations applied during analysis must be preserved in execution provenance.
