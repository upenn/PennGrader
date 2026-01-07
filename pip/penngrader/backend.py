import json
import dill
import base64
import types
import ast
import types
import urllib.request
import pandas as pd
import numpy as np
from datetime import datetime
import inspect
from difflib import SequenceMatcher

from urllib.error import HTTPError
import yaml
from yaml import Loader, Dumper

# Request types
HOMEWORK_ID_REQUEST     = 'GET_HOMEWORK_ID'
UPDATE_METADATA_REQUEST = 'UPDATE_METADATA'
UPDATE_TESTS_REQUEST    = 'UPDATE_TESTS'
GRADES_REQUEST          = 'ALL_STUDENTS_GRADES'

def is_function(val):
    return inspect.isfunction(val)

def is_module(val):
    return inspect.ismodule(val)

def is_class(val):
    return inspect.isclass(val)

def is_external(name):
    return name not in ['__builtin__','__builtins__', 'penngrader','_sh', '__main__'] and 'penngrader' not in name


class PennGraderBackend:
    
    def __init__(self, config_filename, homework_number):
        with open(config_filename) as config_file:
            config = yaml.safe_load(config_file)

            self.config_api_url = config['config_api_url']
            self.config_api_key = config['config_api_key']
            self.grades_api_url = config['grades_api_url']
            self.grades_api_key = config['grades_api_key']
            self.course_name = config['course_id']
            self.token_generator_url = config['token_generator_url']
            self.token_generator_api_key = config.get('token_generator_api_key')

            self.secret_key      = config['secret_id']

            self.homework_number = homework_number
            print('Fetching homework number...')
            self.homework_id = self._get_homework_id()
            if 'Error' not in self.homework_id:
                response  = 'Success! Teacher backend initialized.\n\n'
                response += 'Homework ID: {}'.format(self.homework_id)
                print(response)
            else:
                raise RuntimeError("Error retrieving {}".format(self.homework_id))
            
    def update_metadata(self, deadline, total_score, max_daily_submissions):
        request = { 
            'homework_number' : self.homework_number, 
            'secret_key' : self.secret_key, 
            'request_type' : UPDATE_METADATA_REQUEST,
            'payload' : self._serialize({
                'max_daily_submissions' : max_daily_submissions,
                'total_score' : total_score,
                'deadline' : deadline
            })
        }
        result = self._send_request(request, self.config_api_url, self.config_api_key)
        if result is not None:
            result = json.loads(result)
            if result.get('statusCode') == 200:
                print('Metadata updated successfully.')
            else:
                print('Error updating metadata: {}'.format(result['body']))
        else:
            print('Error updating metadata: No response from server.')
    
    def _get_tokens(self, test_case_id, student_id, student_secret):
        """Request tokens from token_generator for grading this test case."""
        token_request = {
            'student_id': student_id,
            'student_secret': student_secret,
            'test_case': test_case_id,
            'course_name': self.course_name
        }
        params = json.dumps(token_request).encode('utf-8')
        headers = {'content-type': 'application/json'}
        if self.token_generator_api_key:
            headers['x-api-key'] = self.token_generator_api_key
            
        try:
            response = urllib.request.urlopen(
                urllib.request.Request(self.token_generator_url, data=params, headers=headers)
            )
            tokens = json.loads(response.read().decode('utf-8'))
            
            if tokens.get('statusCode') != 200:
                raise SystemExit('Token generation error: {}'.format(tokens.get('body')))
            
            return json.loads(tokens['body'])
        except HTTPError as error:
            raise SystemExit('Token generation error: {}'.format(error.read().decode('utf-8')))
            
    def update_test_cases(self, global_items):
        request = { 
            'homework_number' : self.homework_number, 
            'secret_key' : self.secret_key, 
            'request_type' : UPDATE_TESTS_REQUEST,
            'payload' : self._serialize({
                'libraries'  : self._get_imported_libraries(),
                'test_cases' : self._get_test_cases(global_items),
            })
        }
        result = self._send_request(request, self.config_api_url, self.config_api_key)
        if result is not None:
            result = json.loads(result)
            if result.get('statusCode') == 200:
                print(f'{result["body"]}.')
            else:
                print('Error updating test cases: {}'.format(result['body']))
        else:
            print('Error updating test cases: No response from server.')
    
    def _get_homework_id(self):
        request = { 
            'homework_number' : self.homework_number,
            'secret_key' : self.secret_key,
            'request_type' : HOMEWORK_ID_REQUEST,
            'payload' : self._serialize(None)
        }
        resp = json.loads(self._send_request(request, self.config_api_url, self.config_api_key))
        
        if resp.get('statusCode') == 200:
            return resp.get('body')
        else:
            return 'Error fetching homework ID: {}'.format(resp.get('body'))

        
    def _send_request(self, request, api_url, api_key):
        params = json.dumps(request).encode('utf-8')
        headers = {'content-type': 'application/json', 'x-api-key': api_key}
        try:
          request = urllib.request.Request(api_url, data=params, headers=headers)
        except err:
          return 'Request builder error: {}'.format(err.read().decode("utf-8")) 
        try:
            response = urllib.request.urlopen(request)
            return '{}'.format(response.read().decode('utf-8'))
        except HTTPError as error:
            return 'Http Error: {}'.format(error.read().decode("utf-8")) 
        
    
    def _get_imported_libraries(self):
        # Get all externally imported base packages
        packages = set() # (package, shortname)
        for shortname, val in list(globals().items()):
            if is_module(val) and is_external(shortname):
                base_package = val.__name__.split('.')[0]
                if base_package != 'google' and base_package != 'yaml':
                  packages.add(base_package)
            if (is_function(val) or is_class(val)) and is_external(val.__module__):
                base_package = val.__module__.split('.')[0]
                packages.add(base_package)
        print ('Importing packages ', packages)

        # Get all sub-imports i.e import sklearn.svm etc 
        imports = set() # (module path , shortname )
        for shortname, val in list(globals().items()):
            if is_module(val) and is_external(shortname):
                if val.__name__ in packages:
                    packages.remove(val.__name__)
                if shortname != 'drive' and shortname != 'yaml':
                  imports.add((val.__name__, shortname))

        print ('Importing libraries ', imports)
        # Get all function imports 
        functions = set() # (module path , function name)
        for shortname, val in list(globals().items()):
            if is_function(val)and is_external(val.__module__):
                functions.add((val.__module__, shortname))     
        print ('Importing functions ', functions)

        return {
            'packages' : list(packages), 
            'imports' : list(imports), 
            'functions' : list(functions)
        }

    
    def _get_test_cases(self, global_items):
        # Get all function imports 
        test_cases = {}
        if not global_items:
            global_items = globals().items()
        for shortname, val in list(global_items):
            try:
                if val and is_function(val) and not is_external(val.__module__) and \
                'penngrader' not in val.__module__:
                  test_cases[shortname] = inspect.getsource(val)   
                  print ('Adding case {}', shortname)
            except:
                print ('Skipping {}', shortname)
                pass
        return test_cases

    def get_raw_grades(self, homework_id, student_id, secret=None, with_deadline=False) -> pd.DataFrame | tuple[pd.DataFrame, str]:
        if secret is None:
            secret = student_id
        tokens = self._get_tokens(self.homework_id, student_id, secret)
        request = {
            'homework_id': homework_id,
            'student_id': student_id,
            'secret_key': self.secret_key,
            'request_type': GRADES_REQUEST,
            'token1': tokens.get('token1'),
            'token2': tokens.get('token2')
        }
        response = self._send_request(request, self.grades_api_url, self.grades_api_key)
        if 'Error' in response:
            print(response)
            return None
        else:
            result = json.loads(response)
            if result.get('statusCode') != 200:
                print('Error fetching grades: {}'.format(result.get('body')))
                return None
            
            (grades, deadline, max_daily_submissions, max_score) = json.loads(result.get('body'))
            
            if len(grades) == 0:
                print('No grades found for student ID {} and homework ID: {}'.format(student_id, homework_id))
                return pd.DataFrame()
            if with_deadline:
                return pd.DataFrame(grades), deadline
            else:
                return pd.DataFrame(grades)

    def get_grades(self, id) -> pd.DataFrame | str | None:
        result = self.get_raw_grades(self.homework_id, id, with_deadline=True)
        if isinstance(result, tuple):
            grades_df, deadline = result
        else:
            return result
        if grades_df is not None:

            if grades_df.shape[0] == 0:
                return "There have been no submissions."

            # Extract student ID from [student_submission_id]
            grades_df['student_id'] = grades_df['student_submission_id'].apply(lambda x: str(x).split('_')[0])

            # Convert to correct types
            grades_df['timestamp'] = pd.to_datetime(grades_df['timestamp'])
            grades_df['student_score'] = grades_df['student_score'].astype(int)

            # Get total scores per students
            scores_df = grades_df[['student_id', 'student_score']].groupby('student_id').sum().reset_index()

            # Get late days
            late_df = grades_df.groupby('student_id').max().reset_index()[['student_id', 'timestamp']].rename(
                columns={'timestamp': 'latest_submission'})

            # Calculate number of hours from local to UTC
            local_to_utc = datetime.utcnow() - datetime.now()

            # Subtract timechange offset from timestamp (lambdas are in UTC)
            late_df['latest_submission'] = late_df['latest_submission'] - local_to_utc

            # Add deadline from notebook context
            late_df['deadline'] = pd.to_datetime(deadline)

            # Add delta btw latest_submission and deadline
            late_df['days_late'] = (late_df['latest_submission'] - late_df['deadline']).dt.ceil('D').dt.days

            # Merge final grades
            final_df = scores_df.merge(late_df, on='student_id')[
                ['student_id', 'student_score', 'latest_submission', 'deadline', 'days_late']]
            final_df['days_late'] = final_df['days_late'].apply(lambda x: x if x > 0 else 0)
            return final_df[final_df['student_id'] == id]
    
    def _serialize(self, obj):
        '''Dill serializes Python object into a UTF-8 string'''
        byte_serialized = dill.dumps(obj, recurse = False)
        return base64.b64encode(byte_serialized).decode("utf-8")

    
    def _deserialize(self, obj):
        byte_decoded = base64.b64decode(obj)
        return dill.loads(byte_decoded)
