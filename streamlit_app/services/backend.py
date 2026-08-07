"""Backend service bridge connecting Streamlit UI to CSV Analytics Agent framework."""

from __future__ import annotations

import io

import pandas as pd

from csv_analytics_agent.config.setting import Settings
from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.domain.visualization import VisualizationEngine
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.runtime import AgentRuntime
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.insights.generator import InsightGenerator
from csv_analytics_agent.insights.models import Insight
from csv_analytics_agent.llm.gemini import GeminiLLM
from csv_analytics_agent.memory.service import MemoryService
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.profiler.profiler import DatasetProfiler
from csv_analytics_agent.visualization.models import ChartSpecification
from csv_analytics_agent.visualization.recommender import recommend_visualizations
from csv_analytics_agent.visualization.renderer import render_chart


def load_dataset_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    """Load DataFrame from uploaded byte stream.

    Args:
        content: Binary content of CSV file.
        filename: Target filename string.

    Returns:
        Loaded pandas DataFrame.
    """
    stream = io.BytesIO(content)
    return pd.read_csv(stream)


def profile_dataset(df: pd.DataFrame, dataset_name: str = "dataset.csv") -> DatasetProfile:
    """Generate DatasetProfile from a pandas DataFrame.

    Args:
        df: Target pandas DataFrame.
        dataset_name: Dataset identifier string.

    Returns:
        DatasetProfile instance.
    """
    profiler = DatasetProfiler()
    return profiler.profile(df)


def generate_insights_for_dataset(profile: DatasetProfile) -> list[Insight]:
    """Generate structured Insights for a DatasetProfile.

    Args:
        profile: DatasetProfile instance.

    Returns:
        List of Insight objects.
    """
    generator = InsightGenerator()
    return generator.generate(profile)


def recommend_visualizations_for_dataset(
    profile: DatasetProfile, insights: list[Insight] | None = None
) -> list[ChartSpecification]:
    """Recommend ChartSpecifications for a DatasetProfile.

    Args:
        profile: DatasetProfile instance.
        insights: Optional list of Insight objects.

    Returns:
        List of ChartSpecification objects.
    """
    plan = recommend_visualizations(profile, insights=insights or [])
    charts: list[ChartSpecification] = [plan.primary]
    charts.extend(plan.alternatives)
    return charts


def render_chart_image(spec: ChartSpecification, df: pd.DataFrame) -> bytes:
    """Render ChartSpecification to PNG bytes.

    Args:
        spec: Target ChartSpecification.
        df: Input pandas DataFrame context.

    Returns:
        PNG image bytes.
    """
    return render_chart(spec, df)


def build_configured_registry() -> CapabilityRegistry:
    """Build a CapabilityRegistry populated with AnalyticsEngine and VisualizationEngine.

    Returns:
        Configured CapabilityRegistry.
    """
    registry = CapabilityRegistry()
    analytics_engine = AnalyticsEngine()
    viz_engine = VisualizationEngine()

    for desc in analytics_engine.list_capabilities():
        registry.register(desc, analytics_engine)

    for desc in viz_engine.list_capabilities():
        registry.register(desc, viz_engine)

    return registry


def create_agent_runtime(
    df: pd.DataFrame,
    model_name: str = "gemini-1.5-flash",
    temperature: float = 0.0,
    max_iterations: int = 6,
) -> AgentRuntime:
    """Create an AgentRuntime instance configured for the given DataFrame.

    Args:
        df: Active dataset pandas DataFrame.
        model_name: Gemini model identifier.
        temperature: LLM sampling temperature.
        max_iterations: Maximum loop iterations.

    Returns:
        Configured AgentRuntime instance.
    """
    registry = build_configured_registry()
    memory_service = MemoryService()

    # Seed column memory index for Retrieval Node (Stage 7.5)
    for col in df.columns:
        memory_service.store(
            text=f"Column: {col} in dataset",
            metadata={"column_name": col},
        )

    llm = GeminiLLM(model_name=model_name, temperature=temperature)
    settings = Settings(max_iterations=max_iterations)

    return AgentRuntime(
        llm=llm,
        registry=registry,
        memory_service=memory_service,
        dataframe=df,
        settings=settings,
    )


def execute_agent_query(runtime: AgentRuntime, prompt: str, thread_id: str) -> AgentState:
    """Execute query prompt via AgentRuntime.

    Args:
        runtime: Active AgentRuntime instance.
        prompt: User query string.
        thread_id: Session thread identifier.

    Returns:
        Resulting AgentState dictionary.
    """
    return runtime.run(prompt, thread_id=thread_id)


__all__ = [
    "build_configured_registry",
    "create_agent_runtime",
    "execute_agent_query",
    "generate_insights_for_dataset",
    "load_dataset_from_bytes",
    "profile_dataset",
    "recommend_visualizations_for_dataset",
    "render_chart_image",
]
