"""
Egg format:
    python setup.py sdist --dist-dir=./dist && rm -rf ./*.egg-info

Wheel format:
    python setup.py bdist_wheel --dist-dir=./dist && rm -rf ./*.egg-info
"""
from setuptools import setup

setup()
