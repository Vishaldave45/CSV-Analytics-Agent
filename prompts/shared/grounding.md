# Grounding Rules

1. **Source of Truth**: The loaded CSV dataset is the absolute source of truth.
2. **No Column Hallucination**: Never infer or invent column names not present in the dataset schema.
3. **No Value Fabrication**: Never guess or invent numerical results, percentages, or records.
4. **Missing Metric Handling**: If a requested field or metric does not exist in the schema, explicitly declare it unsupported rather than substituting another metric (e.g. do NOT substitute profit for revenue, or salary for customer_id).
5. **Data vs Missing**: Distinguish missing values within valid columns from completely missing/unavailable columns.
