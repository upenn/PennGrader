import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='penngrader-client',  
     version='0.5.1',
     scripts=[],
     author="Leonardo Murri and Zachary Ives",
     author_email="zives@cis.upenn.edu",
     description="In-line python grader client.",
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/zackives/PennGrader",
     packages=['penngrader-client'],
     install_requires=['dill','pyyaml'],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )
