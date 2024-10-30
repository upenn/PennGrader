# PennGrader Client

Welcome to the PennGrader!  This autograder project was created by Leo Murri at the University of Pennsylvania, and it is currently maintained by the CIS faculty, staff, and students at Penn.  Note that this fork of the project has been split out from the backend, and comprises the Penngrader client *only*.  The backend server-side component has been re-architected on containerized AWS Lambda.

## The PennGrader Philosophy
Here at PennGrader, we believe that learning comes from lots of practice...and from making lots of mistakes. 

From creator Leo Murri: "After many years as a student I found myself very frustrated in the following homework timeline: struggle on a homework assignment for weeks, submit something that may or may not be right and then wait a few more weeks to receive any type of feedback, at which point I had forgotten all about the homework. After many years as a TA, I also found myself very frustrated with the common auto-grading tools, the hours and hours of manual grading and the onslaught of re-grade requests that came thereafter."

From these frustrations, the PennGrader was born!

The PennGrader was built to allow students to get instant feedback and many opportunities for re-submission. After all, programming is about making mistakes and learning from feedback! Moreover, we wanted to allow TAs and Instructors to write their homework in any way they pleased, without having to worry about the structure of a specific auto-grader. The examples below are done using Jupyter Notebooks which is the most common use case, but you can use this for normal Python homework as well. 

## The Student-Facing Experience

Here is what a student sees in their Homework Notebook. All a student has to do is write their solution and run the auto-grading cell.

![Sample Question](https://penngrader-wiki.s3.amazonaws.com/sample_question.gif)

Through the magic of AWS Lambdas, the student's answer (in this case the `addition_function` object) is packaged and shipped to the backend where it is checked against the teacher-defined test case. Finally, a score is returned. All students' scores are saved in the backend and are easily accessible to the instructors. If at first they don't succeed, they can learn from their mistakes and try again.  (Yes, if you'd like, can set a maximum number of daily submissions to incentivize students to start early). This "grader" function can easily be used from any Jupyter notebook (even Google Colab), all you have to do is to `pip install penngrader` or the like. See templates below.

Ok, ok, you might be saying to yourself: "That looks easy enough, but what about us TAs, we want something that simple too!" Well, look no further. The TAs/Instructors' experience is just as seamless. All TAs will share a __Teacher_Backend__ notebook, which contains all the test case functions. The logic of how testing is done is simple: whatever Python object gets passed through the `answer` field in the `grade(...)` function (see above) will be the input to the test case function (see below). In the above example, `addition_function` is passed as the answer to a test case named `"test_case_1"`. Therefore, the TAs will need to write a `test_case_1(addition_function)` function in the __Teacher_Backend__ notebook, as follows:

![Sample Question](https://penngrader-wiki.s3.amazonaws.com/sample_update.gif)

As you can see, this function tests that `addition_function(1,2) == 3`, if correct it adds 5 points to the `student_score`. The test must then return an integer tuple `(student_score, max_score)`, which is what will be displayed to the student. As you can see this type of test function gives the Instructor complete flexibility on what to test and how much partial credit to give. Remember that the answer that gets passed to the test case could be anything... a function, a class, a DataFrame, a list, a picture... anything! The PennGrader automatically serializes it and all its dependencies and ships to AWS for grading.

## Configuring the autograder for your course

The PennGrader has a fairly simple setup.  

Within Penn, you can just email zives@cis.upenn.edu to request the registration of a course.  Otherwise you will want to register the course using the [course registration tool](https://github.com/upenn/cis-penngrader-course).  This will create a series of YAML configuration files -- one for the teacher backend (`backend-config.yaml`), one for the student notebook (`notebook-config.yaml`).

A third YAML file (`gradescope-config.yaml`) is for an additional (optional) component:  [Gradescope integration](https://github.com/upenn/penngrader-gradescope).  Through Gradescope integration, you may (1) pull the PennGrader score for each student and homework into Gradescope, (2) register additional, "hidden" tests if you like, (3) add a manual grading component.

1. Run the course registration tool.  Make note of `backend-config.yaml`, `notebook-config.yaml`, and `gradescope-config.yaml`.

### Registering a homework

Next, go to Colab to set up the homework metadata:

* Using the [PennGrader_TeacherBackend.ipynb](./Test%20Client%20Notebook/PennGrader_TeacherBackend.ipynb) and your `backend-config.yaml` from above, register the homework assignment info (name, deadline, etc.).  To do this, update the `TOTAL_SCORE`, `MAX_DAILY_TEST_CASE_SUBMISSIONS`, and `DEADLINE`.  Beware that the deadline is in GMT.
* Define test case functions for your homework assignment and run the notebook.  **Please see below for some limitations on test case authoring**!

[PennGrader_TeacherBackend.ipynb](./Test%20Client%20Notebook/PennGrader_TeacherBackend.ipynb)

### Defining a homework notebook

Your homework specification should tell the students to upload their final notebook to Gradescope, with the `STUDENT_ID` set to their numeric PennID.  From this Gradescope will look up their Penngrader scores (as of the submission date).

In principle you can include `notebook-config.yaml` with the student notebook. In practice you'll want to use a `%%writefile` cell to write the contents of `notebook-config.yaml` to a local file via the notebook.

[PennGrader_Homework_Template.ipynb](./Test%20Client%20Notebook/PennGrader_Homework_Template.ipynb)

### Linking to Gradescope

The Gradescope integration with PennGrader is simple: we don't attempt to re-run the test suite (which can be very tricky if the student has executed cells out of order). Rather, we simply look up the student's grade from the grades database.

1. Copy the `gradescope-config.yaml` to the PennGrader-Gradescope directory, renaming it to `config.yaml`.
2. Update the `homework_num` in `gradescope-config.yaml` to the homework number.
3. Set up the homework assignment as a *Programming assignment* in Gradescope.  Set an autograder max score.  Zip and upload the PennGrader-Gradescope files (with the generated `gradescope-config.yaml` from above) as the autograder.  **Note you'll need to update the YAML file in each homework to adjust the homework number.**

The TAs may add additional manual grading, or simply release the scores, as appropriate.

## Behind the scenes...
In the following section, we will go into detail about the system implementation. Below is the system design overview we will go into.

![Architecture Design](https://penngrader-wiki.s3.amazonaws.com/design.png)

### Clients
There are two pip installable clients, one for students and one for instructors. You can install these two clients by running `pip install penngrader-client` in your favorite terminal.  When creating a new homework download the [Homework_Template.ipynb](./Test%20Client%20Notebook/PennGrader_Homework_Template.ipynb) and the [TeacherBackend.ipynb](./Test%20Client%20Notebook/PennGrader_TeacherBackend.ipynb) notebooks and follow the instructions. More details are presented below.

#### Student's Client: PennGrader

The student's client will be embedded in the homework release notebook. Its main purpose will be to interface the student's homework with the AWS backend. This client is represented by the `PennGrader` class which needs to be initialized by the instructor when writing the homework as follows. Note: the HOMEWORK_ID needs to be filled in before releasing the notebook. The student should only enter his or her's student id. 

```
from penngrader.grader import *
grader = PennGrader('config.yaml', homework_id = HOMEWORK_ID, STUDENT_ID, SECRET)
```

The HOMEWORK_ID is the string obtained when creating new homework via the teacher backend, see below. 

STUDENT_ID is the student defined variable representing their 8-digit PennID. The student will need to run this cell at the beginning of the notebook to initialize the grader. The SECRET should be set to the STUDENT_ID by default, but allows students to add a unique password protecting their grades. (The only issue: they tend to forget this or change it mid-stream! For this reason you may want to simply pass STUDENT_ID or some other hard-coded string.)

After every question, the Instructor will also need to write a grading cell which the student will run to invoke the grader. A grading cell looks as follows:

```
grader.grade(test_case_id = TEST_CASE_NAME, answer = ANSWER) 
```

TEST_CASE_NAME is the string name of the test case function that will grader the given question. 

ANSWER is the object that needs to be graded. 

For example, you might have a question where you instruct the student to create a DataFrame called `answer_df`. You will need to write `answer_df` as the input answer parameter of the grader function as follows:

```
grader.grade(test_case_id = TEST_CASE_NAME, answer = answer_df) 
```

 That way, when the student runs this cell, the grader will automatically find the test function named TEST_CASE_NAME, serialize the `answer_df` python variable and ship it to AWS. The cool thing about the PennGrader is that you can pass pretty much anything as the answer.

**PennGrader generally assumes *the same versions* of Python and the various libraries on the client and the server. By default, functions generally cannot be passed as parameters.  See below for suggestions.**

#### Teacher's Client: PennGraderBackend

The teacher client allows instructors to create and edit the test cases function mentioned earlier, as well as define multiple homework metadata parameters. As shown in the template notebooks linked above, you first need to initialize the _PennGraderBackend_ for a specific homework as follows:

```
backend = PennGraderBackend('backend-config.yaml', HOMEWORK_NUMBER)
```

The course secret token and other information should come from `backend-config.yaml`. 

HOMEWORK_NUMBER identifies which homework number you are planning to write/edit. 

After running the above cell in a Jupyter Notebook, given a correct YAML file, the assigned HOMEWORK_ID string will be printed out. This HOMEWORK_ID needs to be copied into the initialization of the PennGrader student client for release. Just the homework id, without the secret key, will not allow students to see any of the test cases, so make sure the secret key does not get out. 

After initialization, the  `backend` can be used to 1) update metadata 2) edit/write test cases.

You can edit the following metadata parameters by running the following code:

```
TOTAL_SCORE = 100
DEADLINE = '2019-12-05 11:59 PM'
MAX_DAILY_TEST_CASE_SUBMISSIONS = 100

backend.update_metadata(DEADLINE, TOTAL_SCORE, MAX_DAILY_TEST_CASE_SUBMISSIONS)
```

`TOTAL_SCORE` represents the total number of points the homework is worth and should equal the sum of all test cases weights.

`DEADLINE` represents the deadline of the homework, with format: _YYYY-MM-DD HH:MM A_.  **Please note this deadline is in UTC**.

`MAX_DAILY_TEST_CASE_SUBMISSIONS` represents the number of allowed submissions per test case per day.

Writing test cases is also just as simple. In a Jupyter Notebook (see Teacher Backend template above), you just need to write test case functions for each gradable question.  Each test case will be identified by a _test_case_id_ which is the name of the test case function. A test case functions needs to follow the following format:

```
def test_case_name(answer_object_name):
	student_score = 0 # Current student score
	max_score = 5 # Number of points this question is worth

	# some kind of grading that adds or subtracts from the student_score #

	return (student_score, max_score, 'Diagnostic or error message')
```

The test case function needs to return an integer tuple representing the student score for their answer, the max number of points that can be earned in the given question, and ideally a suggestion / warning if there was a mistake.  The diagnostic message will be ignored if the student received full credit.

After writing all the test cases you need, simply run the following code in a cell and the PennGraderBackend class will automatically extract all user-defined functions in the current notebook and upload them to AWS.

```
backend.update_test_cases(globals().items())
```

A success message will print once the operation has succeeded. If loading a lot of external libraries this might take a few minutes.

### Lambdas

AWS Lambda is an incredibly cool, but also quite complex system to set up.  We recommend that you use an existing API Gateway URL and set of Lambda Layers.

* The Gateway URL exports a Python function (from Penngrader) to a given URL, with a REST interface and an API key.
* The Lambda needs to be granted appropriate DynamoDB permissions and logger permissions.
* The Lambda makes use of Python libraries, in our case including Pandas and Numpy.  You can set these up in an S3 volume and add these to a Layer, to make these accessible to the Penngrader.  **However note that simply running `pip install -t package pandas numpy pytz` will be inadequate: you need special multi-Linux versions of the C libraries.  See https://korniichuk.medium.com/lambda-with-pandas-fd81aa2ff25e for more info.**

#### Grader

The _Grader_ lambda gets triggered from an API Gateway URL from the student's PennGrader client. The student's client as defined above will serialize its answer and make a POST request to the lambda with the following body parameters: 

`{'homework_id' : ______, 'student_id' : ________, 'test_case_id' : ________, 'answer' : _______ }`

The lambda will proceed by downloading the correct serialized _test_case_'s and _libraries_ from the _HomeworksTestCases_ DynamoDB table. It will then deserialize these objects and extract the correct test case given the _test_case_id_ . import the correct libraries used by given test case. If the submission is valid the student score will be recorded in the backend. 

**Update** In recent versions, the _Grader_ Lambda has been substantially revamped. (1) It is now configured in its own [container](https://github.com/upenn/penngrader-lambda) so more libraries can be installed, (2) it has been moved to its own "sandbox" without access to AWS resources.  Given that Python is not a very secure language, our goal is to minimize exposure.

#### Grades

The grades lambda interfaces the TeacherBackend and student notebook with the Gradebook. Using this API Gateway triggered lambda the TeacherBackend client can request all grades for a given homework. The payload body used to trigger this lambda will need to include 

`{'homework_id' : ______, 'secret_key' : ________, 'request_type' : ________ }`

Where the _secret_key_ parameter is optional and will allow a properly initialized TeacherBackend to download all grades for the selected homework. Students will also be able to view their scores.

#### HomeworkConfig

The _HomeworkConfig_  lambda interfaces the TeacherBackend with the _HomeworkTestCases_ and _HomeworkMetadata_ DynamoDB Tables (see below for table schema). This lambda can be triggered in two ways 1) to update metadata and 2) to update test cases. After unparsing and deserializing the triggered payload, the inputted data gets written into the appropriate DynamoDB table. 

### DynamoDB Tables & S3 Buckets
As shown in the above schematic we maintain the majority of the data needed for grading and grade storage on DynamoDB. Below we list the information recorded in each table.

**Classes DynamoDB Table**

_Classes_ contains information about all courses currently registered for the PennGrader. The grading protocol is on a per-class basis. Each class that wants to create a course that uses the PennGrader will receive `SECRET_KEY`, this secret key will be passed in the TeacherBackend client to allow instructors to edit test cases. The tables contain the following schema:

`secret_key` : Unique UUID used as a secret identifier for a course.

`course_id`  : Human-readable identifier representing the course number and semester of the class offered i.e. 'CIS545_Spring_2019'. This ID will be the pre-fix of the `homework_id`, which will be used to identify a homework assignment.

**HomeworksMetadata DynamoDB Table**

The _HomeworksMetadata_ is used to maintain updatable information about a specific homework. The information in this table will be editable from the TeacherBackend even after homework release. The tables contain the following schema:

`homework_id` : Unique identifier representing a course + homework number pair. _homeowork_id_ is constructed by taking the _course_id_ defined above and appending the homework number of the assignment in question. For example, given the course id defined above (CIS545_Spring_2019), the _homework_id_ for the first homework will be 'CIS545_Spring_2019_HW1'. This homework_id will be passed into the PennGrader Grader class in the student's homework notebook and will be used to correctly find the correct test cases and store the student scores correctly.

`deadline` : String representing the deadline of the homework in local time i.e. 2019-12-05 11:59 PM (format: YYYY-MM-DD HH:MM A)

`max_daily_submissions` : Number representing the total number of submissions allows per test case per day. For example, if this number is set to 5, it means that all students can submit an answer to a specific test case 5 times a day. Resetting at midnight. 

`max_score` : The total number of points this homework is worth. This number should be equal to the sum of all test case weights. _max_score_ is used to show students how many points they have earned out of the total assignment.

**HomeworksTestCases DynamoDB Table**

The _HomeworksTestCases_ table contains a serialized encoding of the test cases and libraries imports needed to run a student's answer. The tables contain the following schema:

`homework_id` : Same _homework_id_ from the _HomeworksMetadata_ table.

`test_cases` : This field contains a dill UTF-8 string serialization of the test cases defined in the teacher backend. The teacher backend extracts all test case functions from the notebook and creates a dictionary of _name_ -> _function_. This parameter is deserialized when a new grading request is made and the correct test case is extracted and ran. 

`libraries` : Similar to the _test_cases_ field, the libraries are UTF-8 dill serialized list of tuples that contain all libraries and functions imported in the teacher backend notebook and their appropriate short name. This list is used to import all needed libraries to run a specific test case. 


**Gradebook DynamoDB Table**

The _Gradebook_ table contains all grading submissions and student scores. The table contains the following schema:

`homework_id` : Same _homework_id_ from the _HomeworksMetadata_ table.

`student_submission_id` : String representing a student submission. This string is create by appending the student's PennID to the test case name i.e. '12345678_test_case_1'.

`max_score` : Maximum points that can be earned for this test case

`student_score` : Points earned by the student on this test case. 

Note: Currently only the last submission is recorded, thus the latest student score will overwrite all previous scores.

## Writing Effective Test Cases

The thing to remember about test cases is that they are individually indexed functions, which are retrieved and called when `grader.grade()` is run.

1. Make sure imports and variables are computed and set within the local symbol space of the function.  I.e., your functions should look like:

```
def myfn(x):
  import pandas as pd
  import math

...
```

2. Beware of passing objects that belong to packages not installed on the backend, for instance Apache Spark DataFrames.  Additionally, files and other entities unique to the client machine cannot be pickled / passd.

3. Python pickling is notoriously fickle about version mismatches between client and server.  Try to make sure the versions are at least close. You might consider converting more esoteric data into JSON or another similar format, passing as a string, and decoding on the server side.

4. Passing functions must be done as strings, largely to insulate against version mismatches.  You can use the `getsource()` function in the `dill` package to get source code for a client-side function. On the server side you can use `exec` (but be careful to output the results in a new symbol table). Here is an example of how this is done.

Client side:
```
def bob(name: str) -> bool:
  first_name = name.split(' ')[0].lower().strip()
  return first_name == 'bob' or \
    first_name == 'robert' or \
    first_name == 'roberta'

from dill.source import getsource
bob_test(getsource(bob))
```

Server side test case:
```
def bob_test(f):
  import dill

  # Dictionary for new functions + variables
  d = {}
  # Add all global + local symbols to fn context
  symbols = {}
  symbols.update(globals())
  symbols.update(locals())
  # Execute user code within context, adding new
  # symbols into dictionary d
  exec(f, symbols, d)
  # Function bob should be inside the dictionary
  if not 'bob' in d:
    raise RuntimeError("No function called `bob` was defined\n")
  bob = d['bob']

  if not callable(bob):
    return (0, 3, 'bob needs to be a function\n')

  if bob('Robertasmith'):
    return (0, 3, 'bob should only accept first names as specified\n')
  elif not bob('bob'):
    return (1, 3, 'bob should match different cases\n')
  elif not bob('robert') or not bob('roberta'):
    return (1, 3, 'bob should match different name\n')
  else:
    return (3, 3)
```
