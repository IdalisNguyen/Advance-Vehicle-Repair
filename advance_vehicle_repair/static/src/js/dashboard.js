/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, xml } from "@odoo/owl";

class AvrDashboard extends Component {
    static template = xml`
<div class="avr-dashboard o_action">
    <div t-if="state.loading" class="avr-loading">
        <i class="fa fa-spinner fa-spin fa-3x text-muted"/>
        <p class="mt-3 text-muted">Loading dashboard…</p>
    </div>

    <div t-else="" class="avr-dashboard-content">

        <!-- KPI row -->
        <div class="row g-3 mb-4">
            <div class="col-6 col-lg-3">
                <div class="avr-kpi-card" t-on-click="goToBookings">
                    <div class="avr-kpi-label">Total Bookings</div>
                    <div class="avr-kpi-value"><t t-out="state.kpi.total_bookings"/></div>
                    <div class="avr-kpi-sub text-success small">↑ See all bookings</div>
                </div>
            </div>
            <div class="col-6 col-lg-3">
                <div class="avr-kpi-card" t-on-click="goToInspections">
                    <div class="avr-kpi-label">Inspection Cards</div>
                    <div class="avr-kpi-value"><t t-out="state.kpi.job_cards"/></div>
                    <div class="avr-kpi-sub text-warning small">↑ Active cards</div>
                </div>
            </div>
            <div class="col-6 col-lg-3">
                <div class="avr-kpi-card" t-on-click="goToRepairs">
                    <div class="avr-kpi-label">Repair Cards</div>
                    <div class="avr-kpi-value"><t t-out="state.kpi.repair_cards"/></div>
                    <div class="avr-kpi-sub text-info small">↑ In progress</div>
                </div>
            </div>
            <div class="col-6 col-lg-3">
                <div class="avr-kpi-card avr-kpi-revenue">
                    <div class="avr-kpi-label">Revenue (MRR)</div>
                    <div class="avr-kpi-value">$<t t-out="state.kpi.revenue.toLocaleString()"/></div>
                    <div class="avr-kpi-sub text-success small">↑ This month</div>
                </div>
            </div>
        </div>

        <!-- Charts row -->
        <div class="row g-3 mb-4">
            <div class="col-12 col-lg-7">
                <div class="avr-card">
                    <div class="avr-card-header">Revenue Trend</div>
                    <div style="height:240px;">
                        <canvas id="avr-revenue-chart"/>
                    </div>
                </div>
            </div>
            <div class="col-12 col-lg-5">
                <div class="avr-card">
                    <div class="avr-card-header">Booking Type</div>
                    <div style="height:240px;">
                        <canvas id="avr-booking-type-chart"/>
                    </div>
                </div>
            </div>
        </div>

        <!-- Bottom row: recent + alerts + quick actions -->
        <div class="row g-3">
            <div class="col-12 col-lg-8">
                <div class="avr-card">
                    <div class="avr-card-header">Last Activity</div>
                    <div t-if="!state.recent_bookings.length" class="text-muted p-3">
                        No bookings yet.
                    </div>
                    <div t-else="" class="avr-activity-list">
                        <div t-foreach="state.recent_bookings" t-as="b" t-key="b.id"
                             class="avr-activity-item">
                            <div class="avr-activity-icon">
                                <i class="fa fa-car"/>
                            </div>
                            <div class="avr-activity-body">
                                <strong><t t-out="b.name"/></strong>
                                <span class="text-muted ms-2">
                                    <t t-out="b.customer_id[1]"/>
                                </span>
                                <div class="small text-muted">
                                    <t t-out="b.booking_date"/>
                                </div>
                            </div>
                            <div>
                                <span t-attf-class="badge #{
                                    b.state === 'new' ? 'bg-info' :
                                    b.state === 'confirmed' ? 'bg-warning text-dark' :
                                    b.state === 'completed' ? 'bg-success' : 'bg-secondary'}">
                                    <t t-out="b.state"/>
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-12 col-lg-4">
                <div class="avr-card">
                    <div class="avr-card-header">Quick Actions</div>
                    <div class="d-grid gap-2 p-2">
                        <button class="btn btn-warning btn-sm" t-on-click="newBooking">
                            <i class="fa fa-plus me-1"/> New Booking
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" t-on-click="newInspection">
                            <i class="fa fa-search me-1"/> New Inspection
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" t-on-click="goToRepairs">
                            <i class="fa fa-wrench me-1"/> New Repair
                        </button>
                        <button class="btn btn-outline-secondary btn-sm">
                            <i class="fa fa-bell me-1"/> Alerts
                        </button>
                    </div>
                </div>
            </div>
        </div>

    </div>
</div>`;

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            kpi: {
                total_bookings: 0,
                job_cards: 0,
                repair_cards: 0,
                revenue: 0,
                revenue_delta: 0,
                bookings_delta: 0,
            },
            booking_by_type: [],
            recent_bookings: [],
            alerts: {
                overdue_inspections: 0,
                overdue_repairs: 0,
                high_priority: 0,
            },
            revenue_trend: [],
        });

        onMounted(async () => {
            await this._loadDashboardData();
        });
    }

    async _loadDashboardData() {
        try {
            // KPI counts
            const [bookings, inspections, repairs] = await Promise.all([
                this.orm.searchCount("avr.booking", []),
                this.orm.searchCount("avr.job.card", [["job_card_type", "=", "inspection"]]),
                this.orm.searchCount("avr.job.card", [["job_card_type", "=", "repair"]]),
            ]);

            // Booking by type
            const bookingGroups = await this.orm.readGroup(
                "avr.booking",
                [],
                ["booking_type"],
                ["booking_type"]
            );

            // Recent activity
            const recentBookings = await this.orm.searchRead(
                "avr.booking",
                [],
                ["name", "customer_id", "booking_type", "state", "booking_date"],
                { limit: 5, order: "booking_date desc" }
            );

            Object.assign(this.state.kpi, {
                total_bookings: bookings,
                job_cards: inspections,
                repair_cards: repairs,
            });

            this.state.booking_by_type = bookingGroups.map(g => ({
                label: g.booking_type,
                count: g.booking_type_count,
            }));

            this.state.recent_bookings = recentBookings;
            this.state.loading = false;

            // Render charts after data loads
            this._renderCharts();
        } catch (e) {
            console.error("AVR Dashboard load error:", e);
            this.state.loading = false;
        }
    }

    _renderCharts() {
        this._renderRevenueChart();
        this._renderBookingTypeChart();
    }

    _renderRevenueChart() {
        const canvas = document.getElementById("avr-revenue-chart");
        if (!canvas || !window.Chart) return;

        const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const inspectData = [12, 18, 15, 22, 19, 28, 25, 30, 22, 18, 25, 32];
        const repairData  = [8,  14, 10, 16, 14, 20, 18, 25, 17, 13, 20, 28];

        new window.Chart(canvas, {
            type: "line",
            data: {
                labels: months,
                datasets: [
                    {
                        label: "Inspect",
                        data: inspectData,
                        borderColor: "#E07B3A",
                        backgroundColor: "rgba(224,123,58,0.1)",
                        tension: 0.4,
                        fill: true,
                    },
                    {
                        label: "Repair",
                        data: repairData,
                        borderColor: "#6B4FBB",
                        backgroundColor: "rgba(107,79,187,0.08)",
                        tension: 0.4,
                        fill: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "top" } },
                scales: {
                    y: { beginAtZero: true, grid: { color: "rgba(0,0,0,0.05)" } },
                    x: { grid: { display: false } },
                },
            },
        });
    }

    _renderBookingTypeChart() {
        const canvas = document.getElementById("avr-booking-type-chart");
        if (!canvas || !window.Chart) return;

        const colors = ["#E07B3A", "#6B4FBB", "#3ABDE0", "#7FBA00"];
        const labels = this.state.booking_by_type.map(b =>
            b.label === "inspection_only" ? "Inspection Only" :
            b.label === "repair_only" ? "Repair" :
            b.label === "inspection_repair" ? "Inspection + Repair" : b.label
        );
        const data = this.state.booking_by_type.map(b => b.count);

        new window.Chart(canvas, {
            type: "doughnut",
            data: {
                labels: labels.length ? labels : ["No Data"],
                datasets: [{
                    data: data.length ? data : [1],
                    backgroundColor: colors,
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "right" },
                },
            },
        });
    }

    // ── Navigation helpers ────────────────────────────────────────────────────
    goToBookings() {
        this.action.doAction("advance_vehicle_repair.action_avr_booking");
    }
    goToInspections() {
        this.action.doAction("advance_vehicle_repair.action_avr_inspection_job_card");
    }
    goToRepairs() {
        this.action.doAction("advance_vehicle_repair.action_avr_repair_job_card");
    }
    newBooking() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "avr.booking",
            view_mode: "form",
            views: [[false, "form"]],
        });
    }
    newInspection() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "avr.job.card",
            view_mode: "form",
            views: [[false, "form"]],
            context: { default_job_card_type: "inspection" },
        });
    }
}

registry.category("actions").add("avr_dashboard", AvrDashboard);
