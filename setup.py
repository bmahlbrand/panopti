from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = "0.1.0"
DESCRIPTION = "Panopti: a Python package for interactive 3D visualization."

setup(
    name="panopti",
    version=VERSION,
    python_requires=">=3.8",
    description=DESCRIPTION,
    author="Arman Maesumi",
    author_email="arman.maesumi@gmail.com",
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy",
        "requests",
        "flask",
        "flask-socketio",
        "eventlet",
        "python-socketio[client]",
    ],
    package_data={
        # paths are *relative to the package root* (“panopti/”)
        "panopti": [
            # vite bundle
            "server/static/dist/**/*",
            "server/static/dist/.vite/**/*",
            # HTML + any assets referenced inside templates
            "server/static/templates/**/*",
        ],
    },
    keywords=["3D", "visualization", "geometry", "interactive", "web"],
)