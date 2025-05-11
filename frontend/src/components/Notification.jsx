import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

export default function Notification({ type = 'success', message, onClose }) {
  const bgColor = type === 'success' ? 'bg-green-50' : 'bg-red-50';
  const textColor = type === 'success' ? 'text-green-800' : 'text-red-800';
  const borderColor = type === 'success' ? 'border-green-200' : 'border-red-200';

  return (
    <div className={`fixed top-4 right-4 z-50 max-w-sm w-full ${bgColor} rounded-lg shadow-lg border ${borderColor}`}>
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-1">
            <p className={`text-sm font-medium ${textColor}`}>{message}</p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="ml-4 inline-flex text-gray-400 hover:text-gray-500 focus:outline-none"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
} 