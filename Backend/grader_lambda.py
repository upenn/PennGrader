import sys
sys.path.append('/opt/')
sys.path.append('/opt/python/')
sys.path.append('/opt/python/python38/')

import json
import dill
import ast
import base64
import urllib.request
from urllib.error import HTTPError

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

tests_api_url = 'https://kgskaaymdk.execute-api.us-east-1.amazonaws.com/default/gettestcase'
tests_api_key = 'ogZFqWDoWe3G0yhkZOIFtaA00KEaL1jK3wLZlz90'
records_api_url = 'https://xijh7o9657.execute-api.us-east-1.amazonaws.com/default/savestudent'
records_api_key = 'ogZFqWDoWe3G0yhkZOIFtaA00KEaL1jK3wLZlz90'


# Return Codes
SUCCESS = 200
ERROR   = 400

def lambda_handler(event, context):
    try:
        homework_id, student_id, test_case_id, secret, answer = parse_event(event)
        test_case, libraries = get_test_and_libraries(homework_id, test_case_id)
        import_libraries(libraries)
        student_score, max_score = grade(test_case, answer)
        store_submission(student_score, max_score, homework_id, test_case_id, student_id, secret)
        return build_http_response(SUCCESS, build_response_message(student_score, max_score))
    except Exception as exception:
        return build_http_response(ERROR, exception)
        

def parse_event(event):
    try:
        body = ast.literal_eval(event['body'])
        print(body)
        if 'secret' in body:
            return body['homework_id'],  \
                body['student_id'], \
                body['test_case_id'],  \
                body['secret'], \
                deserialize(body['answer']) 
        else:
            return body['homework_id'],  \
                body['student_id'], \
                body['test_case_id'],  \
                body['student_id'], \
                deserialize(body['answer']) 
    except:
        raise Exception('Unable to parse data.')


# Isolated from this container for security        
def get_test_and_libraries(homework_id, test_case_id):
    try:
        res = json.loads(send_request({'homework_id': homework_id}, tests_api_url, tests_api_key))
        print(str(res))
        if res['statusCode'] != 200:
            raise Exception("Unable to retrieve results")

        body = json.loads(res['body'])
        return deserialize(body['tests'])[test_case_id], deserialize(body['libs'])
    except:
        raise Exception('Test case {} was not found.'.format(test_case_id))


def import_libraries(libraries):
    print('Importing libraries...')
    print(libraries)
    try:
        packages = libraries['packages']
        imports = libraries['imports']
        functions = libraries['functions']
        
        for package in packages: 
            if package not in globals() and 'penngrader' not in package and 'pandas' not in package and 'lxml' not in package:
                print('Import * from ' + str(package))
                globals()[package] = __import__(package)
                if hasattr(globals()[package], "__all__"): 
                    globals().update((name, getattr(globals()[package], name)) for name in globals()[package].__all__
                                      if name not in globals())
                else:                                 
                    globals().update((name, getattr(globals()[package], name)) for name in dir(globals()[package]) 
                                      if not (name.startswith("_") or name in globals()))
                print('printing packages for ' + package)
                print(list(globals().items()))
    
    
        for package, shortname in imports:
            if shortname not in globals() and 'penngrader' not in package and 'pandas' not in package and 'lxml' not in package:
                print('Importing: ' + package + ' as ' + shortname)
                globals()[shortname] = __import__(package, globals(), locals(), ['*'])
    
        
        for package, function_name in functions:
            print('Importing function: ' + function_name + ' from ' + package)
            globals()[function_name] = eval(package + "." + function_name)
          
    
        
        print('printing packages final')
        print(list(globals().items()))
    except Exception as exception:
        error_message = '[{}] is not currently supported. '.format(str(exception).split("'")[1])
        error_message += 'Let a TA know you got this error.'
        raise Exception(error_message)


def grade(test_case, answer):
    try:
        from types import FunctionType
        test_case_fun = FunctionType(compile(test_case, "<tuple>", "exec").co_consts[0], globals(), test_case) 
        return test_case_fun(answer) 
    except Exception as exception:
        error_message = 'Test case failed. Test case function could not complete due to an error in your answer.\n'
        error_message += 'Error Hint: {}'.format(exception)
        raise Exception(error_message)
        

# Isolated from this container for security        
def store_submission(student_score, max_score, homework_id, test_case_id, student_id, secret):
    try:
        result = json.loads(send_request({
            "homework_id": homework_id,
            "student_id": student_id,
            "test_case_id": test_case_id,
            "secret": secret,
            "score": student_score,
            "max_score": max_score}, records_api_url, records_api_key))

        print(str(result))
        if result['statusCode'] != 200:
            raise Exception("Could not write to storage")        
    except Exception as exception:
        error_message = 'Uhh no! We could not record your answer in the gradebook for some reason :(\n' + \
                        'It is not your fault, please try again or ask a TA.'
        raise Exception(error_message)


def serialize(obj):
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8") 
    

def deserialize(obj):
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)
    
    
def build_response_message(student_score, max_score):
    if student_score == max_score:
        return 'Correct! You earned {}/{} points. You are a star!\n\n'.format(student_score, max_score) + \
               'Your submission has been successfully recorded in the gradebook.'
    else:
        return 'You earned {}/{} points.\n\n'.format(student_score, max_score) + \
               'But, don\'t worry you can re-submit and we will keep only your latest score.'


def build_http_response(status_code, message):
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
    
def send_request(request, api_url, api_key):
    params = json.dumps(request).encode('utf-8')
    headers = {'content-type': 'application/json', 'x-api-key': api_key}
    request = urllib.request.Request(api_url, data=params, headers=headers)
    try:
        response = urllib.request.urlopen(request)
        return '{}'.format(response.read().decode('utf-8'))
    except HTTPError as error:
        return 'Error: {}'.format(error.read().decode("utf-8")) 
        
