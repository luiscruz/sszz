import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sszz",
    version="0.0.5",
    author="Luis Cruz",
    author_email="luismirandacruz@gmail.com",
    description="Tool to retrieve the a future commit that has refactored a given commit (simple SZZ).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/luiscruz/sszz",
    packages=setuptools.find_packages(),
    install_requires=[
        "Click==7.0",
        "GitPython==3.1.32",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    entry_points = {
        'console_scripts': ['sszz=sszz.sszz:tool'],
    },
)