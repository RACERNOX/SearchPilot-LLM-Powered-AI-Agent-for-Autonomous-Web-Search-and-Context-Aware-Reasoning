import ollama
import sys_msgs
import requests
from bs4 import BeautifulSoup
import trafilatura

from colorama import init,Fore,Style


init(autoreset=True)

assistant_convo = [sys_msgs.assistant_msg]



def search_or_not():
    sys_msg = sys_msgs.search_or_not_msg  # Access the system message
    
    response = ollama.chat(
        model='llama3.1:8b',  # Fix model name (remove spaces)
        messages=[{'role': 'system', 'content': sys_msg},assistant_convo[-1]]  # Use the last message in the conversation   
    )
    
    content = response [ 'message'] ['content']
    if 'true' in content. lower():
        return True
    else:
        return False

def query_generator():
    sys_msg = sys_msgs.query_msg
    query_msg = f'CREATE A SEARCH QUERY FOR THIS PROMPT: \n{assistant_convo[-1]}'
    response = ollama.chat(
        model='llama3.1:8b',
        messages=[
            {'role': 'system', 'content': sys_msg},
            {'role': 'user', 'content': query_msg}
        ]
    )
    return response['message']['content']



def duckduckgo_search(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = f'https://html.duckduckgo.com/html/?q={query}'
    
    response = requests.get(url, headers=headers)
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


def best_search_results(s_results, query):
    sys_msg = sys_msgs.best_search_msg
    best_msg = f'SEARCH_RESULTS: {s_results} \nUSER_PROMPT: {assistant_convo[-1]} \nSEARCH_QUERY: {query}'
    
    for _ in range(2):  # Retry up to 2 times
        try:
            response = ollama.chat(
                model='llama3.1:8b',
                messages=[
                    {'role': 'system', 'content': sys_msg},
                    {'role': 'user', 'content': best_msg}
                ]
            )
            return int(response['message']['content'])
        except:
            continue  # Retry if an error occurs
    
    return 0  # Default return value if all retries fail


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
    
    response = ollama.chat(
        model='llama3.1:8b',
        messages=[
            {'role': 'system', 'content': sys_msg},
            {'role': 'user', 'content': needed_prompt}
        ]
    )
    
    content = response['message']['content']
    if 'true' in content.lower():
        return True
    else:
        return False




def ai_search():
    context = None
    print(f'{Fore.LIGHTCYAN_EX}GENERATING SEARCH QUERY.{Style.RESET_ALL}')
    search_query = query_generator()
    
    
    if search_query[0] == '"' and search_query[-1] == '"':
        search_query = search_query[1:-1]  # Remove surrounding quotes if present
    
    search_results = duckduckgo_search(search_query)
    context_found = False
    
    while not context_found and len(search_results) > 0:
        best_result = best_search_results(s_results=search_results, query=search_query)
        try:
            page_link = search_results[best_result]['link']
            # Add logic here to fetch and process the page content
            context_found = True  # Set to True if context is successfully found
        except:
            print('FAILED TO SELECT BEST SEARCH RESULT, TRYING AGAIN.')
            continue  # Retry if an error occurs

        page_text =scrape_webpage(page_link)
        search_results.pop(best_result)

        if page_text and contains_data_needed(search_content=page_text, query=search_query):
            context=page_text
            context_found=True
    return context  



def stream_assistant_response():
    global assistant_convo
    response_stream = ollama.chat(model='llama3.1:8b', messages=assistant_convo, stream=True)
    complete_response = ''
    print('ASSISTANT: ')
    for chunk in response_stream:
        print(chunk['message']['content'], end='', flush=True)
        complete_response += chunk['message']['content']
    assistant_convo.append({'role': 'assistant', 'content': complete_response})
    print('\n\n')

def main():
    global assistant_convo

    while True:
        prompt = input('USER: \n')
        assistant_convo.append({'role': 'user', 'content': prompt})
        
        if search_or_not():
            context = ai_search()
            assistant_convo = assistant_convo[:-1]  # Corrected variable name and slicing
    
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
    
            assistant_convo.append({'role':'user','content':prompt})
        stream_assistant_response()


        


if __name__ == '__main__':
    main()



