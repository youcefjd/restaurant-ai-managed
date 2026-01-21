import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { Plus, Edit, Trash2, Sparkles, ChevronDown, ChevronUp } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import CreateMenuModal from '../../components/CreateMenuModal'
import EditMenuModal from '../../components/EditMenuModal'

export default function RestaurantMenu() {
  const { user } = useAuth()
  const accountId = user?.id
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [createModalStep, setCreateModalStep] = useState<'create-name' | 'auto-generate'>('create-name')
  const [editingMenu, setEditingMenu] = useState<{ id: number; name: string; description?: string } | null>(null)
  const [expandedMenuIds, setExpandedMenuIds] = useState<Set<number>>(new Set())

  const queryClient = useQueryClient()

  const { data: menuData, isLoading } = useQuery({
    queryKey: ['menu', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId!),
    enabled: !!accountId,
    placeholderData: (previousData) => previousData, // Keep previous data while refetching
    refetchOnMount: 'always', // Refetch on mount but keep previous data visible
  })

  const menu = menuData?.data

  const deleteMenuMutation = useMutation({
    mutationFn: (menuId: number) => restaurantAPI.deleteMenu(menuId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      await queryClient.refetchQueries({ queryKey: ['menu', accountId] })
    },
  })

  const handleDeleteMenu = (menuId: number, menuName: string) => {
    if (window.confirm(`Are you sure you want to delete "${menuName}"? This action cannot be undone and will delete all categories and items in this menu.`)) {
      deleteMenuMutation.mutate(menuId)
    }
  }

  const handleEditMenu = (menuObj: any) => {
    setEditingMenu({
      id: menuObj.id,
      name: menuObj.name,
      description: menuObj.description || '',
    })
  }

  const toggleMenuExpansion = (menuId: number, e: React.MouseEvent) => {
    // Prevent expansion when clicking edit/delete buttons
    if ((e.target as HTMLElement).closest('button')) {
      return
    }
    
    setExpandedMenuIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(menuId)) {
        newSet.delete(menuId)
      } else {
        newSet.add(menuId)
      }
      return newSet
    })
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
            <div className="flex gap-3">
              <button 
                onClick={() => {
                  setCreateModalStep('create-name')
                  setIsCreateModalOpen(true)
                }} 
                className="btn btn-primary"
              >
                <Plus className="w-5 h-5 mr-2" /> Create New Menu
              </button>
              <button 
                onClick={() => {
                  setCreateModalStep('auto-generate')
                  setIsCreateModalOpen(true)
                }} 
                className="btn btn-secondary"
              >
                <Sparkles className="w-5 h-5 mr-2" /> Auto-Generate Menu
              </button>
            </div>
          </div>
          <div className="card text-center py-12">
            <p className="text-gray-500">No menus created yet. Create your first menu to get started.</p>
          </div>
        </div>
        {accountId && (
          <CreateMenuModal
            isOpen={isCreateModalOpen}
            onClose={() => setIsCreateModalOpen(false)}
            accountId={accountId}
            initialStep={createModalStep}
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
        <div className="flex gap-3">
          <button 
            onClick={() => {
              setCreateModalStep('create-name')
              setIsCreateModalOpen(true)
            }} 
            className="btn btn-primary"
          >
            <Plus className="w-5 h-5 mr-2" /> Create New Menu
          </button>
          <button 
            onClick={() => {
              setCreateModalStep('auto-generate')
              setIsCreateModalOpen(true)
            }} 
            className="btn btn-secondary"
          >
            <Sparkles className="w-5 h-5 mr-2" /> Auto-Generate Menu
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {menu.menus.map((menuObj: any) => {
          const isExpanded = expandedMenuIds.has(menuObj.id)
          const allItems = menuObj.categories?.flatMap((cat: any) => 
            cat.items?.map((item: any) => ({ ...item, categoryName: cat.name, categoryId: cat.id })) || []
          ) || []
          
          return (
            <div
              key={menuObj.id}
              className="card overflow-hidden transition-all"
            >
              {/* Menu Header - Clickable */}
              <div
                onClick={(e) => toggleMenuExpansion(menuObj.id, e)}
                className="flex items-center justify-between p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3 flex-1">
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold">{menuObj.name}</h3>
                    {menuObj.description && (
                      <p className="text-sm text-gray-500 mt-1">{menuObj.description}</p>
                    )}
                    {!isExpanded && allItems.length > 0 && (
                      <p className="text-xs text-gray-400 mt-1">{allItems.length} item(s)</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleEditMenu(menuObj)}
                    className="px-4 py-2 text-primary-600 border border-primary-200 rounded-lg hover:bg-primary-50 transition-colors flex items-center gap-2"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteMenu(menuObj.id, menuObj.name)}
                    disabled={deleteMenuMutation.isPending}
                    className="px-4 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    {deleteMenuMutation.isPending ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>

              {/* Expanded Content - Menu Items */}
              {isExpanded && (
                <div className="border-t border-gray-200 p-4 bg-gray-50">
                  {allItems.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <p>No menu items yet. Click "Edit" to add items to this menu.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {menuObj.categories?.map((category: any) => {
                        const categoryItems = category.items || []
                        if (categoryItems.length === 0) return null

                        return (
                          <div key={category.id} className="space-y-3">
                            <h4 className="text-md font-semibold text-gray-800 border-b border-gray-300 pb-2">
                              {category.name}
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {categoryItems.map((item: any) => (
                                <div
                                  key={item.id}
                                  className="bg-white rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow"
                                >
                                  <div className="flex items-start justify-between mb-2">
                                    <div className="flex-1">
                                      <h5 className="font-semibold text-gray-900">{item.name}</h5>
                                      {item.description && (
                                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                                          {item.description}
                                        </p>
                                      )}
                                    </div>
                                    <p className="text-lg font-bold text-primary-600 ml-3">
                                      ${((item.price_cents || 0) / 100).toFixed(2)}
                                    </p>
                                  </div>
                                  {item.dietary_tags && item.dietary_tags.length > 0 && (
                                    <div className="flex flex-wrap gap-1 mt-2">
                                      {item.dietary_tags.map((tag: string) => (
                                        <span
                                          key={tag}
                                          className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded"
                                        >
                                          {tag}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Create Menu Modal */}
      {accountId && (
        <CreateMenuModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          accountId={accountId}
          initialStep={createModalStep}
        />
      )}

      {/* Edit Menu Modal */}
      {accountId && editingMenu && (
        <EditMenuModal
          isOpen={!!editingMenu}
          onClose={() => setEditingMenu(null)}
          accountId={accountId}
          menu={editingMenu}
        />
      )}
    </div>
  )
}
