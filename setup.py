import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="nowem",
    version="0.0.9",
    author="TWT233",
    author_email="TWT2333@outlook.com",
    description="API wrapper for princess connect re:dive(tw server)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TWT233/nowem",
    packages=setuptools.find_packages(),
    install_requires=['requests==2.25.1', 'msgpack>=1.0.1', 'pycryptodomex>=3.9.9'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
