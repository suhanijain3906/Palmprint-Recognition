"""PDF report generation.

Reports are built with ReportLab and stored in the configured storage
backend.  A report never contains a raw biometric image unless the caller
explicitly asks for it (``include_images=True``) - and even then the images
are embedded from the platform's own storage, not from a public URL.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as ReportLabImage,
)
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from ..models import ReportRecord, User
from ..repositories import ExperimentRepository, JobRepository, ReportRepository
from ..storage import StorageBackend, build_storage, random_key
from ..utils.errors import NotFoundError, ValidationError

logger = logging.getLogger("backend.report_service")

DISCLAIMER = (
    "This report was produced by an experimental research platform. The "
    "similarity scores and quality metrics are uncalibrated heuristics and "
    "are not identity verification results. No trained biometric model is "
    "bundled with this deployment. The document must not be used for access "
    "control, law enforcement or any decision with legal consequences."
)

LIMITATIONS = [
    "The combined quality score is an unvalidated engineering heuristic.",
    "The similarity score is an uncalibrated index, not a probability of identity.",
    "Generic feature detectors do not model the oriented line structure of palm ridges.",
    "The region of interest is an approximate proposal, not an anatomical palm ROI.",
    "Metrics are only comparable between captures made with the same sensor and protocol.",
]


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#475569"),
        ),
        "heading": ParagraphStyle(
            "ReportHeading",
            parent=base["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1e293b"),
        ),
        "small": ParagraphStyle(
            "ReportSmall",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#475569"),
        ),
    }


def _pretty_json(value: Any) -> str:
    """Render a JSON serialisable value for a PDF table cell."""
    try:
        return json.dumps(value, indent=1, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(value)


def _table(rows: list[list[Any]], styles: dict[str, ParagraphStyle]) -> Table:
    data = [[Paragraph(str(cell), styles["body"]) for cell in row] for row in rows]
    table = Table(data, colWidths=[60 * mm, 115 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


class ReportService:
    """Creates PDF reports for processing jobs and experiments."""

    def __init__(
        self,
        session: Session,
        *,
        storage: StorageBackend | None = None,
    ) -> None:
        self._session = session
        self._storage = storage or build_storage()
        self._reports = ReportRepository(session)
        self._jobs = JobRepository(session)
        self._experiments = ExperimentRepository(session)

    def create_processing_report(
        self,
        *,
        owner: User,
        title: str,
        report_type: str = "processing",
        job_ids: list[str] | None = None,
        experiment_id: str | None = None,
        include_images: bool = False,
    ) -> ReportRecord:
        """Generate a PDF report and persist its metadata."""
        jobs = []
        for job_id in job_ids or []:
            job = self._jobs.get(job_id)
            if job is None or job.owner_id != owner.id:
                raise NotFoundError(f"Processing job '{job_id}' was not found.")
            jobs.append(job)

        experiment = None
        if experiment_id:
            experiment = self._experiments.get(experiment_id)
            if experiment is None or experiment.owner_id != owner.id:
                raise NotFoundError(f"Experiment '{experiment_id}' was not found.")

        if not jobs and experiment is None:
            raise ValidationError(
                "A report needs at least one processing job or an experiment.",
                code="empty_report",
            )

        record = self._reports.create(
            owner_id=owner.id,
            title=title,
            report_type=report_type,
            status="generating",
            experiment_id=experiment_id,
        )

        try:
            pdf_bytes = self._render_pdf(
                title=title,
                report_id=record.id,
                owner=owner,
                jobs=jobs,
                experiment=experiment,
                include_images=include_images,
            )
        except Exception as exc:
            logger.exception("Report generation failed")
            record.status = "failed"
            record.error_message = str(exc)[:500]
            self._session.flush()
            raise ValidationError(
                "The report could not be generated.", code="report_generation_failed"
            ) from exc

        key = random_key("reports", ".pdf")
        self._storage.save(key, pdf_bytes)
        record.storage_key = key
        record.size_bytes = len(pdf_bytes)
        record.status = "ready"
        record.generated_at = datetime.now(UTC)
        self._session.flush()
        return record

    def load_bytes(self, report: ReportRecord) -> bytes:
        if not report.storage_key:
            raise NotFoundError("The report file is not available.", code="report_file_missing")
        try:
            return self._storage.read(report.storage_key)
        except FileNotFoundError as exc:
            raise NotFoundError(
                "The report file is no longer available.", code="report_file_missing"
            ) from exc

    # -- rendering -------------------------------------------------------
    def _render_pdf(
        self,
        *,
        title: str,
        report_id: str,
        owner: User,
        jobs: list[Any],
        experiment: Any | None,
        include_images: bool,
    ) -> bytes:
        styles = _styles()
        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=title,
            author="Palmprint Research Platform",
        )

        story: list[Any] = []
        story.append(Paragraph(title, styles["title"]))
        story.append(
            Paragraph(
                "Palmprint Research Platform - experimental processing report",
                styles["subtitle"],
            )
        )
        story.append(Spacer(1, 6 * mm))

        story.append(Paragraph("Report metadata", styles["heading"]))
        story.append(
            _table(
                [
                    ["Report identifier", report_id],
                    ["Generated at (UTC)", datetime.now(UTC).isoformat(timespec="seconds")],
                    ["Submitted by", owner.display_name],
                    ["Report type", "experiment" if experiment else "processing"],
                ],
                styles,
            )
        )

        if experiment is not None:
            story.append(Paragraph("Experiment configuration", styles["heading"]))
            rows = [
                ["Identifier", experiment.id],
                ["Name", experiment.name],
                ["Description", experiment.description or "-"],
                ["Operation", experiment.operation],
                ["Algorithm", experiment.algorithm],
                ["Parameters", _pretty_json(experiment.parameters)],
                ["Images", ", ".join(experiment.image_ids) or "-"],
                ["Status", experiment.status],
            ]
            story.append(_table(rows, styles))

            results = self._experiments.list_results(experiment.id)
            if results:
                story.append(Paragraph("Measured results", styles["heading"]))
                rows = [["Metric", "Value"]]
                for result in results:
                    unit = f" {result.unit}" if result.unit else ""
                    value = "-" if result.value is None else f"{result.value}{unit}"
                    rows.append([result.label or result.kind, value])
                story.append(_table(rows, styles))

        if jobs:
            story.append(Paragraph("Processing jobs", styles["heading"]))
            rows = [["Job", "Operation / algorithm", "Parameters", "Duration"]]
            for job in jobs:
                rows.append(
                    [
                        job.id,
                        f"{job.operation} / {job.algorithm} (v{job.algorithm_version or '-'})",
                        _pretty_json(job.parameters),
                        f"{job.duration_ms:.1f} ms" if job.duration_ms else "-",
                    ]
                )
            story.append(_table(rows, styles))

            quality_rows = [["Metric", "Value"]]
            matching_rows = [["Metric", "Value"]]
            has_quality = False
            has_matching = False
            for job in jobs:
                metrics = job.metrics or {}
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        quality_rows.append([key, f"{value}"])
                        has_quality = True
                for key, value in metrics.items():
                    if "match" in key.lower() and isinstance(value, (int, float)):
                        matching_rows.append([key, f"{value}"])
                        has_matching = True
            if has_quality:
                story.append(Paragraph("Quality measurements", styles["heading"]))
                story.append(_table(quality_rows, styles))
            if has_matching:
                story.append(Paragraph("Feature matching statistics", styles["heading"]))
                story.append(_table(matching_rows, styles))

            warning_rows = [["Warnings"]]
            for job in jobs:
                for warning in job.warnings:
                    warning_rows.append([warning])
            if len(warning_rows) > 1:
                story.append(Paragraph("Warnings", styles["heading"]))
                story.append(_table(warning_rows, styles))

            if include_images:
                images = self._collect_images(jobs)
                if images:
                    story.append(PageBreak())
                    story.append(Paragraph("Output visualisations", styles["heading"]))
                    for label, data in images:
                        story.append(Paragraph(label, styles["body"]))
                        try:
                            from PIL import Image as PILImage

                            with PILImage.open(io.BytesIO(data)) as probe:
                                width, height = probe.size
                            max_width = 170 * mm
                            ratio = min(1.0, max_width / (width * 0.264583))
                            story.append(
                                ReportLabImage(
                                    io.BytesIO(data),
                                    width=width * 0.264583 * ratio,
                                    height=height * 0.264583 * ratio,
                                )
                            )
                        except Exception:  # pragma: no cover - defensive
                            story.append(
                                Paragraph(
                                    "The visualisation could not be embedded.", styles["small"]
                                )
                            )
                        story.append(Spacer(1, 4 * mm))

        story.append(Paragraph("Limitations", styles["heading"]))
        for limitation in LIMITATIONS:
            story.append(Paragraph(f"- {limitation}", styles["body"]))

        story.append(Paragraph("Research use disclaimer", styles["heading"]))
        story.append(Paragraph(DISCLAIMER, styles["body"]))

        document.build(story)
        return buffer.getvalue()

    def _collect_images(self, jobs: list[Any]) -> list[tuple[str, bytes]]:
        """Collect the generated artefacts that belong to the given jobs."""
        images: list[tuple[str, bytes]] = []
        for job in jobs:
            try:
                result = json.loads(job.result_json or "{}")
            except json.JSONDecodeError:  # pragma: no cover - defensive
                continue
            for artifact in result.get("artifacts", []) or []:
                key = artifact.get("id")
                if not key:
                    continue
                try:
                    data = self._storage.read(key)
                except (FileNotFoundError, Exception):  # pragma: no cover - defensive
                    continue
                images.append((f"{job.operation} - {artifact.get('kind', 'output')}", data))
        return images


__all__ = ["DISCLAIMER", "LIMITATIONS", "ReportService"]
