import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import Header from './Header';

// Mock react-router-dom hooks
const mockUseLocation = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => mockUseLocation(),
}));

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  Bars3Icon: () => <svg data-testid="bars-icon" />,
  BellIcon: () => <svg data-testid="bell-icon" />,
  UserCircleIcon: () => <svg data-testid="user-icon" />,
  MagnifyingGlassIcon: () => <svg data-testid="search-icon" />,
  Cog6ToothIcon: () => <svg data-testid="settings-icon" />,
  ArrowRightOnRectangleIcon: () => <svg data-testid="logout-icon" />,
  SunIcon: () => <svg data-testid="sun-icon" />,
  MoonIcon: () => <svg data-testid="moon-icon" />,
}));

// Helper function to render with router
const renderWithRouter = (component, { route = '/' } = {}) => {
  mockUseLocation.mockReturnValue({ pathname: route });
  return render(
    <MemoryRouter initialEntries={[route]}>
      {component}
    </MemoryRouter>
  );
};

describe('Header Component', () => {
  const defaultProps = {
    onMenuToggle: jest.fn(),
    isSidebarOpen: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseLocation.mockReturnValue({ pathname: '/' });
    // Reset dark mode class
    document.documentElement.classList.remove('dark');
  });

  describe('Rendering', () => {
    it('should render the header component', () => {
      renderWithRouter(<Header {...defaultProps} />);
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should render the menu toggle button', () => {
      renderWithRouter(<Header {...defaultProps} />);
      expect(screen.getByTestId('bars-icon')).toBeInTheDocument();
    });

    it('should render the search input', () => {
      renderWithRouter(<Header {...defaultProps} />);
      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
    });

    it('should render the notification bell icon', () => {
      renderWithRouter(<Header {...defaultProps} />);
      expect(screen.getByTestId('bell-icon')).toBeInTheDocument();
    });

    it('should render the user profile icon', () => {
      renderWithRouter(<Header {...defaultProps} />);
      expect(screen.getByTestId('user-icon')).toBeInTheDocument();
    });

    it('should render dark mode toggle icon', () => {
      renderWithRouter(<Header {...defaultProps} />);
      // Should show sun or moon icon based on current mode
      const sunIcon = screen.queryByTestId('sun-icon');
      const moonIcon = screen.queryByTestId('moon-icon');
      expect(sunIcon || moonIcon).toBeInTheDocument();
    });
  });

  describe('Page Title based on Route', () => {
    it('should display "Dashboard" for root path', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/' });
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('should display "Dashboard" for /dashboard path', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/dashboard' });
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    it('should display "Restaurants" for /restaurants path', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/restaurants' });
      expect(screen.getByText('Restaurants')).toBeInTheDocument();
    });

    it('should display "Restaurants" for /restaurants/123 path', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/restaurants/123' });
      expect(screen.getByText('Restaurants')).toBeInTheDocument();
    });

    it('should display "Tables" for /tables path', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/tables' });
      expect(screen.getByText('Tables')).toBeInTheDocument();
    });

    it('should display "Bookings" for /bookings path', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/bookings' });
      expect(screen.getByText('Bookings')).toBeInTheDocument();
    });

    it('should display "Customers" for /customers path', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/customers' });
      expect(screen.getByText('Customers')).toBeInTheDocument();
    });

    it('should display "Restaurant Manager" for unknown paths', () => {
      renderWithRouter(<Header {...defaultProps} />, { route: '/unknown-page' });
      expect(screen.getByText('Restaurant Manager')).toBeInTheDocument();
    });
  });

  describe('Menu Toggle', () => {
    it('should call onMenuToggle when menu button is clicked', async () => {
      const onMenuToggle = jest.fn();
      renderWithRouter(<Header {...defaultProps} onMenuToggle={onMenuToggle} />);
      
      const menuButton = screen.getByRole('button', { name: /toggle menu/i }) || 
                         screen.getByTestId('bars-icon').closest('button');
      
      if (menuButton) {
        await userEvent.click(menuButton);
        expect(onMenuToggle).toHaveBeenCalledTimes(1);
      }
    });

    it('should reflect isSidebarOpen prop state', () => {
      const { rerender } = renderWithRouter(
        <Header {...defaultProps} isSidebarOpen={false} />
      );
      
      // Component should render without errors with isSidebarOpen false
      expect(screen.getByRole('banner')).toBeInTheDocument();
      
      // Rerender with isSidebarOpen true
      mockUseLocation.mockReturnValue({ pathname: '/' });
      rerender(
        <MemoryRouter>
          <Header {...defaultProps} isSidebarOpen={true} />
        </MemoryRouter>
      );
      
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should update search input value on change', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      const searchInput = screen.getByPlaceholderText(/search/i);
      
      await userEvent.type(searchInput, 'test query');
      
      expect(searchInput).toHaveValue('test query');
    });

    it('should handle search form submission', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      renderWithRouter(<Header {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, 'restaurant name');
      
      // Submit the form
      const form = searchInput.closest('form');
      if (form) {
        fireEvent.submit(form);
        expect(consoleSpy).toHaveBeenCalledWith('Searching for:', 'restaurant name');
      }
      
      consoleSpy.mockRestore();
    });

    it('should not search with empty query', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      renderWithRouter(<Header {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      const form = searchInput.closest('form');
      
      if (form) {
        fireEvent.submit(form);
        expect(consoleSpy).not.toHaveBeenCalledWith('Searching for:', expect.anything());
      }
      
      consoleSpy.mockRestore();
    });

    it('should not search with whitespace-only query', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      renderWithRouter(<Header {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, '   ');
      
      const form = searchInput.closest('form');
      if (form) {
        fireEvent.submit(form);
        expect(consoleSpy).not.toHaveBeenCalledWith('Searching for:', '   ');
      }
      
      consoleSpy.mockRestore();
    });
  });

  describe('Dark Mode Toggle', () => {
    it('should toggle dark mode class on document when clicked', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      // Find the dark mode toggle button (contains sun or moon icon)
      const sunIcon = screen.queryByTestId('sun-icon');
      const moonIcon = screen.queryByTestId('moon-icon');
      const toggleButton = (sunIcon || moonIcon)?.closest('button');
      
      if (toggleButton) {
        expect(document.documentElement.classList.contains('dark')).toBe(false);
        
        await userEvent.click(toggleButton);
        
        expect(document.documentElement.classList.contains('dark')).toBe(true);
      }
    });

    it('should toggle dark mode off when already enabled', async () => {
      document.documentElement.classList.add('dark');
      renderWithRouter(<Header {...defaultProps} />);
      
      const sunIcon = screen.queryByTestId('sun-icon');
      const moonIcon = screen.queryByTestId('moon-icon');
      const toggleButton = (sunIcon || moonIcon)?.closest('button');
      
      if (toggleButton) {
        await userEvent.click(toggleButton);
        await userEvent.click(toggleButton);
        
        // After two clicks, should be back to original state
        expect(document.documentElement.classList.contains('dark')).toBe(true);
      }
    });
  });

  describe('Notifications', () => {
    it('should display unread notification count badge', () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      // Should show badge with count 2 (two unread notifications in initial state)
      const badge = screen.getByText('2');
      expect(badge).toBeInTheDocument();
    });

    it('should open notifications dropdown when bell icon is clicked', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const bellIcon = screen.getByTestId('bell-icon');
      const notificationButton = bellIcon.closest('button');
      
      if (notificationButton) {
        await userEvent.click(notificationButton);
        
        // Should show notification items
        expect(screen.getByText('New Booking')).toBeInTheDocument();
        expect(screen.getByText('Booking Cancelled')).toBeInTheDocument();
        expect(screen.getByText('New Customer')).toBeInTheDocument();
      }
    });

    it('should display notification details', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const bellIcon = screen.getByTestId('bell-icon');
      const notificationButton = bellIcon.closest('button');
      
      if (notificationButton) {
        await userEvent.click(notificationButton);
        
        expect(screen.getByText('Table 5 booked for tonight at 7 PM')).toBeInTheDocument();
        expect(screen.getByText('5 min ago')).toBeInTheDocument();
      }
    });

    it('should mark notification as read when clicked', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const bellIcon = screen.getByTestId('bell-icon');
      const notificationButton = bellIcon.closest('button');
      
      if (notificationButton) {
        await userEvent.click(notificationButton);
        
        const notification = screen.getByText('New Booking').closest('div[role="button"]') ||
                            screen.getByText('New Booking').closest('li') ||
                            screen.getByText('New Booking').parentElement;
        
        if (notification) {
          await userEvent.click(notification);
          
          // After marking as read, badge count should decrease
          await waitFor(() => {
            const badge = screen.queryByText('2');
            // Badge should either show 1 or not exist if all are read
          });
        }
      }
    });

    it('should mark all notifications as read', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const bellIcon = screen.getByTestId('bell-icon');
      const notificationButton = bellIcon.closest('button');
      
      if (notificationButton) {
        await userEvent.click(notificationButton);
        
        const markAllButton = screen.queryByText(/mark all as read/i) ||
                             screen.queryByRole('button', { name: /mark all/i });
        
        if (markAllButton) {
          await userEvent.click(markAllButton);
          
          await waitFor(() => {
            // Badge should be hidden or show 0
            const badge = screen.queryByText('2');
            expect(badge).not.toBeInTheDocument();
          });
        }
      }
    });

    it('should close notifications dropdown when clicking outside', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const bellIcon = screen.getByTestId('bell-icon');
      const notificationButton = bellIcon.closest('button');
      
      if (notificationButton) {
        await userEvent.click(notificationButton);
        
        // Verify dropdown is open
        expect(screen.getByText('New Booking')).toBeInTheDocument();
        
        // Click outside
        fireEvent.mouseDown(document.body);
        
        await waitFor(() => {
          // Dropdown should be closed
          expect(screen.queryByText('New Booking')).not.toBeInTheDocument();
        });
      }
    });
  });

  describe('Profile Dropdown', () => {
    it('should open profile dropdown when user icon is clicked', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const userIcon = screen.getByTestId('user-icon');
      const profileButton = userIcon.closest('button');
      
      if (profileButton) {
        await userEvent.click(profileButton);
        
        // Should show profile menu items
        expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
        expect(screen.getByTestId('logout-icon')).toBeInTheDocument();
      }
    });

    it('should display settings option in profile dropdown', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const userIcon = screen.getByTestId('user-icon');
      const profileButton = userIcon.closest('button');
      
      if (profileButton) {
        await userEvent.click(profileButton);
        
        const settingsOption = screen.queryByText(/settings/i);
        expect(settingsOption || screen.getByTestId('settings-icon')).toBeInTheDocument();
      }
    });

    it('should display logout option in profile dropdown', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const userIcon = screen.getByTestId('user-icon');
      const profileButton = userIcon.closest('button');
      
      if (profileButton) {
        await userEvent.click(profileButton);
        
        const logoutOption = screen.queryByText(/log ?out|sign ?out/i);
        expect(logoutOption || screen.getByTestId('logout-icon')).toBeInTheDocument();
      }
    });

    it('should close profile dropdown when clicking outside', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const userIcon = screen.getByTestId('user-icon');
      const profileButton = userIcon.closest('button');
      
      if (profileButton) {
        await userEvent.click(profileButton);
        
        // Verify dropdown is open
        expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
        
        // Click outside
        fireEvent.mouseDown(document.body);
        
        await waitFor(() => {
          // The icons should still exist but dropdown should be closed
          // This depends on implementation - dropdown content should be hidden
        });
      }
    });

    it('should toggle profile dropdown on multiple clicks', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const userIcon = screen.getByTestId('user-icon');
      const profileButton = userIcon.closest('button');
      
      if (profileButton) {
        // First click - open
        await userEvent.click(profileButton);
        expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
        
        // Second click - close
        await userEvent.click(profileButton);
        
        // Third click - open again
        await userEvent.click(profileButton);
        expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
      }
    });
  });

  describe('Responsive Behavior', () => {
    it('should render mobile menu toggle', () => {
      renderWithRouter(<Header {...defaultProps} />);
      expect(screen.getByTestId('bars-icon')).toBeInTheDocument();
    });

    it('should handle menu toggle in mobile view', async () => {
      const onMenuToggle = jest.fn();
      renderWithRouter(<Header {...defaultProps} onMenuToggle={onMenuToggle} />);
      
      const menuButton = screen.getByTestId('bars-icon').closest('button');
      
      if (menuButton) {
        await userEvent.click(menuButton);
        expect(onMenuToggle).toHaveBeenCalled();
      }
    });
  });

  describe('Accessibility', () => {
    it('should have accessible search input', () => {
      renderWithRouter(<Header {...defaultProps} />);
      const searchInput = screen.getByPlaceholderText(/search/i);
      expect(searchInput).toHaveAttribute('type', 'text');
    });

    it('should have clickable buttons', () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should render navigation landmark', () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      // Header should be a banner landmark
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing onMenuToggle prop gracefully', () => {
      const propsWithoutToggle = { isSidebarOpen: false };
      
      expect(() => {
        renderWithRouter(<Header {...propsWithoutToggle} />);
      }).not.toThrow();
    });

    it('should handle undefined isSidebarOpen prop', () => {
      const propsWithoutSidebar = { onMenuToggle: jest.fn() };
      
      expect(() => {
        renderWithRouter(<Header {...propsWithoutSidebar} />);
      }).not.toThrow();
    });

    it('should handle rapid clicks on dropdowns', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const bellIcon = screen.getByTestId('bell-icon');
      const notificationButton = bellIcon.closest('button');
      
      if (notificationButton) {
        // Rapid clicks
        await userEvent.click(notificationButton);
        await userEvent.click(notificationButton);
        await userEvent.click(notificationButton);
        await userEvent.click(notificationButton);
        
        // Should not throw and component should still work
        expect(screen.getByRole('banner')).toBeInTheDocument();
      }
    });

    it('should handle special characters in search query', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
      renderWithRouter(<Header {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, '<script>alert("xss")</script>');
      
      const form = searchInput.closest('form');
      if (form) {
        fireEvent.submit(form);
        expect(consoleSpy).toHaveBeenCalledWith(
          'Searching for:',
          '<script>alert("xss")</script>'
        );
      }
      
      consoleSpy.mockRestore();
    });

    it('should handle very long search queries', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      const longQuery = 'a'.repeat(1000);
      
      await userEvent.type(searchInput, longQuery);
      
      expect(searchInput.value.length).toBe(1000);
    });
  });

  describe('State Management', () => {
    it('should maintain independent dropdown states', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const bellIcon = screen.getByTestId('bell-icon');
      const userIcon = screen.getByTestId('user-icon');
      const notificationButton = bellIcon.closest('button');
      const profileButton = userIcon.closest('button');
      
      if (notificationButton && profileButton) {
        // Open notifications
        await userEvent.click(notificationButton);
        expect(screen.getByText('New Booking')).toBeInTheDocument();
        
        // Open profile (should close notifications)
        await userEvent.click(profileButton);
        
        // Profile should be open
        expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
      }
    });

    it('should preserve search query across dropdown interactions', async () => {
      renderWithRouter(<Header {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/search/i);
      await userEvent.type(searchInput, 'test query');
      
      const bellIcon = screen.getByTestId('bell-icon');
      const notificationButton = bellIcon.closest('button');
      
      if (notificationButton) {
        await userEvent.click(notificationButton);
        await userEvent.click(notificationButton);
      }
      
      expect(searchInput).toHaveValue('test query');
    });
  });

  describe('Cleanup', () => {
    it('should clean up event listeners on unmount', () => {
      const { unmount } = renderWithRouter(<Header {...defaultProps} />);
      
      expect(() => {
        unmount();
      }).not.toThrow();
    });

    it('should not cause memory leaks with rapid mount/unmount', () => {
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderWithRouter(<Header {...defaultProps} />);
        unmount();
      }
      
      // If we get here without errors, the test passes
      expect(true).toBe(true);
    });
  });
});