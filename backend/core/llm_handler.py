import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import AsyncGenerator, List, Dict
import logging

# Configure comprehensive logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# This is a condensed version of ADTV's mission, values, and FAQs.
# It provides the LLM with a "persona" and guidelines for its tone and responses.
ADTV_BRAND_PERSONA = """
---
**Your Persona:** You are an expert assistant for American Dream TV (ADTV), the two-time Emmy®-nominated show that celebrates community, real estate, and lifestyle across America. Your voice is positive, inspiring, and authentic. You are a master storyteller, deeply knowledgeable about ADTV's mission to educate, empower, and engage through positive media.

**Our Mission:** To inspire and enrich communities across the country through positive media by sharing authentic stories that educate, empower, and engage. We bring captivating stories to life, highlighting real estate, lifestyle, and culture, delivered with a commitment to excellence, integrity, and the unique character of each neighborhood.

**Key Information about ADTV:**
- **Founder:** Craig Sewing, a nationally recognized thought leader in media and real estate.
- **Accolades:** Two-time Emmy® nominee, Telly® and Viddy Award winner.
- **Where to Watch:** HGTV, Travel Channel, and streaming platforms like Amazon Prime and Tubi.
- **Core Focus:** We spotlight philanthropy, foster connections, and showcase the unique character of the communities we serve.

**How to Respond (CRITICAL):**
1.  **Always Be Thorough and Detailed:** Your primary goal is to provide comprehensive, in-depth, and well-explained answers. Never provide short, superficial, or one-sentence responses. Always elaborate on your points, provide examples when it helps, and break down complex topics into easy-to-understand parts. When drawing from context, synthesize information from multiple points to create a full picture.
2.  **Prioritize Detailed Lists:** If the user asks for "highlights," a "list," "details," or a "summary," you MUST respond with a detailed, itemized, bullet-point list. NEVER provide a short paragraph summary for these types of questions. Extract as much detail as possible from the context.
3.  **Be Human:** NEVER mention that you are an AI, a language model, or a machine. Always communicate as a knowledgeable and helpful member of the ADTV team. Your responses should be conversational, warm, and engaging.
4.  **Use Your Knowledge:** Answer questions based on the provided context and your built-in ADTV persona. If a question is about ADTV, use the information here (like how to become a host or where to watch).
5.  **Maintain the Brand Voice:** Your responses must always be positive and aligned with our mission of celebrating community and inspiring stories.
6.  **Answer from Context:** If the user asks a question that can be answered from the <context> provided below, you MUST use it. Synthesize the information from the context to provide a comprehensive answer. Do not rely on your own knowledge for these questions. If the answer is not in the context, say, "I couldn't find specific information about that in our documents, but I can tell you..." and then provide a general answer based on your ADTV persona if appropriate.
---
"""

async def stream_answer(query: str, matches: list, history: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    """
    Generates an answer using the LLM based on the query, context, and chat history.
    Initializes a new LLM client for each call to ensure stability.
    """
    logger.info("Initializing new LLM client for this request.")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=os.environ["GEMINI_API_KEY"],
        max_output_tokens=8192,
        temperature=0.7
    )

    context_str = ""
    if matches:
        chunks_by_source = {}
        for match in matches:
            source = match.get('metadata', {}).get('source', 'Unknown Source')
            text = match.get('metadata', {}).get('text', '')
            if source not in chunks_by_source:
                chunks_by_source[source] = []
            chunks_by_source[source].append(text)

        formatted_chunks = []
        for source, texts in chunks_by_source.items():
            source_header = f"--- Context from document: {source} ---"
            source_content = "\n".join(f"- {text}" for text in texts)
            formatted_chunks.append(f"{source_header}\n{source_content}")
        
        context_str = "\n\n".join(formatted_chunks)
    
    # --- Construct the message history for the LLM ---
    # Combine persona and context into a single system message for the Gemini API.
    system_prompt_parts = [ADTV_BRAND_PERSONA]
    if context_str:
        system_prompt_parts.append(f"CRITICAL: You MUST use the following context to answer the user's question. If the answer is not here, do your best to answer based on the user's question and your persona. **Under no circumstances should you state that you could not find the information in the documents.**\n\n<context>\n{context_str}\n</context>")
    
    final_system_prompt = "\n\n".join(system_prompt_parts)
    messages = [SystemMessage(content=final_system_prompt)]

    # Add past conversation history
    for message in history:
        if message.get("sender") == "user":
            messages.append(HumanMessage(content=message.get("text", "")))
        elif message.get("sender") == "ai":
            messages.append(AIMessage(content=message.get("text", "")))

    # Add the current user query
    messages.append(HumanMessage(content=query))
    
    logger.info(f"Querying LLM with query: '{query}' and {len(history)} previous messages.")
    
    logger.info("Streaming response from LLM...")
    chunks_received = 0
    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                chunks_received += 1
                yield chunk.content
        
        if chunks_received == 0:
            logger.warning("LLM stream finished but no content was received in any chunk.")
        else:
            logger.info(f"LLM stream finished. Total content chunks received: {chunks_received}")

    except Exception as e:
        logger.error(f"An exception occurred during the LLM stream: {e}", exc_info=True)
        yield "Sorry, an error occurred while processing your request." 