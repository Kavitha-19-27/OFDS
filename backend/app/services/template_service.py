"""
Template service for managing chat prompt templates.
Pre-built prompts for common query patterns.
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.models.chat_template import ChatTemplate, DEFAULT_TEMPLATES
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TemplateService:
    """
    Service for managing chat prompt templates.
    Helps users form effective queries.
    """
    
    async def get_templates(
        self,
        db: AsyncSession,
        tenant_id: str,
        category: Optional[str] = None,
        include_system: bool = True
    ) -> List[Dict]:
        """
        Get available templates for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            category: Filter by category
            include_system: Include system default templates
            
        Returns:
            List of template dicts
        """
        conditions = [
            ChatTemplate.tenant_id == tenant_id,
            ChatTemplate.is_active == True
        ]
        
        if category:
            conditions.append(ChatTemplate.category == category)
        
        result = await db.execute(
            select(ChatTemplate)
            .where(and_(*conditions))
            .order_by(ChatTemplate.usage_count.desc())
        )
        tenant_templates = result.scalars().all()
        
        templates = []
        
        # Add system defaults if requested
        if include_system:
            for t in DEFAULT_TEMPLATES:
                if category is None or t['category'] == category:
                    templates.append({
                        'id': t['id'],
                        'name': t['name'],
                        'prompt_template': t['prompt_template'],
                        'description': t['description'],
                        'category': t['category'],
                        'is_system': True
                    })
        
        # Add tenant templates
        for t in tenant_templates:
            templates.append({
                'id': t.id,
                'name': t.name,
                'prompt_template': t.prompt_template,
                'description': t.description,
                'category': t.category,
                'is_system': False,
                'usage_count': t.usage_count
            })
        
        return templates
    
    async def get_template_by_id(
        self,
        db: AsyncSession,
        tenant_id: str,
        template_id: str
    ) -> Optional[Dict]:
        """Get a specific template by ID."""
        # Check system templates first
        for t in DEFAULT_TEMPLATES:
            if t['id'] == template_id:
                return {
                    'id': t['id'],
                    'name': t['name'],
                    'prompt_template': t['prompt_template'],
                    'description': t['description'],
                    'category': t['category'],
                    'is_system': True
                }
        
        # Check tenant templates
        try:
            template_int_id = int(template_id)
            result = await db.execute(
                select(ChatTemplate).where(
                    and_(
                        ChatTemplate.tenant_id == tenant_id,
                        ChatTemplate.id == template_int_id
                    )
                )
            )
            t = result.scalar_one_or_none()
            
            if t:
                return {
                    'id': t.id,
                    'name': t.name,
                    'prompt_template': t.prompt_template,
                    'description': t.description,
                    'category': t.category,
                    'is_system': False
                }
        except ValueError:
            pass
        
        return None
    
    async def create_template(
        self,
        db: AsyncSession,
        tenant_id: str,
        name: str,
        prompt_template: str,
        category: str = "custom",
        description: Optional[str] = None
    ) -> ChatTemplate:
        """Create a custom template for tenant."""
        template = ChatTemplate(
            tenant_id=tenant_id,
            name=name,
            prompt_template=prompt_template,
            category=category,
            description=description,
            is_active=True
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Created template '{name}' for tenant {tenant_id}")
        return template
    
    async def update_template(
        self,
        db: AsyncSession,
        tenant_id: str,
        template_id: int,
        **updates
    ) -> Optional[ChatTemplate]:
        """Update a custom template."""
        result = await db.execute(
            select(ChatTemplate).where(
                and_(
                    ChatTemplate.tenant_id == tenant_id,
                    ChatTemplate.id == template_id
                )
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        for key, value in updates.items():
            if hasattr(template, key) and key not in ['id', 'tenant_id']:
                setattr(template, key, value)
        
        await db.commit()
        await db.refresh(template)
        
        return template
    
    async def delete_template(
        self,
        db: AsyncSession,
        tenant_id: str,
        template_id: int
    ) -> bool:
        """Delete a custom template."""
        result = await db.execute(
            select(ChatTemplate).where(
                and_(
                    ChatTemplate.tenant_id == tenant_id,
                    ChatTemplate.id == template_id
                )
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return False
        
        await db.delete(template)
        await db.commit()
        
        logger.info(f"Deleted template {template_id} for tenant {tenant_id}")
        return True
    
    async def record_usage(
        self,
        db: AsyncSession,
        tenant_id: str,
        template_id: str
    ) -> None:
        """Record template usage for popularity tracking."""
        # Skip system templates
        try:
            template_int_id = int(template_id)
        except ValueError:
            return
        
        result = await db.execute(
            select(ChatTemplate).where(
                and_(
                    ChatTemplate.tenant_id == tenant_id,
                    ChatTemplate.id == template_int_id
                )
            )
        )
        template = result.scalar_one_or_none()
        
        if template:
            template.usage_count = (template.usage_count or 0) + 1
            await db.commit()
    
    def apply_template(
        self,
        template: Dict,
        **variables
    ) -> str:
        """
        Apply variables to a template.
        
        Example:
            template: "What is {topic} in this document?"
            variables: {"topic": "machine learning"}
            result: "What is machine learning in this document?"
        """
        prompt = template['prompt_template']
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def get_template_variables(self, template: Dict) -> List[str]:
        """Extract variable names from template."""
        import re
        prompt = template['prompt_template']
        variables = re.findall(r'\{(\w+)\}', prompt)
        return list(set(variables))
    
    def get_categories(self) -> List[str]:
        """Get all available template categories."""
        return [
            "summary",
            "analysis",
            "extraction",
            "comparison",
            "explanation",
            "custom"
        ]
