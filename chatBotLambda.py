import json
import boto3
import random

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

modelId = 'cohere.command-text-v14'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ChatHistory')

def lambda_handler(event, context):
    print('Event: ', event)
    
    requestBody = event['body']
    requestBodyElements = requestBody.split('&')
    user_name = requestBodyElements[0][5:]
    user_response = requestBodyElements[1][9:]
    session_id = f'{user_name}_sessionID'

    if (len(user_name) == 0):
        return {
            'statusCode': 200,
            'body': json.dumps({
                'ERROR': 'Please provied a name to begin' 
            })
        } 

    response_dynamo = table.query(
        KeyConditionExpression = boto3.dynamodb.conditions.Key('SessionID').eq(session_id),
        ScanIndexForward = True  # Ensure messages are in order
    )
    history = response_dynamo.get('Items', [])

    operation = 'generating' if len(history) == 0 else 'responding'

    if operation == 'responding':
        prompt = f'Given the following proposition: {history[0]['AssistResponse']}. And Given the following line of reasoning: {user_response}. How good is the line of reasoning in proving the proposition? Also, end by giving me a score out of 10 on how strong my reasoning is. be VERY CRITICAL in your response and score.'
        body = {
            'prompt': prompt,
            'max_tokens': 1000,
            'temperature': 0.75,
            'p': 0.01,
            'k': 0,
            'stop_sequences': [],
            'return_likelihoods': 'NONE'
        }

        bedrockResponse = bedrock.invoke_model(modelId=modelId,
                                        body=json.dumps(body),
                                        accept='*/*',
                                        contentType='application/json')
        response = json.loads(bedrockResponse['body'].read())['generations'][0]['text']

        response_dynamo_del = table.delete_item(
            Key = {
                'SessionID': session_id,
                'Timestamp': 't'
            }
        )

        debugResponse = {
            'statusCode': 200,
            'body': json.dumps({
                'operation': operation,
                'prompt': user_response,
                'response': response,
                'history': history,
                'assistresponse': history[0]['AssistResponse']
            })
        }

        mainResponse = {
            'statusCode': 200,
            'body': json.dumps({
                'operation': operation,
                'response': response
            })
        }

        print(f'assistant: {response}\n{user_name}: {user_response}')

        return mainResponse
    if operation == 'generating':
        prompt = f'{random.randint(1,1000)}as youre an ai, heres a random numebr {random.randint(1,100)} to try and randomize your output {random.randint(1,900000000000000000000000000000)}. in philosophy there is a concept of logic and reasoning. {random.randint(1,100)}a central part of logic and reasoning, is being able to prove statements {random.randint(1,100)} as valid via a line of reasoning. {random.randint(1,100)}give me a random statement {random.randint(1,100)} that i will try to prove via a line of reasoning. make the statment about general knowledge that all people could reasonably prove or disprove. respond with ONLY ONE SENTENCE. I REPEAT REPONSED WITH ONLY ONE SENTENCE and make sure that sentence is only the statement that you think of and nothing else. again, make your response with ONLY THE ONE SENTENCE. if your response is more than 1 setence, it is a bad response.'
        body = {
            'prompt': prompt,
            'max_tokens': 1000,
            'temperature': 0.75,
            'p': 0.01,
            'k': 0,
            'stop_sequences': [],
            'return_likelihoods': 'NONE'
        }

        bedrockResponse = bedrock.invoke_model(modelId=modelId,
                                        body=json.dumps(body),
                                        accept='*/*',
                                        contentType='application/json')
        response = json.loads(bedrockResponse['body'].read())['generations'][0]['text']

        table.put_item(Item={
            'SessionID': session_id,
            'Timestamp': 't',
            'AssistResponse': response 
        })

        debugResponse = {
            'statusCode': 200,
            'body': json.dumps({
                'operation': operation,
                'prompt': prompt,
                'response': response
            })
        }

        mainResponse = {
            'statusCode': 200,
            'body': json.dumps({
                'operation': operation,
                'response': response
            })
        }

        print(f'assistant: {response}\n{user_name}: {user_response}')

        return mainResponse


    return {
        'statusCode': 200,
        'body': json.dumps({
            'session id': session_id,
            'username': user_name,
            'user response': user_response,
            'history': history
        })
    }