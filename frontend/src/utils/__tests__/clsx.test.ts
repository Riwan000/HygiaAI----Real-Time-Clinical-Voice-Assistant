import { describe, it, expect } from 'vitest';
import { clsx } from '../clsx';

describe('clsx', () => {
  it('combines class names', () => {
    expect(clsx('foo', 'bar')).toBe('foo bar');
  });

  it('handles conditional classes', () => {
    expect(clsx('foo', true && 'bar', false && 'baz')).toBe('foo bar');
  });

  it('handles objects', () => {
    expect(clsx({ foo: true, bar: false, baz: true })).toBe('foo baz');
  });

  it('handles arrays', () => {
    expect(clsx(['foo', 'bar'])).toBe('foo bar');
  });

  it('filters out falsy values', () => {
    expect(clsx('foo', null, undefined, false, '', 'bar')).toBe('foo bar');
  });

  it('handles mixed inputs', () => {
    expect(clsx('foo', { bar: true, baz: false }, 'qux')).toBe('foo bar qux');
  });
});

