"""Matplotlib chart renderer engine.

This module consumes a ChartSpecification and pandas DataFrame to render
publication-quality static figures (PNG/bytes). It operates strictly as a rendering engine
without deciding chart selection or modifying data.
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for headless rendering
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from csv_analytics_agent.visualization.exceptions import VisualizationError  # noqa: E402
from csv_analytics_agent.visualization.models import (  # noqa: E402
    ChartSpecification,
    ChartType,
)


def render_chart(
    spec: ChartSpecification,
    df: pd.DataFrame,
    save_path: str | Path | None = None,
    dpi: int = 100,
    figsize: tuple[int, int] = (8, 5),
) -> bytes:
    """Render a Matplotlib chart from a ChartSpecification and DataFrame.

    Args:
        spec: Renderer-independent chart specification.
        df: Pandas DataFrame containing dataset values.
        save_path: Optional file path to save the rendered PNG figure.
        dpi: Dots per inch for output image resolution.
        figsize: Figure dimensions (width, height) in inches.

    Returns:
        Bytes containing the PNG formatted image data.

    Raises:
        VisualizationError: If required columns are missing in DataFrame or rendering fails.
    """
    missing_cols = []
    if spec.x_axis.column not in df.columns:
        missing_cols.append(spec.x_axis.column)

    if (
        spec.y_axis is not None
        and spec.chart_type not in (ChartType.HISTOGRAM, ChartType.PIE)
        and spec.y_axis.column not in df.columns
    ):
        if spec.chart_type == ChartType.BAR and spec.y_axis.column not in df.columns:
            pass  # Fall back to category counts
        elif spec.chart_type == ChartType.BOXPLOT and spec.y_axis.column not in df.columns:
            pass  # Fall back to single column boxplot
        else:
            missing_cols.append(spec.y_axis.column)

    if missing_cols:
        raise VisualizationError(
            f"Cannot render chart: missing column(s) {missing_cols} in provided DataFrame."
        )

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    try:
        if spec.chart_type == ChartType.HISTOGRAM:
            hist_data = list(df[spec.x_axis.column].dropna())
            ax.hist(hist_data, bins=20, color="#3182bd", edgecolor="white")
            ax.set_ylabel("Frequency")

        elif spec.chart_type == ChartType.BAR:
            x_data = [str(x) for x in df[spec.x_axis.column]]
            if spec.y_axis is not None and spec.y_axis.column in df.columns:
                y_data = list(df[spec.y_axis.column])
                ax.bar(x_data, y_data, color="#3182bd")
                ax.set_ylabel(spec.y_axis.label or spec.y_axis.column)
            else:
                counts = df[spec.x_axis.column].value_counts()
                ax.bar([str(k) for k in counts.index], list(counts.values), color="#3182bd")
                ax.set_ylabel((spec.y_axis.label or "Count") if spec.y_axis else "Count")
            plt.xticks(rotation=45, ha="right")

        elif spec.chart_type == ChartType.LINE:
            x_col = spec.x_axis.column
            y_col = (
                spec.y_axis.column if (spec.y_axis and spec.y_axis.column in df.columns) else None
            )

            if y_col is not None and pd.api.types.is_numeric_dtype(df[y_col]):
                sub_df = df[[x_col, y_col]].dropna()
                try:
                    dt_series = pd.to_datetime(sub_df[x_col], errors="coerce")
                    if dt_series.notna().sum() > len(sub_df) * 0.5:
                        sub_df["_sort_dt"] = dt_series
                        sub_df = sub_df.sort_values("_sort_dt")
                except Exception:
                    pass

                if sub_df[x_col].duplicated().any():
                    grouped = sub_df.groupby(x_col, sort=False)[y_col].sum()
                    x_data = [str(x) for x in grouped.index]
                    y_data = [float(v) for v in grouped.values]
                else:
                    x_data = [str(x) for x in sub_df[x_col]]
                    y_data = [float(v) for v in sub_df[y_col]]
            else:
                x_data = list(df[x_col])
                y_data = list(df[y_col]) if y_col else list(df.iloc[:, 0])

            ax.plot(x_data, y_data, marker="o", color="#3182bd", linewidth=2)
            if spec.y_axis is not None:
                ax.set_ylabel(spec.y_axis.label or spec.y_axis.column)
            if len(x_data) > 6:
                plt.xticks(rotation=45, ha="right")

        elif spec.chart_type == ChartType.SCATTER:
            y_col = (
                spec.y_axis.column
                if (spec.y_axis and spec.y_axis.column in df.columns)
                else spec.x_axis.column
            )
            y_label = (
                (spec.y_axis.label or spec.y_axis.column)
                if spec.y_axis is not None
                else spec.x_axis.column
            )
            ax.scatter(list(df[spec.x_axis.column]), list(df[y_col]), color="#3182bd", alpha=0.7)
            ax.set_ylabel(y_label)

        elif spec.chart_type == ChartType.BOXPLOT:
            if spec.y_axis is not None and spec.y_axis.column in df.columns:
                categories = list(df[spec.x_axis.column].unique())
                data = [
                    list(df[df[spec.x_axis.column] == cat][spec.y_axis.column].dropna())
                    for cat in categories
                ]
                ax.boxplot(data, tick_labels=[str(c) for c in categories])
                ax.set_ylabel(spec.y_axis.label or spec.y_axis.column)
            else:
                ax.boxplot(list(df[spec.x_axis.column].dropna()))
                ax.set_ylabel(spec.x_axis.label or spec.x_axis.column)

        elif spec.chart_type == ChartType.PIE:
            counts = df[spec.x_axis.column].value_counts()
            pie_values = [float(v) for v in counts.values]
            pie_labels = [str(k) for k in counts.index]
            ax.pie(pie_values, labels=pie_labels, autopct="%1.1f%%", startangle=90)

        elif spec.chart_type == ChartType.HEATMAP:
            y_col = spec.y_axis.column if spec.y_axis else spec.x_axis.column
            numeric_df = df[[spec.x_axis.column, y_col]].select_dtypes(include="number")
            corr = numeric_df.corr()
            cax = ax.matshow(corr.to_numpy().tolist(), cmap="coolwarm")
            fig.colorbar(cax)
            col_labels = list(corr.columns)
            ax.set_xticks(range(len(col_labels)))
            ax.set_yticks(range(len(col_labels)))
            ax.set_xticklabels(col_labels, rotation=45, ha="left")
            ax.set_yticklabels(col_labels)

        # Apply common labels and formatting
        ax.set_title(spec.title, fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel(spec.x_axis.label or spec.x_axis.column)
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()

        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi)
        buf.seek(0)
        img_bytes = buf.getvalue()

        # Save to disk if path requested
        if save_path is not None:
            out_path = Path(save_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(img_bytes)

        return img_bytes

    except Exception as exc:
        raise VisualizationError(f"Failed to render chart: {exc}") from exc
    finally:
        plt.close(fig)
