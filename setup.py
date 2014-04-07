#!/usr/bin/env python

from setuptools import setup

setup(name='Bytehand',
      version='0.1',
      description='Bytehand sms gateway api',
      author='Aman Orazaev',
      author_email='aorazaev@gmail.com',
      install_requires=['requests>=2.2.1'],
      url='https://github.com/aorazaev/bytehand',
      packages=['bytehand'],
      license = "MIT"
     )
