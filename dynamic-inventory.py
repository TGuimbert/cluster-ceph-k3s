#!/usr/bin/env python3

from isc_dhcp_leases import Lease6, IscDhcpLeases
from collections import defaultdict
import subprocess

def mac2ipv6(mac):
    # only accept MACs separated by a colon
    parts = mac.split(":")

    # modify parts to match IPv6 value
    parts.insert(3, "ff")
    parts.insert(4, "fe")
    parts[0] = "%x" % (int(parts[0], 16) ^ 2)

    # format output
    ipv6Parts = []
    for i in range(0, len(parts), 2):
        ipv6Parts.append("".join(parts[i:i+2]))
    ipv6 = "fe80::%s" % (":".join(ipv6Parts))
    return ipv6


leases = IscDhcpLeases('/var/lib/dhcp/dhcpd6.leases')
#print(leases.get_current())
l = []
for mac in leases.get_current() :
    lease = leases.get_current().get(mac)
    #print(lease)
    ip = lease.ip 
    if not ip in l:
        output = subprocess.Popen(['ping', '-c', '1', ip ], stdout=subprocess.PIPE).communicate()[0]
        if (not "Destination unreachable" in output.decode('utf-8')) and  (not "Request timed out" in output.decode('utf-8')):
            l.append(ip)
            print(ip)
            #print(output.decode('utf-8'))
lmac = [] 
macDict = defaultdict(list)
for i in l :
    output = subprocess.run(['ndisc6', '-1',i,'lan0'],stdout=subprocess.PIPE)
    result = output.stdout.decode('utf-8')
    mac = result[91:108]
    if mac not in lmac:
        lmac.append(mac)
    macDict[mac].append(i)
for mac in lmac:
    lla = mac2ipv6(mac)
    macDict[mac].append(lla) 

#print(macDict)
import json

# writing
json.dump(macDict, open('macMap.json', 'w'))

# reading
#test = json.load(open('macMap.json'))
#for m in test:
#    print(m, ' : ', test[m])


import os

MyFile=open('inventory.ini','w')

MyFile.write("[osds]")
MyFile.write("\n")
for mac in macDict:
    ip1 = macDict[mac][0]
    ip2 = "fd17:67e7:6b1f:ffff" + macDict[mac][0][13:]
    temp = macDict[mac][-1] + "%lan0"
    #print(temp,ip1,ip2)
    os.system("ssh-keyscan -t rsa "+ temp+" >> /home/ansible/.ssh/known_hosts")
    MyFile.write(temp + " ip1="+ ip1 + " ip2=" + ip2)
    MyFile.write('\n')

MyFile.close()

print("Done")

