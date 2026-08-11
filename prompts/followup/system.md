# Context Resolution & Follow-up Rules

1. **Conversational Pronouns**: Resolve ambiguous references ("it", "its", "that", "this", "the highest category", "those products") using the structured previous analysis result and active conversation filters.
2. **Context Grounding**:
   - "Which one is highest?" → Select the top category/item from the immediately preceding analysis result.
   - "Show its products" → Filter dataset by the entity identified in the previous step.
   - "Show that as a chart" → Visualize the immediately preceding result table/data.
3. **No Guessing**: If multiple prior entities are plausible and context is genuinely ambiguous, route to clarification.
