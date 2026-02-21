"""
Chat Feedback model for tracking user ratings on responses.
Enables feedback loop for quality improvement.
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ChatFeedback(BaseModel):
    """
    Chat feedback model for 👍/👎 ratings on responses.
    Critical for quality monitoring and improvement.
    """
    __tablename__ = "chat_feedback"
    
    chat_log_id = Column(
        String(36),
        ForeignKey("chat_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Rating: -1 = thumbs down, 1 = thumbs up
    rating = Column(
        Integer,
        nullable=False,
        index=True
    )
    
    # Optional feedback text
    feedback_text = Column(Text, nullable=True)
    
    # Categorization of negative feedback
    issue_type = Column(String(50), nullable=True)
    # Types: WRONG_ANSWER, INCOMPLETE, IRRELEVANT, HALLUCINATION, OTHER
    
    # Relationships
    chat_log = relationship("ChatLog", backref="feedback")
    user = relationship("User", backref="chat_feedbacks")
    
    __table_args__ = (
        CheckConstraint('rating IN (-1, 1)', name='check_rating_values'),
    )
    
    def __repr__(self) -> str:
        emoji = "👍" if self.rating == 1 else "👎"
        return f"<ChatFeedback({emoji}, chat={self.chat_log_id})>"
    
    @property
    def is_positive(self) -> bool:
        """Check if feedback is positive."""
        return self.rating == 1
    
    @property
    def is_negative(self) -> bool:
        """Check if feedback is negative."""
        return self.rating == -1
