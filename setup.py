# mython's setup.py

from setuptools import setup, find_packages

with open('README.md') as fh:
    long_description = fh.read()

setup(
    name = "mython",
    packages = find_packages(),
    package_data = {
        "" : ["Grammar", "Python.asdl", "Tokens"],
        },
    entry_points={
        "console_scripts": [
            "mython = mython.__main__:main",
        ],
    },
    version = "0.0.3",
    description = "The Mython extensible variant of the Python programming "
    "language.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    author = "Jon Riehl",
    author_email = "jon.riehl@gmail.com",
    url = "http://mython.org/",
    keywords = ["extensible", "syntax", "variant"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
)
