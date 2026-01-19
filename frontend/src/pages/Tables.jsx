import { useState, useEffect, useCallback } from 'react';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  TableCellsIcon,
  UserGroupIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import { useApiHelpers } from '../hooks/useApi';
import Card from '../components/Card';
import Button from '../components/Button';
import Modal from '../components/Modal';
import LoadingSpinner from '../components/LoadingSpinner';

/**
 * Tables Management Page
 * 
 * This page allows users to:
 * 1. Select a restaurant from a dropdown
 * 2. View all tables for the selected restaurant
 * 3. Create new tables
 * 4. Edit existing tables (capacity, table number, availability)
 * 5. Delete tables
 */
export default function Tables() {
  // State for restaurants dropdown
  const [restaurants, setRestaurants] = useState([]);
  const [selectedRestaurantId, setSelectedRestaurantId] = useState('');
  const [loadingRestaurants, setLoadingRestaurants] = useState(true);
  
  // State for tables
  const [tables, setTables] = useState([]);
  const [loadingTables, setLoadingTables] = useState(false);
  const [tablesError, setTablesError] = useState(null);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'
  const [editingTable, setEditingTable] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    table_number: '',
    capacity: 2,
    is_available: true,
  });
  const [formErrors, setFormErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Delete confirmation state
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  const api = useApiHelpers();

  // Fetch restaurants on mount
  useEffect(() => {
    const fetchRestaurants = async () => {
      try {
        setLoadingRestaurants(true);
        const response = await api.get('/api/restaurants/');
        setRestaurants(response.data || []);
        
        // Auto-select first restaurant if available
        if (response.data && response.data.length > 0) {
          setSelectedRestaurantId(response.data[0].id.toString());
        }
      } catch (error) {
        console.error('Failed to fetch restaurants:', error);
      } finally {
        setLoadingRestaurants(false);
      }
    };
    
    fetchRestaurants();
  }, [api]);

  // Fetch tables when restaurant selection changes
  const fetchTables = useCallback(async () => {
    if (!selectedRestaurantId) {
      setTables([]);
      return;
    }
    
    try {
      setLoadingTables(true);
      setTablesError(null);
      const response = await api.get(`/api/${selectedRestaurantId}/tables`);
      setTables(response.data || []);
    } catch (error) {
      console.error('Failed to fetch tables:', error);
      setTablesError('Failed to load tables. Please try again.');
      setTables([]);
    } finally {
      setLoadingTables(false);
    }
  }, [api, selectedRestaurantId]);

  useEffect(() => {
    fetchTables();
  }, [fetchTables]);

  // Handle restaurant selection change
  const handleRestaurantChange = (e) => {
    setSelectedRestaurantId(e.target.value);
  };

  // Open modal for creating a new table
  const handleCreateTable = () => {
    setModalMode('create');
    setEditingTable(null);
    setFormData({
      table_number: '',
      capacity: 2,
      is_available: true,
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  // Open modal for editing an existing table
  const handleEditTable = (table) => {
    setModalMode('edit');
    setEditingTable(table);
    setFormData({
      table_number: table.table_number || '',
      capacity: table.capacity || 2,
      is_available: table.is_available !== false,
    });
    setFormErrors({});
    setIsModalOpen(true);
  };

  // Close modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingTable(null);
    setFormErrors({});
  };

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    
    // Clear error for this field
    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  // Validate form
  const validateForm = () => {
    const errors = {};
    
    if (!formData.table_number.trim()) {
      errors.table_number = 'Table number is required';
    }
    
    if (!formData.capacity || formData.capacity < 1) {
      errors.capacity = 'Capacity must be at least 1';
    } else if (formData.capacity > 20) {
      errors.capacity = 'Capacity cannot exceed 20';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    
    try {
      const payload = {
        table_number: formData.table_number.trim(),
        capacity: parseInt(formData.capacity, 10),
        is_available: formData.is_available,
      };
      
      if (modalMode === 'create') {
        await api.post(`/api/${selectedRestaurantId}/tables`, payload);
      } else {
        // For edit mode, we'd need a PUT endpoint - using POST for now as per API spec
        // In a real app, you'd have PUT /api/{restaurant_id}/tables/{table_id}
        await api.put(`/api/${selectedRestaurantId}/tables/${editingTable.id}`, payload);
      }
      
      // Refresh tables list
      await fetchTables();
      handleCloseModal();
    } catch (error) {
      console.error('Failed to save table:', error);
      setFormErrors({
        submit: error.response?.data?.detail || 'Failed to save table. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle delete confirmation
  const handleDeleteClick = (tableId) => {
    setDeleteConfirmId(tableId);
  };

  // Cancel delete
  const handleCancelDelete = () => {
    setDeleteConfirmId(null);
  };

  // Confirm delete
  const handleConfirmDelete = async () => {
    if (!deleteConfirmId) return;
    
    setIsDeleting(true);
    
    try {
      await api.delete(`/api/${selectedRestaurantId}/tables/${deleteConfirmId}`);
      await fetchTables();
      setDeleteConfirmId(null);
    } catch (error) {
      console.error('Failed to delete table:', error);
      // Show error in UI
      setTablesError('Failed to delete table. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  // Get selected restaurant name
  const selectedRestaurant = restaurants.find(
    (r) => r.id.toString() === selectedRestaurantId
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tables</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage tables for your restaurants
          </p>
        </div>
        
        {selectedRestaurantId && (
          <Button
            onClick={handleCreateTable}
            className="flex items-center gap-2"
            aria-label="Add new table"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Add Table</span>
          </Button>
        )}
      </div>

      {/* Restaurant Selector */}
      <Card>
        <div className="p-4">
          <label
            htmlFor="restaurant-select"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Select Restaurant
          </label>
          
          {loadingRestaurants ? (
            <div className="flex items-center gap-2 text-gray-500">
              <LoadingSpinner size="sm" />
              <span>Loading restaurants...</span>
            </div>
          ) : restaurants.length === 0 ? (
            <p className="text-gray-500">
              No restaurants found. Please create a restaurant first.
            </p>
          ) : (
            <select
              id="restaurant-select"
              value={selectedRestaurantId}
              onChange={handleRestaurantChange}
              className="block w-full max-w-md rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              aria-describedby="restaurant-help"
            >
              <option value="">Select a restaurant</option>
              {restaurants.map((restaurant) => (
                <option key={restaurant.id} value={restaurant.id}>
                  {restaurant.name}
                </option>
              ))}
            </select>
          )}
          <p id="restaurant-help" className="mt-1 text-sm text-gray-500">
            Choose a restaurant to view and manage its tables
          </p>
        </div>
      </Card>

      {/* Tables Content */}
      {!selectedRestaurantId ? (
        <Card>
          <div className="p-8 text-center">
            <TableCellsIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              No Restaurant Selected
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Please select a restaurant to view its tables.
            </p>
          </div>
        </Card>
      ) : loadingTables ? (
        <Card>
          <div className="p-8 flex justify-center">
            <LoadingSpinner size="lg" />
          </div>
        </Card>
      ) : tablesError ? (
        <Card>
          <div className="p-8 text-center">
            <XCircleIcon className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Error Loading Tables
            </h3>
            <p className="mt-1 text-sm text-gray-500">{tablesError}</p>
            <Button
              variant="secondary"
              onClick={fetchTables}
              className="mt-4"
            >
              Try Again
            </Button>
          </div>
        </Card>
      ) : tables.length === 0 ? (
        <Card>
          <div className="p-8 text-center">
            <TableCellsIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              No Tables Found
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {selectedRestaurant?.name} doesn&apos;t have any tables yet.
            </p>
            <Button
              onClick={handleCreateTable}
              className="mt-4 inline-flex items-center gap-2"
            >
              <PlusIcon className="h-5 w-5" />
              Add First Table
            </Button>
          </div>
        </Card>
      ) : (
        <>
          {/* Tables Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <div className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <TableCellsIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Tables</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {tables.length}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
            
            <Card>
              <div className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Available</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {tables.filter((t) => t.is_available !== false).length}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
            
            <Card>
              <div className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <UserGroupIcon className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Total Capacity</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {tables.reduce((sum, t) => sum + (t.capacity || 0), 0)}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Tables Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {tables.map((table) => (
              <Card
                key={table.id}
                className={`relative ${
                  table.is_available === false
                    ? 'border-red-200 bg-red-50'
                    : 'border-green-200 bg-green-50'
                }`}
              >
                <div className="p-4">
                  {/* Table Number */}
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      Table {table.table_number}
                    </h3>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        table.is_available !== false
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {table.is_available !== false ? 'Available' : 'Unavailable'}
                    </span>
                  </div>
                  
                  {/* Capacity */}
                  <div className="flex items-center gap-2 text-gray-600 mb-4">
                    <UserGroupIcon className="h-5 w-5" />
                    <span>Capacity: {table.capacity} guests</span>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleEditTable(table)}
                      className="flex-1 flex items-center justify-center gap-1"
                      aria-label={`Edit table ${table.table_number}`}
                    >
                      <PencilIcon className="h-4 w-4" />
                      Edit
                    </Button>
                    
                    {deleteConfirmId === table.id ? (
                      <div className="flex items-center gap-1">
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={handleConfirmDelete}
                          disabled={isDeleting}
                          aria-label="Confirm delete"
                        >
                          {isDeleting ? <LoadingSpinner size="sm" /> : 'Yes'}
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={handleCancelDelete}
                          disabled={isDeleting}
                          aria-label="Cancel delete"
                        >
                          No
                        </Button>
                      </div>
                    ) : (
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDeleteClick(table.id)}
                        className="flex items-center justify-center gap-1"
                        aria-label={`Delete table ${table.table_number}`}
                      >
                        <TrashIcon className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={modalMode === 'create' ? 'Add New Table' : 'Edit Table'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Table Number */}
          <div>
            <label
              htmlFor="table_number"
              className="block text-sm font-medium text-gray-700"
            >
              Table Number / Name
            </label>
            <input
              type="text"
              id="table_number"
              name="table_number"
              value={formData.table_number}
              onChange={handleInputChange}
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                formErrors.table_number
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              placeholder="e.g., T1, A1, Patio-1"
              aria-describedby={formErrors.table_number ? 'table_number-error' : undefined}
              aria-invalid={!!formErrors.table_number}
            />
            {formErrors.table_number && (
              <p id="table_number-error" className="mt-1 text-sm text-red-600">
                {formErrors.table_number}
              </p>
            )}
          </div>

          {/* Capacity */}
          <div>
            <label
              htmlFor="capacity"
              className="block text-sm font-medium text-gray-700"
            >
              Capacity (guests)
            </label>
            <input
              type="number"
              id="capacity"
              name="capacity"
              value={formData.capacity}
              onChange={handleInputChange}
              min="1"
              max="20"
              className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
                formErrors.capacity
                  ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                  : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
              }`}
              aria-describedby={formErrors.capacity ? 'capacity-error' : 'capacity-help'}
              aria-invalid={!!formErrors.capacity}
            />
            {formErrors.capacity ? (
              <p id="capacity-error" className="mt-1 text-sm text-red-600">
                {formErrors.capacity}
              </p>
            ) : (
              <p id="capacity-help" className="mt-1 text-sm text-gray-500">
                Maximum number of guests this table can accommodate
              </p>
            )}
          </div>

          {/* Availability */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_available"
              name="is_available"
              checked={formData.is_available}
              onChange={handleInputChange}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label
              htmlFor="is_available"
              className="text-sm font-medium text-gray-700"
            >
              Table is available for booking
            </label>
          </div>

          {/* Submit Error */}
          {formErrors.submit && (
            <div className="rounded-md bg-red-50 p-3">
              <p className="text-sm text-red-700">{formErrors.submit}</p>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={handleCloseModal}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2"
            >
              {isSubmitting && <LoadingSpinner size="sm" />}
              {modalMode === 'create' ? 'Create Table' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}