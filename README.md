collectd-iostat-python
======================

Collectd-iostat-python is an iostat plugin for collectd that allows you to graph Linux iostat metrics in graphite or other output formats that are supported by collectd.

This plugin (and mostly that README) is rewrite of [kieran's|https://github.com/keirans/collectd-iostat] [collectd-iostat|https://github.com/keirans/collectd-iostat] in Python and [collectd-python|http://collectd.org/documentation/manpages/collectd-python.5.shtml] instead of Ruby and [collectd-exec|https://collectd.org/documentation/manpages/collectd-exec.5.shtml]

Why ?
-------
Disk performance is quite crucial for most of modern server applications, especially databases. E.g. MySQL - check out [this slides|http://www.percona.com/live/mysql-conference-2013/sessions/monitoring-io-performance-using-iostat-and-pt-diskstats] from Percona Live conference.

Although collectd provides disk statistics out of the box, graphing the metrics as shown by iostat was found to be more useful and graphic, because iostat reports usage of block devices, partitions, multipath devices and LVM volumes.

Also this plugin was rewritten in Python, because its a preferrable language for siteops' tools on my current job, and choice of using [collectd-python|http://collectd.org/documentation/manpages/collectd-python.5.shtml] instead of [collectd-exec|https://collectd.org/documentation/manpages/collectd-exec.5.shtml] was made for performance and stability reasons.

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
            Interval 10
            Verbose False
        </Module>
    </Plugin>

Once functioning, the iostat data should then be visible via your various output plugins.

In the case of Graphite, collectd should be writing data to graphite in the *hostname_domain_tld.collectd_iostat_python.gauge-DEVICE.column-name* style namespaceles have been included for reference to assist in setting this up, see the _rewrite-rules.conf_ file for more information.

Technical notes
-------
For parsing iostat output I'm using [jakamkon's|https://bitbucket.org/jakamkon] [python-iostat|https://bitbucket.org/jakamkon/python-iostat] python module, but as internal part of script instead of separate module.



Additional reading
-------
* [Graphite @ The Architecture of Open Source Applications](http://www.aosabook.org/en/graphite.html)

* [Custom Collectd Plug-ins for Linux](http://support.rightscale.com/12-Guides/RightScale_101/08-Management_Tools/Monitoring_System/Writing_custom_collectd_plugins/Custom_Collectd_Plug-ins_for_Linux)

* [python-iostat|https://bitbucket.org/jakamkon/python-iostat]

* [collectd-iostat|https://github.com/keirans/collectd-iostat]

Contact
-------
[@deniszh](http://twitter.com/deniszh) || [Email - Denis Zhdanov](mailto:denis.zhdanov@gmail.com)