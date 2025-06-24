import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
import pandas as pd
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATOR_PERSONA = """
You are an expert-level marketing and sales copywriter. Your task is to rewrite a piece of core content for a specific individual based on their data.
You must seamlessly weave the user's data into the core content to make it feel personal, natural, and compelling.
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

            # Prepare contextual data for the AI
            context_data = {k: v for k, v in row.items() if k not in key_fields}
            context_str = ", ".join([f"{k}: '{v}'" for k, v in context_data.items() if pd.notna(v)])

            # Conditionally add the overall goal to the prompt
            goal_section = ""
            if generation_goal:
                goal_section = f"""
**Overall Goal for This Personalization:**
---
{generation_goal}
---
"""
            # Construct the prompt
            prompt = f"""
Your Task:
You are an expert copywriter. Your goal is to rewrite and personalize the 'Smart Template' below.
It is crucial that you **maintain the original tone, style, length, and overall structure** of the Smart Template.
The personalization should be subtle and natural, using the 'Contextual Data' to make the message highly relevant to the recipient.
If the Contextual Data is sparse or unhelpful, still do your best to personalize the message. **Under no circumstances should you state that you couldn't find information.**
Do NOT simply list the data. Instead, weave the information naturally into the template.
{goal_section}
**Contextual Data for This Prospect:**
---
{context_str}
---

**Smart Template to Personalize:**
---
{temp_content}
---

**IMPORTANT:** The output should ONLY be the final rewritten text. Do not add any of your own commentary, greetings, or sign-offs.
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