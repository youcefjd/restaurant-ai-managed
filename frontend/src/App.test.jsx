import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

// Mock the components
jest.mock('./components/Layout', () => {
  return function MockLayout({ children }) {
    return <div data-testid="layout">{children}</div>;
  };
});

jest.mock('./pages/Dashboard', () => {
  return function MockDashboard() {
    return <div data-testid="dashboard">Dashboard</div>;
  };
});

jest.mock('./pages/Restaurants', () => {
  return function MockRestaurants() {
    return <div data-testid="restaurants">Restaurants</div>;
  };
});

jest.mock('./pages/Tables', () => {
  return function MockTables() {
    return <div data-testid="tables">Tables</div>;
  };
});

jest.mock('./pages/Bookings', () => {
  return function MockBookings() {
    return <div data-testid="bookings">Bookings</div>;
  };
});

jest.mock('./pages/Customers', () => {
  return function MockCustomers() {
    return <div data-testid="customers">Customers</div>;
  };
});

// Import after mocks
import App, { useAppContext } from './App';

// Helper component to test useAppContext hook
function TestConsumer({ onContext }) {
  const context = useAppContext();
  React.useEffect(() => {
    onContext(context);
  }, [context, onContext]);
  return <div data-testid="test-consumer">Consumer</div>;
}

// Helper component to test context outside provider
function ContextOutsideProvider() {
  try {
    useAppContext();
    return <div>No error</div>;
  } catch (error) {
    return <div data-testid="error">{error.message}</div>;
  }
}

describe('App Component', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  describe('Routing', () => {
    it('renders dashboard at root path', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });

    it('renders restaurants page at /restaurants path', () => {
      render(
        <MemoryRouter initialEntries={['/restaurants']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('restaurants')).toBeInTheDocument();
    });

    it('renders tables page at /tables path', () => {
      render(
        <MemoryRouter initialEntries={['/tables']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('tables')).toBeInTheDocument();
    });

    it('renders bookings page at /bookings path', () => {
      render(
        <MemoryRouter initialEntries={['/bookings']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('bookings')).toBeInTheDocument();
    });

    it('renders customers page at /customers path', () => {
      render(
        <MemoryRouter initialEntries={['/customers']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('customers')).toBeInTheDocument();
    });

    it('wraps content in Layout component', () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('layout')).toBeInTheDocument();
    });
  });

  describe('AppProvider and Context', () => {
    it('provides initial context values', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      expect(capturedContext.selectedRestaurant).toBeNull();
      expect(capturedContext.notification).toBeNull();
      expect(typeof capturedContext.setSelectedRestaurant).toBe('function');
      expect(typeof capturedContext.showNotification).toBe('function');
      expect(typeof capturedContext.clearNotification).toBe('function');
    });

    it('throws error when useAppContext is used outside AppProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(<ContextOutsideProvider />);

      expect(screen.getByTestId('error')).toHaveTextContent(
        'useAppContext must be used within AppProvider'
      );

      consoleSpy.mockRestore();
    });
  });

  describe('Selected Restaurant State', () => {
    it('restores selected restaurant from localStorage on mount', async () => {
      const savedRestaurant = { id: 1, name: 'Test Restaurant' };
      localStorage.setItem('selectedRestaurant', JSON.stringify(savedRestaurant));

      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext?.selectedRestaurant).toEqual(savedRestaurant);
      });
    });

    it('handles invalid JSON in localStorage gracefully', async () => {
      localStorage.setItem('selectedRestaurant', 'invalid-json');

      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      expect(capturedContext.selectedRestaurant).toBeNull();
      expect(localStorage.getItem('selectedRestaurant')).toBeNull();
    });

    it('persists selected restaurant to localStorage when changed', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      const newRestaurant = { id: 2, name: 'New Restaurant' };

      act(() => {
        capturedContext.setSelectedRestaurant(newRestaurant);
      });

      await waitFor(() => {
        const stored = localStorage.getItem('selectedRestaurant');
        expect(JSON.parse(stored)).toEqual(newRestaurant);
      });
    });

    it('removes selected restaurant from localStorage when set to null', async () => {
      localStorage.setItem('selectedRestaurant', JSON.stringify({ id: 1 }));

      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext?.selectedRestaurant).not.toBeNull();
      });

      act(() => {
        capturedContext.setSelectedRestaurant(null);
      });

      await waitFor(() => {
        expect(localStorage.getItem('selectedRestaurant')).toBeNull();
      });
    });
  });

  describe('Notification System', () => {
    it('shows notification with default type and duration', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('Test message');
      });

      await waitFor(() => {
        expect(capturedContext.notification).not.toBeNull();
        expect(capturedContext.notification.message).toBe('Test message');
        expect(capturedContext.notification.type).toBe('info');
        expect(capturedContext.notification.id).toBeDefined();
      });
    });

    it('shows notification with custom type', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('Error occurred', 'error');
      });

      await waitFor(() => {
        expect(capturedContext.notification.type).toBe('error');
      });
    });

    it('shows notification with success type', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('Success!', 'success');
      });

      await waitFor(() => {
        expect(capturedContext.notification.type).toBe('success');
      });
    });

    it('shows notification with warning type', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('Warning!', 'warning');
      });

      await waitFor(() => {
        expect(capturedContext.notification.type).toBe('warning');
      });
    });

    it('auto-dismisses notification after default duration', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('Auto dismiss test');
      });

      await waitFor(() => {
        expect(capturedContext.notification).not.toBeNull();
      });

      // Fast-forward past the default 5000ms duration
      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(capturedContext.notification).toBeNull();
      });
    });

    it('auto-dismisses notification after custom duration', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('Custom duration', 'info', 2000);
      });

      await waitFor(() => {
        expect(capturedContext.notification).not.toBeNull();
      });

      // Should still be visible before duration
      act(() => {
        jest.advanceTimersByTime(1999);
      });

      expect(capturedContext.notification).not.toBeNull();

      // Should be dismissed after duration
      act(() => {
        jest.advanceTimersByTime(1);
      });

      await waitFor(() => {
        expect(capturedContext.notification).toBeNull();
      });
    });

    it('does not auto-dismiss when duration is 0', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('Persistent notification', 'info', 0);
      });

      await waitFor(() => {
        expect(capturedContext.notification).not.toBeNull();
      });

      // Fast-forward a long time
      act(() => {
        jest.advanceTimersByTime(60000);
      });

      // Should still be visible
      expect(capturedContext.notification).not.toBeNull();
    });

    it('clears notification manually', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('To be cleared', 'info', 0);
      });

      await waitFor(() => {
        expect(capturedContext.notification).not.toBeNull();
      });

      act(() => {
        capturedContext.clearNotification();
      });

      await waitFor(() => {
        expect(capturedContext.notification).toBeNull();
      });
    });

    it('assigns unique id to each notification', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      let firstId;
      act(() => {
        capturedContext.showNotification('First', 'info', 0);
      });

      await waitFor(() => {
        firstId = capturedContext.notification.id;
      });

      // Wait a bit to ensure different timestamp
      act(() => {
        jest.advanceTimersByTime(10);
      });

      act(() => {
        capturedContext.showNotification('Second', 'info', 0);
      });

      await waitFor(() => {
        expect(capturedContext.notification.id).not.toBe(firstId);
      });
    });
  });

  describe('Initialization State', () => {
    it('sets isInitialized to true after mount', async () => {
      // This is tested implicitly through the context being available
      // The app should render content after initialization
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );

      // If isInitialized works, the dashboard should render
      await waitFor(() => {
        expect(screen.getByTestId('dashboard')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles empty localStorage', async () => {
      localStorage.clear();

      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      expect(capturedContext.selectedRestaurant).toBeNull();
    });

    it('handles rapid notification changes', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      // Rapidly show multiple notifications
      act(() => {
        capturedContext.showNotification('First', 'info', 1000);
        capturedContext.showNotification('Second', 'success', 1000);
        capturedContext.showNotification('Third', 'error', 1000);
      });

      // Should show the last notification
      await waitFor(() => {
        expect(capturedContext.notification.message).toBe('Third');
      });
    });

    it('handles restaurant selection changes', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      // Set restaurant
      act(() => {
        capturedContext.setSelectedRestaurant({ id: 1, name: 'Restaurant 1' });
      });

      await waitFor(() => {
        expect(capturedContext.selectedRestaurant.id).toBe(1);
      });

      // Change restaurant
      act(() => {
        capturedContext.setSelectedRestaurant({ id: 2, name: 'Restaurant 2' });
      });

      await waitFor(() => {
        expect(capturedContext.selectedRestaurant.id).toBe(2);
      });

      // Clear restaurant
      act(() => {
        capturedContext.setSelectedRestaurant(null);
      });

      await waitFor(() => {
        expect(capturedContext.selectedRestaurant).toBeNull();
      });
    });

    it('handles notification with empty message', async () => {
      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.showNotification('', 'info');
      });

      await waitFor(() => {
        expect(capturedContext.notification.message).toBe('');
      });
    });

    it('handles complex restaurant object', async () => {
      const complexRestaurant = {
        id: 1,
        name: 'Complex Restaurant',
        address: {
          street: '123 Main St',
          city: 'Test City',
          zip: '12345'
        },
        tables: [1, 2, 3],
        metadata: {
          created: new Date().toISOString(),
          updated: null
        }
      };

      let capturedContext = null;
      const handleContext = (ctx) => {
        capturedContext = ctx;
      };

      render(
        <MemoryRouter>
          <App>
            <TestConsumer onContext={handleContext} />
          </App>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(capturedContext).not.toBeNull();
      });

      act(() => {
        capturedContext.setSelectedRestaurant(complexRestaurant);
      });

      await waitFor(() => {
        expect(capturedContext.selectedRestaurant).toEqual(complexRestaurant);
      });

      // Verify it was persisted correctly
      const stored = JSON.parse(localStorage.getItem('selectedRestaurant'));
      expect(stored).toEqual(complexRestaurant);
    });
  });
});

describe('useAppContext Hook', () => {
  it('returns context when used within provider', async () => {
    let hookResult = null;

    function TestComponent() {
      hookResult = useAppContext();
      return <div>Test</div>;
    }

    render(
      <MemoryRouter>
        <App>
          <TestComponent />
        </App>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(hookResult).not.toBeNull();
    });

    expect(hookResult).toHaveProperty('selectedRestaurant');
    expect(hookResult).toHaveProperty('setSelectedRestaurant');
    expect(hookResult).toHaveProperty('notification');
    expect(hookResult).toHaveProperty('showNotification');
    expect(hookResult).toHaveProperty('clearNotification');
  });
});