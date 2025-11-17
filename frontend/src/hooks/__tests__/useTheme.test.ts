import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from '../useTheme';

describe('useTheme', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    
    // Reset document classes
    document.documentElement.classList.remove('light', 'dark');
  });

  it('defaults to light theme', () => {
    const { result } = renderHook(() => useTheme());
    
    expect(result.current.theme).toBe('light');
  });

  it('reads theme from localStorage', () => {
    localStorage.setItem('theme', 'dark');
    
    const { result } = renderHook(() => useTheme());
    
    expect(result.current.theme).toBe('dark');
  });

  it('toggles theme correctly', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('dark');
    expect(localStorage.getItem('theme')).toBe('dark');
    
    act(() => {
      result.current.toggleTheme();
    });
    
    expect(result.current.theme).toBe('light');
    expect(localStorage.getItem('theme')).toBe('light');
  });

  it('sets theme class on document element', () => {
    const { result } = renderHook(() => useTheme());
    
    act(() => {
      result.current.setTheme('dark');
    });
    
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.classList.contains('light')).toBe(false);
  });
});

