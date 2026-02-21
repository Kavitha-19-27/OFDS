"""
Streaming service for Server-Sent Events (SSE) responses.
Provides real-time token-by-token delivery of LLM responses.
"""
from typing import AsyncGenerator, Dict, Any, Optional
import json
import asyncio

from app.utils.logger import get_logger

logger = get_logger(__name__)


class StreamService:
    """
    Service for streaming LLM responses via Server-Sent Events.
    Improves perceived latency and user experience.
    """
    
    async def stream_chat_response(
        self,
        groq_client,
        messages: list,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat response token by token.
        
        Yields SSE-formatted chunks.
        """
        try:
            # Create streaming completion
            stream = await groq_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            # Track for stats
            total_tokens = 0
            full_response = ""
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    total_tokens += 1
                    
                    # Yield SSE formatted chunk
                    yield self._format_sse({
                        'type': 'content',
                        'content': content
                    })
            
            # Send completion message
            yield self._format_sse({
                'type': 'done',
                'total_tokens': total_tokens
            })
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield self._format_sse({
                'type': 'error',
                'error': str(e)
            })
    
    async def stream_with_sources(
        self,
        groq_client,
        messages: list,
        sources: list,
        confidence: Dict[str, Any],
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Stream response with metadata (sources, confidence).
        Sends metadata first, then streams content.
        """
        # Send metadata first
        yield self._format_sse({
            'type': 'metadata',
            'sources': sources[:3],  # Top 3 sources
            'confidence': confidence
        })
        
        # Small delay to ensure metadata arrives first
        await asyncio.sleep(0.01)
        
        # Stream the actual response
        async for chunk in self.stream_chat_response(
            groq_client, messages, model, temperature, max_tokens
        ):
            yield chunk
    
    async def stream_with_progress(
        self,
        groq_client,
        messages: list,
        stages: list,  # e.g., ['Searching...', 'Analyzing...', 'Generating...']
        model: str = "llama-3.3-70b-versatile"
    ) -> AsyncGenerator[str, None]:
        """
        Stream with progress indicators before response.
        Useful for multi-stage RAG pipeline.
        """
        # Send progress stages
        for i, stage in enumerate(stages):
            yield self._format_sse({
                'type': 'progress',
                'stage': stage,
                'step': i + 1,
                'total_steps': len(stages)
            })
            # Brief delay between stages
            await asyncio.sleep(0.1)
        
        # Stream actual response
        async for chunk in self.stream_chat_response(
            groq_client, messages, model
        ):
            yield chunk
    
    def _format_sse(self, data: Dict[str, Any]) -> str:
        """Format data as SSE event."""
        return f"data: {json.dumps(data)}\n\n"
    
    async def heartbeat_generator(
        self,
        interval: float = 15.0
    ) -> AsyncGenerator[str, None]:
        """
        Generate heartbeat events to keep connection alive.
        Use with asyncio.merge or similar for long-running streams.
        """
        while True:
            yield self._format_sse({'type': 'heartbeat'})
            await asyncio.sleep(interval)
    
    @staticmethod
    def get_sse_headers() -> Dict[str, str]:
        """Get standard headers for SSE response."""
        return {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
