# Marketing Campaign Generator

An AI-powered marketing campaign content generation system that creates personalized, multi-platform marketing campaigns using LangChain and GPT-4.

## Features

- **AI Content Generation**: Automatically generate marketing content for multiple platforms
- **Multi-Platform Support**: Facebook, LinkedIn, Twitter, Instagram, and Email
- **Campaign Management**: Create, review, approve, and schedule campaigns
- **Content Personalization**: Uses client documents and brand voice for tailored content
- **RAG (Retrieval Augmented Generation)**: Leverages Pinecone vector database for context
- **Approval Workflow**: Review and approve content before publishing
- **Content Regeneration**: Provide feedback and regenerate specific content items
- **Analytics Integration**: Track campaign performance (planned)

## Architecture

### Backend (FastAPI + LangChain)
- **FastAPI**: REST API framework
- **LangChain**: AI orchestration and RAG
- **Pinecone**: Vector database for document embeddings
- **PostgreSQL**: Campaign and content storage
- **GPT-4**: Primary content generation model

### Frontend (React + TypeScript)
- **React**: UI framework
- **Radix UI**: Component library
- **TypeScript**: Type safety
- **Axios**: API client

## Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL
- Pinecone account
- OpenAI API key

### Backend Setup

1. Navigate to backend directory:
```bash
cd marketing-campaign-generator/backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
# Create .env file
DATABASE_URL=postgresql://user:password@localhost/marketing_campaigns
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENV=us-east-1
PINECONE_INDEX=marketing-content
SECRET_KEY=your-secret-key
```

5. Initialize database:
```bash
python -c "from core.database import init_db; init_db()"
```

6. Run the server:
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd marketing-campaign-generator/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set environment variables:
```bash
# Create .env file
REACT_APP_API_URL=http://localhost:8000/api
```

4. Run the development server:
```bash
npm start
```

## Usage

### Creating a Campaign

1. **Select Client**: Choose the client for the campaign
2. **Campaign Details**: Name, description, and duration
3. **Topics**: Enter up to 5 topics for content generation
4. **Platforms**: Select which platforms to generate content for
5. **Generate**: AI creates a complete campaign with scheduled posts

### Content Generation Process

1. **Context Retrieval**: Fetches relevant client documents from Pinecone
2. **Prompt Engineering**: Creates platform-specific prompts with brand voice
3. **Content Generation**: GPT-4 generates content for each topic/platform
4. **Scheduling**: Automatically schedules posts throughout campaign duration
5. **Review**: All content is created as drafts for review

### Approval Workflow

1. **Draft**: Initial content generation
2. **Pending Approval**: Ready for review
3. **Approved**: Content approved for publishing
4. **Active**: Campaign is live
5. **Completed**: Campaign has ended

## API Endpoints

### Campaigns
- `POST /api/campaigns` - Create new campaign
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{id}` - Get campaign details
- `PUT /api/campaigns/{id}/status` - Update campaign status
- `POST /api/campaigns/{id}/regenerate/{content_id}` - Regenerate content

### Clients
- `POST /api/clients` - Create client
- `GET /api/clients` - List clients
- `POST /api/clients/{id}/documents` - Upload client documents

## Content Types

### Facebook
- Short, engaging posts (100-300 chars)
- Emojis and hashtags
- Call-to-action focused
- Varied post styles

### LinkedIn
- Professional tone (150-600 chars)
- Industry insights
- Thought leadership
- B2B focused

### Email
- Subject line and preview text
- 300-500 word body
- Personalization tokens
- Clear CTA

## Integration with User Roles Module

This module integrates with the exported user-roles-admin module for:
- JWT authentication
- Role-based access control
- User management

## Future Enhancements

- [ ] Social media API integration for direct publishing
- [ ] Analytics dashboard with engagement metrics
- [ ] A/B testing for content variations
- [ ] Image generation with DALL-E
- [ ] Bulk content operations
- [ ] Campaign templates
- [ ] Multi-language support
- [ ] Advanced scheduling rules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 