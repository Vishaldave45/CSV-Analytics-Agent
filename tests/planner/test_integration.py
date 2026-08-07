"""End-to-end integration tests for Stage 6 Planner and Stage 5 Execution Framework."""

import pandas as pd
import pytest

from csv_analytics_agent.execution.domain.analytics import AnalyticsEngine
from csv_analytics_agent.execution.domain.visualization import VisualizationEngine
from csv_analytics_agent.execution.models import ExecutionStatus
from csv_analytics_agent.execution.registry import CapabilityRegistry
from csv_analytics_agent.planner.planner import RulePlanner


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "salary": [50000.0, 60000.0, 75000.0, 90000.0, 110000.0],
            "revenue": [1000.0, 2500.0, 5000.0, 12000.0, 20000.0],
            "age": [25, 30, 35, 40, 45],
            "department": ["HR", "IT", "IT", "HR", "Sales"],
            "customer": ["Customer_A", "Customer_B", "Customer_C", "Customer_D", "Customer_E"],
        }
    )


@pytest.fixture
def configured_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    analytics_engine = AnalyticsEngine()
    viz_engine = VisualizationEngine()

    for desc in analytics_engine.list_capabilities():
        registry.register(desc, analytics_engine)

    for desc in viz_engine.list_capabilities():
        registry.register(desc, viz_engine)

    return registry


def test_e2e_average_salary(
    sample_dataframe: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    planner = RulePlanner()
    columns = list(sample_dataframe.columns)

    # 1. Plan Question -> ExecutionRequest
    plan_res = planner.plan("What is the average salary?", columns, configured_registry)
    assert plan_res.success is True
    assert plan_res.execution_request is not None

    req = plan_res.execution_request
    assert req.capability_name == "aggregate"

    # 2. Lookup Engine in Registry -> Execute
    engine = configured_registry.get_engine(req.capability_name)
    exec_res = engine.execute_capability(req, sample_dataframe)

    # 3. Assert Result
    assert exec_res.status == ExecutionStatus.SUCCESS
    assert exec_res.data == 77000.0


def test_e2e_maximum_revenue(
    sample_dataframe: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    planner = RulePlanner()
    columns = list(sample_dataframe.columns)

    plan_res = planner.plan("What is the maximum revenue?", columns, configured_registry)
    assert plan_res.success is True
    assert plan_res.execution_request is not None

    req = plan_res.execution_request
    engine = configured_registry.get_engine(req.capability_name)
    exec_res = engine.execute_capability(req, sample_dataframe)

    assert exec_res.status == ExecutionStatus.SUCCESS
    assert exec_res.data == 20000.0


def test_e2e_top_5_customers(
    sample_dataframe: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    planner = RulePlanner()
    columns = list(sample_dataframe.columns)

    plan_res = planner.plan("Top 5 customer", columns, configured_registry)
    assert plan_res.success is True
    assert plan_res.execution_request is not None

    req = plan_res.execution_request
    engine = configured_registry.get_engine(req.capability_name)
    exec_res = engine.execute_capability(req, sample_dataframe)

    assert exec_res.status == ExecutionStatus.SUCCESS
    assert isinstance(exec_res.data, pd.DataFrame)
    assert len(exec_res.data) == 5


def test_e2e_group_by_department(
    sample_dataframe: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    planner = RulePlanner()
    columns = list(sample_dataframe.columns)

    plan_res = planner.plan("Group salary by department", columns, configured_registry)
    assert plan_res.success is True
    assert plan_res.execution_request is not None

    req = plan_res.execution_request
    engine = configured_registry.get_engine(req.capability_name)
    exec_res = engine.execute_capability(req, sample_dataframe)

    assert exec_res.status == ExecutionStatus.SUCCESS
    assert isinstance(exec_res.data, dict)
    assert "IT" in exec_res.data


def test_e2e_filter_age(
    sample_dataframe: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    planner = RulePlanner()
    columns = list(sample_dataframe.columns)

    plan_res = planner.plan("Filter age older than 30", columns, configured_registry)
    assert plan_res.success is True
    assert plan_res.execution_request is not None

    req = plan_res.execution_request
    engine = configured_registry.get_engine(req.capability_name)
    exec_res = engine.execute_capability(req, sample_dataframe)

    assert exec_res.status == ExecutionStatus.SUCCESS
    assert isinstance(exec_res.data, pd.DataFrame)
    assert len(exec_res.data) == 3


def test_e2e_unsupported_query(
    sample_dataframe: pd.DataFrame, configured_registry: CapabilityRegistry
) -> None:
    planner = RulePlanner()
    columns = list(sample_dataframe.columns)

    plan_res = planner.plan("Predict future stock prices", columns, configured_registry)
    assert plan_res.success is False
    assert plan_res.execution_request is None
    assert "Could not resolve intent" in str(plan_res.error_message)
