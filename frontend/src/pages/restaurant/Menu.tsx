import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { Plus, Edit, Trash2, ChevronDown, ChevronRight, X } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function RestaurantMenu() {
  const { user } = useAuth()
  const accountId = user?.id
  const [expandedMenuId, setExpandedMenuId] = useState<number | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingMenu, setEditingMenu] = useState<any>(null)
  const [addingItemToCategory, setAddingItemToCategory] = useState<{ menuId: number; categoryId: number } | null>(null)
  const [editingItem, setEditingItem] = useState<any>(null)

  const queryClient = useQueryClient()

  const { data: menuData, isLoading, isFetching } = useQuery({
    queryKey: ['menu', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId!),
    enabled: !!accountId,
    staleTime: 60000,
    gcTime: 300000, // Keep in cache for 5 minutes
    placeholderData: (prev) => prev, // Keep previous data while fetching
  })

  const menu = menuData?.data

  const deleteMenuMutation = useMutation({
    mutationFn: (menuId: number) => restaurantAPI.deleteMenu(menuId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['menu', accountId] }),
  })

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => restaurantAPI.deleteMenuItem(itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['menu', accountId] }),
  })

  const createMenuMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      restaurantAPI.createMenu(accountId!, { menu_name: data.name, menu_description: data.description }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      setShowCreateModal(false)
    },
  })

  // Only show full spinner on initial load (no cached data)
  if (isLoading && !menuData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  const menus = menu?.menus || []

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          Your Menus
          {isFetching && <div className="spinner" style={{ width: '1rem', height: '1rem' }} />}
        </h2>
        <button onClick={() => setShowCreateModal(true)} className="btn btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Menu
        </button>
      </div>

      {/* Menu List */}
      {menus.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-dim">No menus yet. Create your first menu to get started.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {menus.map((menuObj: any) => {
            const isExpanded = expandedMenuId === menuObj.id
            const itemCount = menuObj.categories?.reduce((sum: number, cat: any) => sum + (cat.items?.length || 0), 0) || 0

            return (
              <div key={menuObj.id} className="card p-0">
                {/* Menu Header */}
                <div
                  onClick={() => setExpandedMenuId(isExpanded ? null : menuObj.id)}
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-white/5"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? <ChevronDown className="w-4 h-4 text-dim" /> : <ChevronRight className="w-4 h-4 text-dim" />}
                    <div>
                      <h3 className="font-medium">{menuObj.name}</h3>
                      <p className="text-xs text-dim">{itemCount} items</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                    <button
                      onClick={() => setEditingMenu(menuObj)}
                      className="btn btn-sm btn-secondary flex items-center gap-1"
                    >
                      <Edit className="w-3 h-3" /> Edit
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete "${menuObj.name}"?`)) {
                          deleteMenuMutation.mutate(menuObj.id)
                        }
                      }}
                      className="btn btn-sm btn-danger flex items-center gap-1"
                      disabled={deleteMenuMutation.isPending}
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>

                {/* Expanded Items */}
                {isExpanded && (
                  <div className="border-t border-[--border] p-4 space-y-4">
                    {menuObj.categories?.map((category: any) => (
                      <div key={category.id}>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-medium text-dim">{category.name}</h4>
                          <button
                            onClick={() => setAddingItemToCategory({ menuId: menuObj.id, categoryId: category.id })}
                            className="text-xs text-accent hover:underline"
                          >
                            + Add Item
                          </button>
                        </div>
                        {category.items?.length > 0 ? (
                          <div className="space-y-2">
                            {category.items.map((item: any) => (
                              <div key={item.id} className="flex items-center justify-between py-2 px-3 rounded bg-white/5 group">
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium">{item.name}</p>
                                  {item.description && (
                                    <p className="text-xs text-dim truncate max-w-md">{item.description}</p>
                                  )}
                                </div>
                                <div className="flex items-center gap-3">
                                  <p className="font-medium">${((item.price_cents || 0) / 100).toFixed(2)}</p>
                                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                      onClick={() => setEditingItem({ ...item, categoryId: category.id })}
                                      className="p-1 hover:bg-white/10 rounded"
                                      title="Edit item"
                                    >
                                      <Edit className="w-3.5 h-3.5 text-dim hover:text-white" />
                                    </button>
                                    <button
                                      onClick={() => {
                                        if (confirm(`Delete "${item.name}"?`)) {
                                          deleteItemMutation.mutate(item.id)
                                        }
                                      }}
                                      className="p-1 hover:bg-white/10 rounded"
                                      title="Delete item"
                                      disabled={deleteItemMutation.isPending}
                                    >
                                      <Trash2 className="w-3.5 h-3.5 text-dim hover:text-error" />
                                    </button>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-dim py-2">No items in this category</p>
                        )}
                      </div>
                    ))}
                    {(!menuObj.categories || menuObj.categories.length === 0) && (
                      <p className="text-sm text-dim text-center py-4">No categories yet. Click Edit to add categories and items.</p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Create Menu Modal */}
      {showCreateModal && (
        <CreateMenuModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={(name, description) => createMenuMutation.mutate({ name, description })}
          isLoading={createMenuMutation.isPending}
        />
      )}

      {/* Edit Menu Modal */}
      {editingMenu && accountId && (
        <EditMenuModal
          menu={editingMenu}
          accountId={accountId}
          onClose={() => setEditingMenu(null)}
        />
      )}

      {/* Add Item Modal */}
      {addingItemToCategory && accountId && (
        <AddItemModal
          categoryId={addingItemToCategory.categoryId}
          accountId={accountId}
          onClose={() => setAddingItemToCategory(null)}
        />
      )}

      {/* Edit Item Modal */}
      {editingItem && accountId && (
        <EditItemModal
          item={editingItem}
          accountId={accountId}
          onClose={() => setEditingItem(null)}
        />
      )}
    </div>
  )
}

// Simple Create Menu Modal
function CreateMenuModal({ onClose, onSubmit, isLoading }: {
  onClose: () => void
  onSubmit: (name: string, description: string) => void
  isLoading: boolean
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-[--border]">
          <h3 className="font-semibold">Create Menu</h3>
          <button onClick={onClose} className="text-dim hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form
          onSubmit={e => {
            e.preventDefault()
            if (name.trim()) onSubmit(name, description)
          }}
          className="p-4 space-y-4"
        >
          <div>
            <label className="text-sm text-dim block mb-1">Menu Name *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g., Lunch Menu"
              autoFocus
            />
          </div>
          <div>
            <label className="text-sm text-dim block mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={2}
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={!name.trim() || isLoading}>
              {isLoading ? 'Creating...' : 'Create Menu'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Simple Edit Menu Modal
function EditMenuModal({ menu, accountId, onClose }: {
  menu: any
  accountId: number
  onClose: () => void
}) {
  const [name, setName] = useState(menu.name)
  const [newCategory, setNewCategory] = useState('')
  const queryClient = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: () => restaurantAPI.updateMenu(menu.id, { menu_name: name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      onClose()
    },
  })

  const addCategoryMutation = useMutation({
    mutationFn: (catName: string) => restaurantAPI.createCategory(menu.id, { name: catName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      setNewCategory('')
    },
  })

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-[--border]">
          <h3 className="font-semibold">Edit Menu</h3>
          <button onClick={onClose} className="text-dim hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4 space-y-4">
          {/* Menu Name */}
          <div>
            <label className="text-sm text-dim block mb-1">Menu Name</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
              />
              <button
                onClick={() => updateMutation.mutate()}
                className="btn btn-primary"
                disabled={updateMutation.isPending || name === menu.name}
              >
                Save
              </button>
            </div>
          </div>

          {/* Categories */}
          <div>
            <label className="text-sm text-dim block mb-2">Categories</label>
            <div className="space-y-2 mb-3">
              {menu.categories?.map((cat: any) => (
                <div key={cat.id} className="flex items-center justify-between py-2 px-3 rounded bg-white/5">
                  <span>{cat.name}</span>
                  <span className="text-xs text-dim">{cat.items?.length || 0} items</span>
                </div>
              ))}
              {(!menu.categories || menu.categories.length === 0) && (
                <p className="text-sm text-dim">No categories yet</p>
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newCategory}
                onChange={e => setNewCategory(e.target.value)}
                placeholder="New category name"
              />
              <button
                onClick={() => newCategory.trim() && addCategoryMutation.mutate(newCategory.trim())}
                className="btn btn-secondary"
                disabled={!newCategory.trim() || addCategoryMutation.isPending}
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Simple Add Item Modal
function AddItemModal({ categoryId, accountId, onClose }: {
  categoryId: number
  accountId: number
  onClose: () => void
}) {
  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [description, setDescription] = useState('')
  const queryClient = useQueryClient()

  const addItemMutation = useMutation({
    mutationFn: () =>
      restaurantAPI.createMenuItem({
        category_id: categoryId,
        name,
        price_cents: Math.round(parseFloat(price) * 100),
        description,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      onClose()
    },
  })

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-[--border]">
          <h3 className="font-semibold">Add Menu Item</h3>
          <button onClick={onClose} className="text-dim hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form
          onSubmit={e => {
            e.preventDefault()
            if (name.trim() && price) addItemMutation.mutate()
          }}
          className="p-4 space-y-4"
        >
          <div>
            <label className="text-sm text-dim block mb-1">Item Name *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g., Cheeseburger"
              autoFocus
            />
          </div>
          <div>
            <label className="text-sm text-dim block mb-1">Price *</label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={e => setPrice(e.target.value)}
              placeholder="9.99"
            />
          </div>
          <div>
            <label className="text-sm text-dim block mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={2}
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!name.trim() || !price || addItemMutation.isPending}
            >
              {addItemMutation.isPending ? 'Adding...' : 'Add Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Edit Item Modal
function EditItemModal({ item, accountId, onClose }: {
  item: any
  accountId: number
  onClose: () => void
}) {
  const [name, setName] = useState(item.name)
  const [price, setPrice] = useState(((item.price_cents || 0) / 100).toString())
  const [description, setDescription] = useState(item.description || '')
  const [isAvailable, setIsAvailable] = useState(item.is_available !== false)
  const queryClient = useQueryClient()

  const updateItemMutation = useMutation({
    mutationFn: () =>
      restaurantAPI.updateMenuItem(item.id, {
        name,
        price_cents: Math.round(parseFloat(price) * 100),
        description,
        is_available: isAvailable,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      onClose()
    },
  })

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-[--border]">
          <h3 className="font-semibold">Edit Menu Item</h3>
          <button onClick={onClose} className="text-dim hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form
          onSubmit={e => {
            e.preventDefault()
            if (name.trim() && price) updateItemMutation.mutate()
          }}
          className="p-4 space-y-4"
        >
          <div>
            <label className="text-sm text-dim block mb-1">Item Name *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              autoFocus
            />
          </div>
          <div>
            <label className="text-sm text-dim block mb-1">Price *</label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={e => setPrice(e.target.value)}
            />
          </div>
          <div>
            <label className="text-sm text-dim block mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={2}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="item-available"
              checked={isAvailable}
              onChange={e => setIsAvailable(e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="item-available" className="text-sm">Available for ordering</label>
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!name.trim() || !price || updateItemMutation.isPending}
            >
              {updateItemMutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
