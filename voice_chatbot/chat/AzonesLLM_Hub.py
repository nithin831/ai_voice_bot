from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import replicate
from dotenv import load_dotenv
import os
import json
import google.generativeai as genai
from serpapi import GoogleSearch
import datetime
import pytz
load_dotenv()


# Function to initialize the appropriate client and query the model API
def Azones_query_model_api(conversation_histories, input_text, topic, model_name, chatbot_name, prompt):
    chat_history = "\n".join([f"{entry}." for entry in conversation_histories])

    if model_name == "Mistral":
        model = "mistral-large-latest"
        api_key = os.environ["Mistral_api"]
        return query_mistral(model, api_key, chat_history, input_text, topic, chatbot_name, prompt)

    elif model_name == "LLAMA3":
        model = "meta/meta-llama-3-70b-instruct"
        api_key = os.environ["LLAMA3_api"]
        return query_meta_llama(model, api_key, chat_history, input_text, topic, chatbot_name, prompt)
    
    elif model_name == "Gemini":
        return query_gemini(chat_history, input_text, topic, chatbot_name, prompt)
    else:
        raise ValueError(f"Model '{model}' is not supported.")

# Function to query Mistral model API
def query_mistral(model, api_key, chat_history, input_text, topic, chatbot_name, prompt):
    try:
        client = MistralClient(api_key=api_key)
        messages = [ChatMessage(role="user", content=input_text)]
        x = datetime.datetime.now(pytz.utc)
        # Convert UTC time to IST
        ist = x.astimezone(pytz.timezone('Asia/Kolkata'))
        start_time = ist.strftime("%m/%d/%Y, %H:%M")
        
        instruction_message = ChatMessage(
            role="system",
            content=f"Current DateTime in india is '{start_time}'. You are assigned with the name '{chatbot_name}' and respond only when '{chatbot_name}' is called, and mainly do not include '{chatbot_name}' in the response. Provide a concise, thoughtful, and independent response on the question  '{input_text}' in consideration of '{topic}' in a single statement based on the conversation History: \"'{chat_history}'\", correcting the user if wrong, without repeating previous content, and answering only once to the point. When the user is asking for you to stop then just say only one word that is sorry. The user given Prompt is '{prompt}'"
        )
        messages.insert(0, instruction_message)
        chat_response = client.chat(model=model, messages=messages)
        print(messages)
        return chat_response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return "There is an server error, Sorry!!!, Please use other model."


# Function to query Meta LLaMA 3-70B Instruct model API using Replicate
def query_meta_llama(model, api_key, chat_history, input_text, topic, chatbot_name, prompt):
    try:
        os.environ["REPLICATE_API_TOKEN"] = api_key
        # prompt = "\n".join([entry['content'] for entry in chat_history if entry['role'] == 'user']) + f"\nTopic: {topic}\n"
        
        # instruction_message = "Provide a concise, thoughtful, and independent response on the topic '{topic}' in a single statement, correcting the user if wrong, without repeating previous content, and answering only once to the point.Respond only when called, '{chatbot_name}'"
        # prompt = f"{instruction_message}\n{prompt}"
        x = datetime.datetime.now(pytz.utc)
        # Convert UTC time to IST
        ist = x.astimezone(pytz.timezone('Asia/Kolkata'))
        start_time = ist.strftime("%m/%d/%Y, %H:%M")
        prompt = f"Current DateTime in india is '{start_time}'. You are assigned with the name '{chatbot_name}' and respond only when '{chatbot_name}' is called, and mainly do not include '{chatbot_name}' in the response. Provide a concise, thoughtful, and independent response on the question  '{input_text}' in consideration of '{topic}' in a single statement based on the conversation History: \"'{chat_history}'\", correcting the user if wrong, without repeating previous content, and answering only once to the point. When the user is asking for you to stop then just say only one word that is sorry. The user given Prompt is '{prompt}'"
        print(prompt)
        # Query the model and collect the response
        response = ""
        for event in replicate.stream(model, input={"prompt": prompt}):
            response += str(event)

        return response.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return "There is an server error, Sorry!!!, Please use other model."
 

def get_answer_box(query):
    print("parsed query: ", query)
    search = GoogleSearch({
        "q": query, 
        "api_key": os.environ["Serpapi"]
    })
    results = search.get_dict()
    answer_box = results.get("answer_box", {})
    knowledge_graph = results.get("knowledge_graph", {})
    organic_results = results.get("organic_results", [])
    related_questions = results.get("related_questions", [])
    print("related_questions",related_questions)
    top_result = organic_results[0] if organic_results else {}
    related_list = related_questions[0] if related_questions else {}
    if  not results:
        return "No relevant information found."
    return f"Top Result from google are: 1.{related_list.get('list', 'No direct list found')}, 2.{related_list.get('snippet', 'No direct snippet found')}, 3.{top_result.get('snippet', 'No snippet')}, 4.{answer_box.get('snippet', 'No direct snippet found')}, 5.{answer_box.get('answer', 'No direct answer found')}, 6.{knowledge_graph.get('description', 'No description')}"

    # if answer_box:
    #     return f"Answer: {answer_box.get('answer', 'No direct answer found')}"
    
    # if knowledge_graph:
    #     return f"Knowledge Graph: {knowledge_graph.get('title', 'No title')} - {knowledge_graph.get('description', 'No description')}"
    
    
    # return "No relevant information found."


get_answer_box_declaration = {
    'name': "get_answer_box",
    'description': "Get the answer box result for real-time data from a search query",
    'parameters': {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query to search for"
            }
        },
        "required": [
            "query"
        ]
    },
}
 
    
# Function to query Gemini model with real-time data using SerpApi
def query_gemini(chat_history, input_text, topic, chatbot_name, prompt):
    # try:
        genai.configure(api_key=os.environ["Gemini_api"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            input_text,
            tools=[{
                'function_declarations': [get_answer_box_declaration],
            }],
        )
        print("Model response:", response)

        function_call = response.candidates[0].content.parts[0].function_call
        args = function_call.args
        # print(args['query'])
        function_name = function_call.name
        result = "No real-time data retrieved"
        if function_name == 'get_answer_box':
            result = get_answer_box(args['query'])
            
        x = datetime.datetime.now(pytz.utc)
        # Convert UTC time to IST
        ist = x.astimezone(pytz.timezone('Asia/Kolkata'))
        start_time = ist.strftime("%m/%d/%Y, %H:%M")
        data_from_api = json.dumps(result)
        prompt = f"Current DateTime in india is '{start_time}'. You are assigned with the name '{chatbot_name}' and respond only when '{chatbot_name}' is called, and mainly do not include '{chatbot_name}' in the response. Provide a concise, thoughtful, and independent response on the question  '{input_text}' in consideration of '{topic}' in a single statement based on the conversation History: \"'{chat_history}'\" also take the reference of google's answer: '{data_from_api}' if it is not there in conversation History, correcting the user if wrong, without repeating previous content, and answering only once to the point. When the user is asking for you to stop then just say only one word that is sorry. The user given Prompt is '{prompt}' "
        print(prompt)
        response = model.generate_content(
            prompt
        )
        return response.text
    # except Exception as e:
    #     print(f"An error occurred: {e}")
    #     return "There is a server error, Sorry!!!, Please use another model."
