import urllib.request
from urllib.error import HTTPError
import json
import dill
import base64
import types
import ast
import yaml
from yaml import Loader, Dumper

# Request types
STUDENT_GRADE_REQUEST = 'STUDENT_GRADE'

class PennGrader:
    
    def __init__(self, config_filename, homework_id, student_id, secret):
        if '_' in str(student_id):
            raise Exception("Student ID cannot contain '_'")

        with open(config_filename) as config_file:
            config = yaml.safe_load(config_file)

            self.grader_api_url = config['grader_api_url']
            self.grader_api_key = config['grader_api_key']

            self.homework_id = homework_id
            self.student_id = str(student_id)
            self.student_secret = str(secret)
            print('PennGrader initialized with Student ID: {}'.format(self.student_id))
            print('\nMake sure this correct or we will not be able to store your grade')

        
    def grade(self, test_case_id, answer):
        request = { 
            'homework_id' : self.homework_id, 
            'student_id' : self.student_id, 
            'secret': self.student_secret,
            'test_case_id' : test_case_id,
            'answer' : self._serialize(answer)
        }
        response = self._send_request(request, self.grader_api_url, self.grader_api_key)
        print(response)

    def _send_request(self, request, api_url, api_key):
        params = json.dumps(request).encode('utf-8')
        headers = {'content-type': 'application/json', 'x-api-key': api_key}
        try:
            response = requests.post(api_url, data=params, headers=headers, timeout=10)
            return response.text
        except requests.exceptions.HTTPError as error:
            raise SystemExit(error)
        except requests.exceptions.Timeout as error:
            raise SystemExit(error)
        
    def _serialize(self, obj):
        byte_serialized = dill.dumps(obj, recurse = True)
        return base64.b64encode(byte_serialized).decode("utf-8")
