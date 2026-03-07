from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class MfgStockQuant(models.Model):
    _name = 'mfg.stock.quant'
    _description = 'Tồn kho theo vị trí'
    _order = 'product_id, location_id'

    product_id = fields.Many2one(
        comodel_name='mfg.product',
        string='Sản phẩm',
        required=True,
        ondelete='cascade',
        index=True,
    )
    location_id = fields.Many2one(
        comodel_name='mfg.stock.location',
        string='Vị trí kho',
        required=True,
        ondelete='cascade',
        index=True,
        domain=[('location_type', '=', 'internal')],
    )
    qty = fields.Float(
        string='Số lượng tồn',
        digits=(16, 3),
        default=0.0,
    )
    uom = fields.Char(
        string='ĐVT',
        related='product_id.uom',
        store=True,
    )
    is_below_min = fields.Boolean(
        string='Dưới mức tối thiểu',
        compute='_compute_is_below_min',
        store=True,
    )

    _sql_constraints = [
        (
            'unique_product_location',
            'UNIQUE(product_id, location_id)',
            'Mỗi sản phẩm chỉ có một bản ghi tồn kho tại mỗi vị trí.',
        )
    ]

    # ── Computed ─────────────────────────────────────────────────
    @api.depends('qty', 'product_id.min_qty')
    def _compute_is_below_min(self):
        for quant in self:
            quant.is_below_min = quant.qty < quant.product_id.min_qty

    # ── Helpers ───────────────────────────────────────────────────
    @api.model
    def _update_qty(self, product_id, location_id, delta):
        """Cộng/trừ số lượng tồn kho. delta âm = xuất, dương = nhập."""
        quant = self.search([
            ('product_id', '=', product_id),
            ('location_id', '=', location_id),
        ], limit=1)
        if quant:
            new_qty = quant.qty + delta
            if new_qty < 0:
                raise UserError(_(
                    'Tồn kho không đủ tại vị trí "%s" cho sản phẩm "%s".\n'
                    'Tồn hiện tại: %.3f | Yêu cầu xuất: %.3f'
                ) % (quant.location_id.complete_name,
                     quant.product_id.name,
                     quant.qty,
                     abs(delta)))
            quant.qty = new_qty
        else:
            if delta < 0:
                raise UserError(_(
                    'Không có tồn kho tại vị trí này cho sản phẩm "%s".'
                ) % self.env['mfg.product'].browse(product_id).name)
            self.create({
                'product_id': product_id,
                'location_id': location_id,
                'qty': delta,
            })
