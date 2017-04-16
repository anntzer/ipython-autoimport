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
        license="BSD",
        classifiers=[
            "Development Status :: 4 - Beta",
            "Framework :: IPython",
            "License :: OSI Approved :: BSD License",
            "Programming Language :: Python :: 3",
        ],
        py_modules=["ipython_autoimport"],
        install_requires=["ipython"],
    )
