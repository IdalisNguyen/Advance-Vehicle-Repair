from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AvrBooking(models.Model):
    _name = 'avr.booking'
    _description = 'Vehicle Repair Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'booking_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Booking Reference', required=True, copy=False,
        readonly=True, default='New', tracking=True)

    # ── Booking type & source ──────────────────────────────────────────────────
    booking_type = fields.Selection([
        ('inspection_only', 'Vehicle Inspection'),
        ('repair_only', 'Repair Only'),
        ('inspection_repair', 'Vehicle Inspection + Repair'),
    ], string='Booking Type', required=True, default='repair_only', tracking=True)

    booking_source = fields.Selection([
        ('website', 'Website'),
        ('walk_in', 'Walk-in'),
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('fleet', 'Vehicle from Fleet'),
    ], string='Booking Source', default='walk_in', tracking=True)

    vehicle_source = fields.Selection([
        ('fleet', 'Vehicle from Fleet'),
        ('customer', 'Vehicle from Customer'),
    ], string='Vehicle Source', default='customer', tracking=True)

    # ── Dates & time ──────────────────────────────────────────────────────────
    booking_date = fields.Datetime(
        string='Booking Date', default=fields.Datetime.now, tracking=True)
    preferred_date = fields.Date(string='Preferred Date', tracking=True)
    preferred_time_slot = fields.Char(string='Preferred Time Slot')
    appointment_date = fields.Datetime(string='Appointment Date', tracking=True)

    # ── Customer ──────────────────────────────────────────────────────────────
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        tracking=True, index=True)
    phone = fields.Char(string='Phone', related='customer_id.phone', store=True)
    email = fields.Char(string='Email', related='customer_id.email', store=True)
    street = fields.Char(string='Street 1')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip_code = fields.Char(string='ZIP / Pincode')
    country_id = fields.Many2one('res.country', string='Country')

    # ── Vehicle ───────────────────────────────────────────────────────────────
    vehicle_id = fields.Many2one('avr.vehicle', string='Registered Vehicle')
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    brand = fields.Char(string='Brand')
    model_name = fields.Char(string='Model')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'), ('diesel', 'Diesel'),
        ('hybrid_gasoline', 'Hybrid Gasoline'), ('hybrid_diesel', 'Hybrid Diesel'),
        ('electric', 'Electric'), ('lpg', 'LPG'), ('cng', 'CNG'),
    ], string='Fuel Type')
    vin_number = fields.Char(string='VIN No.')
    registration_no = fields.Char(string='Registration No.')
    transmission_type = fields.Selection([
        ('manual', 'Manual'), ('automatic', 'Automatic'), ('cvt', 'CVT'),
    ], string='Transmission Type', default='manual')

    # ── Issue description ──────────────────────────────────────────────────────
    issue_description = fields.Text(string='Describe the Issue / Required Services')

    # ── State ─────────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('new', 'New'),
        ('quotation', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='new', tracking=True, index=True)

    # ── Relations ─────────────────────────────────────────────────────────────
    job_card_ids = fields.One2many('avr.job.card', 'booking_id', string='Job Cards')
    job_card_count = fields.Integer(compute='_compute_job_card_count', string='Job Cards')
    inspection_count = fields.Integer(compute='_compute_job_card_count')
    repair_count = fields.Integer(compute='_compute_job_card_count')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    receptionist_id = fields.Many2one('res.users', string='Receptionist')
    notes = fields.Text(string='Internal Notes')
    sale_order_id = fields.Many2one('sale.order', string='Quotation / Sale Order', copy=False, tracking=True)
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sale Orders')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)

    # ── Website token (portal access) ─────────────────────────────────────────
    access_token = fields.Char(string='Access Token', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('avr.booking') or 'New'
        return super().create(vals_list)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            v = self.vehicle_id
            self.brand = v.brand
            self.model_name = v.model
            self.fuel_type = v.fuel_type
            self.vin_number = v.vin_number
            self.registration_no = v.registration_no
            self.transmission_type = v.transmission_type

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.street = self.customer_id.street
            self.city = self.customer_id.city
            self.state_id = self.customer_id.state_id
            self.zip_code = self.customer_id.zip
            self.country_id = self.customer_id.country_id

    def _compute_job_card_count(self):
        for rec in self:
            cards = rec.job_card_ids
            rec.job_card_count = len(cards)
            rec.inspection_count = len(cards.filtered(lambda c: c.job_card_type == 'inspection'))
            rec.repair_count = len(cards.filtered(lambda c: c.job_card_type == 'repair'))

    @api.depends('job_card_ids.total_amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(rec.job_card_ids.mapped('total_amount'))

    @api.depends('sale_order_id')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = 1 if rec.sale_order_id else 0

    def _prepare_sale_order_values(self):
        self.ensure_one()
        return {
            'partner_id': self.customer_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
        }

    def _prepare_sale_order_lines(self):
        self.ensure_one()
        line_commands = []
        for job_card in self.job_card_ids.filtered(lambda c: c.job_card_type == 'repair'):
            line_commands.extend(job_card._prepare_sale_order_line_commands())
        return line_commands

    def _validate_outgoing_pickings(self, sale_order):
        for picking in sale_order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
            picking.action_assign()
            for move in picking.move_ids_without_package:
                if move.product_uom_qty and move.quantity == 0:
                    move.quantity = move.product_uom_qty
            picking.button_validate()

    # ── Actions ───────────────────────────────────────────────────────────────
    def action_create_quotation(self):
        for rec in self:
            if rec.state not in ('new', 'quotation'):
                raise UserError(_('Quotation can only be created from New state.'))
            if not rec.job_card_ids.filtered(lambda c: c.job_card_type == 'repair'):
                raise UserError(_('Please create at least one Repair Job Card before generating quotation.'))
            if rec.sale_order_id:
                continue

            order_lines = rec._prepare_sale_order_lines()
            if not order_lines:
                raise UserError(_('No saleable service/spare part lines found in repair job cards.'))

            sale_order = self.env['sale.order'].create({
                **rec._prepare_sale_order_values(),
                'order_line': order_lines,
            })
            rec.sale_order_id = sale_order.id
            rec.job_card_ids.filtered(lambda c: c.job_card_type == 'repair').write({'sale_order_id': sale_order.id})
            rec.state = 'quotation'

        if len(self) == 1 and self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Quotation'),
                'res_model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'view_mode': 'form',
            }
        return True

    def action_confirm(self):
        for rec in self:
            if rec.state != 'quotation':
                raise UserError(_('Only quotation bookings can be confirmed.'))
            if not rec.sale_order_id:
                raise UserError(_('Please create quotation before confirmation.'))
            if rec.sale_order_id.state in ('draft', 'sent'):
                rec.sale_order_id.action_confirm()
            rec._validate_outgoing_pickings(rec.sale_order_id)
            rec.state = 'confirmed'

    def action_start_progress(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_('Only confirmed bookings can be moved to In Progress.'))
            rec.state = 'in_progress'

    def action_complete(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError(_('Only In Progress bookings can be completed.'))
            rec.state = 'completed'

    def action_mark_paid(self):
        for rec in self:
            if rec.state != 'completed':
                raise UserError(_('Only completed bookings can be marked as paid.'))
            rec.state = 'paid'

    def action_create_inspection_job_card(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Inspection Job Card'),
            'res_model': 'avr.job.card',
            'view_mode': 'form',
            'context': {
                'default_booking_id': self.id,
                'default_customer_id': self.customer_id.id,
                'default_vehicle_id': self.vehicle_id.id,
                'default_job_card_type': 'inspection',
            },
        }

    def action_create_repair_job_card(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Repair Job Card'),
            'res_model': 'avr.job.card',
            'view_mode': 'form',
            'context': {
                'default_booking_id': self.id,
                'default_customer_id': self.customer_id.id,
                'default_vehicle_id': self.vehicle_id.id,
                'default_job_card_type': 'repair',
            },
        }

    def action_view_job_cards(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Job Cards'),
            'res_model': 'avr.job.card',
            'view_mode': 'list,form',
            'domain': [('booking_id', '=', self.id)],
        }

    def action_view_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quotation / Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_new(self):
        self.write({'state': 'new'})

    @api.constrains('preferred_date', 'booking_date')
    def _check_dates(self):
        for rec in self:
            if rec.preferred_date and rec.booking_date:
                if fields.Date.from_string(str(rec.preferred_date)) < fields.Date.today():
                    pass  # Allow past dates for historical records
