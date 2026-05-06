from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AvrJobCard(models.Model):
    _name = 'avr.job.card'
    _description = 'Vehicle Job Card'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    def _domain_avr_group_users(self, group_xmlid):
        """Restrict to internal users that belong to a specific AVR security group."""
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        if not group:
            return [('id', '=', False)]
        return [('groups_id', 'in', [group.id]), ('share', '=', False)]

    name = fields.Char(
        string='Job Card No.', required=True, copy=False,
        readonly=True, default='New', tracking=True)
    booking_id = fields.Many2one('avr.booking', string='Booking', tracking=True)
    job_card_type = fields.Selection([
        ('inspection', 'Inspection'),
        ('repair', 'Repair'),
    ], string='Job Card Type', required=True, default='repair', tracking=True)

    # ── Inspection stages ──────────────────────────────────────────────────────
    inspection_state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
        ('cancelled', 'Cancelled'),
    ], string='Inspection Status', default='new', tracking=True)

    # ── Repair stages ─────────────────────────────────────────────────────────
    repair_state = fields.Selection([
        ('new', 'New'),
        ('assign_technician', 'Assign to Technician'),
        ('in_diagnosis', 'In Diagnosis'),
        ('supervisor_inspection', 'In Supervisor Inspection'),
        ('hold', 'Hold'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
        ('reject', 'Reject'),
        ('cancel', 'Cancel'),
    ], string='Repair Status', default='new', tracking=True)

    # ── Unified state helper (for views) ──────────────────────────────────────
    state = fields.Char(
        string='Status', compute='_compute_state', store=True)

    @api.depends('job_card_type', 'inspection_state', 'repair_state')
    def _compute_state(self):
        for rec in self:
            if rec.job_card_type == 'inspection':
                rec.state = rec.inspection_state
            else:
                rec.state = rec.repair_state

    # ── Dates ─────────────────────────────────────────────────────────────────
    date = fields.Date(string='Date', default=fields.Date.today, tracking=True)
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')

    # ── Inspection type ───────────────────────────────────────────────────────
    inspection_report_type = fields.Selection([
        ('classic', 'Classic Inspection'),
        ('advanced', 'Advanced Inspection'),
    ], string='Inspection Report Type')

    type_of_inspection = fields.Selection([
        ('full', 'Full Inspection'),
        ('specific', 'Specific Inspection'),
    ], string='Type of Inspection')

    inspection_template_id = fields.Many2one(
        'avr.inspection.template', string='Inspection Template')
    inspection_line_ids = fields.One2many(
        'avr.job.card.inspection.line', 'job_card_id',
        string='Inspection Lines')

    # ── Repair type ───────────────────────────────────────────────────────────
    repair_type = fields.Selection([
        ('with_services', 'With OEM Services and Spare Parts'),
        ('with_oem', 'With OEM Services and Parts'),
    ], string='Repair Type')

    # ── People ────────────────────────────────────────────────────────────────
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True, tracking=True)
    technician_id = fields.Many2one(
        'res.users', string='Technician', tracking=True,
        domain=lambda self: self._domain_avr_group_users(
            'advance_vehicle_repair.group_avr_technician'))
    supervisor_id = fields.Many2one(
        'res.users', string='Supervisor', tracking=True,
        domain=lambda self: self._domain_avr_group_users(
            'advance_vehicle_repair.group_avr_supervisor'))
    inspected_by = fields.Many2one('res.users', string='Inspected By')
    team_id = fields.Many2one('avr.team', string='Repair Team')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # ── Vehicle ───────────────────────────────────────────────────────────────
    vehicle_id = fields.Many2one('avr.vehicle', string='Registered Vehicle')
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
    ], string='Transmission Type')
    year = fields.Integer(string='Year')
    last_odometer = fields.Float(string='Last Odometer')
    vehicle_color = fields.Char(string='Vehicle Color')
    vehicle_grade = fields.Char(string='Vehicle Grade')
    warranty = fields.Char(string='Warranty')
    vehicle_source = fields.Selection([
        ('fleet', 'Vehicle from Fleet'),
        ('customer', 'Vehicle from Customer'),
    ], string='Vehicle Source', default='customer')

    # ── Address ───────────────────────────────────────────────────────────────
    street = fields.Char(string='Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip_code = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')

    # ── Inspection charges ────────────────────────────────────────────────────
    inspection_charges = fields.Float(string='Inspection Charges', digits=(16, 2))
    inspection_charge_type = fields.Selection([
        ('fixed', 'Fixed'), ('percentage', 'Percentage'),
    ], string='Charge Type', default='fixed')

    # ── Services & spare parts ────────────────────────────────────────────────
    service_ids = fields.One2many('avr.job.card.service', 'job_card_id', string='Services')
    spare_part_ids = fields.One2many('avr.job.card.spare.part', 'job_card_id', string='Spare Parts')
    total_service_amount = fields.Float(
        string='Total Service', compute='_compute_totals', store=True)
    total_spare_part_amount = fields.Float(
        string='Total Parts', compute='_compute_totals', store=True)
    total_amount = fields.Float(
        string='Total Amount', compute='_compute_totals', store=True)

    # ── Tasks ─────────────────────────────────────────────────────────────────
    task_ids = fields.One2many('project.task', 'job_card_id', string='Tasks')
    task_count = fields.Integer(compute='_compute_task_count', string='Tasks')

    # ── Sale / Invoice ────────────────────────────────────────────────────────
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sale Orders')
    invoice_ids = fields.Many2many('account.move', string='Invoices')
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Invoices')

    # ── Image / attachment ────────────────────────────────────────────────────
    image_ids = fields.Many2many(
        'ir.attachment', string='Vehicle Images',
        relation='avr_job_card_attachment_rel',
        column1='job_card_id', column2='attachment_id')
    customer_observations = fields.Text(string='Customer Observations')
    internal_notes = fields.Text(string='Internal Notes')

    # ── Authorization ──────────────────────────────────────────────────────────
    customer_signature = fields.Binary(string='Customer Signature')
    technician_signature = fields.Binary(string='Technician Signature')

    # ── Approval mail sent ─────────────────────────────────────────────────────
    approval_mail_sent = fields.Boolean(default=False)

    # ── Compute ───────────────────────────────────────────────────────────────
    @api.depends('service_ids.subtotal', 'spare_part_ids.subtotal')
    def _compute_totals(self):
        for rec in self:
            rec.total_service_amount = sum(rec.service_ids.mapped('subtotal'))
            rec.total_spare_part_amount = sum(rec.spare_part_ids.mapped('subtotal'))
            rec.total_amount = rec.total_service_amount + rec.total_spare_part_amount

    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_ids)

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends('sale_order_id')
    def _compute_sale_order_count(self):
        for rec in self:
            rec.sale_order_count = 1 if rec.sale_order_id else 0

    # ── Sequence ─────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                seq_code = 'avr.job.card.inspection' \
                    if vals.get('job_card_type') == 'inspection' \
                    else 'avr.job.card.repair'
                vals['name'] = self.env['ir.sequence'].next_by_code(seq_code) or 'New'
        return super().create(vals_list)

    # ── Onchange ──────────────────────────────────────────────────────────────
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
            self.last_odometer = v.last_odometer

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.phone = self.customer_id.phone
            self.email = self.customer_id.email
            self.street = self.customer_id.street
            self.city = self.customer_id.city
            self.state_id = self.customer_id.state_id
            self.country_id = self.customer_id.country_id

    @api.onchange('inspection_template_id')
    def _onchange_inspection_template(self):
        if self.inspection_template_id:
            self.inspection_line_ids = [(5, 0, 0)]
            lines = []
            for tpl_line in self.inspection_template_id.line_ids:
                lines.append((0, 0, {
                    'part': tpl_line.part,
                    'category': tpl_line.category,
                    'condition': 'ok',
                }))
            self.inspection_line_ids = lines

    # ── State transitions ─────────────────────────────────────────────────────

    # Inspection transitions
    def action_insp_start(self):
        self.write({'inspection_state': 'in_progress', 'start_date': fields.Datetime.now()})

    def action_insp_review(self):
        self.write({'inspection_state': 'in_review'})

    def action_insp_complete(self):
        self.write({'inspection_state': 'completed', 'end_date': fields.Datetime.now()})

    def action_insp_lock(self):
        self.write({'inspection_state': 'locked'})

    def action_insp_cancel(self):
        self.write({'inspection_state': 'cancelled'})

    # Repair transitions
    def action_repair_assign(self):
        if not self.technician_id:
            raise UserError(_('Please assign a technician before proceeding.'))
        self.write({'repair_state': 'assign_technician'})

    def action_repair_diagnose(self):
        self.write({'repair_state': 'in_diagnosis'})

    def action_repair_supervisor(self):
        self.write({'repair_state': 'supervisor_inspection'})

    def action_repair_complete(self):
        self.write({'repair_state': 'completed', 'end_date': fields.Datetime.now()})

    def action_repair_hold(self):
        self.write({'repair_state': 'hold'})

    def action_repair_lock(self):
        self.write({'repair_state': 'locked'})

    def action_repair_reject(self):
        self.write({'repair_state': 'reject'})

    def action_repair_cancel(self):
        self.write({'repair_state': 'cancel'})

    def action_send_approval_mail(self):
        self.ensure_one()
        template = self.env.ref(
            'advance_vehicle_repair.email_template_job_card_approval', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.approval_mail_sent = True

    # ── Smart buttons ──────────────────────────────────────────────────────────
    def action_view_tasks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tasks'),
            'res_model': 'project.task',
            'view_mode': 'kanban,list,form',
            'domain': [('job_card_id', '=', self.id)],
            'context': {'default_job_card_id': self.id},
        }

    def action_view_sale_order(self):
        self.ensure_one()
        if not self.sale_order_id:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _avr_generic_service_product(self):
        tmpl = self.env.ref(
            'advance_vehicle_repair.product_tmpl_avr_generic_service',
            raise_if_not_found=False,
        )
        if not tmpl:
            return self.env['product.product']
        return tmpl.product_variant_ids[:1]

    def _prepare_sale_order_line_commands(self):
        """(0, 0, vals) commands for sale.order order_line from this repair card."""
        self.ensure_one()
        commands = []
        generic = self._avr_generic_service_product()

        for service_line in self.service_ids:
            product = service_line.service_id.product_id or generic
            if not product:
                continue
            qty = service_line.quantity or 1.0
            price = service_line.unit_price
            if not price and service_line.service_id:
                price = service_line.service_id.list_price
            commands.append((0, 0, {
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': qty,
                'price_unit': price or 0.0,
                'name': service_line.service_id.name,
            }))

        for spare_line in self.spare_part_ids:
            product = spare_line.product_id
            commands.append((0, 0, {
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': spare_line.quantity or 1.0,
                'price_unit': spare_line.unit_price or 0.0,
                'name': spare_line.description or product.display_name,
            }))
        return commands

    def action_create_quotation(self):
        self.ensure_one()
        if self.job_card_type != 'repair':
            raise UserError(_('Only repair job cards can create a sales quotation.'))
        line_cmds = self._prepare_sale_order_line_commands()
        if not line_cmds:
            raise UserError(_('Add at least one service or spare part line before creating a quotation.'))

        sale = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
            'order_line': line_cmds,
        })
        self.sale_order_id = sale.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale.id,
            'view_mode': 'form',
        }


class AvrJobCardService(models.Model):
    _name = 'avr.job.card.service'
    _description = 'Job Card Service Line'

    job_card_id = fields.Many2one('avr.job.card', required=True, ondelete='cascade')
    service_id = fields.Many2one('avr.service', string='Service', required=True)
    team_id = fields.Many2one('avr.team', string='Team')
    technician_id = fields.Many2one('res.users', string='Technician')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    quantity = fields.Float(string='Qty', default=1.0)
    unit_price = fields.Float(string='Unit Price', digits=(16, 2))
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    task_id = fields.Many2one('project.task', string='Task')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.unit_price = self.service_id.list_price


class AvrJobCardSparePart(models.Model):
    _name = 'avr.job.card.spare.part'
    _description = 'Job Card Spare Part Line'

    job_card_id = fields.Many2one('avr.job.card', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Spare Part', required=True )
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Qty', default=1.0)
    unit_price = fields.Float(string='Unit Price', digits=(16, 2))
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number')

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_price = self.product_id.lst_price
            self.description = self.product_id.description_sale
