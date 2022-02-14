from setuptools import setup


setup(
    name="ipython-autoimport",
    description="Automagically import missing modules in IPython.",
    long_description=open("README.rst", encoding="utf-8").read(),
    long_description_content_type="text/x-rst",
    author="Antony Lee",
    url="https://github.com/anntzer/ipython-autoimport",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: IPython",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    py_modules=["ipython_autoimport"],
    package_dir={"": "lib"},
    python_requires=">=3.6",
    setup_requires=["setuptools_scm"],
    use_scm_version=lambda: {
        "version_scheme": "post-release",
        "local_scheme": "node-and-date",
    },
    install_requires=[
        "ipython>=4.1",  # IPython#8985 is needed for tests to pass(?).
        "importlib_metadata; python_version<'3.8'",
    ],
)
