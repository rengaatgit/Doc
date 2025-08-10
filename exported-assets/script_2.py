# Create requirements.txt and configuration files
requirements = '''
langchain==0.1.0
langchain-openai==0.0.5
langchain-community==0.0.10
langgraph==0.0.20
llama-index==0.9.0
chromadb==0.4.20
openai==1.3.0
pandas==2.1.0
numpy==1.24.0
pydantic==2.5.0
python-dotenv==1.0.0
pypdf2==3.0.0
python-docx==1.0.0
aiofiles==23.2.0
asyncio-throttle==1.0.2
tenacity==8.2.0
matplotlib==3.7.0
seaborn==0.12.0
plotly==5.17.0
streamlit==1.28.0
'''

# Create requirements.txt
with open('lc_validation_system/requirements.txt', 'w') as f:
    f.write(requirements)

# Create configuration file
config = {
    "openai_api_key": "your_openai_api_key_here",
    "model_name": "gpt-4o",
    "embedding_model": "text-embedding-3-small",
    "chroma_db_path": "./data/chroma_db",
    "max_tokens": 4000,
    "temperature": 0.1,
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "top_k_retrieval": 5,
    "validation_confidence_threshold": 0.8,
    "parallel_agent_limit": 8
}

with open('lc_validation_system/config/settings.json', 'w') as f:
    json.dump(config, f, indent=2)

# Create environment template
env_template = '''
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_api_key_here

# Database Configuration
CHROMA_DB_PATH=./data/chroma_db

# Model Configuration
MODEL_NAME=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
'''

with open('lc_validation_system/.env.template', 'w') as f:
    f.write(env_template)

print("Configuration files created:")
print("- requirements.txt")
print("- config/settings.json")  
print("- .env.template")