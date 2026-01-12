import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import Button from './Button';

describe('Button Component', () => {
  describe('Rendering', () => {
    it('renders children text correctly', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
    });

    it('renders with default props', () => {
      render(<Button>Default Button</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('type', 'button');
      expect(button).not.toBeDisabled();
    });

    it('renders children as React elements', () => {
      render(
        <Button>
          <span data-testid="icon">🚀</span>
          <span>Launch</span>
        </Button>
      );
      
      expect(screen.getByTestId('icon')).toBeInTheDocument();
      expect(screen.getByText('Launch')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      render(<Button className="custom-class">Custom</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveClass('custom-class');
    });

    it('passes additional props to button element', () => {
      render(<Button data-testid="test-button" id="my-button">Props Test</Button>);
      const button = screen.getByTestId('test-button');
      
      expect(button).toHaveAttribute('id', 'my-button');
    });
  });

  describe('Variants', () => {
    it('applies primary variant styles by default', () => {
      render(<Button>Primary</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('bg-blue-600');
      expect(button.className).toContain('text-white');
    });

    it('applies primary variant styles when specified', () => {
      render(<Button variant="primary">Primary</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('bg-blue-600');
    });

    it('applies secondary variant styles', () => {
      render(<Button variant="secondary">Secondary</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('bg-gray-100');
      expect(button.className).toContain('text-gray-700');
      expect(button.className).toContain('border');
    });

    it('applies danger variant styles', () => {
      render(<Button variant="danger">Danger</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('bg-red-600');
      expect(button.className).toContain('text-white');
    });

    it('applies ghost variant styles', () => {
      render(<Button variant="ghost">Ghost</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('bg-transparent');
      expect(button.className).toContain('text-gray-600');
    });

    it('applies success variant styles', () => {
      render(<Button variant="success">Success</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('bg-green-600');
      expect(button.className).toContain('text-white');
    });

    it('falls back to primary styles for invalid variant', () => {
      render(<Button variant="invalid-variant">Invalid</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('bg-blue-600');
    });
  });

  describe('Sizes', () => {
    it('applies medium size by default', () => {
      render(<Button>Medium</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('px-4');
      expect(button.className).toContain('py-2');
    });

    it('applies small size styles', () => {
      render(<Button size="sm">Small</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('px-3');
      expect(button.className).toContain('py-1.5');
      expect(button.className).toContain('text-sm');
    });

    it('applies medium size styles', () => {
      render(<Button size="md">Medium</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('px-4');
      expect(button.className).toContain('py-2');
    });

    it('applies large size styles', () => {
      render(<Button size="lg">Large</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('px-6');
      expect(button.className).toContain('py-3');
      expect(button.className).toContain('text-base');
    });

    it('applies extra large size styles', () => {
      render(<Button size="xl">Extra Large</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('px-8');
      expect(button.className).toContain('py-4');
      expect(button.className).toContain('text-lg');
    });

    it('falls back to medium size for invalid size', () => {
      render(<Button size="invalid-size">Invalid</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('px-4');
      expect(button.className).toContain('py-2');
    });
  });

  describe('Button Types', () => {
    it('has type="button" by default', () => {
      render(<Button>Default Type</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('type', 'button');
    });

    it('accepts type="submit"', () => {
      render(<Button type="submit">Submit</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('type', 'submit');
    });

    it('accepts type="reset"', () => {
      render(<Button type="reset">Reset</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('type', 'reset');
    });
  });

  describe('Full Width', () => {
    it('does not apply full width by default', () => {
      render(<Button>Normal Width</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).not.toContain('w-full');
    });

    it('applies full width when fullWidth is true', () => {
      render(<Button fullWidth>Full Width</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('w-full');
    });

    it('does not apply full width when fullWidth is false', () => {
      render(<Button fullWidth={false}>Not Full Width</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).not.toContain('w-full');
    });
  });

  describe('Disabled State', () => {
    it('is not disabled by default', () => {
      render(<Button>Enabled</Button>);
      const button = screen.getByRole('button');
      
      expect(button).not.toBeDisabled();
    });

    it('is disabled when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toBeDisabled();
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = jest.fn();
      render(<Button disabled onClick={handleClick}>Disabled</Button>);
      const button = screen.getByRole('button');
      
      fireEvent.click(button);
      
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('applies disabled styles', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('disabled:opacity-50');
      expect(button.className).toContain('disabled:cursor-not-allowed');
    });
  });

  describe('Loading State', () => {
    it('is not loading by default', () => {
      render(<Button>Not Loading</Button>);
      
      expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });

    it('shows loading spinner when loading is true', () => {
      render(<Button loading>Loading</Button>);
      
      const spinner = document.querySelector('svg.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('disables button when loading', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toBeDisabled();
    });

    it('does not call onClick when loading', async () => {
      const handleClick = jest.fn();
      render(<Button loading onClick={handleClick}>Loading</Button>);
      const button = screen.getByRole('button');
      
      fireEvent.click(button);
      
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('still renders children when loading', () => {
      render(<Button loading>Submit</Button>);
      
      expect(screen.getByText('Submit')).toBeInTheDocument();
    });

    it('spinner has aria-hidden attribute', () => {
      render(<Button loading>Loading</Button>);
      
      const spinner = document.querySelector('svg.animate-spin');
      expect(spinner).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Click Handler', () => {
    it('calls onClick when clicked', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      
      render(<Button onClick={handleClick}>Click Me</Button>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('passes event to onClick handler', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      
      render(<Button onClick={handleClick}>Click Me</Button>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      
      expect(handleClick).toHaveBeenCalledWith(expect.objectContaining({
        type: 'click',
        target: button,
      }));
    });

    it('does not throw when onClick is not provided', async () => {
      const user = userEvent.setup();
      
      render(<Button>No Handler</Button>);
      const button = screen.getByRole('button');
      
      await expect(user.click(button)).resolves.not.toThrow();
    });

    it('handles multiple clicks', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      
      render(<Button onClick={handleClick}>Multi Click</Button>);
      const button = screen.getByRole('button');
      
      await user.click(button);
      await user.click(button);
      await user.click(button);
      
      expect(handleClick).toHaveBeenCalledTimes(3);
    });
  });

  describe('Accessibility', () => {
    it('uses ariaLabel when provided', () => {
      render(<Button ariaLabel="Custom label">Button</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toHaveAttribute('aria-label', 'Custom label');
    });

    it('is focusable', async () => {
      const user = userEvent.setup();
      
      render(<Button>Focusable</Button>);
      const button = screen.getByRole('button');
      
      await user.tab();
      
      expect(button).toHaveFocus();
    });

    it('can be activated with keyboard Enter', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      
      render(<Button onClick={handleClick}>Keyboard</Button>);
      const button = screen.getByRole('button');
      
      button.focus();
      await user.keyboard('{Enter}');
      
      expect(handleClick).toHaveBeenCalled();
    });

    it('can be activated with keyboard Space', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();
      
      render(<Button onClick={handleClick}>Keyboard</Button>);
      const button = screen.getByRole('button');
      
      button.focus();
      await user.keyboard(' ');
      
      expect(handleClick).toHaveBeenCalled();
    });

    it('has focus ring styles', () => {
      render(<Button>Focus Ring</Button>);
      const button = screen.getByRole('button');
      
      expect(button.className).toContain('focus:ring-2');
      expect(button.className).toContain('focus:ring-offset-2');
    });

    it('is not focusable when disabled', () => {
      render(
        <>
          <Button>First</Button>
          <Button disabled>Disabled</Button>
          <Button>Last</Button>
        </>
      );
      
      const disabledButton = screen.getByRole('button', { name: 'Disabled' });
      expect(disabledButton).toBeDisabled();
    });
  });

  describe('Style Composition', () => {
    it('combines base, variant, size, and custom styles', () => {
      render(
        <Button 
          variant="danger" 
          size="lg" 
          fullWidth 
          className="my-custom-class"
        >
          Combined
        </Button>
      );
      const button = screen.getByRole('button');
      
      // Base styles
      expect(button.className).toContain('inline-flex');
      expect(button.className).toContain('items-center');
      expect(button.className).toContain('justify-center');
      expect(button.className).toContain('rounded-lg');
      
      // Variant styles
      expect(button.className).toContain('bg-red-600');
      
      // Size styles
      expect(button.className).toContain('px-6');
      expect(button.className).toContain('py-3');
      
      // Width styles
      expect(button.className).toContain('w-full');
      
      // Custom class
      expect(button.className).toContain('my-custom-class');
    });

    it('removes extra whitespace from combined styles', () => {
      render(<Button>Whitespace Test</Button>);
      const button = screen.getByRole('button');
      
      // Should not have multiple consecutive spaces
      expect(button.className).not.toMatch(/\s{2,}/);
    });
  });

  describe('Edge Cases', () => {
    it('handles empty children', () => {
      render(<Button>{''}</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toBeInTheDocument();
    });

    it('handles null children', () => {
      render(<Button>{null}</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toBeInTheDocument();
    });

    it('handles undefined onClick gracefully', () => {
      render(<Button onClick={undefined}>No Handler</Button>);
      const button = screen.getByRole('button');
      
      expect(() => fireEvent.click(button)).not.toThrow();
    });

    it('handles both disabled and loading simultaneously', () => {
      const handleClick = jest.fn();
      render(<Button disabled loading onClick={handleClick}>Both</Button>);
      const button = screen.getByRole('button');
      
      expect(button).toBeDisabled();
      fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('renders with all props at once', () => {
      const handleClick = jest.fn();
      
      render(
        <Button
          variant="success"
          size="xl"
          type="submit"
          disabled={false}
          loading={false}
          fullWidth
          onClick={handleClick}
          className="extra-class"
          ariaLabel="Complete button"
          data-testid="complete-button"
        >
          Complete
        </Button>
      );
      
      const button = screen.getByTestId('complete-button');
      
      expect(button).toHaveAttribute('type', 'submit');
      expect(button).toHaveAttribute('aria-label', 'Complete button');
      expect(button.className).toContain('bg-green-600');
      expect(button.className).toContain('px-8');
      expect(button.className).toContain('w-full');
      expect(button.className).toContain('extra-class');
      expect(button).not.toBeDisabled();
    });
  });

  describe('Loading Spinner Component', () => {
    it('has correct SVG attributes', () => {
      render(<Button loading>Loading</Button>);
      
      const spinner = document.querySelector('svg.animate-spin');
      
      expect(spinner).toHaveAttribute('xmlns', 'http://www.w3.org/2000/svg');
      expect(spinner).toHaveAttribute('fill', 'none');
      expect(spinner).toHaveAttribute('viewBox', '0 0 24 24');
    });

    it('has circle and path elements', () => {
      render(<Button loading>Loading</Button>);
      
      const circle = document.querySelector('svg.animate-spin circle');
      const path = document.querySelector('svg.animate-spin path');
      
      expect(circle).toBeInTheDocument();
      expect(path).toBeInTheDocument();
    });

    it('spinner has animation class', () => {
      render(<Button loading>Loading</Button>);
      
      const spinner = document.querySelector('svg');
      
      expect(spinner).toHaveClass('animate-spin');
    });
  });
});