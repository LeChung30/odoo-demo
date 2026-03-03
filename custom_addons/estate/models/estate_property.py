from odoo import models, fields, api, exceptions, _


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── Basic Info ───────────────────────────────────────────────
    name = fields.Char(string='Property Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    postcode = fields.Char(string='Postcode')
    date_availability = fields.Date(string='Available From', copy=False)
    active = fields.Boolean(string='Active', default=True)

    # ── Classification ───────────────────────────────────────────
    property_type_id = fields.Many2one(
        'estate.property.type', string='Property Type', tracking=True
    )
    tag_ids = fields.Many2many(
        'estate.property.tag', string='Tags'
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Favorite'),
    ], string='Priority', default='0')

    # ── State ────────────────────────────────────────────────────
    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled'),
    ], string='Status', required=True, copy=False, default='new',
       group_expand='_expand_states', tracking=True)

    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready'),
        ('blocked', 'Blocked'),
    ], string='Kanban State', default='normal', copy=False)

    # ── Pricing ──────────────────────────────────────────────────
    expected_price = fields.Float(
        string='Expected Price', required=True, tracking=True
    )
    selling_price = fields.Float(
        string='Selling Price', copy=False, tracking=True
    )
    unit_price = fields.Float(
        string='Price per m²',
        compute='_compute_unit_price',
        store=True,
    )

    # ── Physical Attributes ──────────────────────────────────────
    bedrooms = fields.Integer(string='Bedrooms', default=2)
    living_area = fields.Integer(string='Living Area (m²)')
    facades = fields.Integer(string='Facades')
    garage = fields.Boolean(string='Garage')
    garden = fields.Boolean(string='Garden')
    garden_area = fields.Integer(string='Garden Area (m²)')
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
    ], string='Garden Orientation')

    # ── People ──────────────────────────────────────────────────
    salesperson_id = fields.Many2one(
        'res.users', string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True,
    )
    buyer_id = fields.Many2one(
        'res.partner', string='Buyer', copy=False, tracking=True,
    )

    # ── Offers ───────────────────────────────────────────────────
    offer_ids = fields.One2many(
        'estate.property.offer', 'property_id', string='Offers'
    )
    offer_count = fields.Integer(
        string='Offers', compute='_compute_offer_count'
    )

    # ── Computed Fields ──────────────────────────────────────────
    color = fields.Integer(string='Color Index')
    best_price = fields.Float(
        string='Best Offer',
        compute='_compute_best_price',
    )

    @api.depends('selling_price', 'living_area')
    def _compute_unit_price(self):
        for rec in self:
            if rec.living_area and rec.selling_price:
                rec.unit_price = rec.selling_price / rec.living_area
            else:
                rec.unit_price = 0.0

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for rec in self:
            rec.best_price = max(rec.offer_ids.mapped('price'), default=0.0)

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for rec in self:
            rec.offer_count = len(rec.offer_ids)

    def _expand_states(self, states, domain, order):
        """Always show all kanban columns even if empty."""
        return [key for key, _ in type(self).state.selection]

    # ── Actions ──────────────────────────────────────────────────
    def action_sold(self):
        for rec in self:
            if rec.state == 'canceled':
                raise exceptions.UserError(
                    _("Cannot sell a cancelled property!")
                )
            rec.state = 'sold'
            # Send notification email to buyer
            template = self.env.ref(
                'estate.mail_template_property_sold',
                raise_if_not_found=False,
            )
            if template and rec.buyer_id:
                template.send_mail(rec.id, force_send=False)
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == 'sold':
                raise exceptions.UserError(
                    _("Cannot cancel a sold property!")
                )
            rec.state = 'canceled'
        return True

    def action_view_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Offers'),
            'res_model': 'estate.property.offer',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    # ── Constraints ───────────────────────────────────────────────
    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for rec in self:
            if (rec.selling_price > 0
                    and rec.expected_price > 0
                    and rec.selling_price < rec.expected_price * 0.9):
                raise exceptions.ValidationError(
                    _("Selling price cannot be lower than 90%% of the expected price.")
                )