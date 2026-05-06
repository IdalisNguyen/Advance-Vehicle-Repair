from odoo import api, fields, models, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    job_card_id = fields.Many2one(
        'avr.job.card', string='Job Card',
        index=True, ondelete='set null')
    team_id = fields.Many2one(
        'avr.team', string='Repair Team', index=True)
    service_id = fields.Many2one(
        'avr.service', string='Service')
    vehicle_id = fields.Many2one(
        'avr.vehicle', string='Vehicle',
        related='job_card_id.vehicle_id', store=True)

    # Vehicle detail fields (read-only, sourced from job card)
    vehicle_brand = fields.Char(
        string='Brand', related='job_card_id.brand', store=True)
    vehicle_model = fields.Char(
        string='Model', related='job_card_id.model_name', store=True)
    vehicle_registration_no = fields.Char(
        string='Registration No.', related='job_card_id.registration_no', store=True)
    vehicle_fuel_type = fields.Selection(
        related='job_card_id.fuel_type', store=True)
    vehicle_vin = fields.Char(
        string='VIN No.', related='job_card_id.vin_number', store=True)
    vehicle_transmission = fields.Selection(
        related='job_card_id.transmission_type', store=True)

    @api.onchange('job_card_id')
    def _onchange_job_card(self):
        if self.job_card_id:
            self.partner_id = self.job_card_id.customer_id
