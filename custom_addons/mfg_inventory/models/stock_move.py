from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MfgStockMove(models.Model):
    _name = 'mfg.stock.move'
    _description = 'Phiếu kho (Nhập / Xuất / Điều chuyển)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    # ── Core Fields ───────────────────────────────────────────────
    name = fields.Char(
        string='Số phiếu',
        readonly=True,
        default='/',
    )
    move_type = fields.Selection(
        selection=[
            ('in', 'Nhập kho'),
            ('out', 'Xuất kho'),
            ('transfer', 'Điều chuyển'),
        ],
        string='Loại phiếu',
        required=True,
        default='in',
        tracking=True,
    )
    product_id = fields.Many2one(
        comodel_name='mfg.product',
        string='Sản phẩm',
        required=True,
        tracking=True,
    )
    qty = fields.Float(
        string='Số lượng',
        required=True,
        digits=(16, 3),
        tracking=True,
    )
    location_src_id = fields.Many2one(
        comodel_name='mfg.stock.location',
        string='Từ vị trí',
        tracking=True,
    )
    location_dest_id = fields.Many2one(
        comodel_name='mfg.stock.location',
        string='Đến vị trí',
        tracking=True,
    )
    date = fields.Datetime(
        string='Ngày',
        default=fields.Datetime.now,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('confirmed', 'Đã xác nhận'),
            ('done', 'Hoàn thành'),
            ('cancelled', 'Đã huỷ'),
        ],
        string='Trạng thái',
        default='draft',
        tracking=True,
        readonly=True,
    )
    ref = fields.Char(string='Tham chiếu')
    note = fields.Text(string='Ghi chú')

    # ── Computed ─────────────────────────────────────────────────
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
                raise UserError(_('Số lượng phải lớn hơn 0.'))

    @api.constrains('move_type', 'location_src_id', 'location_dest_id')
    def _check_locations(self):
        for rec in self:
            if rec.move_type == 'in' and not rec.location_dest_id:
                raise UserError(_('Phiếu nhập kho cần chỉ định vị trí đến.'))
            if rec.move_type == 'out' and not rec.location_src_id:
                raise UserError(_('Phiếu xuất kho cần chỉ định vị trí xuất.'))
            if rec.move_type == 'transfer' and (
                not rec.location_src_id or not rec.location_dest_id
            ):
                raise UserError(_('Phiếu điều chuyển cần chỉ định cả vị trí xuất và vị trí đến.'))

    # ── Actions ───────────────────────────────────────────────────
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chỉ có thể xác nhận phiếu ở trạng thái Nháp.'))
            rec.state = 'confirmed'

    def action_validate(self):
        Quant = self.env['mfg.stock.quant']
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('Chỉ có thể hoàn thành phiếu đã xác nhận.'))

            if rec.move_type == 'in':
                Quant._update_qty(rec.product_id.id, rec.location_dest_id.id, rec.qty)

            elif rec.move_type == 'out':
                Quant._update_qty(rec.product_id.id, rec.location_src_id.id, -rec.qty)

            elif rec.move_type == 'transfer':
                Quant._update_qty(rec.product_id.id, rec.location_src_id.id, -rec.qty)
                Quant._update_qty(rec.product_id.id, rec.location_dest_id.id, rec.qty)

            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('Không thể huỷ phiếu đã hoàn thành.'))
            rec.state = 'cancelled'

    def action_reset_draft(self):
        for rec in self:
            if rec.state == 'cancelled':
                rec.state = 'draft'

    # ── ORM ───────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('mfg.stock.move') or '/'
        return super().create(vals_list)
