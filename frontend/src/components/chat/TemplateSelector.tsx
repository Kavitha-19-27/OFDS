/**
 * Template selector component.
 * Pre-built prompts for common query patterns.
 */
import React, { useState } from 'react';
import { 
  DocumentDuplicateIcon, 
  ChevronDownIcon,
  MagnifyingGlassIcon,
  DocumentMagnifyingGlassIcon,
  ClipboardDocumentListIcon,
  ArrowsRightLeftIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';

interface Template {
  id: string;
  name: string;
  prompt_template: string;
  description?: string;
  category: string;
  is_system: boolean;
}

interface TemplateCategory {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const CATEGORIES: TemplateCategory[] = [
  { id: 'summary', label: 'Summary', icon: ClipboardDocumentListIcon },
  { id: 'analysis', label: 'Analysis', icon: MagnifyingGlassIcon },
  { id: 'extraction', label: 'Extraction', icon: DocumentMagnifyingGlassIcon },
  { id: 'comparison', label: 'Comparison', icon: ArrowsRightLeftIcon },
  { id: 'explanation', label: 'Explanation', icon: AcademicCapIcon },
  { id: 'custom', label: 'Custom', icon: DocumentDuplicateIcon }
];

interface TemplateSelectorProps {
  templates: Template[];
  onSelect: (prompt: string) => void;
}

const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  onSelect
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredTemplates = templates.filter(t => {
    const matchesCategory = !selectedCategory || t.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleSelect = (template: Template) => {
    onSelect(template.prompt_template);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 
                   hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
        title="Use a template"
      >
        <DocumentDuplicateIcon className="h-5 w-5" />
        <span>Templates</span>
        <ChevronDownIcon className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-0 mb-2 w-80 bg-white rounded-lg shadow-lg border z-50">
          {/* Search */}
          <div className="p-3 border-b">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border rounded-md 
                         focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Categories */}
          <div className="p-2 border-b flex flex-wrap gap-1">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-2 py-1 text-xs rounded ${
                !selectedCategory 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              All
            </button>
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`flex items-center gap-1 px-2 py-1 text-xs rounded ${
                    selectedCategory === cat.id
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="h-3 w-3" />
                  {cat.label}
                </button>
              );
            })}
          </div>

          {/* Templates list */}
          <div className="max-h-64 overflow-y-auto p-2">
            {filteredTemplates.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No templates found
              </p>
            ) : (
              <div className="space-y-1">
                {filteredTemplates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleSelect(template)}
                    className="w-full text-left p-2 rounded hover:bg-gray-50 
                             transition-colors group"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-700 group-hover:text-primary-600">
                          {template.name}
                        </p>
                        {template.description && (
                          <p className="text-xs text-gray-500 mt-0.5">
                            {template.description}
                          </p>
                        )}
                      </div>
                      {template.is_system && (
                        <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded">
                          System
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateSelector;
