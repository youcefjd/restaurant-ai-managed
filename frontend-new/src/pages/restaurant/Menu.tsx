import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { Plus, Edit, Leaf, Flame, Trash2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import CreateMenuModal from '../../components/CreateMenuModal'

export default function RestaurantMenu() {
  const { user } = useAuth()
  const accountId = user?.id
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: menuData, isLoading } = useQuery({
    queryKey: ['menu', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId!),
    enabled: !!accountId,
  })

  const menu = menuData?.data

  // Mutation to delete a single menu item
  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => restaurantAPI.deleteMenuItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
    },
  })

  // Mutation to delete all menu items
  const deleteAllItemsMutation = useMutation({
    mutationFn: ({ accountId, menuId }: { accountId: number; menuId: number }) =>
      restaurantAPI.deleteAllMenuItems(accountId, menuId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
    },
  })

  const handleDeleteItem = (itemId: number, itemName: string) => {
    if (window.confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) {
      deleteItemMutation.mutate(itemId)
    }
  }

  const handleDeleteAllItems = (menuId: number, menuName: string) => {
    if (window.confirm(`Are you sure you want to delete ALL items from "${menuName}"? This action cannot be undone.`)) {
      if (accountId) {
        deleteAllItemsMutation.mutate({ accountId, menuId })
      }
    }
  }

  const getDietaryBadge = (tags: string[]) => {
    const badges = []
    if (tags?.includes('vegetarian')) {
      badges.push(
        <span key="veg" className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
          <Leaf className="w-3 h-3" /> Vegetarian
        </span>
      )
    }
    if (tags?.includes('vegan')) {
      badges.push(
        <span key="vegan" className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
          <Leaf className="w-3 h-3" /> Vegan
        </span>
      )
    }
    if (tags?.includes('halal')) {
      badges.push(
        <span key="halal" className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
          Halal
        </span>
      )
    }
    if (tags?.includes('spicy')) {
      badges.push(
        <span key="spicy" className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-red-100 text-red-700 rounded">
          <Flame className="w-3 h-3" /> Spicy
        </span>
      )
    }
    return badges
  }

  if (isLoading) {
    return <div className="text-center py-12">Loading menu...</div>
  }

  if (!menu?.menus || menu.menus.length === 0) {
    return (
      <>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Menu</h1>
              <p className="text-gray-600 mt-1">Manage your restaurant menu</p>
            </div>
            <button onClick={() => setIsCreateModalOpen(true)} className="btn btn-primary">
              <Plus className="w-5 h-5 mr-2" /> Create Menu
            </button>
          </div>
          <div className="card text-center py-12">
            <p className="text-gray-500">No menu created yet. Start by creating your first menu.</p>
          </div>
        </div>
        {accountId && (
          <CreateMenuModal
            isOpen={isCreateModalOpen}
            onClose={() => setIsCreateModalOpen(false)}
            accountId={accountId}
          />
        )}
      </>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Menu</h1>
          <p className="text-gray-600 mt-1">{menu.business_name}</p>
        </div>
        <button
          onClick={() => alert('Add item form coming soon!')}
          className="btn btn-primary"
        >
          <Plus className="w-5 h-5 mr-2" /> Add Item
        </button>
      </div>

      {menu.menus.map((menuObj: any) => {
        const totalItems = menuObj.categories.reduce((sum: number, cat: any) => sum + (cat.items?.length || 0), 0)
        return (
          <div key={menuObj.id} className="mb-8">
            <div className="flex items-center justify-between mb-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <h2 className="text-xl font-bold">{menuObj.name}</h2>
                <p className="text-sm text-gray-500 mt-1">{totalItems} item(s) total</p>
              </div>
              {totalItems > 0 && (
                <button
                  onClick={() => handleDeleteAllItems(menuObj.id, menuObj.name)}
                  disabled={deleteAllItemsMutation.isPending}
                  className="px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-lg font-medium hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  {deleteAllItemsMutation.isPending ? 'Deleting...' : 'Delete All Items'}
                </button>
              )}
            </div>
            {menuObj.categories.map((category: any) => (
              <div key={category.id} className="mb-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold">{category.name}</h2>
                  <button className="text-sm text-primary-600 hover:text-primary-700">
                    Edit Category
                  </button>
                </div>

              <div className="grid gap-4">
                {category.items.map((item: any) => (
                  <div key={item.id} className="card hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-lg">{item.name}</h3>
                            <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                          </div>
                          <p className="text-xl font-bold text-primary-600 ml-4">
                            ${(item.price_cents / 100).toFixed(2)}
                          </p>
                        </div>

                        {item.dietary_tags && item.dietary_tags.length > 0 && (
                          <div className="flex gap-2 mt-3">
                            {getDietaryBadge(item.dietary_tags)}
                          </div>
                        )}

                        {item.modifiers && item.modifiers.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-xs font-medium text-gray-700 mb-2">Customizations:</p>
                            <div className="flex flex-wrap gap-2">
                              {item.modifiers.map((mod: any) => (
                                <span
                                  key={mod.id}
                                  className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                                >
                                  {mod.name}
                                  {mod.price_cents > 0 && ` (+$${(mod.price_cents / 100).toFixed(2)})`}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="ml-4 flex gap-2">
                        <button className="p-2 text-gray-400 hover:text-gray-600">
                          <Edit className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => handleDeleteItem(item.id, item.name)}
                          disabled={deleteItemMutation.isPending}
                          className="p-2 text-red-400 hover:text-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="Delete item"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          </div>
        )
      })}
    </div>
  )
}
