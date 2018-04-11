IFCBondCollector
================

|image0|_

.. |image0| image:: https://api.travis-ci.org/DreamLab/IFCBondCollector.png?branch=master
.. _image0: https://travis-ci.org/DreamLab/IFCBondCollector


About
=====
Monitoring for bonding network interfaces based on diamond collector and llpd.

How to build/install
====================

Simply install package via `pip`:

::

    pip install diamond-ifcbondcollector

    # or
    # python setup.py install

or with deb

::

    make deb
    dpkg -i ./bin/diamond-ifcbondcollector_2.0.0_amd64.deb


Requirements
------------
Collector requires following packages to be installed:
- Python2 (>=2.7)
- diamond
- lldpd


Example configuration 
=====================

Base
----

Default configuration

::

    enabled = True
    ifc_name = "bond0"


Extended
--------

Extended configuration with rules collector will check if the designated network interfaces are connected to the correct network device (interface names must be the same as those available from lldpctl).


In this example we check if eth0 is connected to switch with name test_name_switch1, and eth1 to test_name_switch2. Below configuration matches switch by chassis_name - a field fromm `llpdctl` output, you can specify to test against different field eg. chassis_mac, port_descr etc.

:: 

    enabled = True
    ifc_name = "bond0"

    eth0_on_sw1 = eth0, chassis_name, test_name_switch1
    eth1_on_sw2 = eth1, chassis_name, test_name_switch2

    rules = eth0_on_sw1, eth1_on_sw2


License
=======

`Apache License 2.0 <LICENSE>`_
