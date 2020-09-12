from setuptools import setup, find_packages

with open("README.md") as fd:
    long_description=fd.read()

setup(
    name='tokex',
    version='2.0.2',
    description="String tokenizing and parsing library",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Warren Spencer",
    author_email="warrenspencer27@gmail.com",
    url="https://github.com/warrenspe/tokex",
    keywords=["tokex", "tokenize", "parse"],

    packages=find_packages(),

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries",
        "Topic :: Text Processing"
    ]
)
