import { useState } from 'react';
import {
  XMarkIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/outline';
import { useSettingsStore } from '../stores/settingsStore';
import toast from 'react-hot-toast';

interface CustomTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTemplate: (content: string) => void;
}

const DEFAULT_TEMPLATES = [
  { name: '📊 Summary Request', prompt: 'Please provide a comprehensive summary of this document, including key points, main arguments, and conclusions.' },
  { name: '🔍 Detailed Analysis', prompt: 'Analyze this document in detail. What are the main themes, supporting evidence, and potential implications?' },
  { name: '❓ Q&A Format', prompt: 'Please answer the following questions about this document:\n1. What is the main purpose?\n2. Who is the target audience?\n3. What are the key takeaways?' },
  { name: '📝 Extract Facts', prompt: 'Extract all important facts, statistics, dates, and figures mentioned in this document.' },
  { name: '⚖️ Compare & Contrast', prompt: 'Compare and contrast the different viewpoints or sections presented in this document.' },
  { name: '🎯 Action Items', prompt: 'What are the key action items, recommendations, or next steps suggested in this document?' },
];

const CustomTemplateModal: React.FC<CustomTemplateModalProps> = ({
  isOpen,
  onClose,
  onSelectTemplate,
}) => {
  const { customTemplates, addTemplate, removeTemplate, updateTemplate } = useSettingsStore();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newName, setNewName] = useState('');
  const [newContent, setNewContent] = useState('');

  if (!isOpen) return null;

  const handleCreate = () => {
    if (!newName.trim() || !newContent.trim()) {
      toast.error('Please fill in both name and content');
      return;
    }
    addTemplate(newName.trim(), newContent.trim());
    setNewName('');
    setNewContent('');
    setIsCreating(false);
    toast.success('Template created! 📝');
  };

  const handleUpdate = (id: string) => {
    if (!newName.trim() || !newContent.trim()) {
      toast.error('Please fill in both name and content');
      return;
    }
    updateTemplate(id, { name: newName.trim(), prompt: newContent.trim() });
    setNewName('');
    setNewContent('');
    setEditingId(null);
    toast.success('Template updated!');
  };

  const handleDelete = (id: string) => {
    removeTemplate(id);
    toast.success('Template deleted');
  };

  const handleSelectTemplate = (prompt: string) => {
    onSelectTemplate(prompt);
    onClose();
  };

  const startEdit = (id: string) => {
    const template = customTemplates.find(t => t.id === id);
    if (template) {
      setEditingId(template.id);
      setNewName(template.name);
      setNewContent(template.prompt);
      setIsCreating(false);
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setIsCreating(false);
    setNewName('');
    setNewContent('');
  };

  const allTemplates = [
    ...DEFAULT_TEMPLATES.map((t, i) => ({ ...t, id: `default-${i}`, isDefault: true })),
    ...customTemplates.map((t) => ({ ...t, isDefault: false })),
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <DocumentTextIcon className="h-5 w-5" />
            📋 Template Library
          </h2>
          <div className="flex items-center gap-2">
            {!isCreating && !editingId && (
              <button
                onClick={() => {
                  setIsCreating(true);
                  setEditingId(null);
                }}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                <PlusIcon className="h-4 w-4" />
                New
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <XMarkIcon className="h-5 w-5 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </div>

        {/* Create/Edit Form */}
        {(isCreating || editingId) && (
          <div className="p-4 bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Template name..."
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                          bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                          focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <textarea
                placeholder="Template content..."
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                          bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                          focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              />
              <div className="flex justify-end gap-2">
                <button
                  onClick={cancelEdit}
                  className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => editingId ? handleUpdate(editingId) : handleCreate()}
                  className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  {editingId ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Templates List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {allTemplates.map((template) => (
            <div
              key={template.id}
              className="group p-4 rounded-lg border border-gray-200 dark:border-gray-700 
                        hover:border-blue-300 dark:hover:border-blue-600 
                        hover:bg-blue-50 dark:hover:bg-blue-900/20 
                        transition-all cursor-pointer"
              onClick={() => handleSelectTemplate(template.prompt)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 dark:text-white">
                    {template.name}
                    {template.isDefault && (
                      <span className="ml-2 text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded">
                        Built-in
                      </span>
                    )}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                    {template.prompt}
                  </p>
                </div>
                {!template.isDefault && (
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startEdit(template.id);
                      }}
                      className="p-1.5 text-gray-500 hover:text-blue-500 hover:bg-white dark:hover:bg-gray-800 rounded"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(template.id);
                      }}
                      className="p-1.5 text-gray-500 hover:text-red-500 hover:bg-white dark:hover:bg-gray-800 rounded"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700">
          <p className="text-xs text-center text-gray-500 dark:text-gray-400">
            Click any template to use it • Create custom templates for repeated tasks
          </p>
        </div>
      </div>
    </div>
  );
};

export default CustomTemplateModal;
