from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.decorators import api_view
import whisper
import os
import tempfile
import subprocess
from django.http import JsonResponse
import base64
import hmac
import hashlib
import requests
from datetime import datetime
import json
import urllib
from urllib.parse import urlencode
import google.generativeai as genai
import sys
from concurrent.futures import ThreadPoolExecutor
import time
import random


model = whisper.load_model("small")
api_key = "AIzaSyCHp33Vzn6f8P7DqRPHzPk1KCiEH5f7Txk"
# api_key = "AIzaSyDGF_Hn0aWHyiGAooe_ytQUyaou_0N-HmE"
genai.configure(api_key=api_key)
nlp_model = genai.GenerativeModel('gemini-1.5-flash')

# Create your views here.
def home(request):
    return render(request, "home.html")

def test(request):
    return render(request, 'test.html')

def test_sound(request):
    return render(request, 'transcribe.html')

@api_view(['POST'])
def transcribe_audio(request):
    if request.method == 'POST':
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return JsonResponse({'error': 'No audio file provided'}, status=400)

        # Save the file to a known location for debugging
        save_path = os.path.join(tempfile.gettempdir(), audio_file.name)
        with open(save_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
        

        # Transcribe the audio using Whisper
            # result = model.transcribe(save_path, language = "en")
        try:
            result = model.transcribe(save_path, language = "en")
            transcription = result['text']
        except Exception as e:
            return JsonResponse({'error': 'Transcription failed', 'details': str(e)}, status=500)

        # Clean up the temporary file
        os.remove(save_path)
        
        return JsonResponse({'transcription': transcription})
    
def NLP(query):
    prompt = f"""You are part of a library information system that process search queries. 
          Without any additional words in the answer, extract the title, author, date and type(e.g., book, journal, thesis)
          from the following query based on your understanding and knoweldge: '{query}'. Return the parameters in this format: Title: title, and so on separated by a new line.
          if you cannot extract a parameter of them, just write NA. However, there has to be a title(it might be the only thing there).
          If there are typos, fix them, and if there are words that are not words, remove them. If you know the date is in the title, include it in the title not the date.
          PLEASE FOLLOW THE EXAMPLE BELOW CAREFULLY!
          Example: "2014 politica debaate"
          Title: political debate
          Author: NA
          Date: 2014
          Type: NA 
          """
    nlp_response = nlp_model.generate_content(prompt).text
    nlp_params = nlp_response.split('\n')
    title = nlp_params[0].split('Title: ')[1]
    author = nlp_params[1].split('Author: ')[1]
    date = nlp_params[2].split('Date: ')[1]
    type = nlp_params[3].split('Type: ')[1]
    print(title, author, date, type)

    params = {}
    if title != "NA":
        params["title"] = title
    if author != "NA":
        params["author"] = author
    if date != "NA":
        params["first_publish_year"] = date

    return params
    
# def search(request):
#     query = request.GET.get('query', '')
#     print(query)
#     maxx = 0
#     ans = []
#     for _ in range(5):
#         params = NLP(query)
#         url = "https://openlibrary.org/search.json"
#         response = requests.get(url, params=params)
#         data = response.json()
#         if(data.get('num_found', 0) == 0):
#             print("NOT WORKING CURRENTLY")
#         print(data.get('num_found', 0))

#         # Prepare context data to pass to the template
#         books = []
#         if data.get('docs'):
#             for book in data['docs'][:10]:  # Limiting to the first 5 results
#                 books.append({
#                     'title': book.get('title'),
#                     'author': book.get('author_name', ['Unknown'])[0],
#                     'first_publish_year': book.get('first_publish_year', 'Unknown')
#                 })
        
#         if(data.get('num_found', 0) > maxx):
#             ans = books

#     context = {'books': ans}
#     return render(request, 'result.html', context)

def search(request):
    query = request.GET.get('query', '')
    print(query)
    maxx = 0
    ans = []

    # Define a function to process each search call
    def process_search():
        params = NLP(query)
        url = "https://openlibrary.org/search.json"
        max_retries = 5
        retry_delay = 1  # Start with 1 second

        for i in range(max_retries):
            try:
                response = requests.get(url, params=params)
                if response.status_code == 429:
                    # Too many requests, backoff
                    retry_delay = min(60, retry_delay * 2)  # Limit the max delay
                    print(f"Rate limit hit, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay + random.random())  # Add jitter for more randomness
                    continue
                elif response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                data = response.json()
                break  # Exit loop if successful
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {str(e)}")
                return 0, []

        # Process data
        if data.get('num_found', 0) == 0:
            print("NOT WORKING CURRENTLY")
        else:
            print(data.get('num_found', 0))

        books = []
        if data.get('docs'):
            for book in data['docs'][:10]:
                books.append({
                    'title': book.get('title'),
                    'author': book.get('author_name', ['Unknown'])[0],
                    'first_publish_year': book.get('first_publish_year', 'Unknown')
                })
        return data.get('num_found', 0), books
    # def process_search():
    #     params = NLP(query)
    #     url = "https://openlibrary.org/search.json"
    #     response = requests.get(url, params=params)
    #     data = response.json()
        
    #     if data.get('num_found', 0) == 0:
    #         print("NOT WORKING CURRENTLY")
    #     else: print(data.get('num_found', 0))
        
    #     books = []
    #     if data.get('docs'):
    #         for book in data['docs'][:10]:  # Limiting to the first 10 results
    #             books.append({
    #                 'title': book.get('title'),
    #                 'author': book.get('author_name', ['Unknown'])[0],
    #                 'first_publish_year': book.get('first_publish_year', 'Unknown')
    #             })
    #     return data.get('num_found', 0), books

    # Use ThreadPoolExecutor to run the API calls concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_search) for _ in range(5)]
    
    # Collect the results
    for future in futures:
        num_found, books = future.result()
        if num_found > maxx:
            maxx = num_found
            ans = books

    context = {'books': ans}
    return render(request, 'result.html', context)



def response_view(request):
    json_response = request.session.get('json_response', '{}')
    context = {
        'json_response': json_response
    }
    return render(request, 'response.html', context)