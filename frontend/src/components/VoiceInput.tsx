import { useState, useCallback } from 'react';
import { MicrophoneIcon, StopIcon } from '@heroicons/react/24/solid';
import { useChatStore } from '../stores/chatStore';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, disabled = false }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { languageMode } = useChatStore();

  // Check browser support
  const SpeechRecognition = 
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  
  const isSupported = !!SpeechRecognition;

  const startListening = useCallback(() => {
    if (!isSupported) {
      setError('Speech recognition not supported in this browser');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = languageMode === 'tanglish' ? 'ta-IN' : 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
    };

    recognition.onresult = (event: any) => {
      const current = event.resultIndex;
      const transcriptText = event.results[current][0].transcript;
      setTranscript(transcriptText);
      
      if (event.results[current].isFinal) {
        onTranscript(transcriptText);
        setTranscript('');
        setIsListening(false);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setError(`Error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
    
    // Store recognition instance for stopping
    (window as any).__recognition = recognition;
  }, [isSupported, languageMode, onTranscript]);

  const stopListening = useCallback(() => {
    const recognition = (window as any).__recognition;
    if (recognition) {
      recognition.stop();
    }
    setIsListening(false);
  }, []);

  if (!isSupported) {
    return null;
  }

  return (
    <div className="relative">
      <button
        onClick={isListening ? stopListening : startListening}
        disabled={disabled}
        className={`
          p-2 rounded-xl transition-all duration-300
          ${isListening
            ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/30'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-primary-100 dark:hover:bg-primary-900 hover:text-primary-600 dark:hover:text-primary-400'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
        title={isListening ? 'Stop recording' : 'Voice input'}
      >
        {isListening ? (
          <StopIcon className="h-5 w-5" />
        ) : (
          <MicrophoneIcon className="h-5 w-5" />
        )}
      </button>
      
      {/* Listening indicator */}
      {isListening && (
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-gray-900 dark:bg-gray-700 text-white text-xs px-3 py-1.5 rounded-lg whitespace-nowrap">
          🎤 Listening... {transcript && <span className="text-primary-300">"{transcript}"</span>}
        </div>
      )}
      
      {/* Error display */}
      {error && (
        <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-red-500 text-white text-xs px-3 py-1.5 rounded-lg whitespace-nowrap">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};

export default VoiceInput;
