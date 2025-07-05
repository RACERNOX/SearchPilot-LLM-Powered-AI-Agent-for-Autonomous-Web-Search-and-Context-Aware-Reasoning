from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
import os
import requests
from bs4 import BeautifulSoup
import trafilatura
import uvicorn
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SearchPilot", description="AI Search Agent with Web Interface")

# Setup templates
try:
    templates = Jinja2Templates(directory="templates")
    logger.info("Templates directory loaded successfully")
except Exception as e:
    logger.error(f"Failed to load templates: {e}")

# Simple system messages
ASSISTANT_MSG = {
    'role': 'system',
    'content': (
        'You are an AI assistant that has another AI model working to get you live data from search '
        'engine results that will be attached before a USER PROMPT. You must analyze the SEARCH RESULT '
        'and use any relevant data to generate the most useful & intelligent response an AI assistant '
        'that always impresses the user would generate.'
    )
}

SEARCH_OR_NOT_MSG = (
    'You are not an AI assistant. Your only task is to decide if the last user prompt in a conversation '
    'with an AI assistant requires more data to be retrieved from a searching Google for the assistant '
    'to respond correctly. If the assistant should search Google for more data before responding to ensure a correct response, '
    'simply respond "True". If the conversation already has the context, or a Google search is not what an '
    'intelligent human would do to respond correctly to the last message in the convo, respond "False". '
    'Do not generate any explanations. Only generate "True" or "False" as a response.'
)

# Global conversation state
assistant_convo = [ASSISTANT_MSG]

def chat_with_groq(messages, timeout=30):
    """Chat with Groq API with better error handling"""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY not found in environment")
            return "API key not configured."
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama3-8b-8192",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        logger.info("Making request to Groq API")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()["choices"][0]["message"]["content"]
            logger.info("Groq API response received successfully")
            return result
        else:
            logger.error(f"Groq API error: {response.status_code} - {response.text}")
            return f"API Error: {response.status_code}"
            
    except requests.exceptions.Timeout:
        logger.error("Groq API request timed out")
        return "Request timed out. Please try again."
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return "I'm having trouble connecting to the AI service. Please try again."

def simple_search(query, max_results=3):
    """Simple DuckDuckGo search with better error handling"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f'https://html.duckduckgo.com/html/?q={query}'
        
        logger.info(f"Searching for: {query}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for i, result in enumerate(soup.find_all('div', class_='result'), start=1):
            if i > max_results:
                break
            title_tag = result.find('a', class_='result_a')
            if not title_tag:
                continue
            link = title_tag['href']
            snippet_tag = result.find('a', class_='result_snippet')
            snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'
            results.append(f"Link {i}: {snippet}")
        
        return "\n".join(results) if results else "No search results found."
    except Exception as e:
        logger.error(f"Search error: {e}")
        return "Search temporarily unavailable."

async def generate_response_stream(prompt: str):
    """Generate streaming response"""
    global assistant_convo
    
    try:
        # Check if Groq API key is available
        if not os.getenv("GROQ_API_KEY"):
            yield f"data: {json.dumps({'content': 'API key not configured. Please contact administrator.'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
            return
        
        logger.info(f"Processing user prompt: {prompt[:50]}...")
        assistant_convo.append({'role': 'user', 'content': prompt})
        
        # Simple search decision (check for question words)
        needs_search = any(word in prompt.lower() for word in ['what', 'how', 'when', 'where', 'who', 'latest', 'current', 'today', 'news'])
        
        if needs_search:
            logger.info("Performing web search")
            search_results = simple_search(prompt)
            enhanced_prompt = f'SEARCH RESULTS: {search_results}\n\nUSER PROMPT: {prompt}'
            assistant_convo[-1]['content'] = enhanced_prompt
        
        # Get AI response
        response = chat_with_groq(assistant_convo)
        
        # Simulate streaming
        words = response.split(' ')
        complete_response = ''
        
        for word in words:
            complete_response += word + ' '
            yield f"data: {json.dumps({'content': word + ' '})}\n\n"
            await asyncio.sleep(0.03)
        
        assistant_convo.append({'role': 'assistant', 'content': complete_response.strip()})
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        error_msg = f"I encountered an error: {str(e)}. Please try again."
        yield f"data: {json.dumps({'content': error_msg})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page"""
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Template error: {e}")
        return HTMLResponse("<h1>SearchPilot</h1><p>Service starting...</p>")

@app.post("/chat")
async def chat(message: str = Form(...)):
    """Handle chat messages"""
    return StreamingResponse(
        generate_response_stream(message),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    api_configured = bool(os.getenv("GROQ_API_KEY"))
    return {
        "status": "healthy",
        "service": "SearchPilot",
        "api_configured": api_configured,
        "version": "railway-optimized"
    }

@app.post("/clear")
async def clear_conversation():
    """Clear conversation"""
    global assistant_convo
    assistant_convo = [ASSISTANT_MSG]
    return {"status": "cleared"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting SearchPilot on port {port}")
    logger.info(f"Groq API Key configured: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        access_log=True
    )
