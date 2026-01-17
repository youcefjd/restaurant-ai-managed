import { useState } from 'react'
import { X, Plus, Edit, Trash2 } from 'lucide-react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../services/api'
import AddMenuItemModal from './AddMenuItemModal'

interface EditMenuModalProps {
  isOpen: boolean
  onClose: () => void
  accountId: number
  menu: {
    id: number
    name: string
    description?: string
  }
}

export default function EditMenuModal({ isOpen, onClose, accountId, menu }: EditMenuModalProps) {
  const queryClient = useQueryClient()
  const [menuName, setMenuName] = useState(menu.name)
  const [menuDescription, setMenuDescription] = useState(menu.description || '')
  const [isAddItemModalOpen, setIsAddItemModalOpen] = useState(false)

  // Fetch full menu data to get items
  const { data: menuData } = useQuery({
    queryKey: ['menu', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId),
    enabled: isOpen,
  })

  // Find the current menu and all its items
  const currentMenuData = menuData?.data?.menus?.find((m: any) => m.id === menu.id)
  const allItems = currentMenuData?.categories?.flatMap((cat: any) => 
    cat.items?.map((item: any) => ({ ...item, categoryName: cat.name, categoryId: cat.id })) || []
  ) || []

  const allCategories = currentMenuData?.categories?.map((cat: any) => ({
    id: cat.id,
    name: cat.name,
    menu_id: menu.id
  })) || []

  const allMenus = menuData?.data?.menus?.map((m: any) => ({ id: m.id, name: m.name })) || []

  const updateMenuMutation = useMutation({
    mutationFn: (data: { menu_name?: string; menu_description?: string }) =>
      restaurantAPI.updateMenu(menu.id, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      await queryClient.refetchQueries({ queryKey: ['menu', accountId] })
    },
  })

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => restaurantAPI.deleteMenuItem(itemId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      await queryClient.refetchQueries({ queryKey: ['menu', accountId] })
    },
  })

  const handleSaveMenuName = () => {
    if (!menuName.trim()) {
      alert('Please enter a menu name')
      return
    }

    updateMenuMutation.mutate({
      menu_name: menuName.trim(),
      menu_description: menuDescription.trim() || undefined,
    })
  }

  const handleDeleteItem = (itemId: number, itemName: string) => {
    if (window.confirm(`Are you sure you want to delete "${itemName}"?`)) {
      deleteItemMutation.mutate(itemId)
    }
  }

  const handleItemAdded = () => {
    setIsAddItemModalOpen(false)
  }

  if (!isOpen) return null

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white z-10">
            <h2 className="text-2xl font-bold">Edit Menu</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Menu Name and Description */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Menu Name *
                </label>
                <input
                  type="text"
                  value={menuName}
                  onChange={(e) => setMenuName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Menu name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Menu Description (optional)
                </label>
                <input
                  type="text"
                  value={menuDescription}
                  onChange={(e) => setMenuDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Menu description"
                />
              </div>
              <button
                onClick={handleSaveMenuName}
                disabled={updateMenuMutation.isPending || !menuName.trim()}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {updateMenuMutation.isPending ? 'Saving...' : 'Save Menu Name'}
              </button>
            </div>

            {/* Menu Items Section */}
            <div className="border-t pt-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Menu Items</h3>
                <button
                  onClick={() => setIsAddItemModalOpen(true)}
                  className="btn btn-primary"
                >
                  <Plus className="w-5 h-5 mr-2" />
                  Add Menu Item
                </button>
              </div>

              {allItems.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <p className="text-gray-500">No menu items yet. Add your first item to get started.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {allItems.map((item: any) => (
                    <div
                      key={item.id}
                      className="card p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg mb-1">{item.name}</h4>
                          <p className="text-xs text-gray-500 mb-1">Category: {item.categoryName}</p>
                          {item.description && (
                            <p className="text-sm text-gray-600 mb-2 line-clamp-2">{item.description}</p>
                          )}
                          <p className="text-lg font-bold text-primary-600">
                            ${((item.price_cents || 0) / 100).toFixed(2)}
                          </p>
                        </div>
                      </div>

                      <div className="flex gap-2 mt-3 pt-3 border-t">
                        <button
                          onClick={() => {
                            // TODO: Implement edit item functionality
                            alert('Edit item functionality coming soon')
                          }}
                          className="flex-1 px-3 py-2 text-sm text-primary-600 border border-primary-200 rounded-lg hover:bg-primary-50 transition-colors flex items-center justify-center gap-2"
                        >
                          <Edit className="w-4 h-4" />
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteItem(item.id, item.name)}
                          disabled={deleteItemMutation.isPending}
                          className="flex-1 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Add Menu Item Modal */}
      {isAddItemModalOpen && (
        <AddMenuItemModal
          isOpen={isAddItemModalOpen}
          onClose={() => setIsAddItemModalOpen(false)}
          accountId={accountId}
          categories={allCategories}
          menus={allMenus}
          keepOpenAfterAdd={false}
          onItemAdded={handleItemAdded}
        />
      )}
    </>
  )
}
