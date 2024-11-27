from setuptools import setup, find_packages

setup(
    name="siteoptimizer",
    version="0.1.0",
    author="Pradyumna Rao",
    author_email="pradyumna.rao@colorado.edu",
    description="A package to select wind and solar sites based on zonal network",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/prao7/siteoptimizer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[

    ],
)