collectd-iostat-python
======================

`collectd-iostat-python` is an `iostat` plugin for Collectd that allows you to
graph Linux `iostat` metrics in Graphite or other output formats that are
supported by Collectd.

This plugin (and mostly this `README`) is rewrite of the
[collectd-iostat](https://github.com/keirans/collectd-iostat) from Ruby to Python
using the
[collectd-python](http://collectd.org/documentation/manpages/collectd-python.5.shtml)
plugin.


Why?
----

Disk performance is quite crucial for most of modern server
applications, especially databases (e.g. MySQL - check out [this
slides](http://www.percona.com/live/mysql-conference-2013/sessions/monitoring-io-performance-using-iostat-and-pt-diskstats)
from Percona Live conference).

Although Collectd [provides disk statistics out of the
box](https://collectd.org/wiki/index.php/Plugin:Disk), graphing the metrics as
shown by `iostat` was found to be more useful and graphic, because `iostat`
reports usage of block devices, partitions, multipath devices and LVM volumes.

Also this plugin was rewritten in Python, because it's a preferable language for
siteops' tools on my current job, and choice of using
[collectd-python](http://collectd.org/documentation/manpages/collectd-python.5.shtml)
instead of
[collectd-exec](https://collectd.org/documentation/manpages/collectd-exec.5.shtml)
was made for performance and stability reasons.


How?
----

`collectd-iostat-python` functions by calling `iostat` with some predefined
intervals and push that data to Collectd using Collectd `python` plugin.

Collectd can be then configured to write the Collected data into many output
formats that are supported by it's write plugins, such as `graphite`, which was
the primary use case for this plugin.


Setup
-----

Deploy the Collectd Python plugin into a suitable plugin directory for your
Collectd instance.

Configure Collectd's `python` plugin to execute the `iostat` plugin using a
stanza similar to the following:


```
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
        Verbose false
        NiceNames false
        PluginName collectd_iostat_python
    </Module>
</Plugin>
```

If you need to select a subset of the devices listed by iostat you can utilize 
`DisksRegex` to write a regular expression to select the appropriate devices for your environment.
```
# Only collect data for these devices
DisksRegex "^[hs]d"
```

In large and changing environments it benefital if your device statistics maintain the same device names across reboots or reconfigurations so that historical data is not compromised. This can be achived by enabling persistent naming based on udev attributes.
Simply enable persistent naming by setting UdevNameAttr to the attribute you want to use to name your devices. A good example would be ID_SERIAL which is persistent and unique per device. To find useful attributes you can use `udevadm info /dev/<devicename>`
```
# Enable persistent device naming
UdevNameAttr "ID_SERIAL"
```

If you would like to use more legible metric names (e.g.
`requests_merged_per_second-read` instead of `rrqm_s`), you have to set
`NiceNames` to `true` and add load the custom types database (see the
`iostat_types.db` file) by adding the following into the Collectd config file:

```
# The default Collectd types database
TypesDB "/usr/share/collectd/types.db"
# The custom types database
TypesDB "/usr/share/collectd/iostat_types.db"
```

Once functioning, the `iostat` data should then be visible via your various
output plugins. Please note, that you need to restart collectd service after
plugin installation, as usual.

In the case of Graphite, Collectd should be writing data in the
`hostname_domain_tld.collectd_iostat_python.DEVICE.column-name` style namespaces.
Symbols like `/`, `-` and `%` in metric names (but not in device names) are
automatically replaced by underscores (i.e. `_`).

Please note that this plugin will take only last line of `iostat` output, so big
`Count` numbers also have no sense, but `Count` needs to be more than `1` to get
actual and not historical data. But please note that `2 * Interval * Count` should be less then 
`Collectd.INTERVAL`. Default `Collectd.INTERVAL` is 10 seconds, so default value of `Count=2` and
`Interval=2` works quite well for me.


Technical notes
---------------

For parsing `iostat` output, I'm using
[jakamkon's](https://bitbucket.org/jakamkon)
[python-iostat](https://bitbucket.org/jakamkon/python-iostat) Python module, but
as an internal part of the script instead of a separate module because of couple
of fixes I have made (using Kbytes instead of blocks, adding -N to `iostat` for
LVM endpoint resolving, migration to `subprocess` module as replacement of
deprecated `popen3`, `objectification` etc).


Compatibility
-------------

Plugin was tested on Ubuntu 12.04/14.04 (Collectd 5.2/5.3/5.4, Python 2.7) and
CentOS (Collectd 5.4 / Python 2.6). Please note that if running Python 2.6 or
older (i.e. on CentOS and its derivatives) we trying to restore `SIGCHLD` signal
handler to mitigate a known [bug](http://bugs.python.org/issue1731717) which
according to the Collectd's
[documentation](https://collectd.org/documentation/manpages/collectd-python.5.shtml#configuration)
breaks the `exec` plugin, unfortunately.


TODO
----

* Maybe some data aggregation needed (e.g. we can use some max / avg aggregation
of data across intervals instead of picking last line of `iostat` output).
* The `Disks` parameter could support regexp.


Additional reading
------------------

* [man iostat(1)](http://linux.die.net/man/1/iostat)
* [Custom Collectd Plug-ins for Linux](http://support.rightscale.com/12-Guides/RightScale_101/08-Management_Tools/Monitoring_System/Writing_custom_collectd_plugins/Custom_Collectd_Plug-ins_for_Linux)
* [python-iostat](https://bitbucket.org/jakamkon/python-iostat)
* [collectd-iostat](https://github.com/keirans/collectd-iostat)
* [Graphite @ The Architecture of Open Source Applications](http://www.aosabook.org/en/graphite.html)

License
-------

[MIT](http://mit-license.org/)


Support
-------

Please do not send me PMs in Twitter with issues. Just open an [issue](https://github.com/deniszh/collectd-iostat-python/issues) on [projects' Github](https://github.com/deniszh/collectd-iostat-python) instead and I'll respond ASAP!


Contact
-------

[Denis Zhdanov](mailto:denis.zhdanov@gmail.com)
([@deniszh](http://twitter.com/deniszh))
