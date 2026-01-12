import { useQuery } from '@tanstack/react-query'
import { restaurantAPI } from '../../services/api'
import { Plus, Edit, Leaf, Flame } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function RestaurantMenu() {
  const { user } = useAuth()
  const accountId = user?.id

  const { data: menuData, isLoading } = useQuery({
    queryKey: ['menu', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId!),
    enabled: !!accountId,
  })

  const menu = menuData?.data

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
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Menu</h1>
            <p className="text-gray-600 mt-1">Manage your restaurant menu</p>
          </div>
          <button onClick={() => alert('Menu creation form coming soon!')} className="btn btn-primary">
            <Plus className="w-5 h-5 mr-2" /> Create Menu
          </button>
        </div>
        <div className="card text-center py-12">
          <p className="text-gray-500">No menu created yet. Start by creating your first menu.</p>
        </div>
      </div>
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

      {menu.menus.map((menuObj: any) => (
        <div key={menuObj.id}>
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

                      <button className="ml-4 p-2 text-gray-400 hover:text-gray-600">
                        <Edit className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
