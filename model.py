# -*- coding: utf-8 -*-
'''
Created on 2017. 6. 13.
@author: HyechurnJang
'''

import os
import re
import pygics
import ipaddress
import grammar 
from bucket import *

class NetOps(pygics.__PYGICS__):
    
    def __init__(self, base_dir):
        self.pid = base_dir + '/netops.pid'
        self.conf = base_dir + '/netops.conf'
        self.d_dhcp = base_dir + '/dhcp'
        self.r_dhcp = self.d_dhcp + '/range.conf'
        self.h_dhcp = self.d_dhcp + '/host.conf'
        self.r_dns = base_dir + '/resolv.dns'
        self.h_dns = base_dir + '/host.dns'
    
    def __release__(self):
        self.stop()
    
    def start(self):
        cmd = '/usr/sbin/dnsmasq --user=root --group=root -h -x %s -C %s -7 %s -r %s -H %s' % (self.pid, self.conf, self.d_dhcp, self.r_dns, self.h_dns)
        print('NetOps Start : %s' % ('ok' if os.system(cmd) == 0 else 'failed'))
        return self
    
    def stop(self):
        cmd = 'kill -9 `cat %s`; rm -rf %s' % (self.pid, self.pid)
        print('NetOps Stop : %s' % ('ok' if os.system(cmd) == 0 else 'failed'))
        return self
    
    def reload(self):
        self.stop()
        self.start()
        return self

no = NetOps(PWD() + '/native').reload()
bk = FileBucket()

@Bucket.register(bk)
class Environment(Model):
    
    domain = Column(Text)
    cidr = Column(String(24))
    network = Column(String(16))
    prefix = Column(String(4))
    netmask = Column(String(16))
    gateway = Column(String(16))
    dns_int = Column(Text)
    dns_ext = Column(Text)
    
    def __init__(self, domain='', cidr='', network='', prefix='', netmask='', gateway='', dns_int='', dns_ext=''):
        self.domain = domain
        self.cidr = cidr
        self.network = network
        self.prefix = prefix
        self.netmask = netmask
        self.gateway = gateway
        self.dns_int = dns_int
        self.dns_ext = dns_ext
    
    @classmethod
    def set(cls, domain='', cidr='', gateway='', dns_int='', dns_ext=''):
        kv = re.match('^\s*(?P<domain>[\w\d\-]+)\s*$', domain)
        domain = kv.group('domain').lower() if kv != None else ''
        network, prefix = grammar.Network.isCIDR(cidr)
        if network and prefix: cidr = network + '/' + prefix
        else: cidr = None
        _ia_net = ipaddress.IPv4Network(unicode(cidr))
        netmask = _ia_net.with_netmask.split('/')[1]
        gateway = grammar.Network.isIP(gateway)
        dns_int = grammar.Network.isIP(dns_int)
        dns_ext = grammar.Network.isIP(dns_ext)
        
        env = Environment.one()
        if domain: env.domain = domain
        if cidr:
            if env.cidr != cidr:
                for dr in DynamicRange.list(): dr.delete()
                for sr in StaticRange.list(): sr.delete()
                for host in Host.list(): host.delete()
                ips = [str(ip) for ip in _ia_net]
                print ips
                if re.search('^\d+\.\d+\.\d+\.0$', ips[0]): ips.pop(0)
                elif re.search('^\d+\.\d+\.\d+\.255$', ips[-1]): ips.pop(-1)
                for ip in ips:
                    Host(ip=ip, ip_num=int(ipaddress.ip_address(unicode(ip)))).create()
            env.cidr = cidr
        if network: env.network = network
        if prefix: env.prefix = prefix
        if netmask: env.netmask = netmask
        if gateway: env.gateway = gateway
        if dns_int: env.dns_int = dns_int
        if dns_ext: env.dns_ext = dns_ext
        env.update()
        
        drs = DynamicRange.list()
        hosts = Host.list()
        with open(no.conf, 'w') as fd:
            if env.netmask != '': fd.write('dhcp-option=1,%s\n' % env.netmask)
            if env.gateway != '': fd.write('dhcp-option=3,%s\n' % env.gateway)
            if env.dns_int != '': fd.write('dhcp-option=6,%s\n' % env.dns_int)
        with open(no.r_dns, 'w') as fd:
            if env.dns_ext != '': fd.write('nameserver\t%s\n' % env.dns_ext)
        with open(no.r_dhcp, 'w') as fd:
            for dr in drs:
                if env.netmask != '' and dr.stt != '' and dr.end != '' and dr.lease_num != '' and dr.lease_tag != '':
                    fd.write('dhcp-range=%s,%s,%s,%s%s\n' % (dr.stt, dr.end, env.netmask, dr.lease_num, dr.lease_tag[0]))
        with open(no.h_dhcp, 'w') as fd:
            for host in hosts:
                if host.range_type == 'static' and host.mac != '' and host.ip != '':
                    fd.write('dhcp-host=%s,%s\n' % (host.mac, host.ip))
        with open(no.h_dns, 'w') as fd:
            for host in hosts:
                if env.domain != '' and host.model != '' and host.name != '' and host.ip != '':
                    fd.write('%s\t%s.%s.%s\n' % (host.ip, host.name, host.model, env.domain))
        no.reload()
        return env

_range_ip_lease_tag = ['seconds', 'minutes', 'hours']
@Bucket.register(bk)
class DynamicRange(Model):
    
    name = Column(Text)
    stt = Column(String(16))
    end = Column(String(16))
    stt_num = Column(Integer(unsigned=True))
    end_num = Column(Integer(unsigned=True))
    lease_num = Column(String(16))
    lease_tag = Column(String(4))
    desc = Column(Text)
    
    def __init__(self, name='', stt='', end='', stt_num=0, end_num=0, lease_num='', lease_tag='', desc=''):
        self.name = name
        self.stt = stt
        self.end = end
        self.stt_num = stt_num
        self.end_num = end_num
        self.lease_num = lease_num
        self.lease_tag = lease_tag
        self.desc = desc
    
    @classmethod
    def add(cls, name='', stt='', end='', lease_num='', lease_tag='', desc=''):
        kv = re.match('^\s*(?P<val>[\w\-\.\:]+)\s*$', name)
        name = kv.group('val') if kv != None else None
        stt = grammar.Network.isIP(stt)
        end = grammar.Network.isIP(end)
        kv = re.match('^\s*(?P<val>\d+)\s*$', lease_num)
        lease_num = kv.group('val') if kv != None else None
        lease_tag = lease_tag if lease_tag in _range_ip_lease_tag else None
        
        if name and stt and end and lease_num and lease_tag:
            if DynamicRange.one(DynamicRange.name==name): return None
            if StaticRange.one(StaticRange.name==name): return None
            stt_num = int(ipaddress.ip_address(unicode(stt)))
            end_num = int(ipaddress.ip_address(unicode(end)))
            hosts = Host.list(Host.ip_num>=stt_num, Host.ip_num<=end_num)
            for host in hosts:
                if host.range_id != 0: return None
            _dr = DynamicRange(name, stt, end, stt_num, end_num, lease_num, lease_tag, desc).create()
            for host in hosts:
                host.range_type = 'dynamic'
                host.range_name = name
                host.range_id = _dr.id
                host.update()
            
            env = Environment.one()
            drs = DynamicRange.list()
            with open(no.r_dhcp, 'w') as fd:
                for dr in drs:
                    if env.netmask != '' and dr.stt != '' and dr.end != '' and dr.lease_num != '' and dr.lease_tag != '':
                        fd.write('dhcp-range=%s,%s,%s,%s%s\n' % (dr.stt, dr.end, env.netmask, dr.lease_num, dr.lease_tag[0]))
            no.reload()
            return _dr
        return None
    
    @classmethod
    def remove(cls, id):
        dr = DynamicRange.get(id)
        if dr:
            hosts = Host.list(Host.ip_num>=dr.stt_num, Host.ip_num<=dr.end_num)
            for host in hosts:
                if host.range_type != 'dynamic' or host.range_id != dr.id: return False
            for host in hosts:
                host.range_type = ''
                host.range_name = ''
                host.range_id = 0
                host.update()
            dr.delete()
            
            env = Environment.one()
            drs = DynamicRange.list()
            with open(no.r_dhcp, 'w') as fd:
                for dr in drs:
                    if env.netmask != '' and dr.stt != '' and dr.end != '' and dr.lease_num != '' and dr.lease_tag != '':
                        fd.write('dhcp-range=%s,%s,%s,%s%s\n' % (dr.stt, dr.end, env.netmask, dr.lease_num, dr.lease_tag[0]))
            no.reload()
            return True
        return False

@Bucket.register(bk)
class StaticRange(Model):

    name = Column(Text)
    stt = Column(String(16))
    end = Column(String(16))
    stt_num = Column(Integer(unsigned=True))
    end_num = Column(Integer(unsigned=True))
    desc = Column(Text)
    
    def __init__(self, name='', stt='', end='', stt_num=0, end_num=0, desc=''):
        self.name = ''
        self.stt = ''
        self.end = ''
        self.stt_num = stt_num
        self.end_num = end_num
        self.desc = ''
    
    @classmethod
    def add(cls, name='', stt='', end='', desc=''):
        kv = re.match('^\s*(?P<val>[\w\-\.\:]+)\s*$', name)
        name = kv.group('val') if kv != None else None
        stt = grammar.Network.isIP(stt)
        end = grammar.Network.isIP(end)
        
        if name and stt and end:
            if DynamicRange.one(DynamicRange.name==name): return None
            if StaticRange.one(StaticRange.name==name): return None
            stt_num = int(ipaddress.ip_address(unicode(stt)))
            end_num = int(ipaddress.ip_address(unicode(end)))
            hosts = Host.list(Host.ip_num>=stt_num, Host.ip_num<=end_num)
            for host in hosts:
                if host.range_id != 0: return None
            sr = StaticRange(name, stt, end, stt_num, end_num, desc).create()
            for host in hosts:
                host.range_type = 'static'
                host.range_name = name
                host.range_id = sr.id
                host.update()
            return sr
        return None
    
    @classmethod
    def remove(cls, id):
        sr = StaticRange.get(id)
        if sr:
            hosts = Host.list(Host.ip_num>=sr.stt_num, Host.ip_num<=sr.end_num)
            for host in hosts:
                if host.range_type != 'static' or host.range_id != sr.id: return False
            for host in hosts:
                host.range_type = ''
                host.range_name = ''
                host.range_id = 0
                host.update()
            sr.delete()
            
            env = Environment.one()
            with open(no.h_dhcp, 'w') as fd:
                for host in hosts:
                    if host.range_type == 'static' and host.mac != '' and host.ip != '':
                        fd.write('dhcp-host=%s,%s\n' % (host.mac, host.ip))
            with open(no.h_dns, 'w') as fd:
                for host in hosts:
                    if env.domain != '' and host.model != '' and host.name != '' and host.ip != '':
                        fd.write('%s\t%s.%s.%s\n' % (host.ip, host.name, host.model, env.domain))
            no.reload()
            return True
        return False

_host_models = ['Unknown', 'Nexus', 'Catalyst', 'ASA', 'UCS', 'Host', 'VM', 'Node']
@Bucket.register(bk)
class Host(Model):
    
    name = Column(Text)
    mac = Column(String(24))
    ip = Column(String(16))
    ip_num = Column(Integer(unsigned=True))
    model = Column(Text)
    serial = Column(Text)
    range_type = Column(Text)
    range_name = Column(Text)
    range_id = Column(Integer)
    desc = Column(Text)
    
    def __init__(self, name='', mac='', ip='', ip_num=0, model='Unknown', serial='', range_type='', range_name='', range_id=0, desc=''):
        self.name = name
        self.mac = mac
        self.ip = ip
        self.ip_num = ip_num
        self.model = model
        self.serial = serial
        self.range_type = range_type
        self.range_name = range_name
        self.range_id = range_id
        self.desc = desc
        
    @classmethod
    def add(cls, name='', mac='', ip='', model='', serial='', desc=''):
        kv = re.match('^\s*(?P<name>[\w\d\-]+)\s*$', name)
        name = kv.group('name').lower() if kv != None else ''
        mac = grammar.Network.isMAC(mac)
        ip = grammar.Network.isIP(ip)
        model = model if model in _host_models else 'Unknown'
        kv = re.match('^\s*(?P<serial>[\w\d\-]+)\s*$', serial)
        serial = kv.group('serial') if kv != None else ''
        
        if name and mac and ip:
            if Host.one(Host.name==name): return None
            if Host.one(Host.mac==mac): return None
            _host = Host.one(Host.ip==ip)
            if _host.mac != '' or _host.range_type != 'static': return None
            _host.name = name
            _host.mac = mac
            _host.model = model
            _host.serial = serial
            _host.desc = desc
            _host.update()
            
            env = Environment.one()
            hosts = Host.list()
            with open(no.h_dhcp, 'w') as fd:
                for host in hosts:
                    if host.range_type == 'static' and host.mac != '' and host.ip != '':
                        fd.write('dhcp-host=%s,%s\n' % (host.mac, host.ip))
            with open(no.h_dns, 'w') as fd:
                for host in hosts:
                    if env.domain != '' and host.model != '' and host.name != '' and host.ip != '':
                        fd.write('%s\t%s.%s.%s\n' % (host.ip, host.name, host.model, env.domain))
            no.reload()
            return _host
        return None
    
    @classmethod
    def remove(cls, id):
        host = Host.get(id)
        if host:
            host.name = ''
            host.mac = ''
            host.model = 'Unknown'
            host.serial = ''
            host.desc = ''
            host.update()
            
            env = Environment.one()
            hosts = Host.list()
            with open(no.h_dhcp, 'w') as fd:
                for host in hosts:
                    if host.range_type == 'static' and host.mac != '' and host.ip != '':
                        fd.write('dhcp-host=%s,%s\n' % (host.mac, host.ip))
            with open(no.h_dns, 'w') as fd:
                for host in hosts:
                    if env.domain != '' and host.model != '' and host.name != '' and host.ip != '':
                        fd.write('%s\t%s.%s.%s\n' % (host.ip, host.name, host.model, env.domain))
            no.reload()
            return True
        return False
