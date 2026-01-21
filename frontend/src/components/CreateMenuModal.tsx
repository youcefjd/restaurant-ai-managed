import { useState, useEffect } from 'react'
import { X, Upload, FileText, Image as ImageIcon, FileJson, Plus, ArrowLeft, Sparkles } from 'lucide-react'
import { restaurantAPI } from '../services/api'
import { useQueryClient, useQuery } from '@tanstack/react-query'
import AddMenuItemModal from './AddMenuItemModal'

interface CreateMenuModalProps {
  isOpen: boolean
  onClose: () => void
  accountId: number
  initialStep?: 'create-name' | 'auto-generate'
}

type ViewStep = 'list' | 'create-name' | 'create-items' | 'auto-generate'
type InputType = 'text' | 'json' | 'pdf' | 'image' | 'images'

export default function CreateMenuModal({ isOpen, onClose, accountId, initialStep = 'create-name' }: CreateMenuModalProps) {
  const [currentStep, setCurrentStep] = useState<ViewStep>(initialStep)
  const [newMenuId, setNewMenuId] = useState<number | null>(null)
  
  // Menu creation form state
  const [menuName, setMenuName] = useState('')
  const [menuDescription, setMenuDescription] = useState('')
  
  // Auto-generate form state
  const [inputType, setInputType] = useState<InputType>('text')
  const [textInput, setTextInput] = useState('')
  const [jsonInput, setJsonInput] = useState('')
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imageFiles, setImageFiles] = useState<File[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const queryClient = useQueryClient()

  // Fetch menu data for list view
  const { data: menuData } = useQuery({
    queryKey: ['menu', accountId],
    queryFn: () => restaurantAPI.getMenu(accountId),
    enabled: isOpen && (currentStep === 'list' || currentStep === 'create-items'),
  })

  const menu = menuData?.data
  const menus = menu?.menus || []
  const allCategories = menus?.flatMap((m: any) =>
    m.categories.map((cat: any) => ({ id: cat.id, name: cat.name, menu_id: m.id }))
  ) || []
  const allMenus = menus?.map((m: any) => ({ id: m.id, name: m.name })) || []

  // Reset to initial step when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentStep(initialStep)
      setNewMenuId(null)
      setMenuName('')
      setMenuDescription('')
      setError(null)
      setSuccessMessage(null)
    }
  }, [isOpen, initialStep])

  const handleCreateMenu = async () => {
    if (!menuName.trim()) {
      setError('Please enter a menu name')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await restaurantAPI.createMenu(accountId, {
        menu_name: menuName,
        menu_description: menuDescription || undefined,
      })
      
      const createdMenuId = response.data.id
      setNewMenuId(createdMenuId)
      
      // Refresh menu data and move to items step
      await queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      await queryClient.refetchQueries({ queryKey: ['menu', accountId] })
      setCurrentStep('create-items')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create menu')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleAutoGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const formData = new FormData()
      
      if (menuName) formData.append('menu_name', menuName)
      if (menuDescription) formData.append('menu_description', menuDescription)

      switch (inputType) {
        case 'text':
          if (!textInput.trim()) {
            throw new Error('Please enter menu text')
          }
          formData.append('text_data', textInput)
          break
        case 'json':
          if (!jsonInput.trim()) {
            throw new Error('Please enter JSON data')
          }
          formData.append('json_data', jsonInput)
          break
        case 'pdf':
          if (!pdfFile) {
            throw new Error('Please select a PDF file')
          }
          formData.append('pdf_file', pdfFile)
          break
        case 'image':
          if (!imageFile) {
            throw new Error('Please select an image file')
          }
          formData.append('image_file', imageFile)
          break
        case 'images':
          if (imageFiles.length === 0) {
            throw new Error('Please select at least one image file')
          }
          imageFiles.forEach((file) => {
            formData.append('image_files', file)
          })
          break
      }

      await restaurantAPI.importMenu(accountId, formData)
      
      // Refresh menu data
      await queryClient.invalidateQueries({ queryKey: ['menu', accountId] })
      await queryClient.refetchQueries({ queryKey: ['menu', accountId] })
      
      // Reset and close
      resetAutoGenerateForm()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to import menu')
    } finally {
      setIsSubmitting(false)
    }
  }

  const resetAutoGenerateForm = () => {
    setMenuName('')
    setMenuDescription('')
    setTextInput('')
    setJsonInput('')
    setPdfFile(null)
    setImageFile(null)
    setImageFiles([])
    setError(null)
    setInputType('text')
  }

  const handleClose = () => {
    resetAutoGenerateForm()
    setCurrentStep('list')
    setNewMenuId(null)
    setError(null)
    setSuccessMessage(null)
    onClose()
  }

  const handleItemAdded = () => {
    setSuccessMessage('Menu item added successfully! You can add another item or click Done to finish.')
    // Clear success message after 3 seconds
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  if (!isOpen) return null

  // List View
  if (currentStep === 'list') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-2xl font-bold">Menu Management</h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Existing Menus List */}
            {menus.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold mb-4">Existing Menus</h3>
                <div className="space-y-2">
                  {menus.map((menuObj: any) => {
                    const totalItems = menuObj.categories.reduce(
                      (sum: number, cat: any) => sum + (cat.items?.length || 0),
                      0
                    )
                    return (
                      <div
                        key={menuObj.id}
                        className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => {
                          // For now, just close modal. In future, could navigate to menu edit view
                          handleClose()
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-medium text-lg">{menuObj.name}</h4>
                            <p className="text-sm text-gray-500 mt-1">
                              {totalItems} item(s) • {menuObj.categories.length} categor{menuObj.categories.length === 1 ? 'y' : 'ies'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-500">No menus created yet.</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t">
              <button
                onClick={() => setCurrentStep('create-name')}
                className="btn btn-primary flex-1"
              >
                <Plus className="w-5 h-5 mr-2" />
                Create New Menu
              </button>
              <button
                onClick={() => setCurrentStep('auto-generate')}
                className="btn btn-secondary flex-1"
              >
                <Sparkles className="w-5 h-5 mr-2" />
                Auto-Generate Menu
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Create Name Step
  if (currentStep === 'create-name') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setCurrentStep('list')}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h2 className="text-2xl font-bold">Create New Menu</h2>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6 space-y-6">
            {/* Step Indicator */}
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded font-medium">Step 1 of 2</span>
              <span>Menu Name</span>
            </div>

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
                  placeholder="e.g., Dinner Menu, Lunch Specials"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Menu Description (optional)
                </label>
                <textarea
                  value={menuDescription}
                  onChange={(e) => setMenuDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Optional description"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={() => setCurrentStep('list')}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                disabled={isSubmitting}
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleCreateMenu}
                className="btn btn-primary"
                disabled={isSubmitting || !menuName.trim()}
              >
                {isSubmitting ? 'Creating...' : 'Next'}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Create Items Step - Use inline AddMenuItemModal component logic
  if (currentStep === 'create-items') {
    const targetMenuId = newMenuId || menus[0]?.id
    const targetMenus = targetMenuId ? [{ id: targetMenuId, name: menuName || 'Menu' }] : allMenus
    const targetCategories = allCategories.filter((cat: any) => 
      cat.menu_id === targetMenuId
    )

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setCurrentStep('create-name')}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <h2 className="text-2xl font-bold">Add Menu Items</h2>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6">
            {/* Step Indicator */}
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-6">
              <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded font-medium">Step 2 of 2</span>
              <span>Add Items to "{menuName || 'Menu'}"</span>
            </div>

            {successMessage && (
              <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
                {successMessage}
              </div>
            )}

            {/* Inline Item Form - Using AddMenuItemModal component with keepOpenAfterAdd */}
            <AddMenuItemModal
              isOpen={true}
              onClose={handleClose}
              accountId={accountId}
              categories={targetCategories}
              menus={targetMenus}
              keepOpenAfterAdd={true}
              onItemAdded={handleItemAdded}
              hideModalWrapper={true}
            />
            
            {/* Done Button */}
            <div className="mt-6 pt-4 border-t">
              <button
                onClick={handleClose}
                className="btn btn-primary w-full"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Auto-Generate View
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setCurrentStep('list')}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h2 className="text-2xl font-bold">Auto-Generate Menu</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleAutoGenerateSubmit} className="p-6 space-y-6">
          {/* Menu Name and Description */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Menu Name (optional)
              </label>
              <input
                type="text"
                value={menuName}
                onChange={(e) => setMenuName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g., Dinner Menu, Lunch Specials"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Menu Description (optional)
              </label>
              <textarea
                value={menuDescription}
                onChange={(e) => setMenuDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="Optional description"
              />
            </div>
          </div>

          {/* Input Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Input Method
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                { value: 'text' as InputType, label: 'Text', icon: FileText },
                { value: 'json' as InputType, label: 'JSON', icon: FileJson },
                { value: 'pdf' as InputType, label: 'PDF', icon: FileText },
                { value: 'image' as InputType, label: 'Image', icon: ImageIcon },
                { value: 'images' as InputType, label: 'Images', icon: ImageIcon },
              ].map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setInputType(value)}
                  className={`flex flex-col items-center justify-center p-3 border-2 rounded-lg transition-colors ${
                    inputType === value
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-gray-300 text-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5 mb-1" />
                  <span className="text-xs font-medium">{label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Input Fields Based on Type */}
          <div className="space-y-4">
            {inputType === 'text' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Menu Text
                </label>
                <textarea
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
                  placeholder="Paste or type your menu here..."
                  required
                />
              </div>
            )}

            {inputType === 'json' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  JSON Data
                </label>
                <textarea
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
                  placeholder='{"name": "Menu Name", "categories": [...]}'
                  required
                />
              </div>
            )}

            {inputType === 'pdf' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  PDF File
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  <input
                    type="file"
                    accept=".pdf,application/pdf"
                    onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="pdf-upload"
                    required
                  />
                  <label
                    htmlFor="pdf-upload"
                    className="cursor-pointer text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {pdfFile ? pdfFile.name : 'Click to upload PDF'}
                  </label>
                  {pdfFile && (
                    <p className="text-xs text-gray-500 mt-1">
                      {(pdfFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  )}
                </div>
              </div>
            )}

            {inputType === 'image' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Image File
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <ImageIcon className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/jpg,image/webp"
                    onChange={(e) => setImageFile(e.target.files?.[0] || null)}
                    className="hidden"
                    id="image-upload"
                    required
                  />
                  <label
                    htmlFor="image-upload"
                    className="cursor-pointer text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {imageFile ? imageFile.name : 'Click to upload image'}
                  </label>
                  {imageFile && (
                    <p className="text-xs text-gray-500 mt-1">
                      {(imageFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  )}
                </div>
              </div>
            )}

            {inputType === 'images' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Image Files (Multiple)
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <ImageIcon className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/jpg,image/webp"
                    onChange={(e) => {
                      const files = Array.from(e.target.files || [])
                      setImageFiles(files)
                    }}
                    className="hidden"
                    id="images-upload"
                    multiple
                    required
                  />
                  <label
                    htmlFor="images-upload"
                    className="cursor-pointer text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Click to upload images
                  </label>
                  {imageFiles.length > 0 && (
                    <div className="mt-3 text-sm text-gray-600">
                      <p>{imageFiles.length} file(s) selected:</p>
                      <ul className="list-disc list-inside mt-1 text-xs">
                        {imageFiles.map((file, idx) => (
                          <li key={idx}>{file.name}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          {/* Submit Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => setCurrentStep('list')}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              Back
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Processing...' : 'Create Menu'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
