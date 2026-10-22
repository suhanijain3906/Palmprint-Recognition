"""Benchmark dataset catalogue.

The platform does **not** ship any biometric dataset.  The catalogue below
lists the well known public palmprint benchmarks together with their official
source, their licence and the access procedure.

Availability is determined at runtime: a dataset is only reported as
*installed* when a corresponding directory exists below the configured
``DATASET_ROOT``.  Image and subject counts are only reported when they could
be verified locally - they are never copied from a publication.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter

from ...core.config import settings
from ...schemas.experiment import DatasetAvailability, DatasetResponse

logger = logging.getLogger("backend.routes.datasets")

router = APIRouter(prefix="/datasets", tags=["datasets"])

#: Static description of the public benchmarks.
DATASET_CATALOGUE: list[dict[str, str]] = [
    {
        "id": "polyu_contact_palm",
        "name": "PolyU Palmprint Database (contactless, v2)",
        "description": (
            "A large contactless palmprint database captured with an infrared "
            "camera.  It is the most frequently used benchmark for contactless "
            "palmprint recognition and is distributed for academic research."
        ),
        "official_source": "http://www4.comp.polyu.edu.hk/~biometrics/contact_palm.html",
        "licence": "Academic research use only, registration required.",
        "access_requirements": (
            "A signed agreement has to be requested from the hosting laboratory. "
            "Redistribution of the images is not permitted."
        ),
        "modality": "Contactless, infrared, 500 dpi",
        "reference": "Zhou et al., 'Palmprint verification using a 2D-3D combination'.",
    },
    {
        "id": "iitd_touchless",
        "name": "IITD Touchless Palmprint Dataset",
        "description": (
            "Touchless palmprints captured with a hand-held infrared camera.  "
            "It is frequently used to evaluate contactless recognition and "
            "cross-sensor matching."
        ),
        "official_source": "http://www3.iitd.ac.in/~biometrics/",
        "licence": "Academic research use only, request form required.",
        "access_requirements": (
            "Access requires a request form and an academic affiliation. The "
            "dataset must not be redistributed."
        ),
        "modality": "Touchless, infrared",
        "reference": "Kang, J. et al., 'Touchless palmprint recognition system'.",
    },
    {
        "id": "casia_palmprint",
        "name": "CASIA Palmprint Database",
        "description": (
            "A contactless palmprint database published by the Institute of "
            "Automation, Chinese Academy of Sciences.  It is used for "
            "contactless identification and verification studies."
        ),
        "official_source": "http://biometrics.idealtest.org/db.phpFor=chinesePalmprint",
        "licence": "Academic research use only, request form required.",
        "access_requirements": (
            "An application form has to be sent to the institute. The images "
            "may not be redistributed or used for commercial purposes."
        ),
        "modality": "Contactless, visible light",
        "reference": "Jia et al., CASIA palmprint database, 2012.",
    },
    {
        "id": "tongji_palmprint",
        "name": "Tongji Palmprint Database",
        "description": (
            "A contactless palmprint database released by Tongji University.  "
            "It complements the CASIA collection and is used in cross-dataset "
            "evaluation studies."
        ),
        "official_source": "http://biometrics.idealtest.org/db.phpFor=chinesePalmprint",
        "licence": "Academic research use only, request form required.",
        "access_requirements": (
            "Access is granted through the same application channel as the "
            "CASIA collection.  Redistribution is not permitted."
        ),
        "modality": "Contactless, visible light",
        "reference": "Zhang, L. et al., 'Efficient palmprint recognition'.",
    },
    {
        "id": "nirfis_palmprint_v2",
        "name": "NIRFIS Palmprint Database v2",
        "description": (
            "A contactless palmprint database with a large number of "
            "participants, distributed by the Nanyang Technological "
            "University for research purposes."
        ),
        "official_source": "https://www.nirfis.org/projects/palmprint/",
        "licence": "Academic research use, registration required.",
        "access_requirements": (
            "A registration form has to be completed with the research group. "
            "The dataset must not be redistributed."
        ),
        "modality": "Contactless, visible light",
        "reference": "Zhou, Y. et al., 'NIRFIS palmprint database v2'.",
    },
]

#: File extensions that are counted when verifying a local installation.
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def _verify_local_installation(directory: Path) -> DatasetAvailability:
    """Count the images and (if possible) the subjects of a local dataset."""
    if not directory.is_dir():
        return DatasetAvailability(
            status="not_installed",
            installed=False,
            message=(
                "The dataset is not installed in this deployment. Download it "
                "from the official source and place it in the dataset root "
                "directory to enable local evaluation."
            ),
        )

    image_count = 0
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES:
            image_count += 1

    # Subjects are counted from the immediate sub directories, which is the
    # usual layout of the public benchmarks (one directory per subject).
    subject_dirs = [entry for entry in directory.iterdir() if entry.is_dir()]
    subject_count = len(subject_dirs) if subject_dirs else None

    return DatasetAvailability(
        status="installed",
        installed=True,
        verified_image_count=image_count,
        verified_subject_count=subject_count,
        local_path=str(directory),
        message=(
            f"The dataset was found locally and contains {image_count} image file(s). "
            "Verify the counts against the official documentation before "
            "publishing them."
        ),
    )


@router.get("", response_model=list[DatasetResponse], summary="List the known benchmarks")
def list_datasets() -> list[DatasetResponse]:
    """Return the benchmark catalogue with the local availability status."""
    root = Path(settings.dataset_root)
    responses: list[DatasetResponse] = []
    for entry in DATASET_CATALOGUE:
        availability = _verify_local_installation(root / entry["id"])
        responses.append(
            DatasetResponse(
                id=entry["id"],
                name=entry["name"],
                description=entry["description"],
                official_source=entry["official_source"],
                licence=entry["licence"],
                access_requirements=entry["access_requirements"],
                modality=entry["modality"],
                reference=entry.get("reference"),
                availability=availability,
                notes=(
                    "The platform does not redistribute biometric datasets. "
                    "Always follow the licence and the access procedure of the "
                    "hosting institution."
                ),
            )
        )
    return responses


@router.get("/{dataset_id}", response_model=DatasetResponse, summary="Get a benchmark description")
def get_dataset(dataset_id: str) -> DatasetResponse:
    """Return the description of a single benchmark."""
    from ...utils.errors import NotFoundError

    for entry in DATASET_CATALOGUE:
        if entry["id"] == dataset_id:
            root = Path(settings.dataset_root)
            return DatasetResponse(
                id=entry["id"],
                name=entry["name"],
                description=entry["description"],
                official_source=entry["official_source"],
                licence=entry["licence"],
                access_requirements=entry["access_requirements"],
                modality=entry["modality"],
                reference=entry.get("reference"),
                availability=_verify_local_installation(root / dataset_id),
            )
    raise NotFoundError(f"Dataset '{dataset_id}' is not part of the catalogue.")


__all__ = ["DATASET_CATALOGUE", "router"]
