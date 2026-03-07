from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MfgStockLocation(models.Model):
    _name = 'mfg.stock.location'
    _description = 'Vị trí kho'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(
        string='Tên vị trí',
        required=True,
    )
    complete_name = fields.Char(
        string='Tên đầy đủ',
        compute='_compute_complete_name',
        store=True,
    )
    parent_id = fields.Many2one(
        comodel_name='mfg.stock.location',
        string='Vị trí cha',
        ondelete='cascade',
        index=True,
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        comodel_name='mfg.stock.location',
        inverse_name='parent_id',
        string='Vị trí con',
    )
    location_type = fields.Selection(
        selection=[
            ('internal', 'Kho nội bộ'),
            ('supplier', 'Nhà cung cấp'),
            ('customer', 'Khách hàng'),
            ('virtual', 'Ảo / Sản xuất'),
        ],
        string='Loại vị trí',
        required=True,
        default='internal',
    )
    active = fields.Boolean(default=True)
    note = fields.Text(string='Ghi chú')

    # ── Computed ─────────────────────────────────────────────────
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for loc in self:
            if loc.parent_id:
                loc.complete_name = f'{loc.parent_id.complete_name} / {loc.name}'
            else:
                loc.complete_name = loc.name

    # ── Constraints ───────────────────────────────────────────────
    @api.constrains('parent_id')
    def _check_no_cycle(self):
        if not self._check_recursion():
            raise ValidationError(_('Không thể tạo vòng lặp trong cây vị trí kho.'))
