import boto3
import time

# Dynamo Config
dynamo = boto3.resource('dynamodb')
GRADEBOOK_TABLE  = 'Gradebook'

# Return Codes
SUCCESS = 200
ERROR   = 400

def lambda_handler(event, context):
    try:
        homework_id, student_id, secret, test_case_id, student_score, max_score, message = parse_event(event)
        store_submission(student_score, max_score, homework_id, test_case_id, student_id, secret)
        return build_http_response(SUCCESS, build_response_message(student_score, max_score, message))
    except Exception as exception:
        return build_http_response(ERROR, exception)
        

def parse_event(event):
    try:
        if 'message' in event:
            return event['homework_id'], event['student_id'], event['secret'], event['test_case_id'], event['score'], event['max_score'], event['message']
        else:
            return event['homework_id'], event['student_id'], event['secret'], event['test_case_id'], event['score'], event['max_score'], ''
    except:
        raise Exception('Malformed payload.')


def store_submission(student_score, max_score, homework_id, test_case_id, student_id, secret):
    table = dynamo.Table(GRADEBOOK_TABLE)
    old_version = table.get_item(Key={
            'homework_id': homework_id,
            'student_submission_id': student_id + '_' + test_case_id
    })
    print (old_version)
    if 'Item' in old_version and 'secret' in old_version['Item'] and old_version['Item']['secret'] != secret:
        raise Exception('Yikes! A submission was made to this question using a different secret.  Did you correctly enter your secret code?')
    elif 'Item' in old_version and 'secret' in old_version['Item']:
        print ("Verified %s"%(old_version['Item']['secret']))
    try:
        result = table.put_item(Item={
            'homework_id': homework_id,
            'student_submission_id': student_id + '_' + test_case_id,
            'student_score': str(student_score),
            'max_score': str(max_score),
            'timestamp': str(time.strftime('%Y-%m-%d %H:%M')),
            'secret': secret
        })
        if result['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception("Could not write to storage")
    except Exception as exception:
        error_message = 'Uhh no! We could not record your answer in the gradebook for some reason :(\n' + \
                        'It is not your fault, please try again or ask a TA. '
        raise Exception(error_message)


def build_response_message(student_score, max_score, message):
    if student_score == max_score:
        return 'Correct! You earned {}/{} points. You are a star!\n\n'.format(student_score, max_score) + \
               'Your submission has been successfully recorded in the gradebook.'
    else:
        return 'You earned {}/{} points.  {}\n\n'.format(student_score, max_score, message) + \
               'But, don\'t worry you can re-submit and we will keep only your latest score.'


def build_http_response(status_code, message):
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }