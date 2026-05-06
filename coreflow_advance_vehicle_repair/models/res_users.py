from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    avr_role = fields.Selection([
        ('manager', 'Manager'),
        ('supervisor', 'Supervisor'),
        ('receptionist', 'Receptionist'),
        ('technician', 'Technician'),
    ], string='AVR Role', compute='_compute_avr_role', store=False)

    def _compute_avr_role(self):
        get = lambda ref: self.env.ref(ref, raise_if_not_found=False)
        g_manager = get('coreflow_advance_vehicle_repair.group_avr_manager')
        g_supervisor = get('coreflow_advance_vehicle_repair.group_avr_supervisor')
        g_receptionist = get('coreflow_advance_vehicle_repair.group_avr_receptionist')
        g_technician = get('coreflow_advance_vehicle_repair.group_avr_technician')
        for user in self:
            groups = user.groups_id
            if g_manager and g_manager in groups:
                user.avr_role = 'manager'
            elif g_supervisor and g_supervisor in groups:
                user.avr_role = 'supervisor'
            elif g_receptionist and g_receptionist in groups:
                user.avr_role = 'receptionist'
            elif g_technician and g_technician in groups:
                user.avr_role = 'technician'
            else:
                user.avr_role = False
