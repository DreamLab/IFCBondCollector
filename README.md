# IFCBondCollector

## About:
Monitoring for bonding network interfaces based on diamond collector

## How to build/install:
```
python setup.py install
```
or
```
make deb
dpkg -i ./bin/diamond-ifcbondcollector_2.0.0_amd64.deb
```

## Requirements
Collector requires following packages to be installed:
- Python2 (>=2.7)
- diamond
- lldpd


## Example configuration 

Default configuration

```
enabled = True
ifc_name = "bond0"
```

Extended configuration with rules (We can check if the designated network interfaces are connected to the correct network device - Interface names must be the same as those available from lldpctl ).
In this example we check if eth0 is connected to switch with name test_name_switch1, and eth1 to test_name_switch2, but chassis_name is only variable available from the lldpctl - we can use there any other variable to match it with each other like chassis_mac, port_descr etc.
```
enabled = True
ifc_name = "bond0"

eth0_on_sw1 = eth0, chassis_name, test_name_switch1
eth1_on_sw2 = eth1, chassis_name, test_name_switch2

rules = eth0_on_sw1, eth1_on_sw2
```

##LICENSE
[Apache License 2.0](LICENSE)
