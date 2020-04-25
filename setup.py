"""
Egg format:
    python setup.py sdist --dist-dir=./dist && rm -rf ./*.egg-info

Wheel format:
    python setup.py bdist_wheel --dist-dir=./dist && rm -rf ./*.egg-info

Upload to Pypi:
    pip install -U twine wheel setuptools
    twine check dist/*
    twine upload dist/*
"""
from setuptools import setup

setup()
