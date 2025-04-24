from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="next-identity-oidc",
    version="0.1.0",
    author="Next Identity",
    author_email="info@nextidentity.com",
    description="Python OIDC client for Next Identity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/next-identity/next-identity-oidc-python",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "flask": ["Flask>=2.0.0"],
        "fastapi": ["fastapi>=0.68.0", "starlette>=0.14.2"],
        "all": ["Flask>=2.0.0", "fastapi>=0.68.0", "starlette>=0.14.2"],
    },
) 