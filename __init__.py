# -*- coding: utf-8 -*-
'''
Created on 2017. 6. 10.
@author: HyechurnJang
'''

import pygics
from page import *

#===============================================================================
# Internal APIs
#===============================================================================
from model import Environment, DynamicRange, StaticRange, Host

#===============================================================================
# Init
#===============================================================================
print Environment().create()

#===============================================================================
# REST APIs
#===============================================================================
@pygics.api('GET', '/api/env')
def api_getEnv(req):
    env = Environment.one()
    return {'domain' : env.domain,
            'cidr' : env.cidr,
            'network' : env.network,
            'prefix' : env.prefix,
            'netmask' : env.netmask,
            'gateway' : env.gateway,
            'dns_internal' : env.dns_int,
            'dns_external' : env.dns_ext}

@pygics.api('POST', '/api/env')
def api_setEnv(req):
    env = Environment.set(**req.data)
    return {'domain' : env.domain,
            'cidr' : env.cidr,
            'network' : env.network,
            'prefix' : env.prefix,
            'netmask' : env.netmask,
            'gateway' : env.gateway,
            'dns_internal' : env.dns_int,
            'dns_external' : env.dns_ext}

@pygics.api('GET', '/api/dynamicrange')
def api_getDynamicRange(req, id=None):
    if id != None:
        dr = DynamicRange.get(id)
        if dr:
            return {'id' : dr.id,
                    'name' : dr.name,
                    'start' : dr.stt,
                    'end' : dr.end,
                    'lease_num' : dr.lease_num,
                    'lease_tag' : dr.lease_tag,
                    'desc' : dr.desc}
        return None
    drs = DynamicRange.list()
    ret = []
    for dr in drs:
        ret.append({'id' : dr.id,
                    'name' : dr.name,
                    'desc' : dr.desc})
    return ret

@pygics.api('POST', '/api/dynamicrange')
def api_addDynamicRange(req):
    dr = DynamicRange.add(**req.data)
    if dr:
        return {'id' : dr.id,
                'name' : dr.name,
                'start' : dr.stt,
                'end' : dr.end,
                'lease_num' : dr.lease_num,
                'lease_tag' : dr.lease_tag,
                'desc' : dr.desc}
    return None

@pygics.api('DELETE', '/api/dynamicrange')
def api_delDynamicRange(req, id):
    return DynamicRange.remove(id)

@pygics.api('GET', '/api/staticrange')
def api_getStaticRange(req, id=None):
    if id != None:
        sr = StaticRange.get(id)
        if sr:
            return {'id' : sr.id,
                    'name' : sr.name,
                    'start' : sr.stt,
                    'end' : sr.end,
                    'desc' : sr.desc}
        return None
    srs = StaticRange.list()
    ret = []
    for sr in srs:
        ret.append({'id' : sr.id,
                    'name' : sr.name,
                    'desc' : sr.desc})
    return ret

@pygics.api('POST', '/api/staticrange')
def api_addStaticRange(req):
    sr = StaticRange.add(**req.data)
    if sr:
        return {'id' : sr.id,
                'name' : sr.name,
                'start' : sr.stt,
                'end' : sr.end,
                'desc' : sr.desc}
    return None

@pygics.api('DELETE', '/api/staticrange')
def api_delStaticRange(req, id):
    return StaticRange.remove(id)

@pygics.api('GET', '/api/host')
def api_getHost(req, id=None):
    if id != None:
        host = Host.get(id)
        if host:
            return {'id' : host.id,
                    'name' : host.name,
                    'mac' : host.mac,
                    'ip' : host.ip,
                    'model' : host.model,
                    'serial' : host.serial,
                    'range_name' : host.range_name,
                    'desc' : host.desc}
        return None
    hosts = Host.list()
    ret = []
    for host in hosts:
        ret.append({'id' : host.id,
                    'name' : host.name,
                    'mac' : host.mac,
                    'ip' : host.ip})
    return ret

@pygics.api('POST', '/api/host')
def api_addHost(req):
    host = Host.add(**req.data)
    if host:
        return {'id' : host.id,
                'name' : host.name,
                'mac' : host.mac,
                'ip' : host.ip,
                'model' : host.model,
                'serial' : host.serial,
                'range_name' : host.range_name,
                'desc' : host.desc}
    return None

@pygics.api('DELETE', '/api/host')
def api_delHost(req, id):
    return Host.remove(id)

#===============================================================================
# Page
#===============================================================================
netops = PAGE(resource='resource', template=PAGE.TEMPLATE.SIMPLE_DK)

@PAGE.MAIN(netops, 'NetOps')
def dnsmasq_main_page(req):
    return 'DHCP & DNS'

@PAGE.MENU(netops, 'Environment', 'id-card')
def environment_setting(req):
    
    if req.method == 'POST':
        Environment.set(**req.data)
    
    env = Environment.one()
    
    print env.__dict__
    
    domain = INPUT.TEXT('domain', env.domain)
    cidr = INPUT.TEXT('cidr', env.cidr)
    gateway = INPUT.TEXT('gateway', env.gateway)
    dns_int = INPUT.TEXT('dns_int', env.dns_int)
    dns_ext = INPUT.TEXT('dns_ext', env.dns_ext)
    
    return DIV().html(
        HEAD(1, STYLE='float:left;').html('Environment'),
        DIV(STYLE='float:right;margin:20px 0px 10px 20px;').html(
            netops.context(
                BUTTON(CLASS='btn-primary', STYLE='height:39px;').html('Save'),
                'environment_setting',
                domain,
                cidr,
                gateway,
                dns_int,
                dns_ext,
                
            )
        ),
        
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Domain'),
            domain
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('CIDR'),
            cidr
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Network'),
            INPUT.DISPLAY().html(env.network)
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Prepix'),
            INPUT.DISPLAY().html(env.prefix)
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Netmask'),
            INPUT.DISPLAY().html(env.netmask)
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Gateway'),
            gateway
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Internal DNS (NetOps IP)'),
            dns_int
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('External DNS'),
            dns_ext
        ),
    )

# @PAGE.VIEW(netops)
# def dhcp_range_setting(req):
#     
#     if req.method == 'POST':
#         setDynamicRange(**req.data)
#         commitDynamicRange()
#     
#     rng = getDynamicRange()
#     
#     tag_prio = []
#     for tag in _range_ip_lease_tag: tag_prio.append(tag)
#     if rng.ip_lease_tag != '':
#         tag_prio.remove(rng.ip_lease_tag)
#         tag_prio.insert(0, rng.ip_lease_tag)
#     
#     range_context = CONTEXT().TEXT(
#         'ip_stt', CONTEXT.LABEL_TOP('Range Start'), rng.ip_stt
#     ).TEXT(
#         'ip_end', CONTEXT.LABEL_TOP('Range End'), rng.ip_end
#     ).TEXT(
#         'ip_lease_num', CONTEXT.LABEL_TOP('Lease Time'), rng.ip_lease_num,
#         STYLE='width:70%;float:left;padding-right:5px;'
#     ).SELECT(
#         'ip_lease_tag', CONTEXT.LABEL_TOP('', STYLE='width:100%;height:15px;'), *tag_prio,
#         STYLE='width:30%;float:right;padding-left:5px;'
#     )
#         
#     return DIV().html(
#         HEAD(2, STYLE='float:left;').html('Dynamic Range'),
#         netops.context(
#             BUTTON(CLASS='btn-primary', STYLE='height:33px;').html('Save'),
#             range_context,
#             'dhcp_range_setting',
#             STYLE='float:right;margin:20px 0px 10px 20px;'
#         ),
#         range_context,
#     )
# 
# @PAGE.MENU(netops, 'Host', 'id-card')
# def host_setting(req):
#     
#     return DIV().html(
#         HEAD(1).html('Host Setting'),
#         netops.patch('host_context'),
#     )
# 
# @PAGE.VIEW(netops)
# def host_context(req):
#     
#     if req.method == 'POST':
#         host = setHost(**req.data)
#         if host: commitHost()
#     
#     host_context = CONTEXT().TEXT(
#         'name', CONTEXT.LABEL_TOP('Host Name'),
#     ).TEXT(
#         'mac', CONTEXT.LABEL_TOP('MAC Address'),
#         STYLE='width:50%;float:left;padding-right:5px;'
#     ).TEXT(
#         'ip', CONTEXT.LABEL_TOP('IP Address'),
#         STYLE='width:50%;float:right;padding-left:5px;'
#     ).SELECT(
#         'model', CONTEXT.LABEL_TOP('Model'), 'Host', 'Nexus', 'Catalyst', 'ASA', 'UCS', 'VM',
#         STYLE='width:50%;float:left;padding-right:5px;'
#     ).TEXT(
#         'serial', CONTEXT.LABEL_TOP('Serial'), 
#         STYLE='width:50%;float:right;padding-left:5px;'
#     )
# 
#     return DIV().html(
#         HEAD(2, STYLE='float:left;').html('Register'),
#         netops.context(
#             BUTTON(CLASS='btn-primary', STYLE='height:33px;').html('Save'),
#             host_context,
#             'host_context',
#             STYLE='float:right;margin:20px 0px 10px 10px;'
#         ),
#         host_context,
#         HEAD(2).html('Host List'),
#         netops.patch('host_table_context')
#     )
# 
# @PAGE.VIEW(netops)
# def host_table_context(req, mac='', ip=''):
#     
#     if req.method == 'DELETE':
#         ret = delHost(mac, ip)
#         if ret: commitHost()
#     
#     return netops.dtable(
#         DTABLE('Name', 'Model', 'Serial', 'MAC Address', 'IP Address', ' '),
#         'host_table'
#     )
# 
# @PAGE.TABLE(netops)
# def host_table(req, res):
#     for host in Host.list():
#         res.record(host.name,
#                    host.model,
#                    host.serial,
#                    host.mac,
#                    host.ip,
#                    netops.signal(
#                        ICON('remove'),
#                        'host_table_context',
#                        'DELETE', host.mac, host.ip,
#                        STYLE='text-align:center;').render()
#                    )
