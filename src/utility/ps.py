import sys
import os
import subprocess

# execute sub-process
def execute( name, arguments, logger = None ):

    p = subprocess.Popen( [name] + arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
    out, err = p.communicate()
    code = p.poll();

    return out, err, code

