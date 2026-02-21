import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GuestUpload, GuestChat, TrialModal } from '../components/trial';
import ThemeToggle from '../components/ThemeToggle';
import {
  SparklesIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  RocketLaunchIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [showTrialModal, setShowTrialModal] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [showChat, setShowChat] = useState(false);

  const features = [
    {
      icon: DocumentTextIcon,
      title: 'Smart Document Analysis',
      description: 'Upload PDF, DOCX, or TXT files and get instant AI-powered insights',
      color: 'from-blue-500 to-indigo-600',
    },
    {
      icon: ChatBubbleLeftRightIcon,
      title: 'Chat with Your Docs',
      description: 'Ask questions in natural language and get accurate answers from your documents',
      color: 'from-purple-500 to-pink-600',
    },
    {
      icon: CpuChipIcon,
      title: '6 AI Analysis Modes',
      description: 'Summary, Key Points, Risk Analysis, Action Items, Q&A, and Compare modes',
      color: 'from-amber-500 to-orange-600',
    },
    {
      icon: ShieldCheckIcon,
      title: 'Secure & Private',
      description: 'Enterprise-grade security with encrypted storage and access controls',
      color: 'from-green-500 to-emerald-600',
    },
  ];

  const handleUploadComplete = (file: File, response: any) => {
    setUploadedFileName(file.name);
    setSessionId(response.session_id || 'demo-session');
    setShowChat(true);  // Show chat instead of modal
  };

  const handleBackToUpload = () => {
    setShowChat(false);
  };

  // Quick demo access without upload
  const handleTryDemo = () => {
    setUploadedFileName('Demo Document');
    setSessionId('demo-session-' + Date.now());
    setShowChat(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Navigation */}
      <nav className="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="p-1.5 sm:p-2 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg sm:rounded-xl">
                <SparklesIcon className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
              </div>
              <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                DocuMind AI
              </span>
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              <ThemeToggle />
              <button
                onClick={() => navigate('/login')}
                className="text-sm sm:text-base text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium transition-colors"
              >
                Login
              </button>
              <button
                onClick={() => navigate('/register')}
                className="px-3 sm:px-4 py-1.5 sm:py-2 text-sm sm:text-base bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-lg font-medium hover:opacity-90 transition-opacity shadow-lg shadow-primary-500/25"
              >
                Sign Up
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 sm:pt-16 pb-8 sm:pb-12">
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-gradient-to-r from-primary-100 to-purple-100 dark:from-primary-900/30 dark:to-purple-900/30 rounded-full mb-4 sm:mb-6">
            <RocketLaunchIcon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary-600 dark:text-primary-400" />
            <span className="text-xs sm:text-sm font-medium text-primary-700 dark:text-primary-300">
              Try Free - No Signup Required!
            </span>
          </div>
          
          <h1 className="text-2xl sm:text-4xl md:text-6xl font-bold mb-4 sm:mb-6 px-2">
            <span className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 dark:from-white dark:via-gray-100 dark:to-white bg-clip-text text-transparent">
              Transform Documents into
            </span>
            <br />
            <span className="bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Intelligent Insights
            </span>
          </h1>
          
          <p className="text-base sm:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto mb-6 sm:mb-8 px-4">
            Upload any document and chat with AI to get instant summaries, key points, 
            risk analysis, and more. 🤖📚
          </p>
        </div>

        {/* Upload or Chat Section */}
        <div className="max-w-2xl mx-auto mb-16">
          {showChat ? (
            <GuestChat
              documentName={uploadedFileName}
              sessionId={sessionId}
              onBack={handleBackToUpload}
            />
          ) : (
            <>
              <GuestUpload onUploadComplete={handleUploadComplete} />
              {/* Quick Demo Button */}
              <div className="mt-6 text-center">
                <p className="text-gray-500 dark:text-gray-400 text-sm mb-3">
                  Or try without uploading:
                </p>
                <button
                  onClick={handleTryDemo}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-xl font-medium hover:opacity-90 transition-opacity shadow-lg shadow-emerald-500/25"
                >
                  <SparklesIcon className="h-5 w-5" />
                  Try Demo Chat (10 Free Prompts)
                </button>
              </div>
            </>
          )}
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-10 sm:mb-16 px-2 sm:px-0">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="group bg-white dark:bg-gray-800 rounded-xl sm:rounded-2xl p-4 sm:p-6 border border-gray-100 dark:border-gray-700 hover:shadow-xl hover:shadow-gray-200/50 dark:hover:shadow-gray-900/50 transition-all duration-300 hover:-translate-y-1"
            >
              <div className={`inline-flex p-2 sm:p-3 rounded-lg sm:rounded-xl bg-gradient-to-br ${feature.color} mb-2 sm:mb-4 group-hover:scale-110 transition-transform`}>
                <feature.icon className="h-4 w-4 sm:h-6 sm:w-6 text-white" />
              </div>
              <h3 className="font-semibold sm:font-bold text-sm sm:text-base text-gray-900 dark:text-white mb-1 sm:mb-2">{feature.title}</h3>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 line-clamp-2 sm:line-clamp-none">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-12 text-center text-white mx-2 sm:mx-0">
          <h2 className="text-xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4">
            Ready for Unlimited Access? 🚀
          </h2>
          <p className="text-sm sm:text-lg text-white/90 mb-6 sm:mb-8 max-w-xl mx-auto">
            Create a free account to upload unlimited documents, save chat history, 
            and access all AI analysis modes.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <button
              onClick={() => navigate('/register')}
              className="inline-flex items-center justify-center gap-2 px-6 sm:px-8 py-3 sm:py-4 bg-white text-primary-600 rounded-xl font-bold hover:bg-gray-100 transition-colors shadow-xl text-sm sm:text-base"
            >
              Create Free Account
              <ArrowRightIcon className="h-4 w-4 sm:h-5 sm:w-5" />
            </button>
            <button
              onClick={() => navigate('/login')}
              className="inline-flex items-center justify-center gap-2 px-6 sm:px-8 py-3 sm:py-4 bg-white/20 text-white rounded-xl font-medium hover:bg-white/30 transition-colors border border-white/30 text-sm sm:text-base"
            >
              Login to Dashboard
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-800 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-500 dark:text-gray-400">
          <p>© 2024 DocuMind AI - Enterprise Document Intelligence Platform</p>
        </div>
      </footer>

      {/* Trial Modal */}
      <TrialModal
        isOpen={showTrialModal}
        onClose={() => setShowTrialModal(false)}
        documentName={uploadedFileName}
      />
    </div>
  );
};

export default LandingPage;
