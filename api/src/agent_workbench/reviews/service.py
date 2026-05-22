from __future__ import annotations

import uuid

from sqlalchemy import func, select

from ..database import db
from .models import Review


def list_reviews(
    project_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> tuple[list[Review], int]:
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = select(Review).where(Review.project_id == project_id)
    total = db.session.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.session.scalars(
        base.order_by(Review.created_at.desc()).offset(offset).limit(per_page)
    ).all()
    return list(items), total


def get_review(review_id: uuid.UUID) -> Review | None:
    return db.session.get(Review, review_id)


def create_review(project_id: uuid.UUID, data: dict) -> Review:
    linked_task_id = data.get("linked_task_id")
    review = Review(
        project_id=project_id,
        source=data.get("source", "cloud-review"),
        severity=data.get("severity", "medium"),
        status=data.get("status", "open"),
        finding=data["finding"],
        recommendation=data.get("recommendation"),
        linked_task_id=uuid.UUID(linked_task_id) if linked_task_id else None,
    )
    db.session.add(review)
    db.session.flush()
    return review


def update_review(review: Review, data: dict) -> Review:
    mutable = ("source", "severity", "status", "finding", "recommendation")
    for field in mutable:
        if field in data:
            setattr(review, field, data[field])
    if "linked_task_id" in data:
        tid = data["linked_task_id"]
        review.linked_task_id = uuid.UUID(tid) if tid else None
    review.version += 1
    db.session.flush()
    return review
