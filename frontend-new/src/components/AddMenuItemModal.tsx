import { useState } from 'react'
import { X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../services/api'

interface AddMenuItemModalProps {
  isOpen: boolean
  onClose: () => void
  accountId: number
  categories: Array<{ id: number; name: string }>
}

export default function AddMenuItemModal({ isOpen, onClose, accountId, categories }: AddMenuItemModalProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    category_id: categories[0]?.id || 0,
    name: '',
    description: '',
    price: '',
    dietary_tags: [] as string[],
    is_available: true,
    preparation_time_minutes: '',
    display_order: 0,
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => restaurantAPI.createMenuItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      onClose()
      // Reset form
      setFormData({
        category_id: categories[0]?.id || 0,
        name: '',
        description: '',
        price: '',
        dietary_tags: [],
        is_available: true,
        preparation_time_minutes: '',
        display_order: 0,
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const price_cents = Math.round(parseFloat(formData.price) * 100)
    if (isNaN(price_cents) || price_cents < 0) {
      alert('Please enter a valid price')
      return
    }

    const data = {
      category_id: formData.category_id,
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

    createMutation.mutate(data)
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

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">Add Menu Item</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Category Selection */}
          <div>
            <label className="label">Category *</label>
            <select
              required
              value={formData.category_id}
              onChange={(e) => setFormData({ ...formData, category_id: parseInt(e.target.value) })}
              className="input"
            >
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
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
          {createMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">
                Error: {String(createMutation.error)}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn btn-primary flex-1"
            >
              {createMutation.isPending ? 'Adding...' : 'Add Menu Item'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
