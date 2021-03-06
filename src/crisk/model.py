#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2009 José de Paula Eufrásio Júnior <jose.junior@gmail.com>

#    This file is part of Crisk.
#
#    Crisk is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Crisk is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Crisk.  If not, see <http://www.gnu.org/licenses/>.

"""
:mod:`crisk.model`
==================

This module provides the data model for Crisk, using Elixir with the sqlite 
engine.
"""

import datetime
from elixir import *

class Basic(Entity):
    using_options(autosetup = True, tablename = 'basic')
    
    name = Field(Unicode(64))
    location = Field(Unicode(64))
    initial_date = Field(DateTime, default = datetime.datetime.now)
    scope = Field(UnicodeText)
    
class Asset(Entity):
    using_options(autosetup = True, tablename = 'asset')
    
    name = Field(Unicode(64))
    description = Field(UnicodeText)
    __value = Field(Numeric)
    
    vulns = ManyToMany('Vulnerability', ondelete = 'cascade')
    owner = ManyToOne('Owner')
    applied_controls = OneToMany('AppliedControl')
    
    def set_value(self, value):
        self.__value = int(value)

    def get_value(self):
        return self.__value
    
    
    value = property(get_value, set_value)
    
    
class Vulnerability(Entity):
    using_options(autosetup = True, tablename = 'vulnerability')
    
    description = Field(Unicode(256))
    severity = Field(Numeric)
    chance = Field(Numeric)
    assets = ManyToMany('Asset', ondelete = 'cascade')
    threats = ManyToMany('Threat', ondelete = 'cascade')
    applied_controls = OneToMany('AppliedControl')
    
    def __get_total_risk(self):
        try:
            return self.severity * self.chance
        except:
            return 0
    
    total_risk = property(__get_total_risk) 
                           
class Threat(Entity):
    using_options(autosetup = True, tablename = 'threat')
    
    name = Field(Unicode(64))
    description = Field(Unicode(256))
    
    vulns = ManyToMany('Vulnerability', ondelete = 'cascade')
    
class Owner(Entity):
    using_options(autosetup = True, tablename = 'owner')
    
    name = Field(Unicode(64))
    
    assets = OneToMany('Asset')
    
    def __repr__(self):
        return self.name
    
class Control(Entity):
    using_options(autosetup = True, tablename = 'control')
    
    ref = Field(Unicode(16))
    description = Field(Unicode(256))
    long_description = Field(UnicodeText)
    
    applied_controls = OneToMany('AppliedControl')
    
class AppliedControl(Entity):
    using_options(autosetup = True, tablename = 'applied_controls')
    
    control = ManyToOne('Control')
    asset = ManyToOne('Asset')
    vuln = ManyToOne('Vulnerability')
    status = Field(Numeric)