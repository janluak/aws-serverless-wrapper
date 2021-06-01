"""
The setup file_name.
If development mode (=changes in package code directly delivered to python) `pip install -e .` in directory of this file_name
"""

from setuptools import setup, find_packages
from aws_serverless_wrapper import __versions__

# https://python-packaging.readthedocs.io/en/latest/minimal.html

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="aws_serverless_wrapper",
    version=__versions__,
    description="decorator for speeding up aws serverless development & separating business from infrastructure code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/janluak/aws-serverless-wrapper",
    author="Jan Lukas Braje",
    author_email="aws-serverless-wrapper@getkahawa.com",
    packages=find_packages(),
    python_requires=">=3.8",
    zip_safe=False,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
    ],
    # https://pypi.org/pypi?%3Aaction=list_classifiers
    include_package_data=True,
    install_requires=["boto3", "jsonschema", "botocore"],
    extra_require={"testing": ["pytest", "moto", "freezegun"]},
)
