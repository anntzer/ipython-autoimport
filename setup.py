from setuptools import setup
import versioneer


if __name__ == "__main__":
    setup(
        name="ipython-autoimport",
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        description="Automagically import missing modules in IPython.",
        long_description=open("README.rst").read(),
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
        python_requires=">=3",
        install_requires=["ipython>=4.0"],  # introduced `history_load_length`.
    )
