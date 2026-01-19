/**
 * Menu Management Page
 * View, edit, and import restaurant menu
 */

import { useState, useEffect, useRef } from 'react';
import {
  DocumentTextIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  XMarkIcon,
  PhotoIcon,
  DocumentArrowUpIcon,
  CheckIcon,
  EyeSlashIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import Card from '../../components/Card';
import Button from '../../components/Button';
import { useAppContext } from '../../App';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function formatPrice(cents) {
  return `$${(cents / 100).toFixed(2)}`;
}

function parsePriceToCents(priceStr) {
  const cleaned = priceStr.replace(/[^0-9.]/g, '');
  const dollars = parseFloat(cleaned);
  return Math.round(dollars * 100);
}

function DietaryBadge({ tag }) {
  const colors = {
    vegetarian: 'bg-green-100 text-green-800',
    vegan: 'bg-emerald-100 text-emerald-800',
    gluten_free: 'bg-yellow-100 text-yellow-800',
    spicy: 'bg-red-100 text-red-800',
    halal: 'bg-blue-100 text-blue-800',
    kosher: 'bg-purple-100 text-purple-800',
  };

  const labels = {
    vegetarian: 'V',
    vegan: 'VG',
    gluten_free: 'GF',
    spicy: 'Spicy',
    halal: 'Halal',
    kosher: 'Kosher',
  };

  return (
    <span className={`px-1.5 py-0.5 text-xs rounded ${colors[tag] || 'bg-gray-100 text-gray-800'}`}>
      {labels[tag] || tag}
    </span>
  );
}

// Edit Item Modal
function EditItemModal({ item, categories, onSave, onClose }) {
  const [formData, setFormData] = useState({
    name: item?.name || '',
    description: item?.description || '',
    price: item ? (item.price_cents / 100).toFixed(2) : '',
    category_id: item?.category_id || categories[0]?.id || '',
    dietary_tags: item?.dietary_tags || [],
    is_available: item?.is_available ?? true,
  });
  const [saving, setSaving] = useState(false);

  const dietaryOptions = ['vegetarian', 'vegan', 'gluten_free', 'spicy', 'halal', 'kosher'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    await onSave({
      ...formData,
      price_cents: parsePriceToCents(formData.price),
      category_id: parseInt(formData.category_id),
    });
    setSaving(false);
  };

  const toggleDietaryTag = (tag) => {
    setFormData(prev => ({
      ...prev,
      dietary_tags: prev.dietary_tags.includes(tag)
        ? prev.dietary_tags.filter(t => t !== tag)
        : [...prev.dietary_tags, tag]
    }));
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">{item ? 'Edit Item' : 'Add New Item'}</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="mt-1 w-full border rounded-lg px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={2}
                className="mt-1 w-full border rounded-lg px-3 py-2"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Price ($)</label>
                <input
                  type="text"
                  required
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  placeholder="12.99"
                  className="mt-1 w-full border rounded-lg px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Category</label>
                <select
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  className="mt-1 w-full border rounded-lg px-3 py-2"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dietary Tags</label>
              <div className="flex flex-wrap gap-2">
                {dietaryOptions.map(tag => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => toggleDietaryTag(tag)}
                    className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                      formData.dietary_tags.includes(tag)
                        ? 'bg-green-100 border-green-500 text-green-800'
                        : 'bg-gray-50 border-gray-300 text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {tag.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_available"
                checked={formData.is_available}
                onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="is_available" className="text-sm text-gray-700">Available for ordering</label>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={saving} className="flex-1">
                {saving ? 'Saving...' : (item ? 'Save Changes' : 'Add Item')}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// Import Menu Modal
function ImportMenuModal({ accountId, onSuccess, onClose }) {
  const [importType, setImportType] = useState('image');
  const [textData, setTextData] = useState('');
  const [file, setFile] = useState(null);
  const [menuName, setMenuName] = useState('');
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleImport = async () => {
    setImporting(true);
    setError(null);

    try {
      const token = localStorage.getItem('authToken');
      const formData = new FormData();

      if (menuName) {
        formData.append('menu_name', menuName);
      }

      if (importType === 'text') {
        if (!textData.trim()) {
          setError('Please enter menu text');
          setImporting(false);
          return;
        }
        formData.append('text_data', textData);
      } else if (importType === 'image') {
        if (!file) {
          setError('Please select an image file');
          setImporting(false);
          return;
        }
        formData.append('image_file', file);
      } else if (importType === 'pdf') {
        if (!file) {
          setError('Please select a PDF file');
          setImporting(false);
          return;
        }
        formData.append('pdf_file', file);
      }

      const response = await fetch(`${API_BASE}/api/onboarding/accounts/${accountId}/menus/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        onSuccess(result);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to import menu');
      }
    } catch (err) {
      console.error('Import error:', err);
      setError('Failed to connect to server');
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium">Import Menu</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <div className="space-y-4">
            {/* Menu Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700">Menu Name (optional)</label>
              <input
                type="text"
                value={menuName}
                onChange={(e) => setMenuName(e.target.value)}
                placeholder="Main Menu"
                className="mt-1 w-full border rounded-lg px-3 py-2"
              />
            </div>

            {/* Import Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Import From</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setImportType('image')}
                  className={`p-3 rounded-lg border text-center transition-colors ${
                    importType === 'image'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <PhotoIcon className="h-6 w-6 mx-auto mb-1" />
                  <span className="text-sm">Image</span>
                </button>
                <button
                  type="button"
                  onClick={() => setImportType('pdf')}
                  className={`p-3 rounded-lg border text-center transition-colors ${
                    importType === 'pdf'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <DocumentArrowUpIcon className="h-6 w-6 mx-auto mb-1" />
                  <span className="text-sm">PDF</span>
                </button>
                <button
                  type="button"
                  onClick={() => setImportType('text')}
                  className={`p-3 rounded-lg border text-center transition-colors ${
                    importType === 'text'
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <DocumentTextIcon className="h-6 w-6 mx-auto mb-1" />
                  <span className="text-sm">Text</span>
                </button>
              </div>
            </div>

            {/* Import Content */}
            {importType === 'text' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Paste your menu text
                </label>
                <textarea
                  value={textData}
                  onChange={(e) => setTextData(e.target.value)}
                  rows={8}
                  placeholder={`Example:\n\nAppetizers\nSamosa - Crispy pastry filled with spiced potatoes - $5.99\nPakora - Mixed vegetable fritters - $6.99\n\nMain Course\nButter Chicken - Creamy tomato curry - $15.99\n...`}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload {importType === 'image' ? 'an image' : 'a PDF'} of your menu
                </label>
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-green-500 hover:bg-green-50 transition-colors"
                >
                  {file ? (
                    <div>
                      <CheckIcon className="h-8 w-8 text-green-500 mx-auto mb-2" />
                      <p className="text-sm font-medium text-gray-900">{file.name}</p>
                      <p className="text-xs text-gray-500 mt-1">Click to change file</p>
                    </div>
                  ) : (
                    <div>
                      {importType === 'image' ? (
                        <PhotoIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      ) : (
                        <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      )}
                      <p className="text-sm text-gray-600">Click to upload or drag and drop</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {importType === 'image' ? 'PNG, JPG up to 10MB' : 'PDF up to 10MB'}
                      </p>
                    </div>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={importType === 'image' ? 'image/*' : 'application/pdf'}
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button type="button" variant="secondary" onClick={onClose} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleImport} disabled={importing} className="flex-1">
                {importing ? 'Importing...' : 'Import Menu'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Delete Confirmation Modal
function DeleteConfirmModal({ item, onConfirm, onClose }) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    await onConfirm();
    setDeleting(false);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose}></div>
        <div className="relative bg-white rounded-lg shadow-xl max-w-sm w-full p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Delete Item</h3>
          <p className="text-gray-500 mb-4">
            Are you sure you want to delete "{item.name}"? This action cannot be undone.
          </p>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDelete} disabled={deleting} className="flex-1">
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Menu Category Component
function MenuCategory({ category, isExpanded, onToggle, onEditItem, onDeleteItem, onToggleAvailability }) {
  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDownIcon className="h-5 w-5 text-gray-500" />
          ) : (
            <ChevronRightIcon className="h-5 w-5 text-gray-500" />
          )}
          <div className="text-left">
            <h3 className="font-medium text-gray-900">{category.name}</h3>
            {category.description && (
              <p className="text-sm text-gray-500">{category.description}</p>
            )}
          </div>
        </div>
        <span className="text-sm text-gray-500">{category.items?.length || 0} items</span>
      </button>

      {isExpanded && (
        <div className="divide-y divide-gray-100">
          {category.items?.map((item) => (
            <div key={item.id} className="p-4 hover:bg-gray-50 group">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className={`font-medium ${item.is_available ? 'text-gray-900' : 'text-gray-400'}`}>
                      {item.name}
                    </h4>
                    {!item.is_available && (
                      <span className="px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded">
                        Unavailable
                      </span>
                    )}
                  </div>
                  {item.description && (
                    <p className={`text-sm mt-1 ${item.is_available ? 'text-gray-500' : 'text-gray-400'}`}>
                      {item.description}
                    </p>
                  )}
                  {item.dietary_tags?.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      {item.dietary_tags.map((tag) => (
                        <DietaryBadge key={tag} tag={tag} />
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <span className={`font-medium ${item.is_available ? 'text-gray-900' : 'text-gray-400'}`}>
                    {formatPrice(item.price_cents)}
                  </span>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onToggleAvailability(item)}
                      className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                      title={item.is_available ? 'Mark unavailable' : 'Mark available'}
                    >
                      {item.is_available ? (
                        <EyeSlashIcon className="h-4 w-4" />
                      ) : (
                        <EyeIcon className="h-4 w-4" />
                      )}
                    </button>
                    <button
                      onClick={() => onEditItem(item)}
                      className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="Edit item"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => onDeleteItem(item)}
                      className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      title="Delete item"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {(!category.items || category.items.length === 0) && (
            <div className="p-4 text-center text-gray-500 text-sm">
              No items in this category
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function MenuManagement() {
  const [menuData, setMenuData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedCategories, setExpandedCategories] = useState({});
  const [user, setUser] = useState(null);

  // Modals
  const [showImportModal, setShowImportModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [deletingItem, setDeletingItem] = useState(null);

  const appContext = useAppContext();
  const showNotification = appContext?.showNotification || ((msg, type) => console.log(type, msg));

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const userData = JSON.parse(userStr);
      setUser(userData);
      fetchMenu(userData.id);
    }
  }, []);

  const fetchMenu = async (accountId) => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/onboarding/accounts/${accountId}/menu-full`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMenuData(data);
        // Expand all categories by default
        const allExpanded = {};
        data.menus?.forEach((menu) => {
          menu.categories?.forEach((cat) => {
            allExpanded[cat.id] = true;
          });
        });
        setExpandedCategories(allExpanded);
      } else if (response.status === 404) {
        setMenuData({ menus: [] });
      } else {
        setError('Failed to load menu');
      }
    } catch (err) {
      console.error('Failed to fetch menu:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const getAllCategories = () => {
    const categories = [];
    menuData?.menus?.forEach((menu) => {
      menu.categories?.forEach((cat) => {
        categories.push({ id: cat.id, name: cat.name, menuName: menu.name });
      });
    });
    return categories;
  };

  const handleSaveItem = async (itemData) => {
    const token = localStorage.getItem('authToken');

    try {
      if (editingItem) {
        // Update existing item
        const response = await fetch(`${API_BASE}/api/onboarding/items/${editingItem.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(itemData),
        });

        if (response.ok) {
          showNotification('Item updated successfully', 'success');
          fetchMenu(user.id);
        } else {
          showNotification('Failed to update item', 'error');
        }
      } else {
        // Create new item
        const response = await fetch(`${API_BASE}/api/onboarding/items`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(itemData),
        });

        if (response.ok) {
          showNotification('Item added successfully', 'success');
          fetchMenu(user.id);
        } else {
          showNotification('Failed to add item', 'error');
        }
      }
    } catch (err) {
      console.error('Save error:', err);
      showNotification('Failed to save item', 'error');
    }

    setShowEditModal(false);
    setEditingItem(null);
  };

  const handleDeleteItem = async () => {
    if (!deletingItem) return;

    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${API_BASE}/api/onboarding/items/${deletingItem.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        showNotification('Item deleted successfully', 'success');
        fetchMenu(user.id);
      } else {
        showNotification('Failed to delete item', 'error');
      }
    } catch (err) {
      console.error('Delete error:', err);
      showNotification('Failed to delete item', 'error');
    }

    setDeletingItem(null);
  };

  const handleToggleAvailability = async (item) => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(
        `${API_BASE}/api/onboarding/items/${item.id}/availability?is_available=${!item.is_available}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        showNotification(
          `${item.name} is now ${!item.is_available ? 'available' : 'unavailable'}`,
          'success'
        );
        fetchMenu(user.id);
      } else {
        showNotification('Failed to update availability', 'error');
      }
    } catch (err) {
      console.error('Toggle error:', err);
      showNotification('Failed to update availability', 'error');
    }
  };

  const handleImportSuccess = (result) => {
    setShowImportModal(false);
    showNotification(result.message || 'Menu imported successfully', 'success');
    fetchMenu(user.id);
  };

  const toggleCategory = (categoryId) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [categoryId]: !prev[categoryId],
    }));
  };

  const expandAll = () => {
    const allExpanded = {};
    menuData?.menus?.forEach((menu) => {
      menu.categories?.forEach((cat) => {
        allExpanded[cat.id] = true;
      });
    });
    setExpandedCategories(allExpanded);
  };

  const collapseAll = () => {
    setExpandedCategories({});
  };

  // Count total items
  const totalItems = menuData?.menus?.reduce((total, menu) => {
    return total + (menu.categories?.reduce((catTotal, cat) => {
      return catTotal + (cat.items?.length || 0);
    }, 0) || 0);
  }, 0) || 0;

  const totalCategories = menuData?.menus?.reduce((total, menu) => {
    return total + (menu.categories?.length || 0);
  }, 0) || 0;

  const openAddItem = () => {
    setEditingItem(null);
    setShowEditModal(true);
  };

  const openEditItem = (item) => {
    setEditingItem(item);
    setShowEditModal(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Menu Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            View and manage your restaurant menu
          </p>
        </div>
        <div className="flex gap-2">
          {totalItems > 0 && (
            <Button variant="secondary" onClick={openAddItem}>
              <PlusIcon className="h-4 w-4 mr-1" />
              Add Item
            </Button>
          )}
          <Button onClick={() => setShowImportModal(true)}>
            <DocumentArrowUpIcon className="h-4 w-4 mr-1" />
            Import Menu
          </Button>
        </div>
      </div>

      {loading ? (
        <Card>
          <div className="p-8 text-center text-gray-500">Loading menu...</div>
        </Card>
      ) : error ? (
        <Card>
          <div className="p-8 text-center">
            <DocumentTextIcon className="h-12 w-12 text-red-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Error Loading Menu</h3>
            <p className="mt-1 text-sm text-red-500">{error}</p>
            <Button onClick={() => fetchMenu(user?.id)} className="mt-4" variant="secondary">
              Try Again
            </Button>
          </div>
        </Card>
      ) : !menuData?.menus?.length || totalItems === 0 ? (
        <Card>
          <div className="p-8 text-center">
            <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No Menu Items</h3>
            <p className="mt-1 text-sm text-gray-500">
              Import your menu to enable AI ordering. You can upload a photo of your menu,
              a PDF, or paste the text.
            </p>
            <Button className="mt-4" onClick={() => setShowImportModal(true)}>
              <DocumentArrowUpIcon className="h-4 w-4 mr-1" />
              Import Menu
            </Button>
          </div>
        </Card>
      ) : (
        <>
          {/* Menu Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <div className="p-4">
                <p className="text-sm text-gray-500">Total Items</p>
                <p className="text-2xl font-bold text-gray-900">{totalItems}</p>
              </div>
            </Card>
            <Card>
              <div className="p-4">
                <p className="text-sm text-gray-500">Categories</p>
                <p className="text-2xl font-bold text-gray-900">{totalCategories}</p>
              </div>
            </Card>
            <Card>
              <div className="p-4">
                <p className="text-sm text-gray-500">Menus</p>
                <p className="text-2xl font-bold text-gray-900">{menuData.menus.length}</p>
              </div>
            </Card>
          </div>

          {/* Menu Content */}
          {menuData.menus.map((menu) => (
            <Card key={menu.id}>
              <div className="p-4 border-b">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">{menu.name}</h2>
                    {menu.description && (
                      <p className="text-sm text-gray-500">{menu.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm" onClick={expandAll}>
                      Expand All
                    </Button>
                    <Button variant="ghost" size="sm" onClick={collapseAll}>
                      Collapse All
                    </Button>
                  </div>
                </div>
              </div>

              <div className="p-4 space-y-4">
                {menu.categories?.map((category) => (
                  <MenuCategory
                    key={category.id}
                    category={category}
                    isExpanded={expandedCategories[category.id]}
                    onToggle={() => toggleCategory(category.id)}
                    onEditItem={openEditItem}
                    onDeleteItem={setDeletingItem}
                    onToggleAvailability={handleToggleAvailability}
                  />
                ))}
                {(!menu.categories || menu.categories.length === 0) && (
                  <div className="text-center py-8 text-gray-500">
                    No categories in this menu
                  </div>
                )}
              </div>
            </Card>
          ))}
        </>
      )}

      {/* Modals */}
      {showImportModal && (
        <ImportMenuModal
          accountId={user?.id}
          onSuccess={handleImportSuccess}
          onClose={() => setShowImportModal(false)}
        />
      )}

      {showEditModal && (
        <EditItemModal
          item={editingItem}
          categories={getAllCategories()}
          onSave={handleSaveItem}
          onClose={() => {
            setShowEditModal(false);
            setEditingItem(null);
          }}
        />
      )}

      {deletingItem && (
        <DeleteConfirmModal
          item={deletingItem}
          onConfirm={handleDeleteItem}
          onClose={() => setDeletingItem(null)}
        />
      )}
    </div>
  );
}
