from odoo import api, fields, models


class AvrTeam(models.Model):
    _name = 'avr.team'
    _description = 'Repair Team'
    _rec_name = 'name'

    name = fields.Char(string='Team Name', required=True)
    team_type = fields.Selection([
        ('mechanical', 'Mechanical Repair Team'),
        ('electrical', 'Electrical & ECU Diagnostics Team'),
        ('bodywork', 'Bodywork, Paint & Dent Repair Team'),
        ('inspection', 'Vehicle Inspection & Diagnostic Team'),
        ('other', 'Other'),
    ], string='Team Type', default='mechanical')
    member_ids = fields.Many2many('res.users', string='Team Members')
    leader_id = fields.Many2one('res.users', string='Team Leader')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')
    task_count = fields.Integer(compute='_compute_task_count', string='Tasks')

    def _compute_task_count(self):
        for rec in self:
            rec.task_count = self.env['project.task'].search_count([
                ('team_id', '=', rec.id)])


class AvrSparePart(models.Model):
    _name = 'avr.spare.part'
    _description = 'Spare Part Master'
    _rec_name = 'name'

    name = fields.Char(string='Part Name', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    part_number = fields.Char(string='Part Number')
    brand = fields.Char(string='Brand / OEM')
    category_id = fields.Many2one('product.category', string='Category')
    list_price = fields.Float(string='List Price', digits=(16, 2))
    active = fields.Boolean(default=True)


class AvrService(models.Model):
    _name = 'avr.service'
    _description = 'Repair / Inspection Service'
    _rec_name = 'name'

    name = fields.Char(string='Service Name', required=True)
    service_type = fields.Selection([
        ('inspection', 'Inspection'),
        ('repair', 'Repair'),
        ('maintenance', 'Maintenance'),
        ('diagnostic', 'Diagnostic'),
    ], string='Service Type', default='repair')
    list_price = fields.Float(string='Price', digits=(16, 2))
    duration = fields.Float(string='Estimated Duration (hrs)')
    product_id = fields.Many2one('product.product', string='Linked Product')
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
