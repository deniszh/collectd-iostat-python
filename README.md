collectd-iostat-python
======================

Collectd-iostat-python is an iostat plugin for collectd that allows you to graph Linux iostat metrics in graphite or other output formats that are supported by collectd.

This plugin (and mostly this README) is rewrite of [kieran's](https://github.com/keirans/collectd-iostat) [collectd-iostat](https://github.com/keirans/collectd-iostat) in Python and [collectd-python](http://collectd.org/documentation/manpages/collectd-python.5.shtml) instead of Ruby and [collectd-exec](https://collectd.org/documentation/manpages/collectd-exec.5.shtml)

Why ?
-------
Disk performance is quite crucial for most of modern server applications, especially databases. E.g. MySQL - check out [this slides](http://www.percona.com/live/mysql-conference-2013/sessions/monitoring-io-performance-using-iostat-and-pt-diskstats) from Percona Live conference.

Although collectd [provides disk statistics out of the box](https://collectd.org/wiki/index.php/Plugin:Disk), graphing the metrics as shown by iostat was found to be more useful and graphic, because iostat reports usage of block devices, partitions, multipath devices and LVM volumes.

Also this plugin was rewritten in Python, because its a preferable language for siteops' tools on my current job, and choice of using [collectd-python](http://collectd.org/documentation/manpages/collectd-python.5.shtml) instead of [collectd-exec](https://collectd.org/documentation/manpages/collectd-exec.5.shtml) was made for performance and stability reasons.

How ?
-------
Collectd-iostat-python functions by calling iostat with some predefined intervals and push that data to collectd using collectd-python plugin.

Collectd can be then configured to write the collected data into many output formats that are supported by it's write plugins, such as graphite, which was the primary use case for this plugin.


Setup
-------
Deploy the collectd python plugin into a suitable plugin directory for your collectd instance.

Configure collectd's python plugin to execute the iostat plugin using a stanza similar to the following:


    <LoadPlugin python>
        Globals true
    </LoadPlugin>

    <Plugin python>
        ModulePath "/usr/lib/collectd/plugins/python"
        Import "collectd_iostat_python"

        <Module collectd_iostat_python>
            Path "/usr/bin/iostat"
            Interval 2
            Count 2
            Verbose False
        </Module>
    </Plugin>

Once functioning, the iostat data should then be visible via your various output plugins.

In the case of Graphite, collectd should be writing data to graphite in the *hostname_domain_tld.collectd_iostat_python.DEVICE.column-name* style namespaces.
Symbols like '/','-' and '%' in metric names (but not in device names) automatically replacing by underscores (i.e. '_')
 
Please note that plugin will take only last line of iostat output, so big Count numbers also have no sense, but Count needs to be more than 1 to get actual and not historical data. And please make Interval * Count << Collectd.INTERVAL (20 seconds by default). I found e.g. Count=2 and Interval=2 works quite well for me.


Technical notes
-------
For parsing iostat output I'm using [jakamkon's](https://bitbucket.org/jakamkon) [python-iostat](https://bitbucket.org/jakamkon/python-iostat) python module, but as internal part of script instead of separate module because of couple of fixes - using Kbytes instead of blocks, adding -N to iostat for LVM endpoint resolving, migration to subprocess module as replacement of deprecated popen3, objectification etc.


Compatibility
-------
Plugin was tested to Ubuntu 12.04/14.04 (collectd 5.2/5.3/5.4, python 2.7) and CentOS (collectd 5.4 / python 2.6). Please note that if running python 2.6 or older (i.e. on CentOS and its derivatives) we trying to restore SIGCHLD signal handler to mitigate [this bug](http://bugs.python.org/issue1731717) and according to (collectd documentation)[https://collectd.org/documentation/manpages/collectd-python.5.shtml#configuration] it will break collectd exec plugin, unfortunately.



TODO
-------
Maybe some data aggregation needed, e.g. we can use some max / avg aggregation of data across intervals instead of picking last line of iostat output.


Additional reading
-------
* [man iostat(1)](http://linux.die.net/man/1/iostat)

* [Custom Collectd Plug-ins for Linux](http://support.rightscale.com/12-Guides/RightScale_101/08-Management_Tools/Monitoring_System/Writing_custom_collectd_plugins/Custom_Collectd_Plug-ins_for_Linux)

* [python-iostat](https://bitbucket.org/jakamkon/python-iostat)

* [collectd-iostat](https://github.com/keirans/collectd-iostat)

* [Graphite @ The Architecture of Open Source Applications](http://www.aosabook.org/en/graphite.html)

Contact
-------
[@deniszh](http://twitter.com/deniszh) || [Email - Denis Zhdanov](mailto:denis.zhdanov@gmail.com)
