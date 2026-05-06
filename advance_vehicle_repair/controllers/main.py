from odoo import http, _
from odoo.http import request


class AvrWebsiteBooking(http.Controller):

    @http.route('/vehicle-repair/booking', type='http', auth='public', website=True)
    def booking_page(self, **kwargs):
        """Display the vehicle repair booking form."""
        partner = request.env.user.partner_id
        vehicles = []
        if partner:
            vehicles = request.env['avr.vehicle'].sudo().search([
                ('customer_id', '=', partner.id)
            ])
        return request.render(
            'advance_vehicle_repair.avr_website_booking_page',
            {'vehicles': vehicles}
        )

    @http.route('/vehicle-repair/booking/submit', type='http',
                auth='public', website=True, methods=['POST'], csrf=True)
    def booking_submit(self, **post):
        """Handle booking form submission."""
        env = request.env

        # ── Resolve or create partner ──────────────────────────────────────────
        partner = request.env.user.partner_id
        if not partner or partner == env.ref('base.public_partner'):
            # Guest user: find by email or create
            email = post.get('email', '').strip()
            name = post.get('customer_name', 'Guest').strip()
            partner = env['res.partner'].sudo().search(
                [('email', '=', email)], limit=1)
            if not partner:
                partner = env['res.partner'].sudo().create({
                    'name': name,
                    'email': email,
                    'phone': post.get('phone', ''),
                    'street': post.get('street', ''),
                    'street2': post.get('street2', ''),
                    'city': post.get('city', ''),
                    'zip': post.get('zip_code', ''),
                })

        # ── Resolve vehicle ────────────────────────────────────────────────────
        vehicle_id = False
        vehicle_source_val = post.get('vehicle_source', 'new')
        if vehicle_source_val == 'existing' and post.get('vehicle_id'):
            try:
                vehicle_id = int(post['vehicle_id'])
            except (ValueError, TypeError):
                vehicle_id = False

        if not vehicle_id:
            # Create new vehicle record
            reg_no = post.get('registration_no', '')
            if reg_no:
                existing = env['avr.vehicle'].sudo().search([
                    ('registration_no', '=', reg_no),
                    ('customer_id', '=', partner.id),
                ], limit=1)
                if existing:
                    vehicle_id = existing.id
                else:
                    new_veh = env['avr.vehicle'].sudo().create({
                        'customer_id': partner.id,
                        'brand': post.get('brand', ''),
                        'fuel_type': post.get('fuel_type', False) or False,
                        'vin_number': post.get('vin_number', ''),
                        'registration_no': reg_no,
                        'transmission_type': post.get('transmission_type', 'manual'),
                    })
                    vehicle_id = new_veh.id

        # ── Create booking ─────────────────────────────────────────────────────
        booking_vals = {
            'customer_id': partner.id,
            'vehicle_id': vehicle_id,
            'vehicle_source': 'customer',
            'booking_type': post.get('booking_type', 'repair_only'),
            'booking_source': 'website',
            'preferred_date': post.get('preferred_date') or False,
            'preferred_time_slot': post.get('preferred_time_slot', ''),
            'issue_description': post.get('issue_description', ''),
            'brand': post.get('brand', ''),
            'fuel_type': post.get('fuel_type', False) or False,
            'vin_number': post.get('vin_number', ''),
            'registration_no': post.get('registration_no', ''),
            'transmission_type': post.get('transmission_type', 'manual'),
            'street': post.get('street', ''),
            'street2': post.get('street2', ''),
            'city': post.get('city', ''),
            'zip_code': post.get('zip_code', ''),
            'state': 'new',
        }

        booking = env['avr.booking'].sudo().create(booking_vals)

        return request.render(
            'advance_vehicle_repair.avr_booking_confirmed',
            {'booking': booking}
        )

    @http.route('/vehicle-repair/booking/<int:booking_id>', type='http',
                auth='user', website=True)
    def booking_detail(self, booking_id, **kwargs):
        """Show booking detail page (portal)."""
        booking = request.env['avr.booking'].sudo().browse(booking_id)
        if not booking.exists():
            return request.not_found()
        return request.render(
            'advance_vehicle_repair.avr_booking_confirmed',
            {'booking': booking}
        )

    @http.route('/my/bookings', type='http', auth='user', website=True)
    def my_bookings(self, **kwargs):
        """Portal: list user's bookings."""
        partner = request.env.user.partner_id
        bookings = request.env['avr.booking'].sudo().search([
            ('customer_id', '=', partner.id)
        ], order='booking_date desc')
        return request.render(
            'advance_vehicle_repair.avr_portal_my_bookings',
            {'bookings': bookings}
        )
