import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Layout from './Layout';

// Mock heroicons
jest.mock('@heroicons/react/24/outline', () => ({
  Bars3Icon: ({ className }) => <svg data-testid="bars-icon" className={className} />,
  XMarkIcon: ({ className }) => <svg data-testid="x-icon" className={className} />,
  HomeIcon: ({ className }) => <svg data-testid="home-icon" className={className} />,
  BuildingStorefrontIcon: ({ className }) => <svg data-testid="restaurant-icon" className={className} />,
  TableCellsIcon: ({ className }) => <svg data-testid="table-icon" className={className} />,
  CalendarDaysIcon: ({ className }) => <svg data-testid="calendar-icon" className={className} />,
  UsersIcon: ({ className }) => <svg data-testid="users-icon" className={className} />,
  ChevronLeftIcon: ({ className }) => <svg data-testid="chevron-icon" className={className} />,
}));

// Helper function to render Layout with router
const renderWithRouter = (initialRoute = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/*" element={<Layout />}>
          <Route index element={<div data-testid="dashboard-content">Dashboard Content</div>} />
          <Route path="restaurants/*" element={<div data-testid="restaurants-content">Restaurants Content</div>} />
          <Route path="tables/*" element={<div data-testid="tables-content">Tables Content</div>} />
          <Route path="bookings/*" element={<div data-testid="bookings-content">Bookings Content</div>} />
          <Route path="customers/*" element={<div data-testid="customers-content">Customers Content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
};

describe('Layout Component', () => {
  describe('Rendering', () => {
    it('should render the layout with sidebar and main content area', () => {
      renderWithRouter('/');
      
      // Check for mobile sidebar (hidden by default)
      expect(screen.getByLabelText('Mobile navigation sidebar')).toBeInTheDocument();
      
      // Check for desktop sidebar
      expect(screen.getByLabelText('Desktop navigation sidebar')).toBeInTheDocument();
    });

    it('should render all navigation items', () => {
      renderWithRouter('/');
      
      // Each nav item appears in both mobile and desktop sidebars
      const dashboardLinks = screen.getAllByRole('link', { name: /dashboard/i });
      const restaurantsLinks = screen.getAllByRole('link', { name: /restaurants/i });
      const tablesLinks = screen.getAllByRole('link', { name: /tables/i });
      const bookingsLinks = screen.getAllByRole('link', { name: /bookings/i });
      const customersLinks = screen.getAllByRole('link', { name: /customers/i });
      
      expect(dashboardLinks.length).toBeGreaterThanOrEqual(1);
      expect(restaurantsLinks.length).toBeGreaterThanOrEqual(1);
      expect(tablesLinks.length).toBeGreaterThanOrEqual(1);
      expect(bookingsLinks.length).toBeGreaterThanOrEqual(1);
      expect(customersLinks.length).toBeGreaterThanOrEqual(1);
    });

    it('should render the application title "TableCheck"', () => {
      renderWithRouter('/');
      
      const titles = screen.getAllByText('TableCheck');
      expect(titles.length).toBeGreaterThanOrEqual(1);
    });

    it('should render navigation icons', () => {
      renderWithRouter('/');
      
      expect(screen.getAllByTestId('home-icon').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByTestId('restaurant-icon').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByTestId('table-icon').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByTestId('calendar-icon').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByTestId('users-icon').length).toBeGreaterThanOrEqual(1);
    });

    it('should render the Outlet for child routes', () => {
      renderWithRouter('/');
      
      expect(screen.getByTestId('dashboard-content')).toBeInTheDocument();
    });
  });

  describe('Active Route Highlighting', () => {
    it('should highlight Dashboard when on root path', () => {
      renderWithRouter('/');
      
      // Find the desktop sidebar nav links
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const dashboardLink = desktopSidebar.querySelector('a[href="/"]');
      
      expect(dashboardLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should highlight Restaurants when on /restaurants path', () => {
      renderWithRouter('/restaurants');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const restaurantsLink = desktopSidebar.querySelector('a[href="/restaurants"]');
      
      expect(restaurantsLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should highlight Restaurants when on /restaurants/123 subpath', () => {
      renderWithRouter('/restaurants/123');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const restaurantsLink = desktopSidebar.querySelector('a[href="/restaurants"]');
      
      expect(restaurantsLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should highlight Tables when on /tables path', () => {
      renderWithRouter('/tables');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const tablesLink = desktopSidebar.querySelector('a[href="/tables"]');
      
      expect(tablesLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should highlight Bookings when on /bookings path', () => {
      renderWithRouter('/bookings');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const bookingsLink = desktopSidebar.querySelector('a[href="/bookings"]');
      
      expect(bookingsLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should highlight Customers when on /customers path', () => {
      renderWithRouter('/customers');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const customersLink = desktopSidebar.querySelector('a[href="/customers"]');
      
      expect(customersLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should not highlight Dashboard when on other routes', () => {
      renderWithRouter('/restaurants');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const dashboardLink = desktopSidebar.querySelector('a[href="/"]');
      
      expect(dashboardLink).not.toHaveClass('bg-primary-50');
      expect(dashboardLink).toHaveClass('text-gray-700');
    });
  });

  describe('Page Title', () => {
    it('should display "Dashboard" title on root path', () => {
      renderWithRouter('/');
      
      const header = screen.getByRole('banner');
      expect(header).toHaveTextContent('Dashboard');
    });

    it('should display "Restaurants" title on restaurants path', () => {
      renderWithRouter('/restaurants');
      
      const header = screen.getByRole('banner');
      expect(header).toHaveTextContent('Restaurants');
    });

    it('should display "Tables" title on tables path', () => {
      renderWithRouter('/tables');
      
      const header = screen.getByRole('banner');
      expect(header).toHaveTextContent('Tables');
    });

    it('should display "Bookings" title on bookings path', () => {
      renderWithRouter('/bookings');
      
      const header = screen.getByRole('banner');
      expect(header).toHaveTextContent('Bookings');
    });

    it('should display "Customers" title on customers path', () => {
      renderWithRouter('/customers');
      
      const header = screen.getByRole('banner');
      expect(header).toHaveTextContent('Customers');
    });

    it('should display correct title on nested routes', () => {
      renderWithRouter('/restaurants/123/edit');
      
      const header = screen.getByRole('banner');
      expect(header).toHaveTextContent('Restaurants');
    });
  });

  describe('Mobile Sidebar Toggle', () => {
    it('should have mobile sidebar hidden by default', () => {
      renderWithRouter('/');
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('-translate-x-full');
    });

    it('should open mobile sidebar when menu button is clicked', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('translate-x-0');
    });

    it('should close mobile sidebar when close button is clicked', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Open sidebar first
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      // Close sidebar
      const closeButton = screen.getByRole('button', { name: /close sidebar/i });
      await user.click(closeButton);
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('-translate-x-full');
    });

    it('should close mobile sidebar when overlay is clicked', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Open sidebar first
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      // Click overlay
      const overlay = document.querySelector('[aria-hidden="true"]');
      fireEvent.click(overlay);
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('-translate-x-full');
    });

    it('should close mobile sidebar when a navigation link is clicked', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Open sidebar first
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      // Click a nav link in mobile sidebar
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      const restaurantsLink = mobileSidebar.querySelector('a[href="/restaurants"]');
      await user.click(restaurantsLink);
      
      expect(mobileSidebar).toHaveClass('-translate-x-full');
    });

    it('should show overlay when mobile sidebar is open', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Initially no overlay
      expect(document.querySelector('[aria-hidden="true"]')).not.toBeInTheDocument();
      
      // Open sidebar
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      // Overlay should be present
      const overlay = document.querySelector('[aria-hidden="true"]');
      expect(overlay).toBeInTheDocument();
      expect(overlay).toHaveClass('bg-gray-600', 'bg-opacity-75');
    });
  });

  describe('Desktop Sidebar Collapse', () => {
    it('should have desktop sidebar expanded by default', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      expect(desktopSidebar).toHaveClass('w-64');
    });

    it('should collapse desktop sidebar when collapse button is clicked', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      const collapseButton = screen.getByRole('button', { name: /collapse sidebar/i });
      await user.click(collapseButton);
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      expect(desktopSidebar).toHaveClass('w-20');
    });

    it('should expand desktop sidebar when expand button is clicked', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Collapse first
      const collapseButton = screen.getByRole('button', { name: /collapse sidebar/i });
      await user.click(collapseButton);
      
      // Expand
      const expandButton = screen.getByRole('button', { name: /expand sidebar/i });
      await user.click(expandButton);
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      expect(desktopSidebar).toHaveClass('w-64');
    });

    it('should hide navigation text when sidebar is collapsed', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Collapse sidebar
      const collapseButton = screen.getByRole('button', { name: /collapse sidebar/i });
      await user.click(collapseButton);
      
      // Check that nav item names are hidden (they have sr-only class when collapsed)
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const navItems = desktopSidebar.querySelectorAll('nav a span');
      
      navItems.forEach(span => {
        expect(span).toHaveClass('sr-only');
      });
    });

    it('should show navigation text when sidebar is expanded', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const navItems = desktopSidebar.querySelectorAll('nav a span');
      
      navItems.forEach(span => {
        expect(span).not.toHaveClass('sr-only');
      });
    });

    it('should rotate collapse icon when sidebar is collapsed', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      const collapseButton = screen.getByRole('button', { name: /collapse sidebar/i });
      await user.click(collapseButton);
      
      const chevronIcon = screen.getAllByTestId('chevron-icon')[0];
      expect(chevronIcon).toHaveClass('rotate-180');
    });
  });

  describe('Navigation Links', () => {
    it('should have correct href for Dashboard', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const dashboardLink = desktopSidebar.querySelector('a[href="/"]');
      
      expect(dashboardLink).toHaveAttribute('href', '/');
    });

    it('should have correct href for Restaurants', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const restaurantsLink = desktopSidebar.querySelector('a[href="/restaurants"]');
      
      expect(restaurantsLink).toHaveAttribute('href', '/restaurants');
    });

    it('should have correct href for Tables', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const tablesLink = desktopSidebar.querySelector('a[href="/tables"]');
      
      expect(tablesLink).toHaveAttribute('href', '/tables');
    });

    it('should have correct href for Bookings', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const bookingsLink = desktopSidebar.querySelector('a[href="/bookings"]');
      
      expect(bookingsLink).toHaveAttribute('href', '/bookings');
    });

    it('should have correct href for Customers', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const customersLink = desktopSidebar.querySelector('a[href="/customers"]');
      
      expect(customersLink).toHaveAttribute('href', '/customers');
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label on mobile sidebar', () => {
      renderWithRouter('/');
      
      expect(screen.getByLabelText('Mobile navigation sidebar')).toBeInTheDocument();
    });

    it('should have proper aria-label on desktop sidebar', () => {
      renderWithRouter('/');
      
      expect(screen.getByLabelText('Desktop navigation sidebar')).toBeInTheDocument();
    });

    it('should have proper aria-label on menu button', () => {
      renderWithRouter('/');
      
      expect(screen.getByRole('button', { name: /open sidebar/i })).toBeInTheDocument();
    });

    it('should have proper aria-label on close button', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Open sidebar to make close button visible
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      expect(screen.getByRole('button', { name: /close sidebar/i })).toBeInTheDocument();
    });

    it('should have aria-hidden on overlay', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      const overlay = document.querySelector('[aria-hidden="true"]');
      expect(overlay).toHaveAttribute('aria-hidden', 'true');
    });

    it('should have banner role on header', () => {
      renderWithRouter('/');
      
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should have main role on content area', () => {
      renderWithRouter('/');
      
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('should have navigation role in sidebar', () => {
      renderWithRouter('/');
      
      const navElements = screen.getAllByRole('navigation');
      expect(navElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Responsive Behavior', () => {
    it('should have lg:hidden class on mobile sidebar', () => {
      renderWithRouter('/');
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('lg:hidden');
    });

    it('should have hidden lg:flex class on desktop sidebar', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      expect(desktopSidebar).toHaveClass('hidden', 'lg:flex');
    });

    it('should have lg:hidden class on mobile menu button', () => {
      renderWithRouter('/');
      
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      expect(menuButton).toHaveClass('lg:hidden');
    });
  });

  describe('Content Rendering', () => {
    it('should render Dashboard content on root path', () => {
      renderWithRouter('/');
      
      expect(screen.getByTestId('dashboard-content')).toBeInTheDocument();
    });

    it('should render Restaurants content on restaurants path', () => {
      renderWithRouter('/restaurants');
      
      expect(screen.getByTestId('restaurants-content')).toBeInTheDocument();
    });

    it('should render Tables content on tables path', () => {
      renderWithRouter('/tables');
      
      expect(screen.getByTestId('tables-content')).toBeInTheDocument();
    });

    it('should render Bookings content on bookings path', () => {
      renderWithRouter('/bookings');
      
      expect(screen.getByTestId('bookings-content')).toBeInTheDocument();
    });

    it('should render Customers content on customers path', () => {
      renderWithRouter('/customers');
      
      expect(screen.getByTestId('customers-content')).toBeInTheDocument();
    });
  });

  describe('State Management', () => {
    it('should maintain sidebar open state independently of route changes', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Open mobile sidebar
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      await user.click(menuButton);
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('translate-x-0');
    });

    it('should maintain collapsed state independently of navigation', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      // Collapse desktop sidebar
      const collapseButton = screen.getByRole('button', { name: /collapse sidebar/i });
      await user.click(collapseButton);
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      expect(desktopSidebar).toHaveClass('w-20');
      
      // Navigate to different page
      const restaurantsLink = desktopSidebar.querySelector('a[href="/restaurants"]');
      await user.click(restaurantsLink);
      
      // Sidebar should still be collapsed
      expect(desktopSidebar).toHaveClass('w-20');
    });
  });

  describe('Edge Cases', () => {
    it('should handle unknown routes gracefully', () => {
      renderWithRouter('/unknown-route');
      
      // Should still render layout
      expect(screen.getByLabelText('Desktop navigation sidebar')).toBeInTheDocument();
      
      // Should default to Dashboard title
      const header = screen.getByRole('banner');
      expect(header).toHaveTextContent('Dashboard');
    });

    it('should handle deeply nested routes', () => {
      renderWithRouter('/restaurants/123/tables/456/edit');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const restaurantsLink = desktopSidebar.querySelector('a[href="/restaurants"]');
      
      expect(restaurantsLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should handle routes with query parameters', () => {
      renderWithRouter('/bookings?date=2024-01-01');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const bookingsLink = desktopSidebar.querySelector('a[href="/bookings"]');
      
      expect(bookingsLink).toHaveClass('bg-primary-50', 'text-primary-700');
    });

    it('should handle rapid sidebar toggle clicks', async () => {
      const user = userEvent.setup();
      renderWithRouter('/');
      
      const menuButton = screen.getByRole('button', { name: /open sidebar/i });
      
      // Rapid clicks
      await user.click(menuButton);
      await user.click(screen.getByRole('button', { name: /close sidebar/i }));
      await user.click(menuButton);
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('translate-x-0');
    });
  });

  describe('CSS Classes and Styling', () => {
    it('should apply correct background color to layout', () => {
      renderWithRouter('/');
      
      const layoutContainer = document.querySelector('.min-h-screen');
      expect(layoutContainer).toHaveClass('bg-gray-50');
    });

    it('should apply shadow to sidebar', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      expect(desktopSidebar).toHaveClass('shadow-lg');
    });

    it('should apply transition classes to mobile sidebar', () => {
      renderWithRouter('/');
      
      const mobileSidebar = screen.getByLabelText('Mobile navigation sidebar');
      expect(mobileSidebar).toHaveClass('transition-transform', 'duration-300', 'ease-in-out');
    });

    it('should apply hover styles to navigation links', () => {
      renderWithRouter('/');
      
      const desktopSidebar = screen.getByLabelText('Desktop navigation sidebar');
      const navLinks = desktopSidebar.querySelectorAll('nav a');
      
      navLinks.forEach(link => {
        expect(link).toHaveClass('hover:bg-gray-50');
      });
    });
  });
});