from setuptools import setup
import versioneer


if __name__ == "__main__":
    setup(
        name="ipython-autoimport",
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        description="Autoimport missing modules in IPython",
        author="Antony Lee",
        url="https://github.com/anntzer/ipython-autoimport",
        license="BSD",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Framework :: IPython",
            "License :: OSI Approved :: BSD License",
            "Programming Language :: Python :: 3.3",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
        ],
        py_modules=["ipython_autoimport"],
        python_requires=">=3.3",
    )
