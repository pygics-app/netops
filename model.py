# -*- coding: utf-8 -*-
'''
Created on 2017. 6. 13.
@author: HyechurnJang
'''

from bucket import *

bk = FileBucket()

@Bucket.register(bk)
class Environment(Model):
    
    network = Column(String(16))
    netmask = Column(String(16))
    gateway = Column(String(16))
    domain = Column(Text)
    dns_int = Column(Text)
    dns_ext = Column(Text)
    
    def __init__(self):
        self.domain = ''
        self.network = ''
        self.netmask = ''
        self.gateway = ''
        self.dns_int = ''
        self.dns_ext = ''

@Bucket.register(bk)
class Range(Model):
    
    ip_stt = Column(String(16))
    ip_end = Column(String(16))
    ip_lease_num = Column(Integer)
    ip_lease_tag = Column(Text(4))
    
    def __init__(self):
        self.ip_stt = ''
        self.ip_end = ''
        self.ip_lease_num = ''
        self.ip_lease_tag = ''
          
@Bucket.register(bk)
class Host(Model):
    
    name = Column(Text)
    mac = Column(String(24))
    ip = Column(String(16))
    model = Column(Text)
    serial = Column(Text)
    
    def __init__(self, name, mac, ip, model, serial):
        self.name = name
        self.mac = mac
        self.ip = ip
        self.model = model
        self.serial = serial