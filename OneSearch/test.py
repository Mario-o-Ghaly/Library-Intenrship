import requests
import google.generativeai as genai
import os

api_key = "AIzaSyCHp33Vzn6f8P7DqRPHzPk1KCiEH5f7Txk"
genai.configure(api_key=api_key)
nlp_model = genai.GenerativeModel('gemini-1.5-flash')
query = "political debate"
prompt = f"""This is a search query for a book. Without any additional words in the answer, extract the title, author, date and type(e.g., book, journal, thesis)
          from the following query: '{query}'. Return the parameters in this format: Title: title, and so on separated by a new line.
          if you cannot extract a parameter of them, just write NA. However, there has to be a title(it might be the only thing there).
          If there are typos, fix them, and if there are words that are not words, remove them."""
nlp_response = nlp_model.generate_content(prompt).text
nlp_params = nlp_response.split('\n')
title = nlp_params[0].split('Title: ')[1]
author = nlp_params[1].split('Author: ')[1]
date = nlp_params[2].split('Date: ')[1]
type = nlp_params[3].split('Type: ')[1]

url = "https://openlibrary.org/search.json"
    
params = {}
if title != "NA":
    params["title"] = title
if author != "NA":
    params["author"] = author
if date != "NA":
    params["first_publish_year"] = date

response = requests.get(url, params=params)
data = response.json()

# Prepare context data to pass to the template
books = []
if data.get('docs'):
  for book in data['docs'][:10]:  # Limiting to the first 5 results
    books.append({
    'title': book.get('title'),
    'author': book.get('author_name', ['Unknown'])[0],
    'first_publish_year': book.get('first_publish_year', 'Unknown')
    })
print(books)
# print(title, author, date, type)
