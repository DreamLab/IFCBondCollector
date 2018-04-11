import logging
import datetime
import os
import re
from diamond.collector import Collector


class IFCBondCollector(Collector):

    REGEX_AGE = re.compile('(\d+)\s[^ ]+\s(\d+):(\d+):(\d+)')

    def get_default_config_help(self):
        config_help = super(IFCBondCollector, self).get_default_config_help()
        config_help.update({
            'bond_name': 'Bond interface to monitor',
            'rules': 'matching rules between interfaces and switches'
        })

        return config_help

    def get_default_config(self):
        config = super(IFCBondCollector, self).get_default_config()
        config.update({
            'bond_name': "bond0",
            'rules': [],
        })

        return config

    def parse_bond_status(self, stat):
        """ parsing data from  bond0 stats """

        stat_list = stat.split('\n')
        ifc_list = {}
        master_status = {}
        pos_newln = stat_list.index('')

        while len(stat_list) > 0:

            parsed_settings = {v.split(':')[0]: ''.join(v.split(':')[1:]).strip() for v in stat_list[0:(pos_newln)]}
            stat_list = stat_list[pos_newln + 1:]
            if len(parsed_settings) == 0:
                continue
            elif parsed_settings.get('Slave Interface'):
                parsed_settings.setdefault('lldp_stats', {})
                parsed_settings['active'] = False
                ifc_list[parsed_settings.get('Slave Interface')] = parsed_settings
            elif parsed_settings.get('Primary Slave'):
                master_status = parsed_settings
            if '' not in stat_list:
                continue
            pos_newln = stat_list.index('')

        if master_status.get('Currently Active Slave') in ifc_list.keys():
            ifc_list[master_status['Currently Active Slave']]['active'] = True

        return (master_status, ifc_list)

    def get_link_stat(self, ifc_list):
        """ get lldpctl information """

        cli_command = "sudo lldpctl -f keyvalue"
        link_stat_list = os.popen(cli_command).read().split('\n')

        stat_list = {}
        tmp_list = {}

        self.publish_data = {"ifc": {}}

        for link_stat in link_stat_list:
            if not link_stat.startswith('lldp'):
                continue

            key, val = link_stat.split('=')
            key = key.split('.', 2)
            key[2] = key[2].replace('.', '_')

            ifc_name = key[1]
            lldp_stat = key[-1]

            if ifc_name in stat_list.keys():
                if ifc_name not in tmp_list.keys():
                    tmp_list[ifc_name] = {}

                if lldp_stat in stat_list[ifc_name]:
                    tmp_list[ifc_name][lldp_stat] = val

                    if lldp_stat == 'age' and lldp_stat in stat_list[ifc_name]:
                        days, hours, minutes, seconds = self.REGEX_AGE.match(val).groups()
                        tmp_delta = datetime.timedelta(
                            days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds)
                        )

                        days, hours, minutes, seconds = self.REGEX_AGE.match(stat_list[ifc_name][lldp_stat]).groups()
                        stat_delta = datetime.timedelta(
                            days=int(days), hours=int(hours), minutes=int(minutes), seconds=int(seconds)
                        )

                        if int(tmp_delta.total_seconds()) < int(stat_delta.total_seconds()):
                            stat_list[ifc_name] = tmp_list[ifc_name]
                        else:
                            continue
                else:
                    stat_list[ifc_name][lldp_stat] = val
            else:
                stat_list[ifc_name] = {lldp_stat: val}

        # check for only available interfaces
        for ifc_name in ifc_list.keys():
            ifc_list[ifc_name]['lldp_stats'] = stat_list.get(ifc_name, {})

        # collecting data to publish
        for ifc_name in ifc_list.keys():
            self.publish_data["ifc"].setdefault(ifc_name, {})
            self.publish_data["ifc"][ifc_name]['Status'] = ifc_list.get(ifc_name).get('MII Status') == 'up'
            self.publish_data["ifc"][ifc_name]['Link Failure Count'] = ifc_list.get(ifc_name).get('Link Failure Count')
            self.publish_data["ifc"][ifc_name]['Active'] = ifc_list.get(ifc_name).get('active')
            self.publish_data["ifc"][ifc_name]['lldp_stats_unavailable'] = len(ifc_list.get(ifc_name).get('lldp_stats')) < 1

        return (ifc_list)

    def check_given_rules(self, ifc_list, rules):
        """ compare parameters from ifcbondingcollector.conf with parsed data in lldpctl """

        if rules:
            self.publish_data.setdefault('rules', {})
            for rule_name in rules:
                ifc_name = self.config.get(rule_name)[0]
                chk_param = self.config.get(rule_name)[1]
                val_param = self.config.get(rule_name)[2]

                val_param_match = val_param == ifc_list.get(ifc_name, {}).get('lldp_stats', {}).get(chk_param, {})
                chk_rule = ifc_name not in ifc_list.keys() or not val_param_match
                self.publish_data['rules'][rule_name] = chk_rule

    def check_bonding_match(self, ifc_list):
        """ validation connection to switches """

        dev_list = []
        self.publish_data.setdefault('mismatch_bond', {})

        for ifc_name in ifc_list.keys():
            dev_list.append(ifc_list.get(ifc_name, {}).get('lldp_stats', {}).get('chassis_name', {}))

        self.publish_data['mismatch_bond'] = dev_list[1:] == dev_list[:-1]

    def _publish(self, name, value):
        self.publish(name, value)
        logging.critical('%s %s', name, value)

    def reporting_data(self):
        """ reporting collected data to maas """

        for publish_key in self.publish_data.get('ifc', {}):
            self._publish(
                '{}.status'.format(publish_key),
                self.publish_data.get('ifc').get(publish_key).get('Status')
            )
            self._publish(
                '{}.link_failure_count'.format(publish_key),
                self.publish_data.get('ifc').get(publish_key).get('Link Failure Count')
            )
            self._publish(
                '{}.active'.format(publish_key),
                self.publish_data.get('ifc').get(publish_key).get('Active')
            )
            self._publish(
                '{}.lldp_stats_unavailable'.format(publish_key),
                self.publish_data.get('ifc').get(publish_key).get('lldp_stats_unavailable')
            )

        for publish_key in self.publish_data.get('rules', {}):
            self._publish(
                'mismatch.{}'.format(publish_key),
                self.publish_data.get('rules').get(publish_key)
            )

        self._publish('mismatch.bond', self.publish_data.get('mismatch_bond'))

    def get_bond_dev(self):
        """ get bonding information from /proc/net/bonding/bond0 stats """

        bonddev = self.config.get('bond_name')
        bondpath = "/proc/net/bonding/"
        bstat = ""
        with open("{}{}".format(bondpath, bonddev, 'r')) as proc_f:
            bstat = proc_f.read()

        return bstat

    def collect(self):

        bstat = self.get_bond_dev()

        self.publish_data = {}
        master_stats, slaves_stats = self.parse_bond_status(bstat)
        slaves = self.get_link_stat(slaves_stats)

        rules = self.config.get('rules')
        self.check_given_rules(slaves, rules)
        self.check_bonding_match(slaves)

        self.reporting_data()


if __name__ == '__main__':
    ifcbond = IFCBondCollector()
    ifcbond.collect()
