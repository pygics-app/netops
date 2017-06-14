# -*- coding: utf-8 -*-
'''
Created on 2017. 6. 10.
@author: HyechurnJang
'''

import os
import re
import pygics
from grammar import *
from page import *
from model import *

class NetOper(pygics.__PYGICS__):
    
    def __init__(self, base_dir):
        self.pid = base_dir + '/netoper.pid'
        self.conf = base_dir + '/netoper.conf'
        self.d_dhcp = base_dir + '/dhcp'
        self.r_dhcp = self.d_dhcp + '/range.conf'
        self.h_dhcp = self.d_dhcp + '/host.conf'
        self.r_dns = base_dir + '/resolv.dns'
        self.h_dns = base_dir + '/host.dns'
    
    def __release__(self):
        self.stop()
    
    def start(self):
        cmd = '/usr/sbin/dnsmasq --user=root --group=root -h -x %s -C %s -7 %s -r %s -H %s' % (self.pid, self.conf, self.d_dhcp, self.r_dns, self.h_dns)
        print('NetOper Start : %s' % 'ok' if os.system(cmd) == 0 else 'failed')
        return self
    
    def stop(self):
        cmd = 'kill -9 `cat %s`; rm -rf %s' % (self.pid, self.pid)
        print('NetOper Stop : %s' % 'ok' if os.system(cmd) == 0 else 'failed')
        return self
    
    def reload(self):
        self.stop()
        self.start()
        return self

no = NetOper(PWD() + '/native').reload()
   
#===============================================================================
# Internal APIs
#===============================================================================
def getEnv():
    try: return Environment.list().one()
    except: return Environment().create()
    
def setEnv(domain='', network='', netmask='', gateway='', dns_int='', dns_ext=''):
    kv = re.match('^\s*(?P<domain>[\w\d\-]+)\s*$', domain)
    domain = kv.group('domain').lower() if kv != None else ''
    network = isIP(network)
    netmask = isIP(netmask)
    gateway = isIP(gateway)
    dns_int = isIP(dns_int)
    dns_ext = isIP(dns_ext)
    
    env = getEnv()
    if domain: env.domain = domain
    if network: env.network = network
    if netmask: env.netmask = netmask
    if gateway: env.gateway = gateway
    if dns_int: env.dns_int = dns_int
    if dns_ext: env.dns_ext = dns_ext
    return env.update()

def commitEnv():
    env = getEnv()
    rng = getRange()
    hosts = getHosts()
    with open(no.conf, 'w') as fd:
        if env.netmask != '':
            fd.write('dhcp-option=1,%s\n' % env.netmask)
        if env.gateway != '':
            fd.write('dhcp-option=3,%s\n' % env.gateway)
        if env.dns_int != '':
            fd.write('dhcp-option=6,%s\n' % env.dns_int)
    with open(no.r_dns, 'w') as fd:
        if env.dns_ext != '':
            fd.write('nameserver\t%s\n' % env.dns_ext)
    with open(no.r_dhcp, 'w') as fd:
        if env.netmask != '' and rng.ip_stt != '' and rng.ip_end != '' and rng.ip_lease_num != '' and rng.ip_lease_tag != '':
            fd.write('dhcp-range=%s,%s,%s,%s%s\n' % (rng.ip_stt, rng.ip_end, env.netmask, rng.ip_lease_num, rng.ip_lease_tag))
    with open(no.h_dns, 'w') as dns:
        for host in hosts:
            if env.domain != '' and host.name != '' and host.ip != '':
                dns.write('%s\t%s.%s.%s\n' % (host.ip, host.name, host.model, env.domain))
    no.reload()
    return env

def getRange():
    try: return Range.list().one()
    except: return Range().create()

_range_ip_lease_tag = ['seconds', 'minutes', 'hours']
def setRange(ip_stt='', ip_end='', ip_lease_num='', ip_lease_tag=''):
    ip_stt = isIP(ip_stt)
    ip_end = isIP(ip_end)
    kv = re.match('^\s*(?P<val>\d+)\s*$', ip_lease_num)
    ip_lease_num = kv.group('val') if kv != None else None
    ip_lease_tag = ip_lease_tag if ip_lease_tag in _range_ip_lease_tag else None
    
    rng = getRange()
    if ip_stt and ip_end and ip_lease_num and ip_lease_tag:
        rng.ip_stt = ip_stt
        rng.ip_end = ip_end
        rng.ip_lease_num = ip_lease_num
        rng.ip_lease_tag = ip_lease_tag
        rng.update()
    return rng

def commitRange():
    env = getEnv()
    rng = getRange()
    with open(no.r_dhcp, 'w') as fd:
        if env.netmask != '' and rng.ip_stt != '' and rng.ip_end != '' and rng.ip_lease_num != '' and rng.ip_lease_tag != '':
            fd.write('dhcp-range=%s,%s,%s,%s%s\n' % (rng.ip_stt, rng.ip_end, env.netmask, rng.ip_lease_num, rng.ip_lease_tag[0]))
    no.reload()
    return rng

def getHosts():
    return Host.list()

_host_models = ['Host', 'Nexus', 'Catalyst', 'ASA', 'UCS', 'VM']
def setHost(name='', mac='', ip='', model='', serial=''):
    kv = re.match('^\s*(?P<name>[\w\d\-]+)\s*$', name)
    name = kv.group('name').lower() if kv != None else ''
    mac = isMAC(mac)
    ip = isIP(ip)
    model = model.lower() if model in _host_models else 'unknown'
    kv = re.match('^\s*(?P<serial>[\w\d\-]+)\s*$', serial)
    serial = kv.group('serial') if kv != None else ''
    
    if mac and ip:
        host = Host.list().filter(Host.mac==mac).filter(Host.ip==ip)
        if host.count():
            host = host.one()
            host.name = name
            host.model = model
            host.serial = serial
            return host.update()
        else:
            return Host(name, mac, ip, model, serial).create()
    return None

def delHost(mac='', ip=''):
    mac = isMAC(mac)
    ip = isIP(ip)
    
    if mac and ip:
        try: Host.list().filter(Host.mac==mac).filter(Host.ip==ip).one().delete()
        except: return False
        return True
    return False

def commitHost():
    env = getEnv()
    hosts = getHosts()
    
    with open(no.h_dhcp, 'w') as dhcp, open(no.h_dns, 'w') as dns:
        for host in hosts:
            if host.mac != '' and host.ip != '' and host.ip != '0.0.0.0':
                dhcp.write('dhcp-host=%s,%s\n' % (host.mac, host.ip))
            if env.domain != '' and host.name != '':
                dns.write('%s\t%s.%s.%s\n' % (host.ip, host.name, host.model, env.domain))
    no.reload()
    return hosts

#===============================================================================
# REST APIs
#===============================================================================
@pygics.api('GET', '/api/env')
def api_getEnv(req):
    env = getEnv()
    return {'domain' : env.domain,
            'network' : env.network,
            'netmask' : env.netmask,
            'gateway' : env.gateway,
            'dns_internal' : env.dns_int,
            'dns_external' : env.dns_ext}

@pygics.api('POST', '/api/env')
def api_setEnv(req):
    setEnv(**req.data)
    env = commitEnv()
    return {'domain' : env.domain,
            'network' : env.network,
            'netmask' : env.netmask,
            'gateway' : env.gateway,
            'dns_internal' : env.dns_int,
            'dns_external' : env.dns_ext}

@pygics.api('GET', '/api/range')
def api_getRange(req):
    rng = getRange()
    return {'start' : rng.ip_stt,
            'end' : rng.ip_end,
            'lease_time' : '%s%s' % (rng.ip_lease_num, rng.ip_lease_tag)}

@pygics.api('POST', '/api/range')
def api_setRange(req):
    setRange(**req.data)
    rng = commitRange()
    return {'start' : rng.ip_stt,
            'end' : rng.ip_end,
            'lease_time' : '%s%s' % (rng.ip_lease_num, rng.ip_lease_tag)}

@pygics.api('GET', '/api/host')
def api_getHosts(req, macip=None):
    if macip:
        mac = isMAC(macip)
        ip = isIP(macip)
        if mac:
            try: host = Host.list().filter(Host.mac==mac).one()
            except: raise Exception('could not find host %s' % mac)
        elif ip:
            try: host = Host.list().filter(Host.mac==mac).one()
            except: raise Exception('could not find host %s' % mac)
        return {'name' : host.name,
                'mac' : host.mac,
                'ip' : host.ip,
                'model' : host.model,
                'serial' : host.serial}
    hosts = getHosts()
    ret = []
    for host in hosts:
        ret.append({'name' : host.name,
                    'mac' : host.mac,
                    'ip' : host.ip,
                    'model' : host.model,
                    'serial' : host.serial})
    return ret

@pygics.api('POST', '/api/host')
def api_setHost(req):
    host = setHost(**req.data)
    if host:
        commitHost()
        return {'name' : host.name,
                'mac' : host.mac,
                'ip' : host.ip,
                'model' : host.model,
                'serial' : host.serial}
    raise Exception('could not create host')

@pygics.api('DELETE', '/api/host')
def api_delHost(req, mac='', ip=''):
    ret = delHost(mac, ip)
    if ret: commitHost()
    return ret

#===============================================================================
# Page
#===============================================================================
netoper = PAGE(resource='resource', template=PAGE.TEMPLATE.SIMPLE_DK)

@PAGE.MAIN(netoper, 'DHCP & DNS')
def dnsmasq_main_page(req):
    return 'DHCP & DNS'

@PAGE.MENU(netoper, 'DHCP', 'id-card')
def dhcp_setting(req):
    return DIV().html(
        HEAD(1).html('DHCP Setting'),
        ROW().html(
            COL(6, 'xs', STYLE='min-width:390px;').html(
                netoper.patch('dhcp_environment_setting'),
            ),
            COL(6, 'xs', STYLE='min-width:390px;').html(
                netoper.patch('dhcp_range_setting')
            )
        )
    )
    
@PAGE.VIEW(netoper)
def dhcp_environment_setting(req):
    
    if req.method == 'POST':
        setEnv(**req.data)
        commitEnv()
    
    env = getEnv()
    
    global_context = CONTEXT().TEXT(
        'domain', CONTEXT.LABEL_TOP('Domain Name'), env.domain
    ).TEXT(
        'network', CONTEXT.LABEL_TOP('Network'), env.network,
        STYLE='width:50%;float:left;padding-right:5px;'
    ).TEXT(
        'netmask', CONTEXT.LABEL_TOP('Network Mask'), env.netmask,
        STYLE='width:50%;float:right;padding-left:5px;'
    ).TEXT(
        'gateway', CONTEXT.LABEL_TOP('Gateway'), env.gateway
    ).TEXT(
        'dns_int', CONTEXT.LABEL_TOP('Internal DNS Server'), env.dns_int,
        STYLE='width:50%;float:left;padding-right:5px;'
    ).TEXT(
        'dns_ext', CONTEXT.LABEL_TOP('External DNS Server'), env.dns_ext,
        STYLE='width:50%;float:right;padding-left:5px;'
    )
        
    return DIV().html(
        HEAD(2, STYLE='float:left;').html('Environment'),
        netoper.context(
            BUTTON(CLASS='btn-primary', STYLE='height:33px;').html('Save'),
            global_context,
            'dhcp_environment_setting',
            STYLE='float:right;margin:20px 0px 10px 20px;'
        ),
        global_context,
    )

@PAGE.VIEW(netoper)
def dhcp_range_setting(req):
    
    if req.method == 'POST':
        setRange(**req.data)
        commitRange()
    
    rng = getRange()
    
    tag_prio = []
    for tag in _range_ip_lease_tag: tag_prio.append(tag)
    if rng.ip_lease_tag != '':
        tag_prio.remove(rng.ip_lease_tag)
        tag_prio.insert(0, rng.ip_lease_tag)
    
    range_context = CONTEXT().TEXT(
        'ip_stt', CONTEXT.LABEL_TOP('DHCP Range Start'), rng.ip_stt
    ).TEXT(
        'ip_end', CONTEXT.LABEL_TOP('DHCP Range End'), rng.ip_end
    ).TEXT(
        'ip_lease_num', CONTEXT.LABEL_TOP('IP Lease Time'), rng.ip_lease_num,
        STYLE='width:70%;float:left;padding-right:5px;'
    ).SELECT(
        'ip_lease_tag', CONTEXT.LABEL_TOP('', STYLE='width:100%;height:15px;'), *tag_prio,
        STYLE='width:30%;float:right;padding-left:5px;'
    )
        
    return DIV().html(
        HEAD(2, STYLE='float:left;').html('Range'),
        netoper.context(
            BUTTON(CLASS='btn-primary', STYLE='height:33px;').html('Save'),
            range_context,
            'dhcp_range_setting',
            STYLE='float:right;margin:20px 0px 10px 20px;'
        ),
        range_context,
    )

@PAGE.MENU(netoper, 'Host', 'id-card')
def host_setting(req):
    
    return DIV().html(
        HEAD(1).html('Host Setting'),
        netoper.patch('host_context'),
    )

@PAGE.VIEW(netoper)
def host_context(req):
    
    if req.method == 'POST':
        host = setHost(**req.data)
        if host: commitHost()
    
    host_context = CONTEXT().TEXT(
        'name', CONTEXT.LABEL_TOP('Host Name'),
    ).TEXT(
        'mac', CONTEXT.LABEL_TOP('MAC Address'),
        STYLE='width:50%;float:left;padding-right:5px;'
    ).TEXT(
        'ip', CONTEXT.LABEL_TOP('IP Address'),
        STYLE='width:50%;float:right;padding-left:5px;'
    ).SELECT(
        'model', CONTEXT.LABEL_TOP('Model'), 'Host', 'Nexus', 'Catalyst', 'ASA', 'UCS', 'VM',
        STYLE='width:50%;float:left;padding-right:5px;'
    ).TEXT(
        'serial', CONTEXT.LABEL_TOP('Serial'), 
        STYLE='width:50%;float:right;padding-left:5px;'
    )

    return DIV().html(
        HEAD(2, STYLE='float:left;').html('Register'),
        netoper.context(
            BUTTON(CLASS='btn-primary', STYLE='height:33px;').html('Save'),
            host_context,
            'host_context',
            STYLE='float:right;margin:20px 0px 10px 10px;'
        ),
        host_context,
        HEAD(2).html('Host List'),
        netoper.patch('host_table_context')
    )

@PAGE.VIEW(netoper)
def host_table_context(req, mac='', ip=''):
    
    if req.method == 'DELETE':
        ret = delHost(mac, ip)
        if ret: commitHost()
    
    return netoper.dtable(
        DTABLE('Name', 'Model', 'Serial', 'MAC Address', 'IP Address', ' '),
        'host_table'
    )

@PAGE.TABLE(netoper)
def host_table(req, res):
    for host in Host.list():
        res.record(host.name,
                   host.model,
                   host.serial,
                   host.mac,
                   host.ip,
                   netoper.signal(
                       ICON('remove'),
                       'host_table_context',
                       'DELETE', host.mac, host.ip,
                       STYLE='text-align:center;').render()
                   )
