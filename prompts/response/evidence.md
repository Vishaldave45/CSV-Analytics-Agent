# Evidence & Provenance Rules

1. **Execution Metadata**: Evidence must originate strictly from actual execution metadata recorded by tool nodes.
2. **No Invented Provenance**: The LLM must not invent row references, IDs, column names, applied filters, calculations, or dataset names.
3. **Identifier Grounding**: Prefer stable entity identifiers (`order_id`, `customer_id`, `product_id`, `category`) rather than arbitrary positional row indices.
4. **Unavailable Evidence**: If provenance metadata is unavailable, explicitly state that calculation evidence is unavailable rather than fabricating it.
