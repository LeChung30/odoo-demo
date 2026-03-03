from odoo import models, fields, api, exceptions, _


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Property Type'
    _order = 'sequence, name'

    name = fields.Char(string='Property Type', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')

    property_ids = fields.One2many(
        'estate.property', 'property_type_id', string='Properties'
    )
    property_count = fields.Integer(
        string='Properties', compute='_compute_property_count'
    )
    offer_ids = fields.Many2many(
        'estate.property.offer',
        compute='_compute_offer_ids',
        string='Offers'
    )
    offer_count = fields.Integer(
        string='Offers', compute='_compute_offer_count'
    )

    @api.depends('property_ids')
    def _compute_property_count(self):
        for ptype in self:
            ptype.property_count = len(ptype.property_ids)

    @api.depends('property_ids.offer_ids')
    def _compute_offer_ids(self):
        for ptype in self:
            ptype.offer_ids = ptype.property_ids.mapped('offer_ids')

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for ptype in self:
            ptype.offer_count = len(ptype.offer_ids)
