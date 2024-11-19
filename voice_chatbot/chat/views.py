import csv
from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
import json
import regex as re
from chat import AzonesLLM_Hub
import time
from dotenv import load_dotenv
import os
import datetime
import gc
import pytz

load_dotenv()

# Global variable to store chatbot settings
chatbot_settings = {}


# Global dictionary to store recognized texts
recognized_texts = []


def index(request):
    print(chatbot_settings)
    return render(request, 'speech.html')


start_time = None

def chatbot_name(request):
    if request.method == 'POST':
        global chatbot_name
        model_settings = json.loads(request.body)
        print(model_settings)
        chatbot_name = model_settings["chatbot_name"]
        print(chatbot_name)
        return JsonResponse({'status': 'success', 'message': 'Chatbot name got'})
    
def start_recognition(request):
    global chatbot_settings, start_time
    if request.method == 'POST':
        chatbot_settings = json.loads(request.body)
        global chatbot_name, topic, model_name, prompt
        print("Chatbot settings received:", chatbot_settings)
        topic = chatbot_settings["topic"]
        model_name = chatbot_settings["llmModel"]
        prompt = chatbot_settings["prompt"]
        # Set the start time only if it hasn't been set yet
        if start_time is None:
           # Get the current UTC time
            x = datetime.datetime.now(pytz.utc)
            # Convert UTC time to IST
            ist = x.astimezone(pytz.timezone('Asia/Kolkata'))
            start_time = ist.strftime("%m/%d/%Y, %H:%M")
        
        return JsonResponse({'status': 'success', 'message': 'Chatbot settings updated'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



# Function to check for keyword
def contains_keyword(text, keyword):
    return keyword.lower() in text.lower()

def get_speech_api_key(request):
    return JsonResponse({'subscriptionKey': os.environ["subscriptionKey"], 'serviceRegion': os.environ["serviceRegion"]})


def recognize(request):
    global recognized_texts
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data['text']
        if user_input:
           
            recognized_texts.append(f"{user_input.capitalize()}")
            if contains_keyword(user_input, chatbot_name):
                start_time = time.time()  # Start timing

                response = AzonesLLM_Hub.Azones_query_model_api(recognized_texts, user_input, topic, model_name, chatbot_name, prompt)
                end_time = time.time()  # End timing
                response_time = end_time - start_time  # Calculate the duration
                print(f"Response time: {response_time} seconds")  # Print the response time
                # Get the current UTC time
                x = datetime.datetime.now(pytz.utc)
                # Convert UTC time to IST
                ist = x.astimezone(pytz.timezone('Asia/Kolkata'))
                formatted_time = ist.strftime("%m/%d/%Y, %H:%M")
                recognized_texts.append(f"[{formatted_time}]{chatbot_name.capitalize()}: {response.capitalize()}")
                
                return JsonResponse({'status': 'success', 'chatbot_name': chatbot_name.capitalize(), "response": response.capitalize()})
            # return
            print(recognized_texts) 
        return JsonResponse({'status': 'error', 'message': 'No username found in the recognized text'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def end_recognition(request):
    global chatbot_settings, recognized_texts, start_time
    chatbot_settings = {}
    recognized_texts = []
    start_time = None
    gc.collect()
     # Clear the cache
    cache.clear()
    return JsonResponse({'status': 'success', 'message': 'Chatbot settings and recognized texts cleared'})

def download_conversation_history(request):
    global recognized_texts

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="conversation_history.csv"'
    
    writer = csv.writer(response)
    writer.writerow([f"[{start_time}] Conversation Started"])

    for text in recognized_texts:
       
        writer.writerow([text.capitalize()])

    return response