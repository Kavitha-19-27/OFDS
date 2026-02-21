import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import {
  SparklesIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  ShieldCheckIcon,
  RocketLaunchIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common';

interface TrialModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentName?: string;
}

const TrialModal: React.FC<TrialModalProps> = ({ isOpen, onClose, documentName }) => {
  const navigate = useNavigate();

  const features = [
    { icon: DocumentTextIcon, text: 'Unlimited document uploads', color: 'text-blue-500' },
    { icon: ChatBubbleLeftRightIcon, text: 'AI-powered chat with your documents', color: 'text-purple-500' },
    { icon: ShieldCheckIcon, text: 'Secure & private storage', color: 'text-green-500' },
    { icon: SparklesIcon, text: '6 AI analysis modes', color: 'text-amber-500' },
  ];

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-3xl bg-white dark:bg-gray-800 p-8 shadow-2xl transition-all">
                {/* Close Button */}
                <button
                  onClick={onClose}
                  className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>

                {/* Success Icon */}
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full mb-4 shadow-lg shadow-green-500/30">
                    <RocketLaunchIcon className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    🎉 Document Uploaded!
                  </h2>
                  {documentName && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-full inline-block">
                      {documentName}
                    </p>
                  )}
                </div>

                {/* Message */}
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-2xl p-4 mb-6 border border-amber-200 dark:border-amber-800">
                  <p className="text-amber-800 dark:text-amber-200 text-center font-medium">
                    ✨ Nee oru free trial document upload pannittey!
                  </p>
                  <p className="text-amber-700 dark:text-amber-300 text-center text-sm mt-1">
                    Create account pannaa unlimited access kedaikkum!
                  </p>
                </div>

                {/* Features */}
                <div className="space-y-3 mb-6">
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                    What you'll get:
                  </p>
                  {features.map((feature, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-700 ${feature.color}`}>
                        <feature.icon className="h-4 w-4" />
                      </div>
                      <span className="text-gray-700 dark:text-gray-300 text-sm">{feature.text}</span>
                    </div>
                  ))}
                </div>

                {/* Action Buttons */}
                <div className="space-y-3">
                  <Button
                    onClick={() => navigate('/register')}
                    className="w-full bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 shadow-lg shadow-primary-500/25 text-lg py-3"
                  >
                    🚀 Create Free Account
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/login')}
                    className="w-full text-gray-600 dark:text-gray-400"
                  >
                    Already have account? Login
                  </Button>
                </div>

                {/* Skip Option */}
                <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-4">
                  Or{' '}
                  <button
                    onClick={onClose}
                    className="underline hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    continue as guest
                  </button>{' '}
                  (limited features)
                </p>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default TrialModal;
