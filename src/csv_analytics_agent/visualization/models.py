"""
ChartTypes(Enum)->> histogram , bar , line , scatter , boxplot , pie , heatmap.

axis->> column , lablel.

ChartSpecification-->>chart type , title , axis , description .

VisualizationRecommendation-->> Sometimes more than one chart is suitable.   
-->> primary : chartspecification  &  alternatives : list(chartspecification)


Analytics Engine                           
        │
        ▼
ChartSpecification
        │
        ▼
Matplotlib



--------------------------------------------------


DatasetProfile
        │
        ▼
Visualization Rules
        │
        ▼
ChartSpecification
        │
        ▼
Renderer


Numeric → Histogram
Categorical → Bar
Datetime + Numeric → Line
Two Numeric Columns → Scatter


"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ChartType(str, Enum):
    """Supported chart types for data visualization."""

    HISTOGRAM = "histogram"
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    BOXPLOT = "boxplot"
    PIE = "pie"
    HEATMAP = "heatmap"


class Axis(BaseModel):
    """Represents axis configuration for a chart.

    Attributes:
        column: The dataset column associated with this axis.
        label: Optional human-readable label for display.
    """

    model_config = ConfigDict(frozen=True)

    column: str = Field(..., min_length=1, description="Dataset column name for the axis.")
    label: str | None = Field(default=None, description="Human-readable axis display label.")


class ChartSpecification(BaseModel):
    """Represents a renderer-independent chart specification.

    Attributes:
        chart_type: Type of visualization.
        title: Chart title.
        x_axis: Primary X-axis configuration.
        y_axis: Optional Y-axis configuration.
        description: Human-readable chart description explaining why chart was chosen.
    """

    model_config = ConfigDict(frozen=True)

    chart_type: ChartType = Field(..., description="Type of chart visualization.")
    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Title of the chart.",
    )
    x_axis: Axis = Field(..., description="X-axis configuration.")
    y_axis: Axis | None = Field(default=None, description="Optional Y-axis configuration.")
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation for the chart recommendation.",
    )


class VisualizationPlan(BaseModel):
    """Represents a complete visualization plan containing primary and alternative specifications.

    Attributes:
        primary: Primary chart specification recommended for the dataset.
        alternatives: Optional list of alternative suitable chart specifications.
    """

    model_config = ConfigDict(frozen=True)

    primary: ChartSpecification = Field(
        ..., description="Primary recommended chart specification."
    )
    alternatives: list[ChartSpecification] = Field(
        default_factory=list,
        description="Alternative chart specifications.",
    )
