import os
from newsapi import NewsApiClient
import requests
from time import sleep

KEYWORDS_LIST = os.getenv("KEYWORDS_LIST").split(",")
LOGSTASH_URL = "http://logstash:9700"



newsapi = NewsApiClient(api_key='1364dd175f8d4b75aa0f85023fbba58b')

for keyword in KEYWORDS_LIST:

    messageCount = 0
    all_articles = newsapi.get_everything(q=keyword,
                                      language='it',
                                      sort_by='publishedAt')
    
    for article in all_articles['articles']:
        data = {
            'publishedAt':article['publishedAt'],
            'author':article['author'],
            'title':article['title'],
            'description':article['description'],
            'content':article['content'],
            'url':article['url']
        }
        
        try:
            response = requests.post(LOGSTASH_URL, json=data)
            if response.status_code == 200:
                messageCount+= 1
            else:
                print("Failed to send data to Logstash. Status code:", response.status_code)
        except Exception as e:
            print("An error occurred while sending data to Logstash:", str(e))

    print("Sent "+  str(messageCount) + " messages to Logstash by keyword " + keyword)      
    sleep(5)

