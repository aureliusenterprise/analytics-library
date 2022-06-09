# -*- coding: utf-8 -*-
"""
Created on Tue Aug 21 08:48:18 2018

@author: andre
"""

#%%
from pysnmp.hlapi import *

if __name__ == '__main__': 
    
    SNMP_HOST = '10.239.81.29'
    #SNMP_HOST = '192.168.2.10'
    SNMP_PORT = 161
    SNMP_COMMUNITY = 'public'
    
    g = bulkCmd(SnmpEngine(),
                 CommunityData(SNMP_COMMUNITY),
                 UdpTransportTarget((SNMP_HOST, 161)),
                 ContextData(),
                 3, 25,
                 #v2c.ObjectIdentifier((1, 3, 6,1,2,1,2,2,1,6))
                 ObjectType(ObjectIdentity('IF-MIB', 'ifPhysAddress')),
                 ObjectType(ObjectIdentity('RFC1213-MIB', 'ipAdEntAddr')),
                 ObjectType(ObjectIdentity('RFC1213-MIB', 'sysDescr'))
                 )
    ii = 0
    for item in g:
        print(ii)
        errorIndication, errorStatus, errorIndex, varBinds = next(g)
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                print(' = '.join([x.prettyPrint() for x in varBind]))
            ii = ii+1
            ee = str(varBind[0])        
    
    ref = '1.3.6.1.2.1.2.2.1.6' 
    ee = ref
    ii = 0
    while ii<5:# and ee[:len(ref)]==ref:
        print(ii)
        errorIndication, errorStatus, errorIndex, varBinds = next(g)
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),
                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                print(' = '.join([x.prettyPrint() for x in varBind]))
            ii = ii+1
            ee = str(varBind[0])        
    
    
#%%
from pysnmp.hlapi import *


SNMP_HOST = '10.239.81.29'
#SNMP_HOST = '192.168.2.10'
SNMP_PORT = 161
SNMP_COMMUNITY = 'public'

# add MIBs pip install pysnmp_mibs

errorIndication, errorStatus, errorIndex, varBinds = next(
    getCmd(SnmpEngine(),
           CommunityData(SNMP_COMMUNITY),
           UdpTransportTarget((SNMP_HOST, 161)),
           ContextData(),
           ObjectType(ObjectIdentity('IF-MIB', 'ifPhysAddress', 1)),
           ObjectType(ObjectIdentity('IF-MIB', 'ifOutOctets', 1)))
    )
    
if errorIndication:
    print(errorIndication)
elif errorStatus:
    print('%s at %s' % (errorStatus.prettyPrint(),
                        errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
else:
    for varBind in varBinds:
        print(' = '.join([x.prettyPrint() for x in varBind]))