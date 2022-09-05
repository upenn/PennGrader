import sys
import os
import boto3
import json
import ast
import base64


# Dynamo Config
dynamo = boto3.client('dynamodb')
TEST_CASES_TABLE = 'HomeworksTestCases'

# Return Codes
SUCCESS = 200
ERROR   = 400

def lambda_handler(event, context):
    try:
        homework_id = parse_event(event)
        test_case, libraries = get_test_and_libraries(homework_id)

        return build_http_response(SUCCESS, build_response_message(test_case, libraries))
    except Exception as exception:
        return build_http_response(ERROR, exception)
        

def parse_event(event):
    try:
        return event['homework_id']
    except:
        raise Exception('Malformed payload: %s.'%event)


def get_test_and_libraries(homework_id):
    try:
        response = dynamo.get_item(TableName = TEST_CASES_TABLE, Key={'homework_id': {'S': homework_id}})
        return response['Item']['test_cases']['S'], \
               response['Item']['libraries']['S'], 
    except:
        raise Exception('Homework {} was not found.'.format(homework_id))


def build_response_message(test_case, libraries):
    return json.dumps({"tests": test_case, "libs": libraries})


def build_http_response(status_code, message):
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    
    
    
  