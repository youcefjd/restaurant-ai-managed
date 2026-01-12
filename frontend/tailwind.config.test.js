/**
 * Tests for tailwind.config.js
 * 
 * This file tests the Tailwind CSS configuration for the restaurant admin dashboard.
 * Since tailwind.config.js is a configuration file (not executable code with functions),
 * we test the configuration object's structure, values, and completeness.
 */

import tailwindConfig from './tailwind.config.js';

describe('Tailwind Configuration', () => {
  describe('Configuration Structure', () => {
    it('should export a valid configuration object', () => {
      expect(tailwindConfig).toBeDefined();
      expect(typeof tailwindConfig).toBe('object');
    });

    it('should have content array with correct paths', () => {
      expect(tailwindConfig.content).toBeDefined();
      expect(Array.isArray(tailwindConfig.content)).toBe(true);
      expect(tailwindConfig.content).toContain('./index.html');
      expect(tailwindConfig.content).toContain('./src/**/*.{js,ts,jsx,tsx}');
    });

    it('should have darkMode set to class', () => {
      expect(tailwindConfig.darkMode).toBe('class');
    });

    it('should have theme.extend object', () => {
      expect(tailwindConfig.theme).toBeDefined();
      expect(tailwindConfig.theme.extend).toBeDefined();
      expect(typeof tailwindConfig.theme.extend).toBe('object');
    });
  });

  describe('Color Palette - Primary Colors', () => {
    const primaryColors = tailwindConfig.theme.extend.colors.primary;

    it('should have primary color palette defined', () => {
      expect(primaryColors).toBeDefined();
      expect(typeof primaryColors).toBe('object');
    });

    it('should have all standard shade levels (50-950)', () => {
      const expectedShades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'];
      expectedShades.forEach(shade => {
        expect(primaryColors[shade]).toBeDefined();
      });
    });

    it('should have valid hex color values for primary palette', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(primaryColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });

    it('should have warm orange/amber tones for restaurant theme', () => {
      // Primary 500 should be the main brand color (orange)
      expect(primaryColors['500']).toBe('#ff6b1a');
      // Lightest shade should be very light
      expect(primaryColors['50']).toBe('#fff8f1');
      // Darkest shade should be very dark
      expect(primaryColors['950']).toBe('#451a03');
    });

    it('should have progressively darker shades', () => {
      // Convert hex to brightness value for comparison
      const hexToBrightness = (hex) => {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return (r + g + b) / 3;
      };

      const brightness50 = hexToBrightness(primaryColors['50']);
      const brightness500 = hexToBrightness(primaryColors['500']);
      const brightness950 = hexToBrightness(primaryColors['950']);

      expect(brightness50).toBeGreaterThan(brightness500);
      expect(brightness500).toBeGreaterThan(brightness950);
    });
  });

  describe('Color Palette - Secondary Colors', () => {
    const secondaryColors = tailwindConfig.theme.extend.colors.secondary;

    it('should have secondary color palette defined', () => {
      expect(secondaryColors).toBeDefined();
      expect(typeof secondaryColors).toBe('object');
    });

    it('should have all standard shade levels (50-950)', () => {
      const expectedShades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'];
      expectedShades.forEach(shade => {
        expect(secondaryColors[shade]).toBeDefined();
      });
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(secondaryColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });

    it('should have cool slate tones for professional look', () => {
      expect(secondaryColors['50']).toBe('#f8fafc');
      expect(secondaryColors['500']).toBe('#64748b');
      expect(secondaryColors['950']).toBe('#020617');
    });
  });

  describe('Color Palette - Success Colors', () => {
    const successColors = tailwindConfig.theme.extend.colors.success;

    it('should have success color palette defined', () => {
      expect(successColors).toBeDefined();
      expect(typeof successColors).toBe('object');
    });

    it('should have all standard shade levels', () => {
      const expectedShades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'];
      expectedShades.forEach(shade => {
        expect(successColors[shade]).toBeDefined();
      });
    });

    it('should have green tones for confirmations', () => {
      expect(successColors['500']).toBe('#22c55e');
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(successColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });
  });

  describe('Color Palette - Warning Colors', () => {
    const warningColors = tailwindConfig.theme.extend.colors.warning;

    it('should have warning color palette defined', () => {
      expect(warningColors).toBeDefined();
      expect(typeof warningColors).toBe('object');
    });

    it('should have all standard shade levels', () => {
      const expectedShades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'];
      expectedShades.forEach(shade => {
        expect(warningColors[shade]).toBeDefined();
      });
    });

    it('should have amber tones for pending bookings', () => {
      expect(warningColors['500']).toBe('#f59e0b');
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(warningColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });
  });

  describe('Color Palette - Danger Colors', () => {
    const dangerColors = tailwindConfig.theme.extend.colors.danger;

    it('should have danger color palette defined', () => {
      expect(dangerColors).toBeDefined();
      expect(typeof dangerColors).toBe('object');
    });

    it('should have all standard shade levels', () => {
      const expectedShades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'];
      expectedShades.forEach(shade => {
        expect(dangerColors[shade]).toBeDefined();
      });
    });

    it('should have red tones for cancellations and errors', () => {
      expect(dangerColors['500']).toBe('#ef4444');
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(dangerColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });
  });

  describe('Color Palette - Info Colors', () => {
    const infoColors = tailwindConfig.theme.extend.colors.info;

    it('should have info color palette defined', () => {
      expect(infoColors).toBeDefined();
      expect(typeof infoColors).toBe('object');
    });

    it('should have all standard shade levels', () => {
      const expectedShades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'];
      expectedShades.forEach(shade => {
        expect(infoColors[shade]).toBeDefined();
      });
    });

    it('should have blue tones for information', () => {
      expect(infoColors['500']).toBe('#3b82f6');
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(infoColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });
  });

  describe('Booking Status Colors', () => {
    const bookingColors = tailwindConfig.theme.extend.colors.booking;

    it('should have booking status colors defined', () => {
      expect(bookingColors).toBeDefined();
      expect(typeof bookingColors).toBe('object');
    });

    it('should have all required booking statuses', () => {
      expect(bookingColors.pending).toBeDefined();
      expect(bookingColors.confirmed).toBeDefined();
      expect(bookingColors.cancelled).toBeDefined();
      expect(bookingColors.completed).toBeDefined();
      expect(bookingColors.noshow).toBeDefined();
    });

    it('should have correct colors for each booking status', () => {
      expect(bookingColors.pending).toBe('#f59e0b'); // Amber/warning
      expect(bookingColors.confirmed).toBe('#22c55e'); // Green/success
      expect(bookingColors.cancelled).toBe('#ef4444'); // Red/danger
      expect(bookingColors.completed).toBe('#6366f1'); // Indigo
      expect(bookingColors.noshow).toBe('#8b5cf6'); // Purple
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(bookingColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });

    it('should have exactly 5 booking statuses', () => {
      expect(Object.keys(bookingColors)).toHaveLength(5);
    });
  });

  describe('Table Status Colors', () => {
    const tableColors = tailwindConfig.theme.extend.colors.table;

    it('should have table status colors defined', () => {
      expect(tableColors).toBeDefined();
      expect(typeof tableColors).toBe('object');
    });

    it('should have all required table statuses', () => {
      expect(tableColors.available).toBeDefined();
      expect(tableColors.occupied).toBeDefined();
      expect(tableColors.reserved).toBeDefined();
      expect(tableColors.maintenance).toBeDefined();
    });

    it('should have correct colors for each table status', () => {
      expect(tableColors.available).toBe('#22c55e'); // Green
      expect(tableColors.occupied).toBe('#ef4444'); // Red
      expect(tableColors.reserved).toBe('#f59e0b'); // Amber
      expect(tableColors.maintenance).toBe('#6b7280'); // Gray
    });

    it('should have valid hex color values', () => {
      const hexColorRegex = /^#[0-9a-fA-F]{6}$/;
      Object.values(tableColors).forEach(color => {
        expect(color).toMatch(hexColorRegex);
      });
    });

    it('should have exactly 4 table statuses', () => {
      expect(Object.keys(tableColors)).toHaveLength(4);
    });
  });

  describe('Color Consistency', () => {
    it('should have booking.confirmed match success.500', () => {
      const bookingConfirmed = tailwindConfig.theme.extend.colors.booking.confirmed;
      const success500 = tailwindConfig.theme.extend.colors.success['500'];
      expect(bookingConfirmed).toBe(success500);
    });

    it('should have booking.cancelled match danger.500', () => {
      const bookingCancelled = tailwindConfig.theme.extend.colors.booking.cancelled;
      const danger500 = tailwindConfig.theme.extend.colors.danger['500'];
      expect(bookingCancelled).toBe(danger500);
    });

    it('should have booking.pending match warning.500', () => {
      const bookingPending = tailwindConfig.theme.extend.colors.booking.pending;
      const warning500 = tailwindConfig.theme.extend.colors.warning['500'];
      expect(bookingPending).toBe(warning500);
    });

    it('should have table.available match success.500', () => {
      const tableAvailable = tailwindConfig.theme.extend.colors.table.available;
      const success500 = tailwindConfig.theme.extend.colors.success['500'];
      expect(tableAvailable).toBe(success500);
    });

    it('should have table.occupied match danger.500', () => {
      const tableOccupied = tailwindConfig.theme.extend.colors.table.occupied;
      const danger500 = tailwindConfig.theme.extend.colors.danger['500'];
      expect(tableOccupied).toBe(danger500);
    });

    it('should have table.reserved match warning.500', () => {
      const tableReserved = tailwindConfig.theme.extend.colors.table.reserved;
      const warning500 = tailwindConfig.theme.extend.colors.warning['500'];
      expect(tableReserved).toBe(warning500);
    });
  });

  describe('Content Paths', () => {
    it('should include index.html', () => {
      expect(tailwindConfig.content).toContain('./index.html');
    });

    it('should include all JavaScript/TypeScript files in src', () => {
      expect(tailwindConfig.content).toContain('./src/**/*.{js,ts,jsx,tsx}');
    });

    it('should have exactly 2 content paths', () => {
      expect(tailwindConfig.content).toHaveLength(2);
    });
  });

  describe('Dark Mode Configuration', () => {
    it('should use class-based dark mode', () => {
      expect(tailwindConfig.darkMode).toBe('class');
    });

    it('should not use media-based dark mode', () => {
      expect(tailwindConfig.darkMode).not.toBe('media');
    });
  });

  describe('Edge Cases', () => {
    it('should not have undefined color values', () => {
      const colors = tailwindConfig.theme.extend.colors;
      
      const checkForUndefined = (obj, path = '') => {
        Object.entries(obj).forEach(([key, value]) => {
          const currentPath = path ? `${path}.${key}` : key;
          if (typeof value === 'object' && value !== null) {
            checkForUndefined(value, currentPath);
          } else {
            expect(value).not.toBeUndefined();
            expect(value).not.toBeNull();
          }
        });
      };

      checkForUndefined(colors);
    });

    it('should not have empty string color values', () => {
      const colors = tailwindConfig.theme.extend.colors;
      
      const checkForEmpty = (obj) => {
        Object.values(obj).forEach(value => {
          if (typeof value === 'object' && value !== null) {
            checkForEmpty(value);
          } else if (typeof value === 'string') {
            expect(value.length).toBeGreaterThan(0);
          }
        });
      };

      checkForEmpty(colors);
    });

    it('should have all color palettes as objects', () => {
      const colors = tailwindConfig.theme.extend.colors;
      const paletteKeys = ['primary', 'secondary', 'success', 'warning', 'danger', 'info', 'booking', 'table'];
      
      paletteKeys.forEach(key => {
        expect(typeof colors[key]).toBe('object');
        expect(colors[key]).not.toBeNull();
      });
    });
  });

  describe('Color Value Format Validation', () => {
    it('should have all colors in lowercase hex format', () => {
      const colors = tailwindConfig.theme.extend.colors;
      
      const checkHexFormat = (obj) => {
        Object.values(obj).forEach(value => {
          if (typeof value === 'object' && value !== null) {
            checkHexFormat(value);
          } else if (typeof value === 'string') {
            // Check it starts with # and is lowercase
            expect(value.startsWith('#')).toBe(true);
            expect(value).toBe(value.toLowerCase());
          }
        });
      };

      checkHexFormat(colors);
    });

    it('should have all hex colors with exactly 6 characters after #', () => {
      const colors = tailwindConfig.theme.extend.colors;
      
      const checkHexLength = (obj) => {
        Object.values(obj).forEach(value => {
          if (typeof value === 'object' && value !== null) {
            checkHexLength(value);
          } else if (typeof value === 'string' && value.startsWith('#')) {
            expect(value.length).toBe(7); // # + 6 hex characters
          }
        });
      };

      checkHexLength(colors);
    });
  });

  describe('Complete Color Palette Coverage', () => {
    it('should have exactly 8 color categories', () => {
      const colors = tailwindConfig.theme.extend.colors;
      const expectedCategories = ['primary', 'secondary', 'success', 'warning', 'danger', 'info', 'booking', 'table'];
      
      expect(Object.keys(colors)).toEqual(expect.arrayContaining(expectedCategories));
      expect(Object.keys(colors)).toHaveLength(expectedCategories.length);
    });

    it('should have 11 shades for each main color palette', () => {
      const mainPalettes = ['primary', 'secondary', 'success', 'warning', 'danger', 'info'];
      const colors = tailwindConfig.theme.extend.colors;
      
      mainPalettes.forEach(palette => {
        expect(Object.keys(colors[palette])).toHaveLength(11);
      });
    });
  });
});

describe('Configuration Export', () => {
  it('should be a default export', () => {
    // The config is imported as default export
    expect(tailwindConfig).toBeDefined();
  });

  it('should be a plain object (not a class instance)', () => {
    expect(tailwindConfig.constructor).toBe(Object);
  });

  it('should be serializable to JSON', () => {
    expect(() => JSON.stringify(tailwindConfig)).not.toThrow();
  });

  it('should maintain structure after JSON serialization', () => {
    const serialized = JSON.parse(JSON.stringify(tailwindConfig));
    expect(serialized.content).toEqual(tailwindConfig.content);
    expect(serialized.darkMode).toEqual(tailwindConfig.darkMode);
    expect(serialized.theme.extend.colors.primary['500']).toEqual(
      tailwindConfig.theme.extend.colors.primary['500']
    );
  });
});