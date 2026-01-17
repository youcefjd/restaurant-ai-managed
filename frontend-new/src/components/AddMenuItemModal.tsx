import { useState } from 'react'
import { X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../services/api'

interface AddMenuItemModalProps {
  isOpen: boolean
  onClose: () => void
  accountId: number
  categories: Array<{ id: number; name: string; menu_id?: number }>
  menus?: Array<{ id: number; name: string }>
  keepOpenAfterAdd?: boolean
  onItemAdded?: () => void
  hideModalWrapper?: boolean
}

const PREDEFINED_CATEGORIES = ['Appetizer', 'Main', 'Dessert', 'Drinks', 'Sides'] as const

export default function AddMenuItemModal({ 
  isOpen, 
  onClose, 
  accountId, 
  categories, 
  menus = [], 
  keepOpenAfterAdd = false,
  onItemAdded,
  hideModalWrapper = false
}: AddMenuItemModalProps) {
  const queryClient = useQueryClient()
  const [selectedCategoryName, setSelectedCategoryName] = useState<string>('')
  const [selectedMenuId, setSelectedMenuId] = useState(menus[0]?.id || 0)
  const [formData, setFormData] = useState({
    category_id: 0,
    name: '',
    description: '',
    price: '',
    dietary_tags: [] as string[],
    is_available: true,
    preparation_time_minutes: '',
    display_order: 0,
  })

  const createCategoryMutation = useMutation({
    mutationFn: (data: { menu_id: number; name: string; description?: string }) =>
      restaurantAPI.createCategory(data.menu_id, { name: data.name, description: data.description }),
    onSuccess: (response) => {
      // After creating category, create the menu item with the new category_id
      const newCategoryId = response.data.id
      const price_cents = Math.round(parseFloat(formData.price) * 100)
      if (isNaN(price_cents) || price_cents < 0) {
        alert('Please enter a valid price')
        return
      }

      const itemData = {
        category_id: newCategoryId,
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        price_cents,
        dietary_tags: formData.dietary_tags.length > 0 ? formData.dietary_tags : undefined,
        is_available: formData.is_available,
        preparation_time_minutes: formData.preparation_time_minutes
          ? parseInt(formData.preparation_time_minutes)
          : undefined,
        display_order: formData.display_order,
      }

      createMenuItemMutation.mutate(itemData)
    },
  })

  const createMenuItemMutation = useMutation({
    mutationFn: (data: any) => restaurantAPI.createMenuItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      
      // Reset form
      setSelectedCategoryName('')
      setSelectedMenuId(menus[0]?.id || 0)
      setFormData({
        category_id: 0,
        name: '',
        description: '',
        price: '',
        dietary_tags: [],
        is_available: true,
        preparation_time_minutes: '',
        display_order: 0,
      })
      
      // Call callback if provided
      if (onItemAdded) {
        onItemAdded()
      }
      
      // Only close if keepOpenAfterAdd is false
      if (!keepOpenAfterAdd) {
        onClose()
      }
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate required fields
    if (!formData.name.trim()) {
      alert('Please enter an item name')
      return
    }

    if (!selectedCategoryName) {
      alert('Please select a category')
      return
    }

    if (!formData.price || isNaN(parseFloat(formData.price)) || parseFloat(formData.price) < 0) {
      alert('Please enter a valid price')
      return
    }

    if (!selectedMenuId) {
      alert('Please select a menu')
      return
    }

    const price_cents = Math.round(parseFloat(formData.price) * 100)

    // Find or create the category
    let categoryId: number
    const existingCategory = categories.find(
      cat => cat.name.toLowerCase() === selectedCategoryName.toLowerCase() && 
             (cat.menu_id === selectedMenuId || !cat.menu_id)
    )

    if (existingCategory) {
      categoryId = existingCategory.id
      // Create item with existing category
      const data = {
        category_id: categoryId,
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        price_cents,
        dietary_tags: formData.dietary_tags.length > 0 ? formData.dietary_tags : undefined,
        is_available: formData.is_available,
        preparation_time_minutes: formData.preparation_time_minutes
          ? parseInt(formData.preparation_time_minutes)
          : undefined,
        display_order: formData.display_order,
      }
      createMenuItemMutation.mutate(data)
    } else {
      // Create category first, then create item
      createCategoryMutation.mutate({
        menu_id: selectedMenuId,
        name: selectedCategoryName,
      })
    }
  }

  const toggleDietaryTag = (tag: string) => {
    setFormData((prev) => ({
      ...prev,
      dietary_tags: prev.dietary_tags.includes(tag)
        ? prev.dietary_tags.filter((t) => t !== tag)
        : [...prev.dietary_tags, tag],
    }))
  }

  if (!isOpen) return null

  const formContent = (
    <>
      {!hideModalWrapper && (
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Add Menu Item</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Menu Selection (if multiple menus) */}
          {menus.length > 1 && (
            <div>
              <label className="label">Menu *</label>
              <select
                required
                value={selectedMenuId}
                onChange={(e) => setSelectedMenuId(parseInt(e.target.value))}
                className="input"
              >
                {menus.map((menu) => (
                  <option key={menu.id} value={menu.id}>
                    {menu.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Category Selection */}
          <div>
            <label className="label">Category *</label>
            <select
              required
              value={selectedCategoryName}
              onChange={(e) => setSelectedCategoryName(e.target.value)}
              className="input"
            >
              <option value="">Select a category</option>
              {PREDEFINED_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Item Name */}
          <div>
            <label className="label">Item Name *</label>
            <input
              type="text"
              required
              maxLength={255}
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              placeholder="e.g., Butter Chicken"
            />
          </div>

          {/* Description */}
          <div>
            <label className="label">Description</label>
            <textarea
              rows={3}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input"
              placeholder="Describe your dish..."
            />
          </div>

          {/* Price */}
          <div>
            <label className="label">Price ($) *</label>
            <input
              type="number"
              required
              min="0"
              step="0.01"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: e.target.value })}
              className="input"
              placeholder="e.g., 15.99"
            />
          </div>

          {/* Preparation Time */}
          <div>
            <label className="label">Preparation Time (minutes)</label>
            <input
              type="number"
              min="0"
              value={formData.preparation_time_minutes}
              onChange={(e) => setFormData({ ...formData, preparation_time_minutes: e.target.value })}
              className="input"
              placeholder="e.g., 20"
            />
          </div>

          {/* Dietary Tags */}
          <div>
            <label className="label">Dietary Tags</label>
            <div className="flex flex-wrap gap-2 mt-2">
              {['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'halal', 'spicy'].map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleDietaryTag(tag)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    formData.dietary_tags.includes(tag)
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          {/* Available Toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_available"
              checked={formData.is_available}
              onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
              className="w-4 h-4"
            />
            <label htmlFor="is_available" className="text-sm font-medium">
              Item is available for ordering
            </label>
          </div>

          {/* Error Message */}
          {(createMenuItemMutation.isError || createCategoryMutation.isError) && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">
                Error: {String(createMenuItemMutation.error || createCategoryMutation.error)}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={createMenuItemMutation.isPending || createCategoryMutation.isPending}
              className={`btn btn-primary ${hideModalWrapper ? 'w-full' : 'flex-1'}`}
            >
              {createMenuItemMutation.isPending || createCategoryMutation.isPending
                ? 'Adding...'
                : 'Add Menu Item'}
            </button>
            {!hideModalWrapper && (
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            )}
          </div>
        </form>
    </>
  )

  if (hideModalWrapper) {
    return formContent
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
        {formContent}
      </div>
    </div>
  )
}
