import os

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required_dependencies = f.read().splitlines()
    external_dependencies = []
    for dependency in required_dependencies:
        if dependency[0:2] == "-e":
            repo_name = dependency.split("=")[-1]
            repo_url = dependency[3:]
            external_dependencies.append("{} @ {}".format(repo_name, repo_url))
        else:
            external_dependencies.append(dependency)

# Get version and release info, which is all stored in onsetpy/version.py
ver_file = os.path.join("onsetpy", "version.py")
with open(ver_file) as f:
    exec(f.read())

opts = dict(
    name=NAME,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url=URL,
    download_url=DOWNLOAD_URL,
    license=LICENSE,
    classifiers=CLASSIFIERS,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    platforms=PLATFORMS,
    version=VERSION,
    packages=find_packages(),
    python_requires=PYTHON_VERSION,
    entry_points={
        "console_scripts": [
            "{}=scripts.{}:main".format(
                os.path.basename(s), os.path.basename(s).split(".")[0]
            )
            for s in SCRIPTS
        ]
    },
    install_requires=external_dependencies,
)

setup(**opts)
