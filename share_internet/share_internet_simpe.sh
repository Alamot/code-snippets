#!/bin/bash
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 WAN_interface LAN_interface" >&2
  exit 1
fi
WAN="$1"
LAN="$2"
echo Trying to share $WAN internet connection with $LAN ...
# Kill previous dnsmasq to avoid conflicts
sudo killall dnsmasq
# Set the IP of our would-be LAN gateway 
sudo ifconfig $LAN down
sudo ifconfig $LAN 10.0.0.1 netmask 255.255.255.0 broadcast 10.0.0.255
sudo ifconfig $LAN up
# Or using the ip command
# ip link set $LAN down
# ip addr add 10.0.0.1/24 broadcast 10.0.0.255 dev $LAN
# ip link set $LAN up

# Inform the kernel that IP forwarding is OK:
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward > /dev/null
for f in /proc/sys/net/ipv4/conf/*/rp_filter ; do echo 1 | sudo tee $f > /dev/null; done
echo 1 | sudo tee /proc/sys/net/ipv4/ip_dynaddr > /dev/null

# Flush the current ΝΑΤ rules:
sudo iptables -t nat -F
sudo iptables -t nat -X

# Accept traffic via ports 67 (dhcp) and 53 (dns) from LAN
sudo iptables -I INPUT -i $LAN -j ACCEPT
sudo iptables -I INPUT -p udp --dport 67 -i $LAN -j ACCEPT
sudo iptables -I INPUT -p udp --dport 53 -i $LAN -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 53 -i $LAN -j ACCEPT

# Add the rules for NAT:
sudo iptables -t nat -A POSTROUTING -o $WAN -j MASQUERADE
sudo iptables -A FORWARD -i $LAN -o $WAN -j ACCEPT
sudo iptables -A FORWARD -i $WAN -o $LAN -m state --state RELATED,ESTABLISHED -j ACCEPT

# dnsmasq provides the dhcp and dns servers
sudo dnsmasq -i $LAN --dhcp-range=$LAN,10.0.0.100,10.0.0.250,72h
echo Internet connection sharing is READY.
