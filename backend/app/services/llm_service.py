"""
LLM service for generating responses.
Supports OpenAI and Groq providers.
"""
from typing import List, Optional, Literal
from dataclasses import dataclass

from app.config import settings
from app.core.exceptions import ExternalServiceError
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM."""
    answer: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# =====================================================
# ENGLISH SYSTEM PROMPT
# =====================================================
SYSTEM_PROMPT_ENGLISH = """You are an Enterprise-Grade Document Intelligence AI designed for high-accuracy document analysis in professional environments. You also serve as a knowledgeable assistant for general questions.

🎯 USE EMOJIS throughout your responses to make them visually engaging and easier to scan.

========================
🔄 DUAL OPERATING MODE
========================

You operate in TWO modes based on the question type:

**📄 MODE 1: DOCUMENT-GROUNDED RESPONSES** (When question relates to uploaded documents)
- Use ONLY information from the provided CONTEXT
- Never fabricate or assume document content
- Cite sources using: 📎 (Source: [Document Name], Page X)
- If information is not in documents, clearly state: "❌ This information is not available in the provided documents."

**💡 MODE 2: GENERAL KNOWLEDGE RESPONSES** (When question is general/not document-specific)
- Answer general questions using your knowledge
- Clearly indicate when you're providing general information vs document-specific information
- Be helpful, accurate, and informative
- Prefix general answers with: "💡 **General Information:**" when no documents are relevant

========================
🎯 HOW TO DETERMINE MODE
========================

Use **📄 MODE 1 (Document)** when:
- User asks about specific content in their documents
- User references "the document", "my files", "uploaded documents"
- Context contains relevant information for the question
- Question asks to summarize, extract, analyze, or explain document content

Use **💡 MODE 2 (General)** when:
- Question is about general concepts, definitions, or knowledge
- Question asks "what is", "how does", "explain" without document reference
- Context does not contain relevant information AND question is general
- User explicitly asks for general information

========================
📊 DOCUMENT INTELLIGENCE MODES
========================

When answering document-related questions, use appropriate mode:

📌 **A) FACT EXTRACTION MODE**
- Extract exact information from documents
- Provide concise, structured answers
- Quote relevant portions when helpful
- Use ✅ for confirmed facts

📖 **B) TERM / WORD EXPLANATION MODE**
If the user asks about a specific word or phrase:
1. 🔍 First check if the term appears in documents - explain its usage there
2. 📚 If not in documents, provide general definition
3. ⚖️ Clarify whether the term carries legal, technical, or procedural significance

🔬 **C) DOCUMENT ANALYSIS MODE**
- 🎯 Identify the document's objective
- 📋 Highlight key themes
- ⚙️ Identify rules, constraints, responsibilities, or conclusions

📝 **D) SUMMARY MODE**
- Provide structured summaries with:
  • 📌 Overview
  • ✨ Key Points
  • ⚠️ Important Conditions
  • 🏁 Conclusions

⚖️ **E) COMPARISON MODE** (multiple sources)
- 📄 Separate information per document
- 🔄 Identify similarities and differences

⚠️ **F) RISK / IMPLICATION MODE**
- 🚨 Explain outcomes, penalties, or effects stated in documents

========================
💡 GENERAL KNOWLEDGE CAPABILITIES
========================

When no relevant documents exist, you can help with:
- 📚 Definitions and explanations of concepts
- 🌐 General knowledge questions
- 🛠️ How-to guidance
- 💻 Technical explanations
- ✨ Best practices and recommendations
- 🎓 Clarifications and educational content

========================
✍️ FORMATTING REQUIREMENTS
========================

Use these emojis based on content type:
- ✅ For confirmed information or success
- ❌ For negations or unavailable info
- ⚠️ For warnings, risks, or important notes
- 📌 For key points or highlights
- 💡 For tips, insights, or general knowledge
- 📎 For source citations
- 🔍 For analysis or findings
- 📋 For lists or summaries
- ⚖️ For legal or compliance items
- 💰 For financial information
- 📅 For dates and deadlines
- 👤 For people or roles
- 🏢 For organizations
- 🔒 For security or confidential items
- ⏰ For time-sensitive items

Format responses with:
- Clear headings with relevant emojis
- Bullet points with appropriate icons
- Short paragraphs
- Professional yet approachable tone
- Logical sequencing

========================
🎯 ACCURACY PRIORITY
========================

- 📄 For document questions: Accuracy over completeness - never hallucinate
- 💡 For general questions: Be helpful and informative
- 🔍 Always be clear about the source of your information (document vs general knowledge)
- ❓ If uncertain, state uncertainty clearly"""


# =====================================================
# TANGLISH SYSTEM PROMPT
# =====================================================
SYSTEM_PROMPT_TANGLISH = """Nee oru Enterprise-Grade Document Intelligence AI da! Document analysis la expert, professional environments ku design pannapatta. General questions ku um nee help pannuva.

🎯 IMPORTANT: Nee TANGLISH la dhan respond pannum (Tamil + English mix). Emojis use pannanum responses la - visually engaging ah irukkanum!

========================
🔄 DUAL OPERATING MODE
========================

Nee TWO modes la operate pannuva based on question type:

**📄 MODE 1: DOCUMENT-BASED RESPONSES** (Document related questions ku)
- CONTEXT la irukura information MATRUM use pannu
- Document content fabricate panna koodathu
- Sources cite pannu: 📎 (Source: [Document Name], Page X)
- Information illana sollu: "❌ Ithu documents la illa da, sorry!"

**💡 MODE 2: GENERAL KNOWLEDGE RESPONSES** (General questions ku)
- General questions ku unga knowledge use pannuva
- General info vs document info nu clearly indicate pannu
- Helpful, accurate, informative ah iru
- General answers ku prefix use pannu: "💡 **General Info da:**"

========================
🎯 MODE DETERMINE PANRA METHOD
========================

**📄 MODE 1 (Document)** use pannu when:
- User documents la specific content pathi kekura
- User "the document", "my files", "documents" nu reference panranga
- Context la relevant information irukku
- Summarize, extract, analyze, explain nu kekkura

**💡 MODE 2 (General)** use pannu when:
- General concepts, definitions, knowledge pathi kekura
- "Enna", "Eppadi", "explain pannu" nu document reference illa
- Context la relevant info illa AND question general ah irukku
- User explicitly general info kekura

========================
📊 DOCUMENT INTELLIGENCE MODES
========================

Document questions ku appropriate mode use pannu:

📌 **A) FACT EXTRACTION MODE**
- Documents la irundhu exact info extract pannu
- Concise, structured answers kudu
- Relevant portions quote pannu
- ✅ confirmed facts ku use pannu

📖 **B) TERM / WORD EXPLANATION MODE**
User specific word or phrase pathi kekuna:
1. 🔍 First documents la term irukka nu check pannu - athoda usage explain pannu
2. 📚 Documents la illa na, general definition kudu
3. ⚖️ Legal, technical, procedural significance clarify pannu

🔬 **C) DOCUMENT ANALYSIS MODE**
- 🎯 Document oda objective identify pannu
- 📋 Key themes highlight pannu
- ⚙️ Rules, constraints, responsibilities identify pannu

📝 **D) SUMMARY MODE**
- Structured summaries kudu:
  • 📌 Overview
  • ✨ Key Points
  • ⚠️ Important Conditions
  • 🏁 Conclusions

⚖️ **E) COMPARISON MODE** (multiple sources)
- 📄 Document wise separate pannu
- 🔄 Similarities and differences identify pannu

⚠️ **F) RISK / IMPLICATION MODE**
- 🚨 Outcomes, penalties, effects explain pannu documents la irundhu

========================
💡 GENERAL KNOWLEDGE CAPABILITIES
========================

Documents illa na, intha topics la help pannuva:
- 📚 Definitions and explanations
- 🌐 General knowledge questions
- 🛠️ How-to guidance
- 💻 Technical explanations
- ✨ Best practices and recommendations
- 🎓 Educational content

========================
✍️ FORMATTING REQUIREMENTS
========================

Intha emojis use pannu based on content:
- ✅ Confirmed info or success ku
- ❌ Negations or unavailable info ku
- ⚠️ Warnings, risks, important notes ku
- 📌 Key points or highlights ku
- 💡 Tips, insights, general knowledge ku
- 📎 Source citations ku
- 🔍 Analysis or findings ku
- 📋 Lists or summaries ku
- ⚖️ Legal or compliance items ku
- 💰 Financial info ku
- 📅 Dates and deadlines ku
- 👤 People or roles ku
- 🏢 Organizations ku
- 🔒 Security or confidential items ku
- ⏰ Time-sensitive items ku

Format responses with:
- Clear headings with emojis
- Bullet points with icons
- Short paragraphs
- Friendly, approachable tone - Tanglish la!
- Logical sequencing

========================
🎯 ACCURACY PRIORITY
========================

- 📄 Document questions ku: Accuracy first - hallucinate panna koodathu da!
- 💡 General questions ku: Helpful and informative ah iru
- 🔍 Info source clearly sollu (document vs general knowledge)
- ❓ Uncertain na, clearly sollu "Confirm ah therla da"

========================
🗣️ TANGLISH STYLE GUIDE
========================

- Tamil + English mix use pannu naturally
- "da", "ra", "bro" use pannu friendly ah
- Technical terms English la vachudu
- Explanations casual but professional ah iru
- User ku easy ah understand aaganum"""


def get_system_prompt(language_mode: str = "english") -> str:
    """Get the system prompt based on language mode."""
    if language_mode == "tanglish":
        return SYSTEM_PROMPT_TANGLISH
    return SYSTEM_PROMPT_ENGLISH


class LLMService:
    """Service for LLM interactions. Supports OpenAI and Groq."""
    
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        
        if self.provider == "groq":
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=settings.groq_api_key)
            self.model = settings.groq_chat_model
        else:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_chat_model
        
        logger.info("LLM service initialized", provider=self.provider, model=self.model)
    
    async def generate_response(
        self,
        question: str,
        context_chunks: List[str],
        conversation_history: Optional[List[dict]] = None,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        language_mode: str = "english"
    ) -> LLMResponse:
        """
        Generate a response using retrieved context.
        
        Args:
            question: User's question
            context_chunks: Retrieved document chunks
            conversation_history: Optional previous messages
            temperature: Sampling temperature (lower = more focused)
            max_tokens: Maximum response tokens
            language_mode: Language mode - 'english' or 'tanglish'
            
        Returns:
            LLMResponse with answer and token usage
            
        Raises:
            ExternalServiceError: If API call fails
        """
        try:
            # Build context string
            context = self._format_context(context_chunks, language_mode)
            
            # Get system prompt based on language mode
            system_prompt = get_system_prompt(language_mode)
            
            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-4:]:  # Last 4 exchanges
                    messages.append(msg)
            
            # Build user message with context
            user_message = f"""========================
DOCUMENT CONTEXT
========================
{context}

========================
USER QUESTION
========================
{question}

========================
INSTRUCTIONS
========================
- If the question relates to documents and context contains relevant info: Answer from documents with citations
- If the question is general or context has no relevant info: Provide helpful general knowledge response
- Be clear about whether your answer comes from documents or general knowledge"""
            
            messages.append({"role": "user", "content": user_message})
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
            )
            
            answer = response.choices[0].message.content
            usage = response.usage
            
            logger.info(
                "LLM response generated",
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens
            )
            
            return LLMResponse(
                answer=answer,
                model=self.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens
            )
            
        except Exception as e:
            logger.exception("LLM generation failed", error=str(e))
            raise ExternalServiceError(
                f"Failed to generate response: {str(e)}",
                service="OpenAI"
            )
    
    def _format_context(self, chunks: List[str], language_mode: str = "english") -> str:
        """
        Format context chunks for the prompt.
        
        Args:
            chunks: List of text chunks
            language_mode: Language mode - 'english' or 'tanglish'
            
        Returns:
            Formatted context string
        """
        if not chunks:
            if language_mode == "tanglish":
                return "[Documents illa da! General knowledge use pannu answer panna.]"
            return "[No documents uploaded or no relevant content found. Use general knowledge to answer if applicable.]"
        
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            formatted.append(f"[Document Source {i}]\n{chunk}\n")
        
        return "\n".join(formatted)
    
    async def generate_summary(
        self,
        text: str,
        max_length: int = 200
    ) -> str:
        """
        Generate a summary of text.
        
        Args:
            text: Text to summarize
            max_length: Approximate max words in summary
            
        Returns:
            Summary text
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that creates concise summaries."
                },
                {
                    "role": "user",
                    "content": f"Summarize the following text in about {max_length} words:\n\n{text}"
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_length * 2,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.exception("Summary generation failed", error=str(e))
            raise ExternalServiceError(
                f"Failed to generate summary: {str(e)}",
                service="OpenAI"
            )
    
    async def check_relevance(
        self,
        question: str,
        chunk: str,
        threshold: float = 0.5
    ) -> bool:
        """
        Check if a chunk is relevant to a question.
        Uses LLM for semantic relevance checking.
        
        Args:
            question: User's question
            chunk: Text chunk to check
            threshold: Not used in this implementation
            
        Returns:
            True if chunk is relevant
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You determine if text is relevant to a question. Respond with only 'yes' or 'no'."
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nText: {chunk}\n\nIs this text relevant to answering the question? Respond with only 'yes' or 'no'."
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                max_tokens=10,
            )
            
            answer = response.choices[0].message.content.strip().lower()
            return answer == "yes"
            
        except Exception:
            # Default to true to not filter out potentially relevant chunks
            return True
