"""Streamlit renderer component for IMAGE artifacts in Quiet Data Studio."""

from __future__ import annotations

import base64
import io
from typing import Any

import streamlit as st

from csv_analytics_agent.results.models import AnalysisArtifact


def render_image(artifact: AnalysisArtifact | dict[str, Any]) -> None:
    """Render a static image (PNG/JPEG/WebP/Matplotlib) artifact inside Streamlit.

    Args:
        artifact: AnalysisArtifact model or dictionary representation.
    """
    payload: Any = None
    title: str | None = None
    description: str | None = None
    name: str = "image"
    mime_type: str = "image/png"

    if isinstance(artifact, dict):
        payload = artifact.get("payload")
        title = artifact.get("title")
        description = artifact.get("description")
        name = artifact.get("name", "image")
        mime_type = artifact.get("mime_type", "image/png") or "image/png"
    else:
        payload = artifact.payload
        title = artifact.title or artifact.name.replace("_", " ").title()
        description = artifact.description
        name = artifact.name
        mime_type = artifact.mime_type or "image/png"

    if title:
        st.markdown(f"##### {title}")
    if description:
        st.caption(description)

    if payload is None:
        st.info("No image payload available.")
        return

    image_bytes: bytes | None = None

    if isinstance(payload, bytes):
        image_bytes = payload
    elif isinstance(payload, str):
        if payload.startswith("data:image/"):
            try:
                b64_data = payload.split(",", 1)[1]
                image_bytes = base64.b64decode(b64_data)
            except Exception:
                image_bytes = None
        else:
            try:
                image_bytes = base64.b64decode(payload)
            except Exception:
                image_bytes = None
    elif hasattr(payload, "savefig") and callable(payload.savefig):
        try:
            buf = io.BytesIO()
            payload.savefig(buf, format="png", bbox_inches="tight")
            image_bytes = buf.getvalue()
        except Exception as err:
            st.error(f"Failed to render figure: {err}")
            return

    if image_bytes is not None:
        st.image(image_bytes, use_container_width=True)
        st.download_button(
            label=f"Download {name}.png",
            data=image_bytes,
            file_name=f"{name}.png",
            mime=mime_type,
            key=f"dl_img_{name}_{hash(str(payload))}",
        )
    else:
        st.warning("Unable to decode image payload.")


__all__ = ["render_image"]
