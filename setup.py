#!/usr/bin/env python
import io
from os.path import join, dirname, abspath
from setuptools import setup

def read(name):
    here = abspath(dirname(__file__))
    return io.open(
        join(here, name), encoding='utf8'
    ).read()

setup(
    name='diamond-ifcbondcollector',
    version='2.0.0',
    author='Onet - HW Platforms KRK',
    author_email='hw-priv@dreamlab.pl',
    description='Diamond collector for bonding status',
    py_modules=['src/ifcbondcollector'],
    data_files=[
        (r'/etc/sudoers.d/', ['conf/lldpctl']),
        (r'/etc/diamond/collectors/', ['conf/IFCBondCollector.conf']),
        (r'/usr/share/diamond/collectors/ifcbondcollector/', ['src/ifcbondcollector.py'])
    ],
    install_requires=read('requirements.txt').split('\n'),
    include_package_data=True,
    keywords=[
                'diamond', 'collector', 'bonding', 'network', 'interfaces'
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ],
)
