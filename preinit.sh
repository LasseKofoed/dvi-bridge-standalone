#!/bin/sh

mount -o remount,rw /

assert_systemctl_watchdog() {
    if ! command -v -- "systemctl" > /dev/null 2>&1; then
        exit 255
    fi

    systemctl daemon-reload
    SOUT=$(systemctl is-active --quiet dvi_watchdog)
    SRES=$?

    if [ $SRES -ne 0 ]; then
      systemctl enable /home/code/dvi-net3/dvi_watchdog.service
    fi

    systemctl restart dvi_watchdog
}

if [ -f /home/code/resetserviceinstalled ]; then
    systemctl stop DVI-net3-Reset
    systemctl disable /home/code/dvi-net3/DVI-net3-Reset.service
    systemctl daemon-reload
    chmod +x __resetinit__.py
    rm /home/code/resetserviceinstalled
fi

if ! [ -f /home/code/watchdog ]; then

    systemctl enable /home/code/dvi-net3/dvi_watchdog.service
    systemctl daemon-reload
    chmod +x /home/code/dvi-net3/watchdog.sh
    systemctl start /home/code/dvi-net3/dvi_watchdog.service
    touch /home/code/watchdog
fi

assert_systemctl_watchdog

mount -o remount,ro /

touch /tmp/dvi_net_posted
