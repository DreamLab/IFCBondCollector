#!/usr/bin/python
# coding=utf-8

from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from mock import Mock, patch
from io import BytesIO
from StringIO import StringIO
from diamond.collector import Collector
import os
import sys
sys.path.append('../src/')
from ifcbondcollector import IFCBondCollector

test_base = os.path.dirname(os.path.realpath(__file__))


class TestIFCBondCollectorCollector(CollectorTestCase):

    def setUp(self, custom_config={}):
        super(TestIFCBondCollectorCollector, self).setUp()
        config = get_collector_config('IFCBondCollector', custom_config)
        self.collector = IFCBondCollector(config, None)
        self.publish_mock = patch.object(Collector, 'publish').start()
        self.mock_os_popen = patch('os.popen').start()

    def tearDown(self):
        super(TestIFCBondCollectorCollector, self).tearDown()
        self.mock_os_popen.stop
        self.publish_mock.stop

    def test_import(self):
        self.assertTrue(IFCBondCollector)

    def test_check_bonding_match_fail(self):

        self.collector.publish_data = {}
        ifc_list = {'eth100':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw1.test.switch'
                            }
                        },
                    'eth101':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw1.test.switch'
                            }
                        }
                    }
        self.collector.check_bonding_match(ifc_list)

        #check if it raises a mismatch_bond
        self.assertTrue(self.collector.publish_data['mismatch_bond'])


    def test_check_bonding_match_ok(self):

        self.collector.publish_data = {}
        ifc_list = {'eth100':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw1.test.switch'
                            }
                        },
                    'eth101':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw2.test.switch'
                            }
                        }
                    }

        #call a bonding collector check_bonding_match func
        self.collector.check_bonding_match(ifc_list)

        #check if it NOT raises a mismatch_bond
        self.assertFalse(self.collector.publish_data['mismatch_bond'])

    def test_reporting_data(self):

        self.collector.publish_data = {'mismatch_bond': False}
        metrics = {
            'mismatch.bond': 0,
        }

        #call a bonding collector reporting_data func
        self.collector.reporting_data()

        self.assertPublishedMany(
            [self.publish_mock],
            metrics,
        )

    def test_proc_bonding_read(self):

        with open(os.path.join(test_base, 'bonding_content.txt'), 'r') as bond0_content_f:
            bond0_content = bond0_content_f.read()

        with patch('__builtin__.open', Mock(return_value=BytesIO(bond0_content))):
            bondx_content = self.collector.get_bond_dev()

        self.assertEqual(bondx_content, bond0_content)

    def test_get_link_stat_1(self):
        """
        test bug with multiply interfaces on lldpctl output

        example of age used in this case:

        ...
        lldp.eth1.age=0 day, 19:27:04
        lldp.eth0.age=256 days, 04:22:30
        lldp.eth0.age=0 day, 04:22:30
        lldp.eth1.age=0 day, 20:00:04
        ...

        """

        ifc_stats = {
          'eth0': { 'lldp_stats' : {}
                    },
          'eth1': { 'lldp_stats' : {}
            }
        }

        with open(os.path.join(test_base, 'bug_multiply_interfaces.txt'), 'r') as lldp_entry_content_f:
            lldp_entry_content = lldp_entry_content_f.read()

        expected_output = {
            'eth1':
                {'lldp_stats':
                    {'vlan_vlan-id': '101',
                        'vlan_pvid': 'yes',
                        'via': 'LLDP',
                        'chassis_mgmt-ip': '11.111.111.11',
                        'age': '0 day, 19:27:04',
                        'chassis_descr': 'Cisco Nexus Operating System (NX-OS) Software',
                        'chassis_mac': 'yy:yy:yy:yy:yy:yy',
                        'chassis_Bridge_enabled': 'on',
                        'port_local': 'Eth122/1/2',
                        'chassis_name': 'sw2.test.switch',
                        'rid': '1',
                        'port_descr': 'Ethernet122/1/2'}
                    },
            'eth0':
                {'lldp_stats':
                    {'vlan_vlan-id': '101',
                        'vlan_pvid': 'yes',
                        'via': 'LLDP',
                        'chassis_mgmt-ip': '22.222.222.22',
                        'age': '0 day, 04:22:30',
                        'chassis_descr': 'Cisco Nexus Operating System (NX-OS) Software',
                        'chassis_mac': 'zz:zz:zz:zz:zz:zz',
                        'chassis_Bridge_enabled': 'on',
                        'port_local': 'Eth122/1/2',
                        'chassis_name': 'sw1.test.switch',
                        'rid': '2',
                        'port_descr': 'Ethernet122/1/2'}
                }
        }

        self.mock_os_popen.return_value = StringIO(lldp_entry_content)
        result = self.collector.get_link_stat(ifc_stats)
        self.assertDictEqual(expected_output, result)

    def test_get_link_stat_2(self):
        """ test with only one interface available on lldpctl """

        ifc_stats = {
          'eth0': { 'lldp_stats' : {}
                    },
          'eth1': { 'lldp_stats' : {}
            }
        }

        with open(os.path.join(test_base, 'one_interface_available_lldpctl.txt'), 'r') as lldp_entry_content_f:
            lldp_entry_content = lldp_entry_content_f.read()

        expected_output = {
                'eth1':
                    {'lldp_stats':
                        {'vlan_vlan-id': '101',
                        'vlan_pvid': 'yes',
                        'via': 'LLDP',
                        'chassis_mgmt-ip': '11.111.111.11',
                        'age': '22 day, 19:27:04',
                        'chassis_descr': 'Cisco Nexus Operating System (NX-OS) Software',
                        'chassis_mac': 'yy:yy:yy:yy:yy:yy',
                        'chassis_Bridge_enabled': 'on',
                        'port_local': 'Eth122/1/2',
                        'chassis_name': 'sw2.test.switch',
                        'rid': '1', 'port_descr': 'Ethernet122/1/2'}
                        },
                'eth0':
                    {'lldp_stats': {}
            }
        }

        self.mock_os_popen.return_value = StringIO(lldp_entry_content)
        result = self.collector.get_link_stat(ifc_stats)
        self.assertDictEqual(expected_output, result)

    def test_get_link_stat3(self):
        """ test with all data available on lldpctl """

        ifc_stats = {
          'eth0': { 'lldp_stats' : {}
                    },
          'eth1': { 'lldp_stats' : {}
            }
        }

        with open(os.path.join(test_base, 'normal_data_lldpctl.txt'), 'r') as lldp_entry_content_f:
            lldp_entry_content = lldp_entry_content_f.read()

        expected_output = {
            'eth1':
                {'lldp_stats':
                    {'vlan_vlan-id': '101',
                        'vlan_pvid': 'yes',
                        'via': 'LLDP',
                        'chassis_mgmt-ip': '22.222.222.22',
                        'age': '30 days, 12:14:20',
                        'chassis_descr': 'Cisco Nexus Operating System (NX-OS) Software',
                        'chassis_mac': 'zz:zz:zz:zz:zz:zz',
                        'chassis_Bridge_enabled': 'on',
                        'port_local': 'Eth122/1/2',
                        'chassis_name': 'sw1.test.switch',
                        'rid': '1',
                        'port_descr': 'Ethernet122/1/2'
                        }
                    },
            'eth0':
                {'lldp_stats':
                    {'vlan_vlan-id': '101',
                        'vlan_pvid': 'yes',
                        'via': 'LLDP',
                        'chassis_mgmt-ip': '11.111.111.11',
                        'age': '30 days, 06:05:28',
                        'chassis_descr': 'Cisco Nexus Operating System (NX-OS) Software',
                        'chassis_mac': 'yy:yy:yy:yy:yy:yy',
                        'chassis_Bridge_enabled': 'on',
                        'port_local': 'Eth122/1/2',
                        'chassis_name': 'sw2.test.switch',
                        'rid': '5', 'port_descr': 'Ethernet122/1/2'
                }
            }
        }

        self.mock_os_popen.return_value = StringIO(lldp_entry_content)
        result = self.collector.get_link_stat(ifc_stats)
        self.assertDictEqual(expected_output, result)

    def test_rules_1(self):
        """ test rules no.1 - failure match on rule eth1_on_sdr2 """

        self.setUp(custom_config={
            'rules': ['eth0_on_sw1', 'eth1_on_sw2'],
            'eth0_on_sw1' : ['eth0', 'chassis_name', 'sw1.test.switch'],
            'eth1_on_sw2' : [ 'eth1', 'chassis_name', 'sw2.test.switch']
        })

        self.collector.publish_data = {}
        ifc_list = {'eth0':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw1.test.switch'
                            }
                        },
                    'eth1':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw3.test.switch'
                            }
                        }
                    }

        rules = self.collector.config['rules']
        self.collector.check_given_rules(ifc_list, rules)
        self.assertTrue(self.collector.publish_data['rules']['eth1_on_sw2'])

    def test_rules_2(self):
        """ test rules no.2 - all matches are correct """

        self.setUp(custom_config={
            'rules': ['eth0_on_sw1', 'eth1_on_sw2'],
            'eth0_on_sw1' : ['eth0', 'chassis_name', 'sw1.test.switch'],
            'eth1_on_sw2' : [ 'eth1', 'chassis_name', 'sw2.test.switch']
        })

        self.collector.publish_data = {}
        ifc_list = {'eth0':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw1.test.switch'
                            }
                        },
                    'eth1':
                        {'lldp_stats':
                            {
                                'chassis_name': 'sw2.test.switch'
                            }
                        }
                    }

        #call a bonding collector check_bonding_match func
        rules = self.collector.config['rules']
        self.collector.check_given_rules(ifc_list, rules)

        #check if it NOT raises a mismatch_bond
        self.assertFalse(self.collector.publish_data['rules']['eth0_on_sw1'])
        self.assertFalse(self.collector.publish_data['rules']['eth1_on_sw2'])

if __name__ == "__main__":
    unittest.main()
