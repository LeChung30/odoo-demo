{
    'name': 'Real Estate Advertisement',
    'version': '17.0.3.0.0',
    'category': 'Real Estate',
    'summary': 'Professional real estate management with Reports, Dashboard and Security',
    'description': """
Real Estate Advertisement
=========================
Module quản lý bất động sản chuyên nghiệp:
- Kanban view kéo thả theo trạng thái
- Pipeline đề nghị mua (Offer)
- Phân loại theo Property Type
- Tags màu sắc
- Priority stars (yêu thích)
- Chatter + Activities (mail.thread)
- Theo dõi thay đổi field (tracking)
- Báo cáo PDF (Property Detail, Sales Summary)
- Dashboard thống kê (Graph, Pivot)
- Phân quyền Agent / Manager
- Email thông báo tự động
- Hỗ trợ đa ngôn ngữ (i18n)
    """,
    'author': 'Estate Team',
    'depends': ['base', 'mail'],
    'data': [
        # Security (groups first, then access, then rules)
        'security/estate_groups.xml',
        'security/ir.model.access.csv',
        'security/estate_rules.xml',

        # Data
        'data/mail_template_data.xml',

        # Reports
        'report/estate_property_reports.xml',
        'report/estate_property_templates.xml',

        # Views (property_views first - defines estate_property_action used by type_views)
        'views/estate_property_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_offer_statistics_views.xml',
        'views/estate_property_statistics_views.xml',
        'views/estate_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
