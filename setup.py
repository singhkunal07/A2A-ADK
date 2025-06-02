from setuptools import setup, find_packages

setup(
    name="decision-flow-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai",
        "a2a",
        "google-generativeai",
    ],
) 