#!/usr/bin/env python
# coding=utf-8
#
#  collectd-iostat-python
# ========================
#
# Collectd-iostat-python is an iostat plugin for collectd that allows you to graph Linux iostat metrics in Graphite
# or other output formats that are supported by collectd.
#
# https://github.com/powdahound/redis-collectd-plugin - was used as template
# https://github.com/keirans/collectd-iostat/ - was used as inspiration
# contains some code from
# https://bitbucket.org/jakamkon/python-iostat by Kuba Kończyk <jakamkon at users.sourceforge.net>
#

__version__ = '0.0.1'
__author__ = 'denis.zhdanov@gmail.com'

import sys
import subprocess

class IOStatError(Exception):
    pass

class CmdError(IOStatError):
    pass

class ParseError(IOStatError):
    pass

class IOStat(object):

    def __init__(self, path='/usr/bin/iostat', interval=1, count=10, disks=None):
        self.path = path
        self.interval = interval
        self.count = count
        if disks:
            self.disks = disks
        else:
            self.disks = []

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
        tps   Blk_read/s   Blk_wrtn/s   Blk_read   Blk_wrtn
        Extended staistics (available with post 2.5 kernels):
        rrqm/s wrqm/s   r/s   w/s  rsec/s  wsec/s    rkB/s    wkB/s avgrq-sz avgqu-sz   await  svctm  %util
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
        args = '%s %s %s %s %s' % (self.path, ''.join(options), self.interval, self.count, ' '.join(self.disks))
        return subprocess.Popen(args, bufsize=1, shell=True, stdout=subprocess.PIPE, close_fds=close_fds)

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
        self.iostat_interval = 2
        self.iostat_count = 2
        self.iostat_disks = []
        self.verbose_logging = False

    def log_verbose(self, msg):
        if not self.verbose_logging:
            return
        collectd.info('collectd-iostat-python plugin [verbose]: %s' % msg)

    def configure_callback(self, conf):
        """
        Receive configuration block
        """
        for node in conf.children:
            if node.key == 'Path':
                self.iostat_path = node.values[0]
            elif node.key == 'Interval':
                self.iostat_interval = int(node.values[0])
            elif node.key == 'Count':
                self.iostat_count = int(node.values[0])
            elif node.key == 'Disks':
                self.iostat_disks = str(node.values[0]).split(',')
            elif node.key == 'Verbose':
                self.verbose_logging = bool(node.values[0])
            else:
                collectd.warning('collectd-iostat-python plugin: Unknown config key: %s.' % node.key)
        self.log_verbose('Configured with iostat=%s, interval=%s, count=%s, disks=%s' %
                         (self.iostat_path, self.iostat_interval, self.iostat_count, self.iostat_disks))

    def dispatch_value(self, plugin_instance, value_type, instance, value):
        """
        Dispatch a value to collectd
        """
        self.log_verbose('Sending value: %s.%s.%s=%s' % (self.plugin_name, plugin_instance, instance, value))
        val = collectd.Values()
        val.plugin = self.plugin_name
        val.plugin_instance = plugin_instance
        val.type = value_type
        val.type_instance = instance
        val.values = [value, ]
        val.dispatch()

    def read_callback(self):
        """
        Collectd read callback
        """
        self.log_verbose('Read callback called')
        iostat = IOStat(path=self.iostat_path, interval=self.iostat_interval,
                count=self.iostat_count, disks=self.iostat_disks)
        ds = iostat.get_diskstats()
        if not ds:
            self.log_verbose('collectd-iostat-python plugin: No info received.')
            return
        for disk in ds.keys():
            for metric in ds[disk]:
                metric_name = metric.replace('/', '_').replace('-', '_').replace('%', '_')
                self.dispatch_value(disk, 'gauge', metric_name, ds[disk][metric])

if __name__ == '__main__':
    iostat = IOStat(interval=2, count=2)
    ds = iostat.get_diskstats()
    for disk in ds.keys():
        for metric in ds[disk]:
            metric_name = metric.replace('/', '_').replace('-', '_').replace('%', '_')
            print "%s.%s:%s" % (disk, metric_name, ds[disk][metric])
    sys.exit(0)
else:
    import collectd
    iomon = IOMon()
    # register callbacks
    collectd.register_config(iomon.configure_callback)
    collectd.register_read(iomon.read_callback)
