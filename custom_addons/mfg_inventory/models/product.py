from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MfgProduct(models.Model):
    _name = 'mfg.product'
    _description = 'Sản phẩm kho'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ── Basic Info ──────────────────────────────────────────────
    name = fields.Char(
        string='Tên sản phẩm',
        required=True,
        tracking=True,
    )
    default_code = fields.Char(
        string='Mã SKU',
        tracking=True,
    )
    product_type = fields.Selection(
        selection=[
            ('raw', 'Nguyên vật liệu'),
            ('finished', 'Thành phẩm'),
            ('consumable', 'Vật tư tiêu hao'),
        ],
        string='Loại sản phẩm',
        required=True,
        default='raw',
        tracking=True,
    )
    uom = fields.Char(
        string='Đơn vị tính',
        required=True,
        default='Cái',
    )
    cost_price = fields.Float(
        string='Giá vốn',
        digits=(16, 2),
        tracking=True,
    )
    min_qty = fields.Float(
        string='Tồn kho tối thiểu',
        default=0.0,
        help='Cảnh báo khi tồn kho thực tế xuống dưới ngưỡng này.',
    )
    description = fields.Text(string='Mô tả')
    active = fields.Boolean(default=True)

    # ── Computed ─────────────────────────────────────────────────
    qty_on_hand = fields.Float(
        string='Tồn kho',
        compute='_compute_qty_on_hand',
        store=True,
    )
    stock_quant_ids = fields.One2many(
        comodel_name='mfg.stock.quant',
        inverse_name='product_id',
        string='Tồn kho theo vị trí',
    )
    bom_ids = fields.One2many(
        comodel_name='mfg.bom',
        inverse_name='product_id',
        string='Bill of Materials',
    )
    bom_count = fields.Integer(compute='_compute_bom_count', string='Số BOM')

    # ── Computed Methods ─────────────────────────────────────────
    @api.depends('stock_quant_ids.qty')
    def _compute_qty_on_hand(self):
        for product in self:
            product.qty_on_hand = sum(product.stock_quant_ids.mapped('qty'))

    @api.depends('bom_ids')
    def _compute_bom_count(self):
        for product in self:
            product.bom_count = len(product.bom_ids)

    # ── Constraints ───────────────────────────────────────────────
    @api.constrains('min_qty')
    def _check_min_qty(self):
        for rec in self:
            if rec.min_qty < 0:
                raise ValidationError(_('Tồn kho tối thiểu không thể âm.'))

    # ── Actions ───────────────────────────────────────────────────
    def action_open_boms(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill of Materials',
            'res_model': 'mfg.bom',
            'view_mode': 'list,form',
            'domain': [('product_id', '=', self.id)],
            'context': {'default_product_id': self.id},
        }

    # ── Display Name ──────────────────────────────────────────────
    def name_get(self):
        result = []
        for rec in self:
            name = f'[{rec.default_code}] {rec.name}' if rec.default_code else rec.name
            result.append((rec.id, name))
        return result
