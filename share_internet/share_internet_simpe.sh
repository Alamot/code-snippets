#!/bin/bash
WAN="$1"
LAN="$2"
echo Sharing $WAN connection with $LAN
killall dnsmasq
ifconfig $LAN down
ifconfig $LAN 10.0.0.1 netmask 255.255.255.0
ifconfig $LAN up
# Inform the kernel that IP forwarding is OK:
echo 1 > /proc/sys/net/ipv4/ip_forward
for f in /proc/sys/net/ipv4/conf/*/rp_filter ; do echo 1 > $f ; done
echo 1 > /proc/sys/net/ipv4/ip_dynaddr
# Flush the current ΝΑΤ rules:
iptables -t nat -F
iptables -t nat -X
# Accept ports 67 (dhcp) and 53 (dns)
iptables -I INPUT -i $LAN -j ACCEPT
iptables -I INPUT -p udp --dport 67 -i $LAN -j ACCEPT
iptables -I INPUT -p udp --dport 53 -i $LAN -j ACCEPT
iptables -I INPUT -p tcp --dport 53 -i $LAN -j ACCEPT
# Add the rules for NAT:
iptables -t nat -A POSTROUTING -o $WAN -j MASQUERADE
iptables -A FORWARD -i $LAN -o $WAN -j ACCEPT
iptables -A FORWARD -i $WAN -o $LAN -m state --state RELATED,ESTABLISHED -j ACCEPT
# dnsmasq provides the dhcp and dns servers
dnsmasq -i $LAN --dhcp-range=$LAN,10.0.0.100,10.0.0.250,72h
