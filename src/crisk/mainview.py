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
:mod:`crisk.mainview`
=====================

This module manages the main window of the Crisk app, using Kiwi GladeView as base view
for the other SlaveViews.
"""

import gtk
import pygtk
import sys, os
import kiwi.environ
import gettext

from elixir import *
from os import path
from kiwi.ui.dialogs import error, warning, yesno, save, messagedialog
from kiwi.ui.dialogs import open as open_dialog
from kiwi.ui.objectlist import Column, ObjectList
from kiwi.currency import currency
from kiwi.ui.widgets import textview, label, entry
from kiwi.ui.delegates import GladeDelegate, GladeSlaveDelegate, ProxySlaveDelegate
from kiwi.environ import environ
from geraldo.generators import PDFGenerator

# Pedacos do programa

import crisk
from model import *
from basicsview import BasicsView
from inventoryview import InventoryView
from vulnerabilitiesview import VulnerabilitiesView
from controlsview import ControlsView

_ = gettext.gettext

class Step:
    """    
    Simple placeholder class for the maintree.
    
    :param name: name of the new step
    :param idx: index on the main tree
    :type name: String
    :type idx: Integer
    :rtype: :class:`Step` instance
    """
    def __init__(self, name, idx):
        self.name = name
        self.idx = idx        
        
class MainView(GladeDelegate):
    """
    The Kiwi BaseView, using GladeDelegate. Provides the main tree, menu bars and
    status bar. Also provides the placeholder frame on the right where the kiwi
    SlaveViews will be shown.
    """
    
    db_file = None

    def __init__(self):
        
        GladeDelegate.__init__(self, "ui", toplevel_name = 'MainWindow', 
                               delete_handler = self.on_exit__activate)        
        self.tree = self.get_widget('maintree')        
        tree = self.tree
        cols =  [ Column('name', title=_('Step'), data_type = str, expand = True) ]
        tree.set_columns(cols)
        tree.set_headers_visible(False)
        basics = tree.append(None, Step(_('Assessment'), 0))
        first = tree.append(basics, Step(_('Target Information'), 1))
        self.first = first
        tree.append(basics, Step(_('Inventory'), 2))
        tree.append(basics, Step(_('Vulnerabilities'), 3))
        tree.expand(basics)
        controls = tree.append(None, Step(_('Treatment'), 4))
        self.first_control = tree.append(controls, Step(_('Control Library'), 5))
        tree.append(controls, Step(_('Applied Controls'), 5))

        # Open or create a file before doing much
        if self.db_file is None:
            self.open_or_new()   
        
        tree.expand(controls)
        tree.select(self.first)
        icon = environ.find_resource('pixmaps', 'criskicon.png')
        __window = self.get_widget('MainWindow')
        __window.set_icon_from_file(icon)


    
    def open_or_new(self):
        """
        Shows a dialog with options for opening a file or creating a new one. Used
        on the startup to provide a ``db_file``
        """
        result = yesno(_('Do you want to open a previous file?\n\n') + 
                       _('Choose \'Yes\' to open a previous work, or\n') + 
                       _('choose \'No\' if you want to create a new DB')) 
        if result == gtk.RESPONSE_YES:
            res = self.on_open__activate()
            if res is None:
                sys.exit()
        elif result == gtk.RESPONSE_NO:
            res = self.on_new__activate()
            if res is None:
                sys.exit()
        else:
            sys.exit()
    
    def check_and_detach(self):
        """
        Checks if there is a slave attached to the mainview and detaches it if true.
        """
        if self.get_slave('placeholder') is not None:
            self.detach_slave('placeholder')
    
    def on_maintree__selection_changed(self, *args):
        tree, step = args
        self.check_and_detach()
        index = step.idx
        if index == 0:
            tree.select(self.first)
        if index == 1:
            slave = BasicsView() 
            self.attach_slave('placeholder', slave)
        if index == 2:
            slave = InventoryView(parent = self)
            self.attach_slave('placeholder', slave)
        if index == 3:
            slave = VulnerabilitiesView(parent = self)
            self.attach_slave('placeholder', slave)
        if index == 4:
            tree.select(self.first_control)
        if index == 5:
            slave = ControlsView(parent = self)
            self.attach_slave('placeholder', slave)  
                        
    def on_about__activate(self, *args):
        diag = gtk.AboutDialog()
        logofile = environ.find_resource('pixmaps', 'aboutlogo.png')
        logo = gtk.gdk.pixbuf_new_from_file(logofile)
        diag.set_logo(logo)
        diag.set_name('Crisk')
        diag.set_version(crisk.__version__)
        diag.set_copyright('Copyright 2009 - José de Paula E. Júnior')
        diag.set_authors(['José de Paula E. Júnior <jose.junior@gmail.com>'])
        diag.set_comments(_('A simple risk management tool'))
        diag.set_website('https://coredump.github.com/crisk')
        diag.set_license(crisk.__license__)
        x = diag.run()
        diag.hide()
        
    def on_open__activate(self, *args):
        filter = gtk.FileFilter()
        filter.add_pattern('*.crisk')
        selected_file = open_dialog(_('Open'), filter = filter)
        if selected_file is None:
            return None
        try:
            db_url = 'sqlite:///%s' % selected_file
            metadata.bind = db_url
            metadata.bind.echo = False
            metadata.bind.has_table('model_asset')
            setup_all()
            self.db_file = selected_file
            self.tree.select(self.first)
            return True
        except Exception, info:
            error(_('Error opening database'), str(info))
        
    def on_new__activate(self, *args):
        new_file = save(_('Save'))        
        if new_file is None:
            return None

        if not new_file.endswith('.crisk'):
            new_file = new_file + '.crisk'
        
        try:
            db_url = 'sqlite:///%s' % new_file
            metadata.bind = db_url
            metadata.bind.echo = False
            setup_all()
            create_all()
            tmp = Basic()
            session.commit()
            self.db_file = new_file
            self.tree.select(self.first)
            return True
        except Exception, info:
            res = error(_("An error has ocurred"), info.__str__())
    
    def on_inventory_report__activate(self, *args):
        from crisk.reports.invent_report import InventoryReport
        filename = save(_('Save report'),
                        current_name = _('Inventory Report.pdf'))
        if filename is not None:
            assets = Asset.query().all()
            report = InventoryReport(queryset = assets)
            report.generate_by(PDFGenerator, filename = filename)
            
    def on_total_asset_report__activate(self, *args):
        pass
    
    def on_total_vuln_report__activate(self, *args):
        from crisk.reports.vuln_report import TotalVulnReport
        filename = save(_('Save report'),
                        current_name = _('Total Vulnerability Risk Report.pdf'))
        if filename is not None:
            vulns = Vulnerability.query().all()
            report = TotalVulnReport(queryset = vulns)
            report.generate_by(PDFGenerator, filename)
        
    def on_exit__activate(self, *args):
        session.commit()
        gtk.main_quit()