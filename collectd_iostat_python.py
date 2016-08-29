#!/usr/bin/env python
# coding=utf-8
#
# collectd-iostat-python
# ======================
#
# Collectd-iostat-python is an iostat plugin for collectd that allows you to
# graph Linux iostat metrics in Graphite or other output formats that are
# supported by collectd.
#
# https://github.com/powdahound/redis-collectd-plugin
#   - was used as template
# https://github.com/keirans/collectd-iostat/
#   - was used as inspiration and contains some code from
# https://bitbucket.org/jakamkon/python-iostat
#   - by Kuba Kończyk <jakamkon at users.sourceforge.net>
#

import signal
import string
import subprocess
import sys


__version__ = '0.0.3'
__author__ = 'denis.zhdanov@gmail.com'


class IOStatError(Exception):
    pass


class CmdError(IOStatError):
    pass


class ParseError(IOStatError):
    pass


class IOStat(object):
    def __init__(self, path='/usr/bin/iostat', interval=2, count=2, disks=[]):
        self.path = path
        self.interval = interval
        self.count = count
        self.disks = disks

    def parse_diskstats(self, input):
        """
        Parse iostat -d and -dx output.If there are more
        than one series of statistics, get the last one.
        By default parse statistics for all avaliable block devices.

        @type input: C{string}
        @param input: iostat output

        @type disks: list of C{string}s
        @param input: lists of block devices that
        statistics are taken for.

        @return: C{dictionary} contains per block device statistics.
        Statistics are in form of C{dictonary}.
        Main statistics:
          tps  Blk_read/s  Blk_wrtn/s  Blk_read  Blk_wrtn
        Extended staistics (available with post 2.5 kernels):
          rrqm/s  wrqm/s  r/s  w/s  rsec/s  wsec/s  rkB/s  wkB/s  avgrq-sz \
          avgqu-sz  await  svctm  %util
        See I{man iostat} for more details.
        """
        dstats = {}
        dsi = input.rfind('Device:')
        if dsi == -1:
            raise ParseError('Unknown input format: %r' % input)

        ds = input[dsi:].splitlines()
        hdr = ds.pop(0).split()[1:]

        for d in ds:
            if d:
                d = d.split()
                dev = d.pop(0)
                if (dev in self.disks) or not self.disks:
                    dstats[dev] = dict([(k, float(v)) for k, v in zip(hdr, d)])

        return dstats

    def sum_dstats(self, stats, smetrics):
        """
        Compute the summary statistics for chosen metrics.
        """
        avg = {}

        for disk, metrics in stats.iteritems():
            for mname, metric in metrics.iteritems():
                if mname not in smetrics:
                    continue
                if mname in avg:
                    avg[mname] += metric
                else:
                    avg[mname] = metric

        return avg

    def _run(self, options=None):
        """
        Run iostat command.
        """
        close_fds = 'posix' in sys.builtin_module_names
        args = '%s %s %s %s %s' % (
            self.path,
            ''.join(options),
            self.interval,
            self.count,
            ' '.join(self.disks))

        return subprocess.Popen(
            args,
            bufsize=1,
            shell=True,
            stdout=subprocess.PIPE,
            close_fds=close_fds)

    @staticmethod
    def _get_childs_data(child):
        """
        Return child's data when avaliable.
        """
        (stdout, stderr) = child.communicate()
        ecode = child.poll()

        if ecode != 0:
            raise CmdError('Command %r returned %d' % (child.cmd, ecode))

        return stdout

    def get_diskstats(self):
        """
        Get all avaliable disks statistics that we can get.
        """
        dstats = self._run(options=['-kNd'])
        extdstats = self._run(options=['-kNdx'])
        dsd = self._get_childs_data(dstats)
        edd = self._get_childs_data(extdstats)
        ds = self.parse_diskstats(dsd)
        eds = self.parse_diskstats(edd)

        for dk, dv in ds.iteritems():
            if dk in eds:
                ds[dk].update(eds[dk])

        return ds


class IOMon(object):
    def __init__(self):
        self.plugin_name = 'collectd-iostat-python'
        self.iostat_path = '/usr/bin/iostat'
        self.interval = 60.0
        self.iostat_interval = 2
        self.iostat_count = 2
        self.iostat_disks = []
        self.iostat_nice_names = False
        self.iostat_disks_regex = ''
        self.verbose_logging = False
        self.names = {
            'tps': {'t': 'transfers_per_second'},
            'Blk_read/s': {'t': 'blocks_per_second', 'ti': 'read'},
            'kB_read/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1024},
            'MB_read/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1048576},
            'Blk_wrtn/s': {'t': 'blocks_per_second', 'ti': 'write'},
            'kB_wrtn/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1024},
            'MB_wrtn/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1048576},
            'Blk_read': {'t': 'blocks', 'ti': 'read'},
            'kB_read': {'t': 'bytes', 'ti': 'read', 'm': 1024},
            'MB_read': {'t': 'bytes', 'ti': 'read', 'm': 1048576},
            'Blk_wrtn': {'t': 'blocks', 'ti': 'write'},
            'kB_wrtn': {'t': 'bytes', 'ti': 'write', 'm': 1024},
            'MB_wrtn': {'t': 'bytes', 'ti': 'write', 'm': 1048576},
            'rrqm/s': {'t': 'requests_merged_per_second', 'ti': 'read'},
            'wrqm/s': {'t': 'requests_merged_per_second', 'ti': 'write'},
            'r/s': {'t': 'per_second', 'ti': 'read'},
            'w/s': {'t': 'per_second', 'ti': 'write'},
            'rsec/s': {'t': 'sectors_per_second', 'ti': 'read'},
            'rkB/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1024},
            'rMB/s': {'t': 'bytes_per_second', 'ti': 'read', 'm': 1048576},
            'wsec/s': {'t': 'sectors_per_second', 'ti': 'write'},
            'wkB/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1024},
            'wMB/s': {'t': 'bytes_per_second', 'ti': 'write', 'm': 1048576},
            'avgrq-sz': {'t': 'avg_request_size'},
            'avgqu-sz': {'t': 'avg_request_queue'},
            'await': {'t': 'avg_wait_time'},
            'r_await': {'t': 'avg_wait_time', 'ti': 'read'},
            'w_await': {'t': 'avg_wait_time', 'ti': 'write'},
            'svctm': {'t': 'avg_service_time'},
            '%util': {'t': 'percent', 'ti': 'util'}
        }

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def configure_callback(self, conf):
        """
        Receive configuration block
        """
        for node in conf.children:
            val = str(node.values[0])

            if node.key == 'Path':
                self.iostat_path = val
            elif node.key == 'Interval':
                self.interval = float(val)
            elif node.key == 'IostatInterval':
                self.iostat_interval = int(float(val))
            elif node.key == 'Count':
                self.iostat_count = int(float(val))
            elif node.key == 'Disks':
                self.iostat_disks = val.split(',')
            elif node.key == 'NiceNames':
                self.iostat_nice_names = val in ['True', 'true']
            elif node.key == 'DisksRegex':
                self.iostat_disks_regex = val
            elif node.key == 'PluginName':
                self.plugin_name = val
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            else:
                collectd.warning(
                    '%s plugin: Unknown config key: %s.' % (
                        self.plugin_name,
                        node.key))

        self.log_verbose(
            'Configured with iostat=%s, interval=%s, count=%s, disks=%s, '
            'disks_regex=%s' % (
                self.iostat_path,
                self.iostat_interval,
                self.iostat_count,
                self.iostat_disks,
                self.iostat_disks_regex))

        collectd.register_read(self.read_callback, self.interval)

    def dispatch_value(self, plugin_instance, val_type, type_instance, value):
        """
        Dispatch a value to collectd
        """
        self.log_verbose(
            'Sending value: %s-%s.%s=%s' % (
                self.plugin_name,
                plugin_instance,
                '-'.join([val_type, type_instance]),
                value))

        val = collectd.Values()
        val.plugin = self.plugin_name
        val.plugin_instance = plugin_instance
        val.type = val_type
        if len(type_instance):
            val.type_instance = type_instance
        val.values = [value, ]
        val.meta={'0': True}
        val.dispatch()

    def read_callback(self):
        """
        Collectd read callback
        """
        self.log_verbose('Read callback called')
        iostat = IOStat(
            path=self.iostat_path,
            interval=self.iostat_interval,
            count=self.iostat_count,
            disks=self.iostat_disks)
        ds = iostat.get_diskstats()

        if not ds:
            self.log_verbose('%s plugin: No info received.' % self.plugin_name)
            return

        for disk in ds:
            for name in ds[disk]:
                if self.iostat_nice_names and name in self.names:
                    val_type = self.names[name]['t']

                    if 'ti' in self.names[name]:
                        type_instance = self.names[name]['ti']
                    else:
                        type_instance = ''

                    value = ds[disk][name]
                    if 'm' in self.names[name]:
                        value *= self.names[name]['m']
                else:
                    val_type = 'gauge'
                    tbl = string.maketrans('/-%', '___')
                    type_instance = name.translate(tbl)
                    value = ds[disk][name]

                self.dispatch_value(
                    disk, val_type, type_instance, value)


def restore_sigchld():
    """
    Restore SIGCHLD handler for python <= v2.6
    It will BREAK exec plugin!!!
    See https://github.com/deniszh/collectd-iostat-python/issues/2 for details
    """
    if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)


if __name__ == '__main__':
    iostat = IOStat()
    ds = iostat.get_diskstats()

    for disk in ds:
        for metric in ds[disk]:
            tbl = string.maketrans('/-%', '___')
            metric_name = metric.translate(tbl)
            print("%s.%s:%s" % (disk, metric_name, ds[disk][metric]))

    sys.exit(0)
else:
    import collectd

    iomon = IOMon()

    # Register callbacks
    collectd.register_init(restore_sigchld)
    collectd.register_config(iomon.configure_callback)
