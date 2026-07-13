import { render, screen, fireEvent } from '@testing-library/react';
import { AboutTab } from './AboutTab';
import { vi } from 'vitest';

describe('AboutTab Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
  });

  it('should render the main headings correctly', () => {
    render(<AboutTab />);

    expect(screen.getByText('About Padho Abhi')).toBeInTheDocument();
    expect(screen.getByText('Revolutionizing Education with AI')).toBeInTheDocument();
    expect(screen.getByText('Why Padho Abhi?')).toBeInTheDocument();
    expect(screen.getByText('The Creator')).toBeInTheDocument();
    expect(screen.getByText('Support Us')).toBeInTheDocument();
  });

  it('should handle the copy UPI ID button correctly', () => {
    // Mock navigator.clipboard.writeText
    const mockWriteText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: mockWriteText,
      },
    });

    // Mock window.alert
    const mockAlert = vi.fn();
    window.alert = mockAlert;

    render(<AboutTab />);

    // Find and click the copy button
    const copyButton = screen.getByRole('button', { name: /COPY/i });
    fireEvent.click(copyButton);

    // Verify copy functionality
    expect(mockWriteText).toHaveBeenCalledWith('padhoabhidonation@axl');
    expect(mockAlert).toHaveBeenCalledWith('UPI ID copied!');
  });
});
