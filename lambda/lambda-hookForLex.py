import time
import logging
import os
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
runtime = boto3.client('sagemaker-runtime')


## Updated model
ENDPOINT_NAME = 'huggingface-pytorch-inference-2025-07-20-06-59-49-558'

silence_count=-1

def silence_analyzer(intent_request):
    global silence_count
    input_transcript = intent_request.get("inputTranscript", "").strip()
    print(f"input_transcript: {input_transcript}")

    print("checking for silence")
    if input_transcript:
        print("Inside if")
        silence_count = -1
    else:
        print("Inside else")
        silence_count += 1

    return silence_count

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
   
    session_attributes = event.get('sessionState',{}).get('sessionAttributes',{})

    print("session attributes: ", session_attributes)
    silence = silence_analyzer(event)
    print("silence count: ", silence)
    session_attributes['silence_counter'] = silence
    print("session attributes: ", session_attributes)

    last_intent_used = session_attributes.get("routedIntent","")
    print("last intent used: ", last_intent_used)
    if silence == 1:
        print ("No input twice")
        session_attributes['routedIntent'] = "connect_to_agent"
        return {
            'sessionState': {
                'sessionAttributes': session_attributes,
                'dialogAction': {
                    'type': 'Close'
                },
                'intent': {
                    'name': 'FallbackIntent',
                    'state': 'Fulfilled'
                }
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': "I'm sorry, but I didn't hear a response. Let me transfer you to an agent."
                }
            ]
        }    
    elif silence >= 0:
        print("last tool used 2: ", last_intent_used)
        session_attributes['routedIntent'] = "fallback"
        return {
            'sessionState': {
                'sessionAttributes': session_attributes,
                'dialogAction': {
                    'type': 'ElicitIntent'
                },
                'state': 'Fulfilled',
            },
            'messages': [
                {
                    'contentType': 'PlainText',
                    'content': "Hi! I can help you with Algoworks services, pricing, contact info, or even take a message. What would you like to know?"
                }
            ]
        }



    utterance = event.get('inputTranscript',{})  
    payload = json.dumps({"text": utterance})
    print(payload)
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType='application/json',
        Body=payload
    )

    # print(response)
    prediction = response['Body'].read().decode('utf-8').strip()
    prediction_json = json.loads(prediction)
    label = prediction_json.get("label")
    score = prediction_json.get("score")
    print(f"Routed Intent, {label}")
    # return {'intent': label, 'score': score}
    session_attributes['routedIntent'] = label
    next_state = {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': { 
                'name': 'FallbackIntent',
                'state': 'Fulfilled'
            },
            'sessionAttributes': session_attributes
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': f'Intent identified as {label}'
                # 'content': f'Intent identified as {label}, with score  {score:.2f}'
            }
        ]
    }
    return next_state
