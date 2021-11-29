import os
import re
from setuptools import setup

requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
with open(requirements_file) as f:
    requirements = f.read().splitlines()

with open('src/pyamicreator/__init__.py', 'r') as fd:
    VERSION = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)


if __name__ == "__main__":
    try:
        setup(
            version=VERSION,
            install_requires=requirements,
        )
    except:  # noqa
        print(
            "\n\nAn error occurred while building the project, "
            "please ensure you have the most updated version of setuptools, "
            "setuptools_scm and wheel with:\n"
            "   pip install -U setuptools setuptools_scm wheel\n\n"
        )
        raise
