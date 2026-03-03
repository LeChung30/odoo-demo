from odoo import models, fields, api, exceptions, _
from datetime import timedelta


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Property Offer'
    _order = 'price desc'

    price = fields.Float(string='Price', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], string='Status', copy=False, default='pending')
    partner_id = fields.Many2one(
        'res.partner', string='Buyer', required=True
    )
    property_id = fields.Many2one(
        'estate.property', string='Property', required=True, ondelete='cascade'
    )
    property_type_id = fields.Many2one(
        related='property_id.property_type_id',
        string='Property Type',
        store=True,
    )
    validity = fields.Integer(string='Validity (days)', default=7)
    date_deadline = fields.Date(
        string='Deadline',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
        store=True,
    )

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        for offer in self:
            base = offer.create_date or fields.Date.today()
            offer.date_deadline = base + timedelta(days=offer.validity)

    def _inverse_date_deadline(self):
        for offer in self:
            base = offer.create_date or fields.Date.today()
            offer.validity = (offer.date_deadline - base.date()).days

    def action_accept(self):
        for offer in self:
            if offer.property_id.state == 'canceled':
                raise exceptions.UserError(
                    _("Cannot accept an offer on a cancelled property!")
                )
            # Refuse all other offers first
            other_offers = offer.property_id.offer_ids.filtered(
                lambda o: o.id != offer.id
            )
            other_offers.write({'status': 'refused'})
            # Accept this offer
            offer.status = 'accepted'
            offer.property_id.write({
                'state': 'offer_accepted',
                'selling_price': offer.price,
                'buyer_id': offer.partner_id.id,
            })
            # Send accepted notification to buyer
            template = self.env.ref(
                'estate.mail_template_offer_accepted',
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(offer.id, force_send=False)
        return True

    def action_refuse(self):
        for offer in self:
            if offer.status == 'accepted':
                offer.property_id.write({
                    'state': 'offer_received',
                    'selling_price': 0,
                    'buyer_id': False,
                })
            offer.status = 'refused'
            # Send refused notification to buyer
            template = self.env.ref(
                'estate.mail_template_offer_refused',
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(offer.id, force_send=False)
        return True

    @api.model
    def create(self, vals):
        property_id = self.env['estate.property'].browse(vals.get('property_id'))
        if property_id.state == 'new':
            property_id.state = 'offer_received'
        if vals.get('price') and property_id.expected_price:
            if vals['price'] < property_id.expected_price * 0.9:
                raise exceptions.UserError(
                    _("The offer price cannot be lower than 90%% of the expected price!")
                )
        offer = super().create(vals)
        # Send notification to salesperson
        template = self.env.ref(
            'estate.mail_template_offer_received',
            raise_if_not_found=False,
        )
        if template and offer.property_id.salesperson_id:
            template.send_mail(offer.id, force_send=False)
        return offer
