# OpenAI API Configuration

## API Key Setup

To configure the OpenAI API key for GPT-4.1, follow these steps:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and replace `your_openai_api_key_here` with your actual OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-proj-[YOUR_ACTUAL_API_KEY_HERE]
   ```

3. The system is pre-configured to use:
   - **LLM Model**: `gpt-4.1-preview` (latest GPT-4 variant)
   - **Embedding Model**: `text-embedding-3-small`

## Security Notes

- The `.env` file is included in `.gitignore` to prevent accidental commits
- Never commit API keys to version control
- Contact the project owner for the actual API key if needed

## Model Configuration

The system automatically uses GPT-4.1 for:
- Conversational chat responses
- Content structuring and metadata extraction
- SAP IS-U technical question answering

For production deployment, ensure the API key has sufficient quota and rate limits configured.
