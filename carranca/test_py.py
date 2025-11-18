import flask
import sys
from importlib.metadata import version
print(flask.__version__)
print("Flask version:", version("flask"))
print("Interpreter path:", sys.executable)
