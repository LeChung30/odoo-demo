from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MfgBom(models.Model):
    _name = 'mfg.bom'
    _description = 'Bill of Materials (Công thức sản xuất)'
    _order = 'product_id, name'

    name = fields.Char(
        string='Tên BOM',
        required=True,
        default=lambda self: _('BOM mới'),
    )
    product_id = fields.Many2one(
        comodel_name='mfg.product',
        string='Thành phẩm',
        required=True,
        domain=[('product_type', '=', 'finished')],
    )
    product_qty = fields.Float(
        string='Số lượng sản xuất / lần',
        required=True,
        default=1.0,
        digits=(16, 3),
    )
    uom = fields.Char(
        related='product_id.uom',
        string='ĐVT',
        store=True,
    )
    bom_line_ids = fields.One2many(
        comodel_name='mfg.bom.line',
        inverse_name='bom_id',
        string='Thành phần NVL',
        copy=True,
    )
    active = fields.Boolean(default=True)
    note = fields.Text(string='Ghi chú')

    # ── Constraints ───────────────────────────────────────────────
    @api.constrains('product_qty')
    def _check_product_qty(self):
        for rec in self:
            if rec.product_qty <= 0:
                raise ValidationError(_('Số lượng sản xuất phải lớn hơn 0.'))

    # ── Display ───────────────────────────────────────────────────
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f'{rec.name} ({rec.product_id.name})'))
        return result


class MfgBomLine(models.Model):
    _name = 'mfg.bom.line'
    _description = 'Thành phần BOM'
    _order = 'bom_id, product_id'

    bom_id = fields.Many2one(
        comodel_name='mfg.bom',
        string='BOM',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='mfg.product',
        string='Nguyên vật liệu',
        required=True,
        domain=[('product_type', 'in', ['raw', 'consumable'])],
    )
    qty = fields.Float(
        string='Số lượng',
        required=True,
        default=1.0,
        digits=(16, 3),
    )
    uom = fields.Char(
        related='product_id.uom',
        string='ĐVT',
        store=True,
    )

    # ── Constraints ───────────────────────────────────────────────
    @api.constrains('qty')
    def _check_qty(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_('Số lượng NVL phải lớn hơn 0.'))
