import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="nowem",
    version="0.0.5",
    author="TWT233",
    author_email="TWT2333@outlook.com",
    description="API wrapper for princess connect re:dive(tw server)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TWT233/nowem",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
