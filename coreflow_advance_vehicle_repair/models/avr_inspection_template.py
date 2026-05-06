from odoo import api, fields, models, _


class AvrInspectionTemplate(models.Model):
    _name = 'avr.inspection.template'
    _description = 'Inspection Template'
    _rec_name = 'name'

    name = fields.Char(string='Template Name', required=True)
    template_type = fields.Selection([
        ('classic', 'Classic Full Vehicle Inspection'),
        ('advanced', 'Advanced Inspection'),
        ('quick', 'Quick Check'),
        ('custom', 'Custom'),
    ], string='Template Type', default='classic')
    line_ids = fields.One2many(
        'avr.inspection.template.line', 'template_id',
        string='Inspection Items')
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')

    def action_duplicate(self):
        self.ensure_one()
        new = self.copy({'name': _('%s (Copy)') % self.name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': new.id,
            'view_mode': 'form',
        }


class AvrInspectionTemplateLine(models.Model):
    _name = 'avr.inspection.template.line'
    _description = 'Inspection Template Line'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'avr.inspection.template', string='Template',
        required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    part = fields.Char(string='Part / Area', required=True)
    category = fields.Selection([
        ('exterior', 'Exterior'),
        ('interior', 'Interior'),
        ('under_hood', 'Under Hood / Manufacturer Parts'),
        ('under_vehicle', 'Under Vehicle / Parts'),
        ('wheels', 'Wheel / Fluid'),
        ('transmission', 'Transmission'),
        ('other', 'Other'),
    ], string='Category', default='exterior')
    description = fields.Char(string='Description')
    is_required = fields.Boolean(string='Required', default=True)


class AvrJobCardInspectionLine(models.Model):
    _name = 'avr.job.card.inspection.line'
    _description = 'Job Card Inspection Line'
    _order = 'sequence, id'

    job_card_id = fields.Many2one(
        'avr.job.card', string='Job Card',
        required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    part = fields.Char(string='Part / Area', required=True)
    category = fields.Selection([
        ('exterior', 'Exterior'),
        ('interior', 'Interior'),
        ('under_hood', 'Under Hood / Manufacturer Parts'),
        ('under_vehicle', 'Under Vehicle / Parts'),
        ('wheels', 'Wheel / Fluid'),
        ('transmission', 'Transmission'),
        ('other', 'Other'),
    ], string='Category', default='exterior')
    condition = fields.Selection([
        ('ok', 'Checked OK / Good at this time'),
        ('attention', 'Requires future attention'),
        ('immediate', 'Requires immediate attention'),
    ], string='Condition', default='ok')
    notes = fields.Char(string='Notes / Remarks')
    image_ids = fields.Many2many(
        'ir.attachment', string='Photos',
        relation='avr_insp_line_attachment_rel',
        column1='line_id', column2='attachment_id')
