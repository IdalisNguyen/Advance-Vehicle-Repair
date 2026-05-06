{
    'name': 'Advance Vehicle Repair Management',
    'version': '18.0.1.0.0',
    'category': 'Services/Repair',
    'summary': 'End-to-end vehicle repair workflow: bookings, inspections, job cards, quotation & tasks',
    'description': """
        Advance Vehicle Repair Management covers:
        - Website booking portal (Inspection / Repair / Inspect+Repair)
        - Booking management with source tracking
        - Inspection & Repair Job Cards with configurable stages
        - Inspection templates with checklist lines
        - Customer & vehicle registration
        - Task assignment to teams
        - Dashboard with KPIs and charts
        - Role-based access: Manager, Supervisor, Receptionist, Technician
    """,
    'author': 'Custom Development',
    'website': 'https://www.odoo.com/apps',
    'license': 'LGPL-3',
    'price': 89.0,
    'currency': 'USD',
    'depends': [
        'base', 'mail', 'fleet', 'project',
        'sale_management', 'website', 'hr', 'stock',
        'account', 'portal',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/avr_sale_products.xml',
        'data/stage_data.xml',
        'views/avr_vehicle_views.xml',
        'views/avr_booking_views.xml',
        'views/avr_inspection_template_views.xml',
        'views/avr_job_card_views.xml',
        'views/avr_task_views.xml',
        'views/avr_team_views.xml',
        'views/avr_spare_part_views.xml',
        'views/avr_service_views.xml',
        'views/avr_dashboard_views.xml',
        'views/res_users_views.xml',
        'views/menus.xml',
        'views/website_booking_templates.xml',
    ],
    'demo': [
        'demo/avr_demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'coreflow_advance_vehicle_repair/static/src/css/dashboard.css',
            'coreflow_advance_vehicle_repair/static/src/js/dashboard.js',
        ],
        'website.assets_frontend': [
            'coreflow_advance_vehicle_repair/static/src/css/website_booking.css',
        ],
    },
    'installable': True,
    'application': True,
}
