import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';

import RagApp from './RagApp';

describe('RagApp', () => {
  beforeEach(() => {
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      configurable: true,
      value: vi.fn(),
    });

    const storage = new Map<string, string>();

    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => {
          storage.set(key, value);
        },
        removeItem: (key: string) => {
          storage.delete(key);
        },
        clear: () => {
          storage.clear();
        },
      },
    });

    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);

        if (url.endsWith('/api/documents/summary')) {
          return new Response(JSON.stringify({ document_count: 0 }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }

        return new Response(JSON.stringify({ detail: 'Unexpected request' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('renders and requires a document before answering questions', async () => {
    render(<RagApp />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    const textbox = screen.getByRole('textbox');
    fireEvent.change(textbox, {
      target: { value: 'What does this document say?' },
    });

    fireEvent.keyDown(textbox, {
      key: 'Enter',
      code: 'Enter',
      charCode: 13,
    });

    expect(
      await screen.findByText(
        'Please upload a document first, then ask your question. This assistant answers only from uploaded documents.',
      ),
    ).toBeInTheDocument();
  });
});
