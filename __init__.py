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
from model import Environment, DynamicRange, StaticRange, Host, _host_models

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
def api_setHost(req):
    host = Host.set(**req.data)
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

#===============================================================================
# Page
#===============================================================================
netops = PAGE(resource='resource', template=PAGE.TEMPLATE.SIMPLE_DK)
netops.addCategory('Settings', 'dashboard')

@PAGE.MAIN(netops, 'NetOps')
def netops_main_page(req):
    
    return DIV().html(
        HEAD(2).html('Status'),
        netops.patch('netops_main_status_view'),
        HEAD(2).html('Register'),
        netops.patch('netops_main_context_view')
    )
    
@PAGE.VIEW(netops)
def netops_main_status_view(req):
    host_count = Host.count()
    bar = DIV(STYLE='width:100%;height:20px;background-color:#888;', TITLE='Unsettled Environment')
    
    for host in Host.list():
        if host.range_type == '':
            bar.html(
                DIV(TITLE='Reserved\n%s' % (host.ip),
                    STYLE='float:left;width:calc(100%%/%d);height:20px;background-color:#888;' % host_count)
            )
        elif host.range_type == 'dynamic':
            bar.html(
                DIV(TITLE='Dynamic DHCP\n%s\n%s' % (host.range_name, host.ip),
                    STYLE='float:left;width:calc(100%%/%d);height:20px;background-color:#44ffcc;' % host_count)
            )
        elif host.range_type == 'static':
            sh = DIV(TITLE='Static DHCP\n%s\n%s\n%s' % (host.range_name, host.ip, host.name),
                     STYLE='float:left;width:calc(100%%/%d);height:20px;cursor:pointer;color:#fff;background-color:#44ccff;' % host_count)
            if host.name != '' or host.mac != '': sh.html('!')
            bar.html(sh)
        elif host.range_type == 'environment':
            bar.html(
                DIV(TITLE='Environment\n%s\n%s' % (host.ip, host.name),
                    STYLE='float:left;width:calc(100%%/%d);height:20px;background-color:#f00;' % host_count)
            )
    
    return bar

@PAGE.VIEW(netops)
def netops_main_context_view(req):
    
    nav = NAV()
    nav.TAB('Total', netops.patch('netops_main_total_view'))
    nav.TAB('Dynamic', netops.patch('netops_main_dynamic_view'))
    srs = StaticRange.list()
    for sr in srs:
        nav.TAB(sr.name,
            netops.patch('netops_main_static_view::' + str(sr.id), str(sr.id))
        )
        
    return nav

@PAGE.VIEW(netops)
def netops_main_total_view(req):
    return netops.table(
        TABLE.SYNC('Name',
                   'DNS',
                   'Range',
                   'IP',
                   'MAC',
                   'Model',
                   'Serial',                   
                   'Description'),
        'netops_main_total_table'
    )

@PAGE.VIEW(netops)
def netops_main_dynamic_view(req):
    return netops.table(
        TABLE.SYNC('Range', 'IP'),
        'netops_main_dynamic_table'
    )

@PAGE.VIEW(netops)
def netops_main_static_view(req, sr_id=None, host_id=None):
    
    if req.method == 'POST':
        if 'sr_id' in req.data: sr_id = req.data.pop('sr_id')
        Host.set(**req.data)
    elif req.method == 'DELETE':
        Host.clear(host_id)
    
    return DIV().html(
        netops.table(
            TABLE.SYNC('Name',
                       'IP',
                       'MAC',
                       'Model',
                       'Serial',
                       'Description',
                       'Action'),
            'netops_main_static_table', sr_id
        ),
        netops.refresh('netops_main_status_view'),
        netops.refresh('netops_main_total_view')
    )

@PAGE.TABLE(netops)
def netops_main_total_table(table):
    env = Environment.one()
    hosts = Host.list()
    for host in hosts:
        if host.name != '' and host.range_name != '' and env.domain != '':
            dns = '%s.%s.%s' % (host.name.replace(' ', '-'), host.range_name.replace(' ', '-'), env.domain)
        else: dns = ''
        if host.model == 'Unknown': model = ''
        else: model = host.model
        table.record(host.name,
                     ANCH(HREF='http://' + dns, TARGET='_blank').html(dns),
                     '%s (%s)' % (host.range_name, host.range_type) if host.range_name != '' else host.range_name,
                     ANCH(HREF='http://' + host.ip, TARGET='_blank').html(host.ip),
                     host.mac,
                     model,
                     host.serial,
                     host.desc)

@PAGE.TABLE(netops)
def netops_main_dynamic_table(table):
    drs = DynamicRange.list()
    for dr in drs:
        hosts = Host.list(Host.ip_num>=dr.stt_num, Host.ip_num<=dr.end_num)
        for host in hosts:
            table.record(dr.name, host.ip)

@PAGE.TABLE(netops)
def netops_main_static_table(table, sr_id):
    if isinstance(sr_id, str): sr_id = int(sr_id)
    env = Environment.one()
    sr = StaticRange.get(sr_id)
    if sr:
        hosts = Host.list(Host.ip_num>=sr.stt_num, Host.ip_num<=sr.end_num)
        for host in hosts:
            sr_id = INPUT.HIDDEN('sr_id', str(sr.id))
            host_id = INPUT.HIDDEN('host_id', str(host.id))
            name = INPUT.TEXT('name', host.name, CLASS='page-input-in-table')
            mac = INPUT.TEXT('mac', host.mac, CLASS='page-input-in-table')
            model_list = [m for m in _host_models]
            model_list.remove(host.model)
            model_list.insert(0, host.model)
            model = INPUT.SELECT('model', *model_list, CLASS='page-input-in-table')
            serial = INPUT.TEXT('serial', host.serial, CLASS='page-input-in-table')
            desc = INPUT.TEXT('desc', host.desc, CLASS='page-input-in-table')
            submit = DIV(STYLE='width:100%;text-align:center;').html(
                netops.context(
                    BUTTON(CLASS='btn-primary btn-xs', STYLE='margin:0px;padding:0px 5px;font-size:11px;').html('Save'),
                    'netops_main_static_view::' + str(sr.id),
                    sr_id, host_id, name, mac, model, serial, desc
                ),
                netops.signal(
                    BUTTON(CLASS='btn-danger btn-xs', STYLE='margin:0px;padding:0px 5px;font-size:11px;').html('Clear'),
                    'DELETE', 'netops_main_static_view::' + str(sr.id),
                    str(sr.id), str(host.id)
                ),
                sr_id,
                host_id
            )
            table.record(name,
                         host.ip,
                         mac,
                         model,
                         serial,
                         desc,
                         submit)

@PAGE.MENU(netops, 'Settings::Environment', 'id-card')
def environment_setting(req):
    
    if req.method == 'POST':
        Environment.set(**req.data)
    
    env = Environment.one()
    
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
                dns_ext
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
        )
    )

@PAGE.MENU(netops, 'Settings::Dynamic DHCP', 'id-card')
def dynamic_dhcp_setting(req):
    
    name = INPUT.TEXT('name')
    stt = INPUT.TEXT('stt')
    end = INPUT.TEXT('end')
    lease_num = INPUT.TEXT('lease_num')
    lease_tag = INPUT.SELECT('lease_tag', 'hours', 'minutes', 'seconds')
    desc = INPUT.TEXT('desc')
    
    return DIV().html(
        HEAD(1, STYLE='float:left;').html('Dynamic DHCP'),
        DIV(STYLE='float:right;margin:20px 0px 10px 20px;').html(
            netops.context(
                BUTTON(CLASS='btn-primary', STYLE='height:39px;').html('Save'),
                'dynamic_dhcp_table_view',
                name,
                stt,
                end,
                lease_num,
                lease_tag,
                desc
            )
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Name'),
            name
        ),
        ROW().html(
            COL(6, 'xs').html(
                INPUT.LABEL_TOP('Range'),
                INPUT.GROUP().html(
                    INPUT.LABEL_LEFT('Start'),
                    stt,
                    INPUT.LABEL_LEFT('End'),
                    end
                )
            ),
            COL(6, 'xs').html(
                INPUT.LABEL_TOP('Lease Time'),
                INPUT.GROUP().html(
                    INPUT.LABEL_LEFT('Number'),
                    lease_num,
                    INPUT.LABEL_LEFT('Type'),
                    lease_tag
                )
            )
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Description'),
            desc
        ),
        netops.patch('dynamic_dhcp_table_view')
    )

@PAGE.VIEW(netops)
def dynamic_dhcp_table_view(req, dr_id=None):
    
    if req.method == 'POST':
        DynamicRange.add(**req.data)
    elif req.method == 'DELETE':
        DynamicRange.remove(int(dr_id))
    
    return netops.table(
        TABLE.SYNC('Name',
                   'Range',
                   'Lease Time',
                   'Description',
                   'Action'),
        'dynamic_dhcp_table'
    )

@PAGE.TABLE(netops)
def dynamic_dhcp_table(table):
    drs = DynamicRange.list()
    for dr in drs:
        table.record(dr.name,
                     '%s ~ %s' % (dr.stt, dr.end),
                     '%s %s' % (dr.lease_num, dr.lease_tag),
                     dr.desc,
                     DIV(STYLE='width:100%;text-align:center;').html(
                         netops.signal(
                             BUTTON(CLASS='btn-danger btn-xs', STYLE='margin:0px;padding:0px 5px;font-size:11px;').html('Delete'),
                            'DELETE',
                            'dynamic_dhcp_table_view', str(dr.id))
                    )
        )

@PAGE.MENU(netops, 'Settings::Static DHCP', 'id-card')
def static_dhcp_setting(req):
    
    name = INPUT.TEXT('name')
    stt = INPUT.TEXT('stt')
    end = INPUT.TEXT('end')
    desc = INPUT.TEXT('desc')
    
    return DIV().html(
        HEAD(1, STYLE='float:left;').html('Static DHCP'),
        DIV(STYLE='float:right;margin:20px 0px 10px 20px;').html(
            netops.context(
                BUTTON(CLASS='btn-primary', STYLE='height:39px;').html('Save'),
                'static_dhcp_table_view',
                name,
                stt,
                end,
                desc
            )
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Name'),
            name
        ),
        INPUT.LABEL_TOP('Range'),
        INPUT.GROUP().html(
            INPUT.LABEL_LEFT('Start'),
            stt,
            INPUT.LABEL_LEFT('End'),
            end
        ),
        INPUT.GROUP().html(
            INPUT.LABEL_TOP('Description'),
            desc
        ),
        netops.patch('static_dhcp_table_view')
    )

@PAGE.VIEW(netops)
def static_dhcp_table_view(req, sr_id=None):
    
    if req.method == 'POST':
        StaticRange.add(**req.data)
    elif req.method == 'DELETE':
        StaticRange.remove(int(sr_id))
    
    return netops.table(
        TABLE.SYNC('Name',
                   'Range',
                   'Description',
                   'Action'),
        'static_dhcp_table'
    )

@PAGE.TABLE(netops)
def static_dhcp_table(table):
    srs = StaticRange.list()
    for sr in srs:
        table.record(sr.name,
                     '%s ~ %s' % (sr.stt, sr.end),
                     sr.desc,
                     DIV(STYLE='width:100%;text-align:center;').html(
                         netops.signal(
                             BUTTON(CLASS='btn-danger btn-xs', STYLE='margin:0px;padding:0px 5px;font-size:11px;').html('Delete'),
                             'DELETE',
                             'static_dhcp_table_view', str(sr.id))
                   )
        )
