from distutils.log import error
import os, sys

class scripter:
    def __init__(self, script_filename):
        self.filename = script_filename
        print('  > wd: ' + os.getcwd())

        file_exists = os.path.exists(self.filename)
        if file_exists:
            print('  > script: ' + self.filename)
        else:
            print('File ' + self.filename + ' cannot be found. Exiting...')
            exit(-1)

    def executeScript(self, tool):
        with open(self.filename,"r") as rnf:
            exec(rnf.read())