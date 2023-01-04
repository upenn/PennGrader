import urllib.request
from urllib.error import HTTPError
import json
import dill
import base64
import types
import ast
<<<<<<< HEAD
import hashlib

# Lambda endpoints
grader_api_url = 'https://wyv616tp17.execute-api.us-east-1.amazonaws.com/default/Grader'
grader_api_key = 'Kd32fl3g3p917iM0zwjiO23Bitj4PO9ga4LektOa'
=======
import yaml
from yaml import Loader, Dumper
>>>>>>> 532f5cf7005d3c33ee0d909b93b90e807e8782db

# Request types
STUDENT_GRADE_REQUEST = 'STUDENT_GRADE'

class PennGrader:
    
<<<<<<< HEAD
    def __init__(self, course_id, homework_id, student_id):
        if '_' in str(student_id):
            raise Exception("Student ID cannot contain '_'")
        self.homework_id = homework_id
        sha_1 = hashlib.sha1()
        key = str('v2' + student_id + course_id).encode('utf-8')
        self.student_id = sha_1.hexdigest()
        print('PennGrader initialized with Student ID: {}'.format(student_id))
        print('\nMake sure this correct or we will not be able to store your grade')
=======
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
>>>>>>> 532f5cf7005d3c33ee0d909b93b90e807e8782db

        
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
        request = urllib.request.Request(api_url, data=params, headers=headers)
        try:
            response = urllib.request.urlopen(request)
            return '{}'.format(response.read().decode('utf-8'))
        except HTTPError as error:
            return 'Error: {}'.format(error.read().decode("utf-8")) 
        
    def _serialize(self, obj):
        byte_serialized = dill.dumps(obj, recurse = True)
        return base64.b64encode(byte_serialized).decode("utf-8")
