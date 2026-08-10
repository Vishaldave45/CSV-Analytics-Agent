"""Backend service bridge connecting Streamlit UI presentation layer to backend engines."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
import streamlit as st

from csv_analytics_agent.config.setting import Settings
from csv_analytics_agent.data.loader import CSVLoader
from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.domain.visualization import VisualizationEngine
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.graph.runtime import AgentRuntime
from csv_analytics_agent.graph.state import AgentState
from csv_analytics_agent.insights.generator import InsightGenerator
from csv_analytics_agent.insights.models import Insight
from csv_analytics_agent.llm.gemini import DEFAULT_MODEL_NAME, GeminiLLM
from csv_analytics_agent.llm.rate_limiter import build_gemini_limiter
from csv_analytics_agent.logging_config import get_logger
from csv_analytics_agent.memory.service import MemoryService
from csv_analytics_agent.persistence.db import get_session
from csv_analytics_agent.persistence.hashing import compute_content_hash
from csv_analytics_agent.persistence.repository import DatasetRepository
from csv_analytics_agent.preprocessing.coercion import coerce_dataframe
from csv_analytics_agent.profiler.models import DatasetProfile
from csv_analytics_agent.profiler.profiler import DatasetProfiler
from csv_analytics_agent.visualization.exceptions import NoSuitableVisualizationError
from csv_analytics_agent.visualization.models import ChartSpecification
from csv_analytics_agent.visualization.recommender import recommend_visualizations
from csv_analytics_agent.visualization.renderer import render_chart

logger = get_logger(__name__)


def upload_dataset(content: bytes, filename: str) -> tuple[pd.DataFrame, DatasetProfile, str]:
    """Load DataFrame and compute/fetch cached DatasetProfile for uploaded CSV bytes.

    Args:
        content: Raw bytes of the uploaded CSV file.
        filename: Original filename used in error messages and dataset entity.

    Returns:
        Tuple of (validated_coerced_df, profile, content_hash).

    Raises:
        EmptyCSVError: If the file is empty.
        CSVEncodingError: If the file cannot be decoded.
        CSVParsingError: If the file cannot be parsed as CSV.
    """
    content_hash = compute_content_hash(content)
    repo = DatasetRepository(get_session())

    df = CSVLoader.load_from_bytes(content, filename=filename)
    coerced_df, report = coerce_dataframe(df)
    logger.info("dataset_coerced", filename=filename, **report.summary())

    cached_profile = repo.get_cached_profile(content_hash)
    if cached_profile is not None:
        logger.info("profile_cache_hit", content_hash=content_hash, filename=filename)
        return coerced_df, cached_profile, content_hash

    logger.info("profile_cache_miss", content_hash=content_hash, filename=filename)
    profiler = DatasetProfiler()
    profile = profiler.profile(coerced_df)

    dataset = repo.get_by_hash(content_hash) or repo.create(
        filename=filename,
        content_hash=content_hash,
        row_count=len(coerced_df),
        column_count=len(coerced_df.columns),
    )
    repo.cache_profile(dataset.id, profile)
    return coerced_df, profile, content_hash


def get_profile(df: pd.DataFrame, dataset_name: str = "dataset.csv") -> DatasetProfile:
    """Generate DatasetProfile from a pandas DataFrame using DatasetProfiler."""
    profiler = DatasetProfiler()
    return profiler.profile(df)


def get_insights(profile: DatasetProfile) -> list[Insight]:
    """Generate structured Insights for a DatasetProfile using InsightGenerator."""
    generator = InsightGenerator()
    return generator.generate(profile)


def recommend_visualization(
    profile: DatasetProfile, insights: list[Insight] | None = None
) -> list[ChartSpecification]:
    """Recommend ChartSpecifications for a DatasetProfile."""
    try:
        plan = recommend_visualizations(profile, insights=insights or [])
        charts: list[ChartSpecification] = [plan.primary]
        charts.extend(plan.alternatives)
        return charts
    except NoSuitableVisualizationError:
        return []


def render_chart_image(spec: ChartSpecification, df: pd.DataFrame) -> bytes:
    """Render ChartSpecification to PNG bytes via Matplotlib Visualization Engine."""
    return render_chart(spec, df)


def build_configured_registry() -> CapabilityRegistry:
    """Build a CapabilityRegistry populated with AnalyticsEngine and VisualizationEngine."""
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
    model_name: str = DEFAULT_MODEL_NAME,
    temperature: float = 0.0,
    max_iterations: int = 6,
    api_key: str | None = None,
    **kwargs: Any,
) -> AgentRuntime:
    """Create an AgentRuntime instance configured for the given DataFrame."""
    registry = build_configured_registry()
    memory_service = MemoryService()

    for col in df.columns:
        memory_service.store(
            text=f"Column: {col} in dataset",
            metadata={"column_name": col},
        )

    settings = Settings(max_iterations=max_iterations)
    effective_api_key = (
        api_key or kwargs.get("api_key") or settings.google_api_key or os.getenv("GOOGLE_API_KEY")
    )
    limiter = build_gemini_limiter(settings)
    llm = GeminiLLM(
        model_name=model_name,
        temperature=temperature,
        api_key=effective_api_key,
        limiter=limiter,
    )

    runtime = AgentRuntime(
        llm=llm,
        registry=registry,
        memory_service=memory_service,
        dataframe=df,
        settings=settings,
    )
    logger.info(
        "agent_runtime_created",
        model=model_name,
        columns=len(df.columns),
        max_iterations=max_iterations,
    )
    return runtime


@st.cache_resource(show_spinner=False)
def get_or_create_runtime(
    dataset_hash: str,
    model_name: str = DEFAULT_MODEL_NAME,
    temperature: float = 0.0,
    max_iterations: int = 6,
    api_key: str | None = None,
    _df: pd.DataFrame | None = None,
) -> AgentRuntime:
    """Get or create cached AgentRuntime keyed by dataset_hash + model configuration."""
    if _df is None:
        raise ValueError("DataFrame context (_df) is required to initialize AgentRuntime.")
    logger.info("agent_runtime_cache_lookup", dataset_hash=dataset_hash, model=model_name)
    return create_agent_runtime(
        df=_df,
        model_name=model_name,
        temperature=temperature,
        max_iterations=max_iterations,
        api_key=api_key,
    )


def ask_agent(
    runtime: AgentRuntime,
    prompt: str,
    thread_id: str,
    profile: DatasetProfile | None = None,
) -> AgentState:
    """Execute query prompt via AgentRuntime."""
    return runtime.run(prompt, thread_id=thread_id, profile=profile)


__all__ = [
    "ask_agent",
    "build_configured_registry",
    "create_agent_runtime",
    "get_insights",
    "get_or_create_runtime",
    "get_profile",
    "recommend_visualization",
    "render_chart_image",
    "upload_dataset",
]
