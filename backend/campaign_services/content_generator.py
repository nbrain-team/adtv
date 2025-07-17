"""
AI Content Generation Service
Uses LangChain with RAG to generate marketing content
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import Pinecone
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pinecone
import numpy as np

from core.campaign_models import Client, Campaign, ContentItem, Platform


class ContentGeneratorService:
    def __init__(self):
        # Initialize Pinecone
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENV", "us-east-1")
        )
        
        # Initialize embeddings using Google Generative AI
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", 
            google_api_key=gemini_api_key
        )
        
        # Initialize vector store
        self.index_name = os.getenv("PINECONE_INDEX", "marketing-content")
        try:
            self.vectorstore = Pinecone.from_existing_index(
                index_name=self.index_name,
                embedding=self.embeddings
            )
        except:
            # If index doesn't exist, we'll create it when we have documents
            self.vectorstore = None
        
        # Initialize Gemini LLMs
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.primary_llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=gemini_api_key,
            temperature=0.7,
            max_output_tokens=2000
        )
        
        self.creative_llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=gemini_api_key,
            temperature=0.9,
            max_output_tokens=1500
        )
        
        # Text splitter for documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def index_client_documents(self, client_id: str, documents: List[Dict[str, Any]]):
        """Index client documents into Pinecone for RAG"""
        all_texts = []
        
        for doc in documents:
            # Split document into chunks
            chunks = self.text_splitter.split_text(doc['content'])
            
            # Create Document objects with metadata
            for i, chunk in enumerate(chunks):
                metadata = {
                    "client_id": client_id,
                    "document_id": doc['id'],
                    "filename": doc['filename'],
                    "chunk_index": i,
                    "type": "client_document"
                }
                all_texts.append(Document(page_content=chunk, metadata=metadata))
        
        # Add to vector store
        if self.vectorstore is None:
            # Create new index if it doesn't exist
            self.vectorstore = Pinecone.from_documents(
                all_texts, 
                self.embeddings,
                index_name=self.index_name
            )
        else:
            self.vectorstore.add_documents(all_texts)
    
    def generate_campaign_content(
        self,
        client: Client,
        campaign: Campaign,
        platforms: List[Platform]
    ) -> Dict[Platform, List[Dict[str, Any]]]:
        """Generate content for all platforms in a campaign"""
        
        # Retrieve relevant client context
        client_context = self._get_client_context(client.id, campaign.topics)
        
        # Generate content for each platform
        generated_content = {}
        
        for platform in platforms:
            if platform == Platform.FACEBOOK:
                content = self._generate_facebook_content(client, campaign, client_context)
            elif platform == Platform.LINKEDIN:
                content = self._generate_linkedin_content(client, campaign, client_context)
            elif platform == Platform.EMAIL:
                content = self._generate_email_sequence(client, campaign, client_context)
            else:
                continue
            
            generated_content[platform] = content
        
        return generated_content
    
    def _get_client_context(self, client_id: str, topics: List[str]) -> str:
        """Retrieve relevant context from vector store"""
        # If no vectorstore, return empty context
        if self.vectorstore is None:
            return ""
            
        # Create query from topics
        query = f"Client information and content related to: {', '.join(topics)}"
        
        # Search vector store
        retriever = self.vectorstore.as_retriever(
            search_kwargs={
                "k": 10,
                "filter": {"client_id": client_id}
            }
        )
        
        docs = retriever.get_relevant_documents(query)
        
        # Combine document contents
        context = "\n\n".join([doc.page_content for doc in docs])
        return context
    
    def _generate_facebook_content(
        self,
        client: Client,
        campaign: Campaign,
        context: str
    ) -> List[Dict[str, Any]]:
        """Generate Facebook posts"""
        
        posts = []
        topics = campaign.topics[:5]  # Max 5 topics
        
        # Calculate posting schedule
        start_date = campaign.start_date
        end_date = campaign.end_date
        days_in_campaign = (end_date - start_date).days
        posts_per_topic = max(1, days_in_campaign // (len(topics) * 3))  # 3 posts per week per topic
        
        for topic in topics:
            prompt = PromptTemplate(
                template="""You are a social media marketing expert creating Facebook posts for {company}.

Client Context:
{context}

Brand Voice: {brand_voice}
Target Audience: {target_audience}

Create {num_posts} engaging Facebook posts about: {topic}

Requirements:
- Each post should be 100-300 characters
- Include relevant emojis
- Add 3-5 hashtags per post
- Make posts conversational and engaging
- Include a call-to-action
- Vary the post styles (questions, tips, announcements, etc.)

Format each post as JSON:
{{
    "content": "post text",
    "hashtags": ["hashtag1", "hashtag2"],
    "media_suggestion": "description of suggested image/video"
}}

Posts:""",
                input_variables=["company", "context", "brand_voice", "target_audience", "topic", "num_posts"]
            )
            
            chain = prompt | self.creative_llm
            
            response = chain.invoke({
                "company": client.company,
                "context": context,
                "brand_voice": client.brand_voice or "professional and friendly",
                "target_audience": json.dumps(client.target_audience or {}),
                "topic": topic,
                "num_posts": posts_per_topic
            })
            
            # Parse response and create post objects
            try:
                # Extract JSON from response
                import re
                json_matches = re.findall(r'\{[^}]+\}', response.content)
                
                for i, json_str in enumerate(json_matches):
                    post_data = json.loads(json_str)
                    
                    # Calculate scheduled date
                    days_offset = (i * days_in_campaign) // len(json_matches)
                    scheduled_date = start_date + timedelta(days=days_offset)
                    
                    posts.append({
                        "platform": Platform.FACEBOOK,
                        "content": post_data.get("content", ""),
                        "hashtags": post_data.get("hashtags", []),
                        "media_suggestion": post_data.get("media_suggestion", ""),
                        "scheduled_date": scheduled_date,
                        "topic": topic
                    })
            except Exception as e:
                print(f"Error parsing Facebook content: {e}")
        
        return posts
    
    def _generate_linkedin_content(
        self,
        client: Client,
        campaign: Campaign,
        context: str
    ) -> List[Dict[str, Any]]:
        """Generate LinkedIn posts"""
        
        posts = []
        topics = campaign.topics[:5]
        
        start_date = campaign.start_date
        end_date = campaign.end_date
        days_in_campaign = (end_date - start_date).days
        posts_per_topic = max(1, days_in_campaign // (len(topics) * 2))  # 2 posts per week per topic
        
        for topic in topics:
            prompt = PromptTemplate(
                template="""You are a B2B marketing expert creating LinkedIn posts for {company}.

Client Context:
{context}

Industry: {industry}
Brand Voice: {brand_voice}

Create {num_posts} professional LinkedIn posts about: {topic}

Requirements:
- Each post should be 150-600 characters
- Professional tone but engaging
- Include industry insights or thought leadership
- Add 3-5 relevant hashtags
- Include statistics or data points when relevant
- End with a question or call-to-action

Format each post as JSON:
{{
    "content": "post text",
    "hashtags": ["hashtag1", "hashtag2"],
    "post_type": "thought_leadership|industry_insight|company_update|tips"
}}

Posts:""",
                input_variables=["company", "context", "industry", "brand_voice", "topic", "num_posts"]
            )
            
            chain = prompt | self.primary_llm
            
            response = chain.invoke({
                "company": client.company,
                "context": context,
                "industry": client.industry or "business",
                "brand_voice": client.brand_voice or "professional and authoritative",
                "topic": topic,
                "num_posts": posts_per_topic
            })
            
            # Parse response
            try:
                import re
                json_matches = re.findall(r'\{[^}]+\}', response.content)
                
                for i, json_str in enumerate(json_matches):
                    post_data = json.loads(json_str)
                    
                    days_offset = (i * days_in_campaign) // len(json_matches)
                    scheduled_date = start_date + timedelta(days=days_offset)
                    
                    posts.append({
                        "platform": Platform.LINKEDIN,
                        "content": post_data.get("content", ""),
                        "hashtags": post_data.get("hashtags", []),
                        "post_type": post_data.get("post_type", "thought_leadership"),
                        "scheduled_date": scheduled_date,
                        "topic": topic
                    })
            except Exception as e:
                print(f"Error parsing LinkedIn content: {e}")
        
        return posts
    
    def _generate_email_sequence(
        self,
        client: Client,
        campaign: Campaign,
        context: str
    ) -> List[Dict[str, Any]]:
        """Generate email sequence"""
        
        emails = []
        topics = campaign.topics[:5]
        
        # Create a weekly email for each topic
        for i, topic in enumerate(topics):
            prompt = PromptTemplate(
                template="""You are an email marketing expert creating an email campaign for {company}.

Client Context:
{context}

Target Audience: {target_audience}
Brand Voice: {brand_voice}

Create a compelling marketing email about: {topic}

Requirements:
- Subject line (50 characters max)
- Preview text (100 characters max)
- Email body (300-500 words)
- Include personalization tokens like {{first_name}}
- Clear call-to-action
- Mobile-friendly formatting
- Professional but engaging tone

Format as JSON:
{{
    "subject": "subject line",
    "preview": "preview text",
    "body": "email body with HTML formatting",
    "cta_text": "call to action text",
    "cta_url": "{{website_url}}/campaign"
}}

Email:""",
                input_variables=["company", "context", "target_audience", "brand_voice", "topic"]
            )
            
            chain = prompt | self.primary_llm
            
            response = chain.invoke({
                "company": client.company,
                "context": context,
                "target_audience": json.dumps(client.target_audience or {}),
                "brand_voice": client.brand_voice or "professional and friendly",
                "topic": topic
            })
            
            # Parse response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    email_data = json.loads(json_match.group())
                    
                    # Schedule weekly
                    scheduled_date = campaign.start_date + timedelta(weeks=i)
                    
                    emails.append({
                        "platform": Platform.EMAIL,
                        "title": email_data.get("subject", ""),
                        "preview": email_data.get("preview", ""),
                        "content": email_data.get("body", ""),
                        "cta_text": email_data.get("cta_text", "Learn More"),
                        "cta_url": email_data.get("cta_url", client.website),
                        "scheduled_date": scheduled_date,
                        "topic": topic
                    })
            except Exception as e:
                print(f"Error parsing email content: {e}")
        
        return emails
    
    def regenerate_content(
        self,
        content_item: ContentItem,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """Regenerate a specific content item with optional feedback"""
        
        prompt = PromptTemplate(
            template="""You are revising marketing content based on feedback.

Original Content:
{original_content}

Platform: {platform}
Feedback: {feedback}

Generate an improved version that addresses the feedback while maintaining the core message.

Requirements:
- Keep the same format and structure
- Address the specific feedback points
- Maintain brand voice and target audience
- Improve engagement potential

Revised Content:""",
            input_variables=["original_content", "platform", "feedback"]
        )
        
        chain = prompt | self.primary_llm
        
        response = chain.invoke({
            "original_content": content_item.content,
            "platform": content_item.platform.value,
            "feedback": feedback or "Make it more engaging and compelling"
        })
        
        return {
            "content": response.content,
            "regenerated_at": datetime.utcnow(),
            "feedback_addressed": feedback
        } 