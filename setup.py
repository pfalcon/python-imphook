import sys
from setuptools import setup


setup(name="imphook",
      version="1.0",
      description="""Simple and clear import hooks for Python - import anything as if it were a Python module""",
      long_description=open('README.rst').read(),
      url="https://github.com/pfalcon/python-imphook",
      author="Paul Sokolovsky",
      author_email="pfalcon@users.sourceforge.net",
      license="MIT",
      py_modules=["imphook"])
