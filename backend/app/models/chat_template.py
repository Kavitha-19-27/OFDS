"""
Chat Template model for pre-built chat actions.
Provides quick actions like summarize, extract, compare.
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey

from app.models.base import BaseModel


class ChatTemplate(BaseModel):
    """
    Chat template model for pre-built prompts and actions.
    Improves UX with one-click actions.
    """
    __tablename__ = "chat_templates"
    
    # NULL tenant_id means global template
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Template info
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # The prompt template (may include {document_name}, {selection}, etc.)
    prompt_template = Column(Text, nullable=False)
    
    # Category for grouping
    category = Column(String(50), nullable=True, index=True)
    # Categories: SUMMARIZE, EXTRACT, COMPARE, ANALYZE, SEARCH, OTHER
    
    # Icon name (for frontend display)
    icon = Column(String(50), default="document", nullable=False)
    
    # Active status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Is this a system template (non-editable by users)
    is_system = Column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    
    # Display order
    display_order = Column(Integer, default=0, nullable=False)
    
    def __repr__(self) -> str:
        return f"<ChatTemplate(name={self.name}, category={self.category})>"
    
    def record_usage(self) -> None:
        """Record template usage."""
        self.usage_count += 1
    
    def format_prompt(self, **kwargs) -> str:
        """Format the template with provided variables."""
        try:
            return self.prompt_template.format(**kwargs)
        except KeyError:
            return self.prompt_template


# Default system templates to be created on startup
DEFAULT_TEMPLATES = [
    {
        "id": "sys-summarize",
        "name": "Summarize Document",
        "description": "Generate a concise summary of the document",
        "prompt_template": "Please provide a concise summary of the key points from my documents.",
        "category": "SUMMARIZE",
        "icon": "document-text",
        "is_system": True,
        "display_order": 1
    },
    {
        "id": "sys-extract-key-points",
        "name": "Extract Key Points",
        "description": "Extract the main points and takeaways",
        "prompt_template": "What are the key points and main takeaways from the documents?",
        "category": "EXTRACT",
        "icon": "list-bullet",
        "is_system": True,
        "display_order": 2
    },
    {
        "id": "sys-find-action-items",
        "name": "Find Action Items",
        "description": "Identify action items and tasks",
        "prompt_template": "What are the action items, tasks, or next steps mentioned in the documents?",
        "category": "EXTRACT",
        "icon": "check-circle",
        "is_system": True,
        "display_order": 3
    },
    {
        "id": "sys-explain-concepts",
        "name": "Explain Concepts",
        "description": "Explain technical concepts in simple terms",
        "prompt_template": "Can you explain the main concepts and terminology used in the documents in simple terms?",
        "category": "ANALYZE",
        "icon": "academic-cap",
        "is_system": True,
        "display_order": 4
    },
    {
        "id": "sys-compare",
        "name": "Compare Information",
        "description": "Compare and contrast different sections or documents",
        "prompt_template": "Compare and contrast the different viewpoints or information presented in the documents.",
        "category": "COMPARE",
        "icon": "arrows-right-left",
        "is_system": True,
        "display_order": 5
    },
    {
        "id": "sys-find-definitions",
        "name": "Find Definitions",
        "description": "Find definitions of key terms",
        "prompt_template": "What are the definitions of the key terms and concepts mentioned in the documents?",
        "category": "SEARCH",
        "icon": "book-open",
        "is_system": True,
        "display_order": 6
    }
]
