"""LangSmith Evaluation Dataset Adapter for Stage 8.9."""

from __future__ import annotations

import logging
import os

from tests.evaluation.schemas import GoldenTestCase

logger = logging.getLogger(__name__)


class LangSmithEvaluationAdapter:
    """Adapter for syncing Golden Dataset cases to LangSmith evaluation datasets."""

    def __init__(self, dataset_name: str = "csv-analytics-agent-golden-questions") -> None:
        self.dataset_name = dataset_name
        self.api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")

    @property
    def is_available(self) -> bool:
        """Check if LangSmith API key is present."""
        return bool(self.api_key and self.api_key.strip())

    def export_dataset(self, cases: list[GoldenTestCase]) -> bool:
        """Export golden test cases to LangSmith platform dataset if key present.

        Args:
            cases: List of GoldenTestCase instances.

        Returns:
            True if exported successfully, False if skipped or failed.
        """
        if not self.is_available:
            logger.info("LangSmith API key not configured. Skipping remote dataset export.")
            return False

        try:
            from langsmith import Client

            client = Client(api_key=self.api_key)

            # Check if dataset exists or create new
            if not client.has_dataset(dataset_name=self.dataset_name):
                ds = client.create_dataset(
                    dataset_name=self.dataset_name,
                    description="Golden evaluation questions dataset for CSV Analytics Agent.",
                )
            else:
                ds = client.read_dataset(dataset_name=self.dataset_name)

            for case in cases:
                client.create_example(
                    inputs={"question": case.question, "category": case.category},
                    outputs={
                        "expected_tool": case.expected_behavior.tool,
                        "artifact_types": case.expected_behavior.artifact_types,
                        "requires_python": case.expected_behavior.requires_python,
                    },
                    dataset_id=ds.id,
                    metadata={"case_id": case.id},
                )

            logger.info(
                "Successfully exported %d cases to LangSmith dataset '%s'.",
                len(cases),
                self.dataset_name,
            )
            return True
        except Exception as exc:
            logger.warning("Failed to export dataset to LangSmith: %s", exc)
            return False
