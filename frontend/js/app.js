/**
 * Main Application Controller
 */

class App {
    constructor() {
        this.currentPage = 'dashboard';
        this.init();
    }

    init() {
        // Set up navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.currentTarget.dataset.page;
                this.navigateTo(page);
            });
        });

        // Load initial page
        this.navigateTo(this.currentPage);
    }

    navigateTo(page) {
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.dataset.page === page) {
                link.classList.add('active');
            }
        });

        // Load page content
        this.currentPage = page;
        this.loadPage(page);
    }

    loadPage(page) {
        const mainContent = document.getElementById('main-content');

        switch (page) {
            case 'dashboard':
                this.loadDashboard(mainContent);
                break;
            case 'restaurants':
                this.loadRestaurants(mainContent);
                break;
            case 'tables':
                this.loadTables(mainContent);
                break;
            case 'bookings':
                this.loadBookings(mainContent);
                break;
            case 'customers':
                this.loadCustomers(mainContent);
                break;
            default:
                mainContent.innerHTML = '<p>Page not found</p>';
        }
    }

    async loadDashboard(container) {
        container.innerHTML = `
            <div class="page-header">
                <h2>Dashboard</h2>
                <p>Overview of your restaurant system</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <h4>Total Restaurants</h4>
                    <div class="value" id="stat-restaurants">-</div>
                </div>
                <div class="stat-card">
                    <h4>Total Bookings</h4>
                    <div class="value" id="stat-bookings">-</div>
                </div>
                <div class="stat-card">
                    <h4>Total Customers</h4>
                    <div class="value" id="stat-customers">-</div>
                </div>
                <div class="stat-card">
                    <h4>Active Tables</h4>
                    <div class="value" id="stat-tables">-</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3>Recent Bookings</h3>
                </div>
                <div id="recent-bookings">
                    <div class="loading">Loading...</div>
                </div>
            </div>
        `;

        // Load stats
        try {
            const [restaurants, bookings, customers] = await Promise.all([
                api.getRestaurants(),
                api.getBookings(),
                api.getCustomers()
            ]);

            document.getElementById('stat-restaurants').textContent = restaurants.length;
            document.getElementById('stat-bookings').textContent = bookings.length;
            document.getElementById('stat-customers').textContent = customers.length;

            // Load recent bookings
            const recentBookingsHtml = bookings.length > 0 ? `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Party Size</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bookings.slice(0, 5).map(booking => `
                            <tr>
                                <td>#${booking.id}</td>
                                <td>${booking.booking_date}</td>
                                <td>${booking.booking_time}</td>
                                <td>${booking.party_size}</td>
                                <td><span class="badge badge-${this.getStatusColor(booking.status)}">${booking.status}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state">No bookings yet</div>';

            document.getElementById('recent-bookings').innerHTML = recentBookingsHtml;
        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    }

    async loadRestaurants(container) {
        container.innerHTML = `
            <div class="page-header">
                <h2>Restaurants</h2>
                <p>Manage your restaurants</p>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3>All Restaurants</h3>
                    <button class="btn btn-primary" onclick="app.showRestaurantModal()">+ Add Restaurant</button>
                </div>
                <div id="restaurants-list">
                    <div class="loading">Loading...</div>
                </div>
            </div>

            <!-- Restaurant Modal -->
            <div class="modal" id="restaurant-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modal-title">Add Restaurant</h3>
                        <button class="modal-close" onclick="app.closeModal('restaurant-modal')">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="restaurant-form">
                            <div class="form-group">
                                <label>Restaurant Name *</label>
                                <input type="text" name="name" class="form-control" required>
                            </div>
                            <div class="form-group">
                                <label>Address *</label>
                                <input type="text" name="address" class="form-control" required>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Phone *</label>
                                    <input type="tel" name="phone" class="form-control" placeholder="+14155551234" required>
                                </div>
                                <div class="form-group">
                                    <label>Email *</label>
                                    <input type="email" name="email" class="form-control" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Opening Time *</label>
                                    <input type="time" name="opening_time" class="form-control" required>
                                </div>
                                <div class="form-group">
                                    <label>Closing Time *</label>
                                    <input type="time" name="closing_time" class="form-control" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Booking Duration (minutes)</label>
                                    <input type="number" name="booking_duration_minutes" class="form-control" value="120">
                                </div>
                                <div class="form-group">
                                    <label>Max Party Size</label>
                                    <input type="number" name="max_party_size" class="form-control" value="10">
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="app.closeModal('restaurant-modal')">Cancel</button>
                        <button class="btn btn-primary" onclick="app.saveRestaurant()">Save</button>
                    </div>
                </div>
            </div>
        `;

        this.loadRestaurantsList();
    }

    async loadRestaurantsList() {
        try {
            const restaurants = await api.getRestaurants();

            const listHtml = restaurants.length > 0 ? `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Address</th>
                            <th>Phone</th>
                            <th>Hours</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${restaurants.map(r => `
                            <tr>
                                <td><strong>${r.name}</strong></td>
                                <td>${r.address}</td>
                                <td>${r.phone}</td>
                                <td>${r.opening_time} - ${r.closing_time}</td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-primary" onclick="app.editRestaurant(${r.id})">Edit</button>
                                    <button class="btn btn-sm btn-danger" onclick="app.deleteRestaurant(${r.id})">Delete</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state"><p>No restaurants yet</p></div>';

            document.getElementById('restaurants-list').innerHTML = listHtml;
        } catch (error) {
            console.error('Error loading restaurants:', error);
            document.getElementById('restaurants-list').innerHTML = '<div class="empty-state"><p>Error loading restaurants</p></div>';
        }
    }

    showRestaurantModal() {
        document.getElementById('restaurant-modal').classList.add('active');
        document.getElementById('restaurant-form').reset();
    }

    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    async saveRestaurant() {
        const form = document.getElementById('restaurant-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        // Convert time format
        data.opening_time += ':00';
        data.closing_time += ':00';
        data.booking_duration_minutes = parseInt(data.booking_duration_minutes);
        data.max_party_size = parseInt(data.max_party_size);

        try {
            await api.createRestaurant(data);
            this.closeModal('restaurant-modal');
            this.loadRestaurantsList();
            alert('Restaurant created successfully!');
        } catch (error) {
            alert('Error creating restaurant: ' + error.message);
        }
    }

    async deleteRestaurant(id) {
        if (!confirm('Are you sure you want to delete this restaurant?')) return;

        try {
            await api.deleteRestaurant(id);
            this.loadRestaurantsList();
            alert('Restaurant deleted successfully!');
        } catch (error) {
            alert('Error deleting restaurant: ' + error.message);
        }
    }

    async loadBookings(container) {
        container.innerHTML = `
            <div class="page-header">
                <h2>Bookings</h2>
                <p>View and manage all bookings</p>
            </div>

            <div class="card">
                <div class="card-header">
                    <h3>All Bookings</h3>
                </div>
                <div id="bookings-list">
                    <div class="loading">Loading...</div>
                </div>
            </div>
        `;

        try {
            const bookings = await api.getBookings();

            const listHtml = bookings.length > 0 ? `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Date</th>
                            <th>Time</th>
                            <th>Party Size</th>
                            <th>Duration</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${bookings.map(b => `
                            <tr>
                                <td>#${b.id}</td>
                                <td>${b.booking_date}</td>
                                <td>${b.booking_time}</td>
                                <td>${b.party_size} people</td>
                                <td>${b.duration_minutes} min</td>
                                <td><span class="badge badge-${this.getStatusColor(b.status)}">${b.status}</span></td>
                                <td class="actions">
                                    <button class="btn btn-sm btn-danger" onclick="app.cancelBooking(${b.id})">Cancel</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state"><p>No bookings yet</p></div>';

            document.getElementById('bookings-list').innerHTML = listHtml;
        } catch (error) {
            console.error('Error loading bookings:', error);
            document.getElementById('bookings-list').innerHTML = '<div class="empty-state"><p>Error loading bookings</p></div>';
        }
    }

    async cancelBooking(id) {
        if (!confirm('Are you sure you want to cancel this booking?')) return;

        try {
            await api.cancelBooking(id);
            this.loadBookings(document.getElementById('main-content'));
            alert('Booking cancelled successfully!');
        } catch (error) {
            alert('Error cancelling booking: ' + error.message);
        }
    }

    async loadTables(container) {
        container.innerHTML = `
            <div class="page-header">
                <h2>Tables</h2>
                <p>Manage restaurant tables</p>
            </div>

            <div class="card">
                <p>Select a restaurant to view and manage its tables.</p>
            </div>
        `;
    }

    async loadCustomers(container) {
        container.innerHTML = `
            <div class="page-header">
                <h2>Customers</h2>
                <p>View customer information</p>
            </div>

            <div class="card">
                <div id="customers-list">
                    <div class="loading">Loading...</div>
                </div>
            </div>
        `;

        try {
            const customers = await api.getCustomers();

            const listHtml = customers.length > 0 ? `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Phone</th>
                            <th>Email</th>
                            <th>Total Bookings</th>
                            <th>No Shows</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${customers.map(c => `
                            <tr>
                                <td><strong>${c.name}</strong></td>
                                <td>${c.phone}</td>
                                <td>${c.email || '-'}</td>
                                <td>${c.total_bookings || 0}</td>
                                <td>${c.no_shows || 0}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<div class="empty-state"><p>No customers yet</p></div>';

            document.getElementById('customers-list').innerHTML = listHtml;
        } catch (error) {
            console.error('Error loading customers:', error);
            document.getElementById('customers-list').innerHTML = '<div class="empty-state"><p>Error loading customers</p></div>';
        }
    }

    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger',
            'completed': 'info',
            'no_show': 'danger'
        };
        return colors[status] || 'info';
    }
}

// Initialize app
const app = new App();
