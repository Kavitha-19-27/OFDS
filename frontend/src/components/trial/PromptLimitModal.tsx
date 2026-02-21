import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useNavigate } from 'react-router-dom';
import {
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  LockClosedIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline';
import { Button } from '../common';

interface PromptLimitModalProps {
  isOpen: boolean;
  onClose: () => void;
  promptsUsed: number;
  maxPrompts: number;
}

const PromptLimitModal: React.FC<PromptLimitModalProps> = ({ 
  isOpen, 
  onClose, 
  promptsUsed,
  maxPrompts 
}) => {
  const navigate = useNavigate();

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
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
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
                {/* Lock Icon */}
                <div className="text-center mb-6">
                  <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full mb-4 shadow-lg shadow-amber-500/30 animate-pulse">
                    <LockClosedIcon className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    🎯 Trial Limit Reached!
                  </h2>
                  <p className="text-gray-500 dark:text-gray-400">
                    You've used <span className="font-bold text-primary-600">{promptsUsed}/{maxPrompts}</span> free prompts
                  </p>
                </div>

                {/* Progress Bar */}
                <div className="mb-6">
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-amber-500 to-red-500 transition-all"
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>

                {/* Message */}
                <div className="bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 rounded-2xl p-4 mb-6 border border-primary-200 dark:border-primary-800">
                  <p className="text-primary-800 dark:text-primary-200 text-center font-medium">
                    ✨ Nee trial prompts ellam use pannittey!
                  </p>
                  <p className="text-primary-700 dark:text-primary-300 text-center text-sm mt-1">
                    Create account for unlimited AI chat access!
                  </p>
                </div>

                {/* What you'll get */}
                <div className="space-y-3 mb-6">
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                    Unlock with free account:
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <ChatBubbleLeftRightIcon className="h-5 w-5 text-purple-500" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">Unlimited chats</span>
                    </div>
                    <div className="flex items-center gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                      <SparklesIcon className="h-5 w-5 text-amber-500" />
                      <span className="text-sm text-gray-700 dark:text-gray-300">All AI modes</span>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="space-y-3">
                  <Button
                    onClick={() => navigate('/register')}
                    className="w-full bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 shadow-lg shadow-primary-500/25 text-lg py-3"
                  >
                    <RocketLaunchIcon className="h-5 w-5 mr-2" />
                    Create Free Account
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/login')}
                    className="w-full text-gray-600 dark:text-gray-400"
                  >
                    Already have account? Login
                  </Button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default PromptLimitModal;
