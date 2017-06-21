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

netops_lock = pygics.Lock()

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
        kv = re.match('^\s*(?P<domain>\w[\w\-\.]*)\s*$', domain)
        domain = kv.group('domain') if kv != None else ''
        network, prefix = grammar.Network.isCIDR(cidr)
        if network and prefix:
            cidr = network + '/' + prefix
            _ia_net = ipaddress.IPv4Network(unicode(cidr))
            netmask = _ia_net.with_netmask.split('/')[1]
        else:
            cidr = None
            netmask = None
        gateway = grammar.Network.isIP(gateway)
        dns_int = grammar.Network.isIP(dns_int)
        dns_ext = grammar.Network.isIP(dns_ext)
        
        netops_lock.acquire()
        try:
            env = Environment.one()
            if domain: env.domain = domain
            if cidr:
                if env.cidr != cidr:
                    for dr in DynamicRange.list(): dr.delete()
                    for sr in StaticRange.list(): sr.delete()
                    for host in Host.list(): host.delete()
                    ips = [str(ip) for ip in _ia_net]
                    if re.search('^\d+\.\d+\.\d+\.0$', ips[0]): ips.pop(0)
                    if re.search('^\d+\.\d+\.\d+\.255$', ips[-1]): ips.pop(-1)
                    for ip in ips:
                        Host(ip=ip, ip_num=int(ipaddress.ip_address(unicode(ip)))).create()
                env.cidr = cidr
            if network: env.network = network
            if prefix: env.prefix = prefix
            if netmask: env.netmask = netmask
            if gateway:
                gw = Host.one(Host.ip==gateway)
                if gw:
                    gw.name = 'gateway'
                    gw.range_type = 'environment'
                    gw.range_name = 'env'
                    gw.range_id = -1
                    gw.update()
                    env.gateway = gateway
            if dns_int:
                di = Host.one(Host.ip==dns_int)
                if di:
                    di.name = 'dns'
                    di.range_type = 'environment'
                    di.range_name = 'env'
                    di.range_id = -1
                    di.update()
                    env.dns_int = dns_int
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
            with open(no.h_dhcp, 'w') as h_dhcp, open(no.h_dns, 'w') as h_dns:
                for host in hosts:
                    if host.range_type == 'static' and host.mac != '' and host.ip != '':
                        h_dhcp.write('dhcp-host=%s,%s\n' % (host.mac, host.ip))
                    if env.domain != '' and host.range_name != '' and host.name != '' and host.ip != '':
                        h_dns.write('%s\t%s.%s.%s\n' % (host.ip, host.name.replace(' ', '-'), host.range_name.replace(' ', '-'), env.domain))
            no.reload()
        except Exception as e:
            netops_lock.release()
            raise e
        netops_lock.release()
        
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
        kv = re.match('^\s*(?P<name>\w[\w\-]*)\s*$', name)
        name = kv.group('name') if kv != None else None
        stt = grammar.Network.isIP(stt)
        end = grammar.Network.isIP(end)
        kv = re.match('^\s*(?P<lnum>\d+)\s*$', lease_num)
        lease_num = kv.group('lnum') if kv != None else None
        lease_tag = lease_tag if lease_tag in _range_ip_lease_tag else None
        
        if name and stt and end and lease_num and lease_tag:
            
            netops_lock.acquire()
            try:
                if DynamicRange.one(DynamicRange.name==name): raise Exception('name %s is already exist' % name)
                if StaticRange.one(StaticRange.name==name): raise Exception('name %s is already exist' % name)
                stt_num = int(ipaddress.ip_address(unicode(stt)))
                end_num = int(ipaddress.ip_address(unicode(end)))
                hosts = Host.list(Host.ip_num>=stt_num, Host.ip_num<=end_num)
                if not hosts.count(): raise Exception('unbound IP address')
                for host in hosts:
                    if host.range_id != 0: raise Exception('already exist mapped IP in range')
                dr = DynamicRange(name, stt, end, stt_num, end_num, lease_num, lease_tag, desc).create()
                for host in hosts:
                    host.range_type = 'dynamic'
                    host.range_name = name
                    host.range_id = dr.id
                    host.update()
                
                env = Environment.one()
                drs = DynamicRange.list()
                with open(no.r_dhcp, 'w') as fd:
                    for _dr in drs:
                        if env.netmask != '' and _dr.stt != '' and _dr.end != '' and _dr.lease_num != '' and _dr.lease_tag != '':
                            fd.write('dhcp-range=%s,%s,%s,%s%s\n' % (_dr.stt, _dr.end, env.netmask, _dr.lease_num, _dr.lease_tag[0]))
                no.reload()
            except Exception as e:
                netops_lock.release()
                raise e
            netops_lock.release()
            
            return dr
        raise Exception('incomplete parameters')
    
    @classmethod
    def remove(cls, dr_id):
        if isinstance(dr_id, str): dr_id = int(dr_id) 
        dr = DynamicRange.get(dr_id)
        if dr:
            
            netops_lock.acquire()
            try:
                hosts = Host.list(Host.ip_num>=dr.stt_num, Host.ip_num<=dr.end_num)
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
            except Exception as e:
                netops_lock.release()
                raise e
            netops_lock.release()
            
            return True
        raise Exception('incorrect dynamic range id')

@Bucket.register(bk)
class StaticRange(Model):

    name = Column(Text)
    stt = Column(String(16))
    end = Column(String(16))
    stt_num = Column(Integer(unsigned=True))
    end_num = Column(Integer(unsigned=True))
    desc = Column(Text)
    
    def __init__(self, name='', stt='', end='', stt_num=0, end_num=0, desc=''):
        self.name = name
        self.stt = stt
        self.end = end
        self.stt_num = stt_num
        self.end_num = end_num
        self.desc = desc
    
    @classmethod
    def add(cls, name='', stt='', end='', desc=''):
        kv = re.match('^\s*(?P<name>\w[\w\-]*)\s*$', name)
        name = kv.group('name') if kv != None else None
        stt = grammar.Network.isIP(stt)
        end = grammar.Network.isIP(end)
        
        if name and stt and end:
            
            netops_lock.acquire()
            try:
                if DynamicRange.one(DynamicRange.name==name): raise Exception('name %s is already exist' % name)
                if StaticRange.one(StaticRange.name==name): raise Exception('name %s is already exist' % name)
                stt_num = int(ipaddress.ip_address(unicode(stt)))
                end_num = int(ipaddress.ip_address(unicode(end)))
                hosts = Host.list(Host.ip_num>=stt_num, Host.ip_num<=end_num)
                if not hosts.count(): raise Exception('unbound IP address')
                for host in hosts:
                    if host.range_id != 0: raise Exception('already exist mapped IP in range')
                sr = StaticRange(name, stt, end, stt_num, end_num, desc).create()
                for host in hosts:
                    host.range_type = 'static'
                    host.range_name = name
                    host.range_id = sr.id
                    host.update()
            except Exception as e:
                netops_lock.release()
                raise e
            netops_lock.release()
            
            return sr
        raise Exception('incomplete parameters')
    
    @classmethod
    def remove(cls, sr_id):
        if isinstance(sr_id, str): sr_id = int(sr_id)
        sr = StaticRange.get(sr_id)
        if sr:
            
            netops_lock.acquire()
            try:
                hosts = Host.list(Host.ip_num>=sr.stt_num, Host.ip_num<=sr.end_num)
                for host in hosts:
                    host.name = ''
                    host.mac = ''
                    host.model = 'Unknown'
                    host.serial = ''
                    host.range_type = ''
                    host.range_name = ''
                    host.range_id = 0
                    host.desc = ''
                    host.update()
                sr.delete()
                
                env = Environment.one()
                hosts = Host.list()
                with open(no.h_dhcp, 'w') as h_dhcp, open(no.h_dns, 'w') as h_dns:
                    for _host in hosts:
                        if _host.range_type == 'static' and _host.mac != '' and _host.ip != '':
                            h_dhcp.write('dhcp-host=%s,%s\n' % (_host.mac, _host.ip))
                        if env.domain != '' and _host.range_name != '' and _host.name != '' and _host.ip != '':
                            h_dns.write('%s\t%s.%s.%s\n' % (_host.ip, _host.name.replace(' ', '-'), _host.range_name.replace(' ', '-'), env.domain))
                no.reload()
            except Exception as e:
                netops_lock.release()
                raise e
            netops_lock.release()
            
            return True
        raise Exception('incorrect static range id')

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
    def set(cls, host_id, name='', mac='', model='', serial='', desc=''):
        if isinstance(host_id, str): host_id = int(host_id)
        kv = re.match('^\s*(?P<name>\w[\w\-]*)\s*$', name)
        name = kv.group('name') if kv != None else ''
        mac = grammar.Network.isMAC(mac)
        if mac == None: mac = ''
        model = model if model in _host_models else 'Unknown'
        kv = re.match('^\s*(?P<serial>[\w\d\-]+)\s*$', serial)
        serial = kv.group('serial') if kv != None else ''
        
        netops_lock.acquire()
        try:
            if name != '':
                dup_host = Host.one(Host.name==name)
                if dup_host and dup_host.id != host_id: raise Exception('name %s is already exist' % name)
            if mac != '':
                _duple_mac = Host.one(Host.mac==mac)
                if _duple_mac and _duple_mac.id != host_id: raise Exception('mac %s is duplicated' % mac)
            host = Host.get(host_id)
            if host.range_type != 'static': raise Exception('range type is not static')
            host.name = name
            host.mac = mac
            host.model = model
            host.serial = serial
            host.desc = desc
            host.update()
            
            if name or mac:
                env = Environment.one()
                hosts = Host.list()
                with open(no.h_dhcp, 'w') as h_dhcp, open(no.h_dns, 'w') as h_dns:
                    for _host in hosts:
                        if _host.range_type == 'static' and _host.mac != '' and _host.ip != '':
                            h_dhcp.write('dhcp-host=%s,%s\n' % (_host.mac, _host.ip))
                        if env.domain != '' and _host.range_name != '' and _host.name != '' and _host.ip != '':
                            h_dns.write('%s\t%s.%s.%s\n' % (_host.ip, _host.name.replace(' ', '-'), _host.range_name.replace(' ', '-'), env.domain))
                no.reload()
        except Exception as e:
            netops_lock.release()
            raise e
        netops_lock.release()
        
        return host
    
    @classmethod
    def clear(cls, host_id):
        if isinstance(host_id, str): host_id = int(host_id)
        host = Host.get(host_id)
        if host.range_type != 'static': raise Exeption('range type is not static')
        host.name = ''
        host.mac = ''
        host.model = 'Unknown'
        host.serial = ''
        host.desc = ''
        host.update()
        
        netops_lock.acquire()
        try:
            env = Environment.one()
            hosts = Host.list()
            with open(no.h_dhcp, 'w') as h_dhcp, open(no.h_dns, 'w') as h_dns:
                for _host in hosts:
                    if _host.range_type == 'static' and _host.mac != '' and _host.ip != '':
                        h_dhcp.write('dhcp-host=%s,%s\n' % (_host.mac, _host.ip))
                    if env.domain != '' and _host.range_name != '' and _host.name != '' and _host.ip != '':
                        h_dns.write('%s\t%s.%s.%s\n' % (_host.ip, _host.name.replace(' ', '-'), _host.range_name.replace(' ', '-'), env.domain))
            no.reload()
        except Exception as e:
            netops_lock.release()
            raise e
        netops_lock.release()
        
        return host

#===============================================================================
# Init
#===============================================================================
if not Environment.one():
    Environment().create()
