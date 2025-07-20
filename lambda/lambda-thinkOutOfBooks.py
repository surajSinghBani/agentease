import time
import logging
import os
import boto3
import json

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=boto3.Session().region_name
)

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    
    os.environ['TZ'] = 'Asia/Kolkata'
    time.tzset()
    
    print("this is event",event)
    # print("this is context",context)


    utterance = event.get('inputTranscript',{})  
    messages = [{"role": "user", "content": [{"text":utterance}]}]

    nova_response = bedrock.converse(
        modelId="us.amazon.nova-pro-v1:0",
        messages=messages,
        system=[{"text":"You are a friendly, emotionally aware AI assistant for Dell support. Answer briefly, clearly, helpfully, and politely. Show empathy where needed."}],
        inferenceConfig={
            "maxTokens": 512,
            "temperature": 0.5,
        }
    )
    response = nova_response['output']['message']['content'][0]['text']
    
    return response

