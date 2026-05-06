from odoo import api, fields, models, _


class AvrVehicle(models.Model):
    _name = 'avr.vehicle'
    _description = 'Registered Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    name = fields.Char(string='Vehicle Name', compute='_compute_name', store=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    brand = fields.Char(string='Brand', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    make = fields.Char(string='Make')
    year = fields.Integer(string='Year')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid_gasoline', 'Hybrid Gasoline'),
        ('hybrid_diesel', 'Hybrid Diesel'),
        ('electric', 'Electric'),
        ('lpg', 'LPG'),
        ('cng', 'CNG'),
    ], string='Fuel Type', tracking=True)
    vin_number = fields.Char(string='VIN Number', tracking=True)
    registration_no = fields.Char(string='Registration No.', tracking=True)
    transmission_type = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
    ], string='Transmission Type', default='manual')
    vehicle_color = fields.Char(string='Color')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    odometer_ids = fields.One2many('avr.vehicle.odometer', 'vehicle_id', string='Odometer History')
    last_odometer = fields.Float(string='Last Odometer', compute='_compute_last_odometer', store=True)
    booking_count = fields.Integer(compute='_compute_counts', string='Bookings')
    inspection_count = fields.Integer(compute='_compute_counts', string='Inspections')
    repair_count = fields.Integer(compute='_compute_counts', string='Repairs')
    notes = fields.Text(string='Notes')

    @api.depends('brand', 'model', 'registration_no')
    def _compute_name(self):
        for rec in self:
            parts = filter(None, [rec.brand, rec.model, rec.registration_no])
            rec.name = ' / '.join(parts) or _('New Vehicle')

    @api.depends('odometer_ids')
    def _compute_last_odometer(self):
        for rec in self:
            if rec.odometer_ids:
                rec.last_odometer = rec.odometer_ids.sorted('date', reverse=True)[0].value
            else:
                rec.last_odometer = 0.0

    def _compute_counts(self):
        for rec in self:
            rec.booking_count = self.env['avr.booking'].search_count([('vehicle_id', '=', rec.id)])
            rec.inspection_count = self.env['avr.job.card'].search_count([
                ('vehicle_id', '=', rec.id), ('job_card_type', '=', 'inspection')])
            rec.repair_count = self.env['avr.job.card'].search_count([
                ('vehicle_id', '=', rec.id), ('job_card_type', '=', 'repair')])

    def action_view_bookings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bookings'),
            'res_model': 'avr.booking',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
        }

    def action_view_inspections(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspections'),
            'res_model': 'avr.job.card',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id), ('job_card_type', '=', 'inspection')],
        }

    def action_view_repairs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Repairs'),
            'res_model': 'avr.job.card',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id), ('job_card_type', '=', 'repair')],
        }

    _sql_constraints = [
        ('vin_unique', 'UNIQUE(vin_number, company_id)',
         'VIN Number must be unique per company!'),
    ]


class AvrVehicleOdometer(models.Model):
    _name = 'avr.vehicle.odometer'
    _description = 'Vehicle Odometer History'
    _order = 'date desc'

    vehicle_id = fields.Many2one('avr.vehicle', string='Vehicle', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.today)
    value = fields.Float(string='Odometer Value (km)', required=True)
    unit = fields.Selection([('km', 'km'), ('mi', 'mi')], default='km', string='Unit')
    notes = fields.Char(string='Notes')
