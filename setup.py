# python setup.py sdist register upload
from setuptools import setup

setup(
    name='sw-python-viber-devino',
    version='0.0.1',
    description='Integration with viber API of devinotele.com',
    author='Telminov Sergey',
    url='https://github.com/telminov/sw-python-viber-devino',
    packages=[
        'viber_devino',
        'viber_devino.tests',
    ],
    include_package_data=True,
    license='The MIT License',
    install_requires=[
        'requests'
    ],
    tests_requirements=[
        'mock',
    ]
)