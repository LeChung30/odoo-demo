{
    'name': 'Kho & Sản xuất',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Quản lý kho hàng và lệnh sản xuất chuyên nghiệp',
    'description': """
Kho & Sản xuất
==============
Module quản lý kho và sản xuất:
- Quản lý sản phẩm (NVL, thành phẩm, vật tư tiêu hao)
- Cây vị trí kho (Warehouse Locations)
- Phiếu nhập / xuất / điều chuyển kho
- Theo dõi tồn kho theo vị trí
- Cảnh báo tồn kho dưới mức tối thiểu
- Bill of Materials (công thức sản xuất)
- Lệnh sản xuất với Kanban board
- Tự động trừ NVL và nhập thành phẩm
- Phân quyền Inventory User / Manager
    """,
    'author': 'MFG Team',
    'depends': ['base', 'mail'],
    'data': [
        # Security
        'security/mfg_groups.xml',
        'security/ir.model.access.csv',

        # Data
        'data/mfg_sequence.xml',

        # Views
        'views/product_views.xml',
        'views/stock_location_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_move_views.xml',
        'views/bom_views.xml',
        'views/work_order_views.xml',
        'views/mfg_menus.xml',

        # Demo
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
