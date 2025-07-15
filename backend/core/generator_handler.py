import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
import pandas as pd
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATOR_PERSONA = """
You are an expert-level marketing and sales copywriter with deep understanding of regional cultures, industries, and human psychology. 
Your task is to intelligently personalize content by:
1. Making direct replacements where placeholders exist
2. Using contextual data to make logical inferences and adaptations
3. Maintaining the original message structure and intent while making it feel naturally personalized

You excel at using limited data points to create rich, contextual personalizations. For example:
- Location data → regional references, weather patterns, local culture, timezone considerations
- Company/Industry → industry challenges, trends, terminology, pain points
- Title/Role → responsibilities, priorities, communication style
- Name → cultural considerations, formality level
- Company size → scale of challenges, decision-making process

The final output should ONLY be the personalized text. Do not add any extra greetings, commentary, or sign-offs.
"""

async def generate_content_rows(
    csv_file: io.BytesIO,
    key_fields: list[str],
    core_content: str,
    is_preview: bool = False,
    generation_goal: str = ""
):
    """
    Reads a CSV, generates personalized content row by row, and yields each
    new row as it's completed.
    """
    try:
        df = pd.read_csv(csv_file)
        # For preview, we only process the first row, but we still need the full logic
        target_df = df.head(1) if is_preview else df

        if len(df) > 1000:
            raise ValueError("CSV file cannot contain more than 1000 rows.")

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=os.environ.get("GEMINI_API_KEY"),
            temperature=0.7,
            max_output_tokens=8192 # This is a high value, ensure it's needed
        )

        total_rows = len(target_df)
        logger.info(f"Starting content generation stream for {total_rows} rows...")

        # Yield header as the first part of the stream
        header = target_df.columns.tolist() + ['ai_generated_content']
        yield header

        for index, row in target_df.iterrows():
            logger.info(f"Streaming processing for row {index + 1}/{total_rows}")

            # Direct replacement for key fields
            temp_content = core_content
            for field in key_fields:
                placeholder = f"{{{{{field}}}}}"
                if placeholder in temp_content and field in row and pd.notna(row[field]):
                    temp_content = temp_content.replace(placeholder, str(row[field]))

            # Prepare contextual data for the AI - include ALL fields for inference
            all_data = {k: v for k, v in row.items() if pd.notna(v)}
            
            # Create rich context descriptions
            context_parts = []
            for k, v in all_data.items():
                if pd.notna(v):
                    context_parts.append(f"{k}: {v}")
            
            context_str = "\n".join(context_parts)

            # Conditionally add the overall goal to the prompt
            goal_section = ""
            if generation_goal:
                goal_section = f"""
**Overall Personalization Goal:**
{generation_goal}
"""
            
            # Construct the enhanced prompt
            prompt = f"""
Your Task:
You are personalizing an email template for a specific recipient. Your goal is to create a version that feels personally written for them while maintaining the original structure and intent.

**INTELLIGENT PERSONALIZATION INSTRUCTIONS:**
1. First, replace any {{placeholders}} that were already handled
2. Then, use ALL the contextual data below to make intelligent adaptations:
   - If they're on the West Coast and template mentions "west coast beauty", keep it
   - If they're on the East Coast and template mentions "west coast beauty", adapt to "East Coast charm" or "beautiful fall foliage"
   - If template mentions industry pain points generically, make them specific to their industry
   - Adapt cultural references, weather mentions, time zones, local events based on location
   - Adjust formality and terminology based on their role/title
   - Reference company-specific details when relevant

3. MAINTAIN the overall structure, length, and core message
4. Make personalizations feel natural, not forced
5. If data is limited, still make subtle adaptations based on what you have

{goal_section}

**Recipient's Data:**
{context_str}

**Email Template to Personalize:**
{temp_content}

**CRITICAL RULES:**
- Output ONLY the final personalized email
- Keep the same overall structure and flow
- Make intelligent inferences from the data (e.g., Boston → cold winters, tech hub, historical city)
- Personalization should enhance, not replace, the core message
- If uncertain about a detail, make reasonable assumptions based on the data provided
"""
            messages = [
                SystemMessage(content=GENERATOR_PERSONA),
                HumanMessage(content=prompt)
            ]

            try:
                response = await llm.ainvoke(messages)
                generated_text = response.content
                logger.info(f"Successfully generated content for row {index + 1}")
            except Exception as e:
                logger.error(f"LLM failed for row {index + 1}. Error: {e}. Using empty string.")
                generated_text = ""

            new_row = row.tolist() + [generated_text]
            yield new_row

        logger.info(f"Finished content generation stream for all {total_rows} rows.")

    except Exception as e:
        logger.error(f"Error processing CSV file in generator: {e}")
        # In a stream, we should yield an error object or handle it gracefully
        # For now, re-raising will be caught by the main endpoint.
        raise 