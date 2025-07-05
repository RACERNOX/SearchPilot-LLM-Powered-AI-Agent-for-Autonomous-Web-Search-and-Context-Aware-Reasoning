from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import asyncio
import json
import openai
import os
import sys_msgs
import requests
from bs4 import BeautifulSoup
import trafilatura
from typing import Optional
import uvicorn

app = FastAPI(title="SearchPilot", description="AI Search Agent with Web Interface")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Global conversation state
assistant_convo = [sys_msgs.assistant_msg]

def chat_with_openai(messages, stream=False):
    """Chat with OpenAI API"""
    try:
        if stream:
            return openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True,
                temperature=0.7
            )
        else:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        if stream:
            return []
        return "I'm having trouble connecting to the AI service. Please try again."

def search_or_not():
    sys_msg = sys_msgs.search_or_not_msg
    
    content = chat_with_openai([
        {'role': 'system', 'content': sys_msg},
        assistant_convo[-1]
    ])
    
    if 'true' in content.lower():
        return True
    else:
        return False

def query_generator():
    sys_msg = sys_msgs.query_msg
    query_msg = f'CREATE A SEARCH QUERY FOR THIS PROMPT: \n{assistant_convo[-1]}'
    
    return chat_with_openai([
        {'role': 'system', 'content': sys_msg},
        {'role': 'user', 'content': query_msg}
    ])

def duckduckgo_search(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = f'https://html.duckduckgo.com/html/?q={query}'
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for i, result in enumerate(soup.find_all('div', class_='result'), start=1):
            if i > 10:
                break
            title_tag = result.find('a', class_='result_a')
            if not title_tag:
                continue
            link = title_tag['href']
            snippet_tag = result.find('a', class_='result_snippet')
            snippet = snippet_tag.text.strip() if snippet_tag else 'No description available'
            results.append({
                'id': i,
                'link': link,
                'search_description': snippet
            })
        
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []

def best_search_results(s_results, query):
    sys_msg = sys_msgs.best_search_msg
    best_msg = f'SEARCH_RESULTS: {s_results} \nUSER_PROMPT: {assistant_convo[-1]} \nSEARCH_QUERY: {query}'
    
    for _ in range(2):
        try:
            content = chat_with_openai([
                {'role': 'system', 'content': sys_msg},
                {'role': 'user', 'content': best_msg}
            ])
            return int(content)
        except:
            continue
    
    return 0

def scrape_webpage(url):
    try:
        downloaded = trafilatura.fetch_url(url=url)
        return trafilatura.extract(downloaded, include_formatting=True, include_links=True)
    except Exception as e:
        print(f"Error scraping webpage: {e}")
        return None

def contains_data_needed(search_content, query):
    sys_msg = sys_msgs.contains_data_msg
    needed_prompt = f'PAGE_TEXT: {search_content} \nUSER_PROMPT: {assistant_convo[-1]} \nSEARCH_QUERY: {query}'
    
    content = chat_with_openai([
        {'role': 'system', 'content': sys_msg},
        {'role': 'user', 'content': needed_prompt}
    ])
    
    if 'true' in content.lower():
        return True
    else:
        return False

def ai_search():
    context = None
    search_query = query_generator()
    
    if search_query and len(search_query) > 2:
        if search_query[0] == '"' and search_query[-1] == '"':
            search_query = search_query[1:-1]
        
        search_results = duckduckgo_search(search_query)
        context_found = False
        
        while not context_found and len(search_results) > 0:
            best_result = best_search_results(s_results=search_results, query=search_query)
            try:
                page_link = search_results[best_result]['link']
                context_found = True
            except:
                if search_results:
                    search_results.pop(0)
                continue

            page_text = scrape_webpage(page_link)
            if search_results and best_result < len(search_results):
                search_results.pop(best_result)

            if page_text and contains_data_needed(search_content=page_text, query=search_query):
                context = page_text
                context_found = True
    return context

async def generate_response_stream(prompt: str):
    """Generate streaming response from the AI assistant"""
    global assistant_convo
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        yield f"data: {json.dumps({'content': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        return
    
    assistant_convo.append({'role': 'user', 'content': prompt})
    
    # Check if search is needed
    try:
        needs_search = search_or_not()
    except:
        needs_search = False
    
    if needs_search:
        # Perform search
        try:
            context = ai_search()
            assistant_convo = assistant_convo[:-1]
            
            if context:
                prompt = f'SEARCH RESULT: {context} \n\nUSER PROMPT: {prompt}'
            else:
                prompt = (
                    f'USER PROMPT: \n{prompt} \n\nFAILED SEARCH: \nThe '
                    'AI search model was unable to extract any reliable data. Explain that '
                    'and ask if the user would like you to search again or respond '
                    'without web search context. Do not respond if a search was needed '
                    'and you are getting this message with anything but the above request '
                    'of how the user would like to proceed.'
                )
        except Exception as e:
            print(f"Search error: {e}")
            context = None
        
        assistant_convo.append({'role': 'user', 'content': prompt})
    
    # Stream response
    try:
        response_stream = chat_with_openai(assistant_convo, stream=True)
        complete_response = ''
        
        for chunk in response_stream:
            if chunk.choices[0].delta.get('content'):
                content = chunk.choices[0].delta.content
                complete_response += content
                yield f"data: {json.dumps({'content': content})}\n\n"
        
        # Add complete response to conversation
        assistant_convo.append({'role': 'assistant', 'content': complete_response})
        yield f"data: {json.dumps({'done': True})}\n\n"
        
    except Exception as e:
        error_msg = f"I encountered an error: {str(e)}. Please try again."
        yield f"data: {json.dumps({'content': error_msg})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(message: str = Form(...)):
    """Handle chat messages with streaming response"""
    return StreamingResponse(
        generate_response_stream(message),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.get("/conversation")
async def get_conversation():
    """Get the current conversation history"""
    # Filter out system messages for display
    display_convo = [msg for msg in assistant_convo if msg['role'] != 'system']
    return {"conversation": display_convo}

@app.post("/clear")
async def clear_conversation():
    """Clear the conversation history"""
    global assistant_convo
    assistant_convo = [sys_msgs.assistant_msg]
    return {"status": "cleared"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SearchPilot"}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
