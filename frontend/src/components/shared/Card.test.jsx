import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Card from './Card';

describe('Card Component', () => {
  describe('Basic Rendering', () => {
    it('renders children content correctly', () => {
      render(<Card>Test Content</Card>);
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders with default props', () => {
      const { container } = render(<Card>Default Card</Card>);
      const card = container.firstChild;
      
      expect(card).toHaveClass('bg-white');
      expect(card).toHaveClass('shadow');
      expect(card).toHaveClass('rounded-lg');
      expect(card).toHaveClass('border');
      expect(card).toHaveClass('border-gray-200');
    });

    it('renders without children', () => {
      const { container } = render(<Card />);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders complex children correctly', () => {
      render(
        <Card>
          <div data-testid="child-1">First Child</div>
          <div data-testid="child-2">Second Child</div>
        </Card>
      );
      
      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
    });
  });

  describe('Header Rendering', () => {
    it('renders header when provided', () => {
      render(<Card header={<div>Header Content</div>}>Body</Card>);
      expect(screen.getByText('Header Content')).toBeInTheDocument();
    });

    it('renders title in header', () => {
      render(<Card title="Card Title">Body</Card>);
      expect(screen.getByText('Card Title')).toBeInTheDocument();
    });

    it('renders subtitle in header', () => {
      render(<Card title="Title" subtitle="Subtitle Text">Body</Card>);
      expect(screen.getByText('Subtitle Text')).toBeInTheDocument();
    });

    it('renders headerAction in header', () => {
      render(
        <Card 
          title="Title" 
          headerAction={<button>Action</button>}
        >
          Body
        </Card>
      );
      expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
    });

    it('applies headerClassName to header', () => {
      const { container } = render(
        <Card header={<div>Header</div>} headerClassName="custom-header-class">
          Body
        </Card>
      );
      
      const header = container.querySelector('.custom-header-class');
      expect(header).toBeInTheDocument();
    });

    it('renders header with border when border prop is true', () => {
      const { container } = render(
        <Card header={<div>Header</div>} border={true}>
          Body
        </Card>
      );
      
      const header = container.querySelector('.border-b');
      expect(header).toBeInTheDocument();
    });
  });

  describe('Footer Rendering', () => {
    it('renders footer when provided', () => {
      render(<Card footer={<div>Footer Content</div>}>Body</Card>);
      expect(screen.getByText('Footer Content')).toBeInTheDocument();
    });

    it('applies footerClassName to footer', () => {
      const { container } = render(
        <Card footer={<div>Footer</div>} footerClassName="custom-footer-class">
          Body
        </Card>
      );
      
      const footer = container.querySelector('.custom-footer-class');
      expect(footer).toBeInTheDocument();
    });

    it('renders footer with border when border prop is true', () => {
      const { container } = render(
        <Card footer={<div>Footer</div>} border={true}>
          Body
        </Card>
      );
      
      const footer = container.querySelector('.border-t');
      expect(footer).toBeInTheDocument();
    });

    it('applies bg-gray-50 to footer for non-dark variant', () => {
      const { container } = render(
        <Card footer={<div>Footer</div>} variant="default">
          Body
        </Card>
      );
      
      const footer = container.querySelector('.bg-gray-50');
      expect(footer).toBeInTheDocument();
    });
  });

  describe('Variant Styles', () => {
    it('applies default variant styles', () => {
      const { container } = render(<Card variant="default">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-white');
    });

    it('applies primary variant styles', () => {
      const { container } = render(<Card variant="primary">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-blue-50');
      expect(container.firstChild).toHaveClass('border-blue-200');
    });

    it('applies success variant styles', () => {
      const { container } = render(<Card variant="success">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-green-50');
      expect(container.firstChild).toHaveClass('border-green-200');
    });

    it('applies warning variant styles', () => {
      const { container } = render(<Card variant="warning">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-yellow-50');
      expect(container.firstChild).toHaveClass('border-yellow-200');
    });

    it('applies danger variant styles', () => {
      const { container } = render(<Card variant="danger">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-red-50');
      expect(container.firstChild).toHaveClass('border-red-200');
    });

    it('applies info variant styles', () => {
      const { container } = render(<Card variant="info">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-cyan-50');
      expect(container.firstChild).toHaveClass('border-cyan-200');
    });

    it('applies dark variant styles', () => {
      const { container } = render(<Card variant="dark">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-gray-800');
      expect(container.firstChild).toHaveClass('text-white');
    });

    it('falls back to default variant for invalid variant', () => {
      const { container } = render(<Card variant="invalid">Content</Card>);
      expect(container.firstChild).toHaveClass('bg-white');
    });
  });

  describe('Padding Styles', () => {
    it('applies no padding when padding is none', () => {
      const { container } = render(<Card padding="none">Content</Card>);
      expect(container.firstChild).not.toHaveClass('p-3');
      expect(container.firstChild).not.toHaveClass('p-4');
      expect(container.firstChild).not.toHaveClass('p-6');
    });

    it('applies small padding', () => {
      const { container } = render(<Card padding="small">Content</Card>);
      expect(container.firstChild).toHaveClass('p-3');
    });

    it('applies default padding', () => {
      const { container } = render(<Card padding="default">Content</Card>);
      expect(container.firstChild).toHaveClass('p-4');
      expect(container.firstChild).toHaveClass('sm:p-6');
    });

    it('applies large padding', () => {
      const { container } = render(<Card padding="large">Content</Card>);
      expect(container.firstChild).toHaveClass('p-6');
      expect(container.firstChild).toHaveClass('sm:p-8');
    });

    it('does not apply padding to card when header exists', () => {
      const { container } = render(
        <Card padding="large" header={<div>Header</div>}>
          Content
        </Card>
      );
      expect(container.firstChild).not.toHaveClass('p-6');
    });

    it('does not apply padding to card when footer exists', () => {
      const { container } = render(
        <Card padding="large" footer={<div>Footer</div>}>
          Content
        </Card>
      );
      expect(container.firstChild).not.toHaveClass('p-6');
    });
  });

  describe('Shadow Styles', () => {
    it('applies no shadow when shadow is none', () => {
      const { container } = render(<Card shadow="none">Content</Card>);
      expect(container.firstChild).not.toHaveClass('shadow');
      expect(container.firstChild).not.toHaveClass('shadow-sm');
      expect(container.firstChild).not.toHaveClass('shadow-md');
    });

    it('applies small shadow', () => {
      const { container } = render(<Card shadow="small">Content</Card>);
      expect(container.firstChild).toHaveClass('shadow-sm');
    });

    it('applies default shadow', () => {
      const { container } = render(<Card shadow="default">Content</Card>);
      expect(container.firstChild).toHaveClass('shadow');
    });

    it('applies medium shadow', () => {
      const { container } = render(<Card shadow="medium">Content</Card>);
      expect(container.firstChild).toHaveClass('shadow-md');
    });

    it('applies large shadow', () => {
      const { container } = render(<Card shadow="large">Content</Card>);
      expect(container.firstChild).toHaveClass('shadow-lg');
    });

    it('applies xl shadow', () => {
      const { container } = render(<Card shadow="xl">Content</Card>);
      expect(container.firstChild).toHaveClass('shadow-xl');
    });

    it('falls back to default shadow for invalid shadow value', () => {
      const { container } = render(<Card shadow="invalid">Content</Card>);
      expect(container.firstChild).toHaveClass('shadow');
    });
  });

  describe('Rounded Styles', () => {
    it('applies no rounded corners when rounded is none', () => {
      const { container } = render(<Card rounded="none">Content</Card>);
      expect(container.firstChild).not.toHaveClass('rounded');
      expect(container.firstChild).not.toHaveClass('rounded-lg');
    });

    it('applies small rounded corners', () => {
      const { container } = render(<Card rounded="small">Content</Card>);
      expect(container.firstChild).toHaveClass('rounded');
    });

    it('applies default rounded corners', () => {
      const { container } = render(<Card rounded="default">Content</Card>);
      expect(container.firstChild).toHaveClass('rounded-lg');
    });

    it('applies large rounded corners', () => {
      const { container } = render(<Card rounded="large">Content</Card>);
      expect(container.firstChild).toHaveClass('rounded-xl');
    });

    it('applies full rounded corners', () => {
      const { container } = render(<Card rounded="full">Content</Card>);
      expect(container.firstChild).toHaveClass('rounded-3xl');
    });

    it('falls back to default rounded for invalid value', () => {
      const { container } = render(<Card rounded="invalid">Content</Card>);
      expect(container.firstChild).toHaveClass('rounded-lg');
    });
  });

  describe('Border Styles', () => {
    it('applies border when border prop is true', () => {
      const { container } = render(<Card border={true}>Content</Card>);
      expect(container.firstChild).toHaveClass('border');
      expect(container.firstChild).toHaveClass('border-gray-200');
    });

    it('does not apply border when border prop is false', () => {
      const { container } = render(<Card border={false}>Content</Card>);
      expect(container.firstChild).not.toHaveClass('border');
      expect(container.firstChild).not.toHaveClass('border-gray-200');
    });

    it('applies border by default', () => {
      const { container } = render(<Card>Content</Card>);
      expect(container.firstChild).toHaveClass('border');
    });
  });

  describe('Interactive States', () => {
    it('applies hoverable styles when hoverable is true', () => {
      const { container } = render(<Card hoverable={true}>Content</Card>);
      expect(container.firstChild).toHaveClass('hover:shadow-lg');
      expect(container.firstChild).toHaveClass('hover:scale-[1.01]');
      expect(container.firstChild).toHaveClass('cursor-pointer');
    });

    it('applies clickable styles when clickable is true', () => {
      const { container } = render(<Card clickable={true}>Content</Card>);
      expect(container.firstChild).toHaveClass('hover:shadow-lg');
      expect(container.firstChild).toHaveClass('cursor-pointer');
    });

    it('does not apply interactive styles by default', () => {
      const { container } = render(<Card>Content</Card>);
      expect(container.firstChild).not.toHaveClass('cursor-pointer');
    });

    it('calls onClick handler when clicked', () => {
      const handleClick = jest.fn();
      render(<Card clickable onClick={handleClick}>Content</Card>);
      
      fireEvent.click(screen.getByText('Content'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not throw when clicked without onClick handler', () => {
      render(<Card clickable>Content</Card>);
      
      expect(() => {
        fireEvent.click(screen.getByText('Content'));
      }).not.toThrow();
    });
  });

  describe('Custom Classes', () => {
    it('applies custom className to card', () => {
      const { container } = render(
        <Card className="custom-card-class">Content</Card>
      );
      expect(container.firstChild).toHaveClass('custom-card-class');
    });

    it('applies bodyClassName to body', () => {
      const { container } = render(
        <Card 
          header={<div>Header</div>} 
          bodyClassName="custom-body-class"
        >
          Content
        </Card>
      );
      
      const body = container.querySelector('.custom-body-class');
      expect(body).toBeInTheDocument();
    });

    it('merges multiple custom classes', () => {
      const { container } = render(
        <Card className="class-one class-two class-three">Content</Card>
      );
      
      expect(container.firstChild).toHaveClass('class-one');
      expect(container.firstChild).toHaveClass('class-two');
      expect(container.firstChild).toHaveClass('class-three');
    });
  });

  describe('Accessibility', () => {
    it('applies aria-label when provided', () => {
      render(<Card aria-label="Test Card">Content</Card>);
      expect(screen.getByLabelText('Test Card')).toBeInTheDocument();
    });

    it('applies aria-labelledby when provided', () => {
      const { container } = render(
        <Card aria-labelledby="card-title">Content</Card>
      );
      expect(container.firstChild).toHaveAttribute('aria-labelledby', 'card-title');
    });

    it('applies role when provided', () => {
      render(<Card role="article">Content</Card>);
      expect(screen.getByRole('article')).toBeInTheDocument();
    });

    it('applies role="region" when specified', () => {
      render(<Card role="region" aria-label="Card Region">Content</Card>);
      expect(screen.getByRole('region')).toBeInTheDocument();
    });
  });

  describe('Rest Props', () => {
    it('passes additional props to the card element', () => {
      const { container } = render(
        <Card data-testid="test-card" id="my-card">Content</Card>
      );
      
      expect(screen.getByTestId('test-card')).toBeInTheDocument();
      expect(container.firstChild).toHaveAttribute('id', 'my-card');
    });

    it('passes data attributes correctly', () => {
      const { container } = render(
        <Card data-custom="custom-value">Content</Card>
      );
      
      expect(container.firstChild).toHaveAttribute('data-custom', 'custom-value');
    });
  });

  describe('Dark Variant Specific Styles', () => {
    it('applies dark border to header in dark variant', () => {
      const { container } = render(
        <Card variant="dark" header={<div>Header</div>}>
          Body
        </Card>
      );
      
      const header = container.querySelector('.border-gray-700');
      expect(header).toBeInTheDocument();
    });

    it('applies dark background to footer in dark variant', () => {
      const { container } = render(
        <Card variant="dark" footer={<div>Footer</div>}>
          Body
        </Card>
      );
      
      const footer = container.querySelector('.bg-gray-900');
      expect(footer).toBeInTheDocument();
    });
  });

  describe('Combined Props', () => {
    it('renders correctly with all props combined', () => {
      const handleClick = jest.fn();
      
      const { container } = render(
        <Card
          header={<div>Header</div>}
          footer={<div>Footer</div>}
          title="Title"
          subtitle="Subtitle"
          headerAction={<button>Action</button>}
          variant="primary"
          padding="large"
          shadow="large"
          rounded="large"
          border={true}
          hoverable={true}
          clickable={true}
          onClick={handleClick}
          className="custom-class"
          headerClassName="custom-header"
          bodyClassName="custom-body"
          footerClassName="custom-footer"
          aria-label="Full Card"
          role="article"
          data-testid="full-card"
        >
          Body Content
        </Card>
      );

      expect(screen.getByTestId('full-card')).toBeInTheDocument();
      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Footer')).toBeInTheDocument();
      expect(screen.getByText('Body Content')).toBeInTheDocument();
      expect(container.firstChild).toHaveClass('bg-blue-50');
      expect(container.firstChild).toHaveClass('shadow-lg');
      expect(container.firstChild).toHaveClass('rounded-xl');
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('handles empty string className gracefully', () => {
      const { container } = render(<Card className="">Content</Card>);
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Transition Styles', () => {
    it('applies transition classes for animations', () => {
      const { container } = render(<Card>Content</Card>);
      expect(container.firstChild).toHaveClass('transition-all');
      expect(container.firstChild).toHaveClass('duration-200');
    });
  });

  describe('Overflow Handling', () => {
    it('applies overflow-hidden to prevent content overflow', () => {
      const { container } = render(<Card>Content</Card>);
      expect(container.firstChild).toHaveClass('overflow-hidden');
    });
  });

  describe('Edge Cases', () => {
    it('handles null children', () => {
      const { container } = render(<Card>{null}</Card>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('handles undefined children', () => {
      const { container } = render(<Card>{undefined}</Card>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('handles boolean children', () => {
      const { container } = render(<Card>{false}</Card>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('handles number children', () => {
      render(<Card>{42}</Card>);
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('handles array children', () => {
      render(
        <Card>
          {['Item 1', 'Item 2', 'Item 3'].map((item, index) => (
            <span key={index}>{item}</span>
          ))}
        </Card>
      );
      
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('Item 3')).toBeInTheDocument();
    });

    it('handles empty header', () => {
      const { container } = render(<Card header="">Content</Card>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('handles empty footer', () => {
      const { container } = render(<Card footer="">Content</Card>);
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Responsive Styles', () => {
    it('includes responsive padding classes', () => {
      const { container } = render(<Card padding="default">Content</Card>);
      expect(container.firstChild).toHaveClass('sm:p-6');
    });

    it('includes responsive header padding', () => {
      const { container } = render(
        <Card header={<div>Header</div>}>Content</Card>
      );
      
      const header = container.querySelector('.sm\\:px-6');
      expect(header).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default card', () => {
      const { container } = render(<Card>Default Content</Card>);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot for card with header and footer', () => {
      const { container } = render(
        <Card
          header={<div>Header</div>}
          footer={<div>Footer</div>}
        >
          Body Content
        </Card>
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot for dark variant', () => {
      const { container } = render(
        <Card variant="dark">Dark Content</Card>
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});