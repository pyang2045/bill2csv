#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bill2csv",
    version="1.0.0",
    author="Your Name",
    description="Convert PDF bills to CSV using Gemini API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.9",
    install_requires=[
        "google-generativeai>=0.3.0",
        "pypdf>=3.17.0",
    ],
    entry_points={
        "console_scripts": [
            "bill2csv=bill2csv.__main__:main",
        ],
    },
)