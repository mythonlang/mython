# mython's setup.py

from distutils.core import setup

setup(
    name = "mython",
    packages = ["mython"],
    version = "0.0.2",
    description = "The Mython extensible variant of the Python programming "
    "language.",
    author = "Jon Riehl",
    author_email = "jon.riehl@gmail.com",
    url = "http://mython.org/",
    keywords = ["extensible", "syntax", "variant"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
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
