/**
 * API Client for Restaurant Reservation System
 */

const API_BASE_URL = 'http://localhost:8000';

class RestaurantAPI {
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || error.detail || 'API request failed');
            }
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Restaurant endpoints
    async getRestaurants() {
        return this.request('/api/');
    }

    async getRestaurant(id) {
        return this.request(`/api/${id}`);
    }

    async createRestaurant(data) {
        return this.request('/api/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateRestaurant(id, data) {
        return this.request(`/api/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteRestaurant(id) {
        return this.request(`/api/${id}`, {
            method: 'DELETE',
        });
    }

    // Table endpoints
    async getTables(restaurantId) {
        return this.request(`/api/${restaurantId}/tables`);
    }

    async createTable(restaurantId, data) {
        return this.request(`/api/${restaurantId}/tables`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateTable(restaurantId, tableId, data) {
        return this.request(`/api/${restaurantId}/tables/${tableId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteTable(restaurantId, tableId) {
        return this.request(`/api/${restaurantId}/tables/${tableId}`, {
            method: 'DELETE',
        });
    }

    // Booking endpoints
    async getBookings(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/api/bookings/?${params}`);
    }

    async getBooking(id) {
        return this.request(`/api/bookings/${id}`);
    }

    async createBooking(data) {
        return this.request('/api/bookings/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateBooking(id, data) {
        return this.request(`/api/bookings/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async cancelBooking(id) {
        return this.request(`/api/bookings/${id}`, {
            method: 'DELETE',
        });
    }

    // Customer endpoints
    async getCustomers() {
        return this.request('/api/customers/');
    }

    async getCustomerByPhone(phone) {
        return this.request(`/api/customers/phone/${phone}`);
    }

    // Availability endpoint
    async checkAvailability(data) {
        return this.request('/api/availability/check', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
}

const api = new RestaurantAPI();
