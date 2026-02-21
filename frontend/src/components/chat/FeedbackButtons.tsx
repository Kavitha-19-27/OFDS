/**
 * Feedback buttons component for rating responses.
 */
import React, { useState } from 'react';
import { 
  HandThumbUpIcon, 
  HandThumbDownIcon 
} from '@heroicons/react/24/outline';
import {
  HandThumbUpIcon as ThumbUpSolid,
  HandThumbDownIcon as ThumbDownSolid
} from '@heroicons/react/24/solid';

interface FeedbackButtonsProps {
  messageId: number;
  sessionId: number;
  onFeedback: (rating: number, issueType?: string, feedbackText?: string) => Promise<void>;
}

const ISSUE_TYPES = [
  { id: 'incorrect', label: 'Incorrect information' },
  { id: 'incomplete', label: 'Incomplete answer' },
  { id: 'irrelevant', label: 'Not relevant to question' },
  { id: 'outdated', label: 'Outdated information' },
  { id: 'unclear', label: 'Unclear or confusing' },
  { id: 'other', label: 'Other issue' }
];

const FeedbackButtons: React.FC<FeedbackButtonsProps> = ({
  messageId,
  sessionId,
  onFeedback
}) => {
  const [rating, setRating] = useState<number | null>(null);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [issueType, setIssueType] = useState<string>('');
  const [feedbackText, setFeedbackText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handlePositive = async () => {
    if (rating === 1) return; // Already rated
    setRating(1);
    setShowFeedbackForm(false);
    await onFeedback(1);
  };

  const handleNegative = () => {
    if (rating === -1) return;
    setRating(-1);
    setShowFeedbackForm(true);
  };

  const handleSubmitFeedback = async () => {
    setIsSubmitting(true);
    await onFeedback(-1, issueType, feedbackText);
    setIsSubmitting(false);
    setShowFeedbackForm(false);
  };

  return (
    <div className="mt-2">
      <div className="flex items-center gap-3">
        <span className="text-xs text-gray-500">Was this helpful?</span>
        <button
          onClick={handlePositive}
          disabled={rating !== null}
          className={`p-1 rounded hover:bg-green-50 transition-colors ${
            rating === 1 ? 'text-green-600' : 'text-gray-400 hover:text-green-600'
          }`}
          title="Helpful"
        >
          {rating === 1 ? (
            <ThumbUpSolid className="h-5 w-5" />
          ) : (
            <HandThumbUpIcon className="h-5 w-5" />
          )}
        </button>
        <button
          onClick={handleNegative}
          disabled={rating !== null}
          className={`p-1 rounded hover:bg-red-50 transition-colors ${
            rating === -1 ? 'text-red-600' : 'text-gray-400 hover:text-red-600'
          }`}
          title="Not helpful"
        >
          {rating === -1 ? (
            <ThumbDownSolid className="h-5 w-5" />
          ) : (
            <HandThumbDownIcon className="h-5 w-5" />
          )}
        </button>
        {rating === 1 && (
          <span className="text-xs text-green-600">Thanks for your feedback!</span>
        )}
      </div>

      {/* Negative feedback form */}
      {showFeedbackForm && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg border">
          <p className="text-sm font-medium text-gray-700 mb-2">
            What was the issue?
          </p>
          <div className="space-y-2 mb-3">
            {ISSUE_TYPES.map((issue) => (
              <label key={issue.id} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="issueType"
                  value={issue.id}
                  checked={issueType === issue.id}
                  onChange={(e) => setIssueType(e.target.value)}
                  className="text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-600">{issue.label}</span>
              </label>
            ))}
          </div>
          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Additional details (optional)"
            className="w-full p-2 text-sm border rounded-md focus:ring-primary-500 focus:border-primary-500"
            rows={2}
          />
          <div className="mt-2 flex justify-end gap-2">
            <button
              onClick={() => setShowFeedbackForm(false)}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmitFeedback}
              disabled={isSubmitting || !issueType}
              className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeedbackButtons;
