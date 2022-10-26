"""Matrix Categories model"""

from sqlalchemy import Column, Integer, ForeignKey

from .database import Base

class MatrixCategories(Base): # pylint: disable=too-few-public-methods
    """MatrixCategories model."""
    __tablename__ = "confusionmatrix_categories"
    id = Column(Integer(), primary_key=True)
    matrix_id = Column(Integer(), ForeignKey("confusion_matrix.id", ondelete="CASCADE"))
    category_id = Column(
        Integer(), ForeignKey("tweet_tag_category.id", ondelete="CASCADE")
    )