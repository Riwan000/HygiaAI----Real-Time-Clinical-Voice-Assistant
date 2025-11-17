/**
 * Search Box Component
 * 
 * Search input with autocomplete suggestions for symptoms/transcripts.
 */

import { useState, useRef, useEffect } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  placeholder?: string;
  suggestions?: string[];
  isLoading?: boolean;
}

export function SearchBox({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search symptoms, transcripts, or case descriptions...',
  suggestions = [],
  isLoading = false,
}: SearchBoxProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const filteredSuggestions = suggestions.filter((suggestion) =>
    suggestion.toLowerCase().includes(value.toLowerCase())
  );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev < filteredSuggestions.length - 1 ? prev + 1 : prev
      );
      setShowSuggestions(true);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && filteredSuggestions[selectedIndex]) {
        handleSelectSuggestion(filteredSuggestions[selectedIndex]);
      } else {
        onSubmit(value);
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }
  };

  const handleSelectSuggestion = (suggestion: string) => {
    onChange(suggestion);
    setShowSuggestions(false);
    setSelectedIndex(-1);
    onSubmit(suggestion);
  };

  const handleClear = () => {
    onChange('');
    inputRef.current?.focus();
  };

  return (
    <div className="relative w-full">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <MagnifyingGlassIcon
            className="h-5 w-5 text-[#64748B] dark:text-[#94A3B8]"
            aria-hidden="true"
          />
        </div>
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setShowSuggestions(true);
            setSelectedIndex(-1);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => setShowSuggestions(true)}
          placeholder={placeholder}
          className="block w-full pl-12 pr-10 py-3.5 border border-slate/30 dark:border-[#475569]/30 rounded-xl bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white placeholder-[#64748B] dark:placeholder-[#94A3B8] focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
        />
        {value && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-0 pr-3 flex items-center focus:outline-none focus:ring-2 focus:ring-primary/30 rounded"
            aria-label="Clear search"
          >
            <XMarkIcon 
              className="h-5 w-5 text-[#64748B] dark:text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-white transition-colors"
              aria-hidden="true"
            />
          </button>
        )}
      </div>

      {/* Autocomplete Suggestions */}
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div
          id="search-suggestions"
          ref={suggestionsRef}
          role="listbox"
          aria-label="Search suggestions"
          className="absolute z-10 mt-2 w-full bg-white dark:bg-[#1E293B] shadow-lg max-h-60 rounded-xl py-2 text-base ring-1 ring-slate/10 dark:ring-[#475569]/30 overflow-auto focus:outline-none border border-slate/20 dark:border-[#475569]/30"
        >
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={index}
              id={`suggestion-${index}`}
              type="button"
              onClick={() => handleSelectSuggestion(suggestion)}
              role="option"
              aria-selected={index === selectedIndex}
              className={`
                w-full text-left px-4 py-2.5 text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-1
                ${
                  index === selectedIndex
                    ? 'bg-[#C4B5FD]/20 dark:bg-[#8B5CF6]/20 text-[#8B5CF6] dark:text-[#C4B5FD]'
                    : 'text-[#0F172A] dark:text-white hover:bg-slate/5 dark:hover:bg-[#475569]/30'
                }
              `}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="absolute right-3 top-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
        </div>
      )}
    </div>
  );
}

