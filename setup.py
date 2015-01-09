#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup


readme = open('README.rst').read()


setup(
    name='schedule',
    version='1.0.0',
    description="Setup an AWS autoscaling group that creates and terminates a single instance on scheduled intervals",
    long_description=readme,
    author='Rob Berry',
    author_email='rob@lostpropertyhq.com',
    url='https://github.com/LostProperty/schedule',
    py_modules=[
        'schedule',
    ],
    include_package_data=True,
    license="MIT",
    zip_safe=False,
)
