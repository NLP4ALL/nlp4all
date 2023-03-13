"""Background tasks for the NLP4ALL application.

This module contains the model for background task processing.
"""

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base, BackgroundTaskStatus, TimestampMixin


class BackgroundTaskModel(TimestampMixin, Base):
    """Background task model.

    This model is used to track the status of background tasks.

    Attributes:
        id: The primary key of the model.
        task_id: The task id of the background task.
        task_status: The status of the background task.
        total_steps: The total number of steps in the background task.
        current_step: The current step of the background task.
    Mixin Attributes:
        created_at: The date and time the model was created.
        updated_at: The date and time the model was last updated.
    """

    __tablename__ = "background_task"
    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    task_status: Mapped[BackgroundTaskStatus] = mapped_column(
        Enum(BackgroundTaskStatus),
        nullable=False,
        default=BackgroundTaskStatus.PENDING)
    total_steps: Mapped[int] = mapped_column(nullable=True)
    current_step: Mapped[int] = mapped_column(default=0, nullable=True)
    status_message: Mapped[str] = mapped_column(String(256), nullable=True)
