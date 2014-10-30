# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

class partner_shipper(osv.osv):
    
    _routes = [
        ('north', 'ภาคเหนือ'),
        ('northeast', 'ภาคอีสาน'),
        ('central', 'ภาคกลาง'),
        ('south', 'ภาคใต้'),
        ('other', 'อื่นๆ'),
        ]    
    
    _description='Shippers'
    _name = 'partner.shipper'
    _order = 'name'
    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'route': fields.selection(_routes, 'Route', required=True),
        'street': fields.char('Street', size=256),
        'street2': fields.char('Street2', size=256),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City', size=256),
        'country': fields.many2one('res.country', 'Country'),
        'email': fields.char('Email', size=64),
        'phone': fields.char('Phone', size=64),
        'fax': fields.char('Fax', size=64),
        'dest_contact': fields.text('Destination Contacts'),
        'area_covered': fields.text('Convered Area'),        
        'active': fields.boolean('Active'),
        'note': fields.text('Notes'),
        'partner_ids': fields.many2many('res.partner', string='Partners'),
    }
    _defaults = {
        'active': lambda *a: 1,
    }
    
    def _display_address(self, cr, uid, address, context=None):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''

        # get the information that will be injected into the display format
        # get the address format
        address_format = "%(street)s\n%(street2)s\n%(city)s %(zip)s\nPhone: %(phone)s\n%(country_name)s"
        args = {
            'country_code': address.country and address.country.code or '',
            'country_name': address.country and address.country.name or '',
        }
        address_field = ['street', 'street2', 'zip', 'city', 'phone']
        for field in address_field :
            args[field] = getattr(address, field) or ''

        return address_format % args
        
partner_shipper()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
