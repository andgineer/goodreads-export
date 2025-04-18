import codecs
import os
import os.path

import setuptools

with open("README.md") as fh:
    long_description = fh.read()

with open("requirements.in") as f:
    requirements = f.read().splitlines()


# Solution from https://packaging.python.org/guides/single-sourcing-package-version/
def read(rel_path: str) -> str:
    """Read file."""
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path: str) -> str:
    """Parse version from file content."""
    for line in read(rel_path).splitlines():
        if line.startswith("VERSION"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


setuptools.setup(
    name="goodreads-export",
    version=get_version("src/goodreads_export/version.py"),
    author="Andrey Sorokin",
    author_email="andrey@sorokin.engineer",
    description=("Convert goodreads books to markdown files, for example for Obsidian."),
    entry_points={
        "console_scripts": [
            "goodreads-export=goodreads_export.main:main",
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://andgineer.github.io/goodreads-export/en/",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=requirements,
    # dict union operator 3.9, walrus operator, cached property 3.8
    python_requires=">=3.9",
    keywords="goodreads book markdown obsidian",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    zip_safe=True,
    include_package_data=True,
    data_files=[("", ["LICENSE.txt"])],
)
