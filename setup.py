from setuptools import setup, find_packages

tests_require = [
    "mock"
]

setup(
    name='todoable',
    version="0.1",
    description="Wrapper around Todoable API",
    license="",
    author="Yuriy Bash",
    author_email="yuriybash@gmail.com",
    url="",
    tests_require=tests_require,
    install_requires=[
        'python-dateutil', 'requests'
    ],
    packages=find_packages(exclude=['tests']),
)
