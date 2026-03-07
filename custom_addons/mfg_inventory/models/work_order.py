from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MfgWorkOrder(models.Model):
    _name = 'mfg.work.order'
    _description = 'Lệnh sản xuất'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, name desc'

    # ── Core Fields ───────────────────────────────────────────────
    name = fields.Char(
        string='Số lệnh SX',
        readonly=True,
        default='/',
        copy=False,
    )
    bom_id = fields.Many2one(
        comodel_name='mfg.bom',
        string='Bill of Materials',
        required=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        comodel_name='mfg.product',
        string='Thành phẩm',
        related='bom_id.product_id',
        store=True,
        readonly=True,
    )
    qty_to_produce = fields.Float(
        string='Số lượng sản xuất',
        required=True,
        default=1.0,
        digits=(16, 3),
        tracking=True,
    )
    uom = fields.Char(
        related='product_id.uom',
        string='ĐVT',
        store=True,
    )
    location_dest_id = fields.Many2one(
        comodel_name='mfg.stock.location',
        string='Nhập thành phẩm vào',
        required=True,
        domain=[('location_type', '=', 'internal')],
        tracking=True,
        help='Vị trí kho nhận thành phẩm khi lệnh sản xuất hoàn thành.',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('in_progress', 'Đang sản xuất'),
            ('done', 'Hoàn thành'),
            ('cancelled', 'Đã huỷ'),
        ],
        string='Trạng thái',
        default='draft',
        tracking=True,
        readonly=True,
        group_expand='_expand_states',
    )
    date_start = fields.Datetime(
        string='Ngày bắt đầu',
        tracking=True,
    )
    date_end = fields.Datetime(
        string='Ngày hoàn thành',
        tracking=True,
    )
    note = fields.Text(string='Ghi chú')

    # ── Constraints ───────────────────────────────────────────────
    @api.constrains('qty_to_produce')
    def _check_qty(self):
        for rec in self:
            if rec.qty_to_produce <= 0:
                raise ValidationError(_('Số lượng sản xuất phải lớn hơn 0.'))

    # ── Group expand for Kanban ───────────────────────────────────
    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, _val in self._fields['state'].selection]

    # ── Actions ───────────────────────────────────────────────────
    def action_start(self):
        """Draft → In Progress: kiểm tra & trừ NVL."""
        Quant = self.env['mfg.stock.quant']
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Chỉ có thể bắt đầu lệnh SX ở trạng thái Nháp.'))
            if not rec.bom_id.bom_line_ids:
                raise UserError(_(
                    'BOM "%s" chưa có thành phần NVL nào. Vui lòng thêm NVL vào BOM trước.'
                ) % rec.bom_id.name)

            # Tính hệ số: qty_to_produce / bom product_qty
            ratio = rec.qty_to_produce / rec.bom_id.product_qty

            # Kiểm tra đủ tồn NVL trước khi trừ
            for line in rec.bom_id.bom_line_ids:
                # Vật tư tiêu hao không chặn lệnh sản xuất khi không theo dõi tồn nghiêm ngặt.
                if line.product_id.product_type == 'consumable':
                    continue
                needed = line.qty * ratio
                available = sum(
                    Quant.search([('product_id', '=', line.product_id.id)]).mapped('qty')
                )
                if available < needed:
                    raise UserError(_(
                        'Không đủ tồn kho cho NVL "%s".\n'
                        'Cần: %.3f %s | Tồn hiện tại: %.3f %s'
                    ) % (line.product_id.name, needed, line.product_id.uom,
                         available, line.product_id.uom))

            # Trừ NVL — lấy vị trí internal có số lượng > 0
            for line in rec.bom_id.bom_line_ids:
                if line.product_id.product_type == 'consumable':
                    continue
                needed = line.qty * ratio
                # Lấy quants của sản phẩm này, ưu tiên đủ số lượng
                quants = Quant.search([
                    ('product_id', '=', line.product_id.id),
                    ('qty', '>', 0),
                ], order='qty desc')
                remaining = needed
                for quant in quants:
                    if remaining <= 0:
                        break
                    deduct = min(quant.qty, remaining)
                    quant.qty -= deduct
                    remaining -= deduct

            rec.date_start = fields.Datetime.now()
            rec.state = 'in_progress'

    def action_done(self):
        """In Progress → Done: nhập thành phẩm vào kho."""
        Quant = self.env['mfg.stock.quant']
        StockMove = self.env['mfg.stock.move']
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError(_('Chỉ có thể hoàn thành lệnh SX đang thực hiện.'))

            # Nhập thành phẩm
            Quant._update_qty(
                rec.product_id.id,
                rec.location_dest_id.id,
                rec.qty_to_produce,
            )

            # Tạo phiếu nhập kho tự động (trạng thái Done)
            move = StockMove.create({
                'name': StockMove._default_name() if hasattr(StockMove, '_default_name') else '/',
                'move_type': 'in',
                'product_id': rec.product_id.id,
                'qty': rec.qty_to_produce,
                'location_dest_id': rec.location_dest_id.id,
                'state': 'done',
                'ref': rec.name,
                'note': _('Phiếu nhập tự động từ lệnh sản xuất %s') % rec.name,
            })
            # Gán tên sequence nếu chưa có
            if move.name == '/':
                move.name = self.env['ir.sequence'].next_by_code('mfg.stock.move') or '/'

            rec.date_end = fields.Datetime.now()
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(_('Không thể huỷ lệnh SX đã hoàn thành.'))
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
                vals['name'] = self.env['ir.sequence'].next_by_code('mfg.work.order') or '/'
        return super().create(vals_list)
