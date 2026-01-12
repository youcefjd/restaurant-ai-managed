/**
 * Tests for postcss.config.js
 * 
 * This is a configuration file that exports a static object.
 * We test that the configuration structure is correct and contains
 * the expected plugins.
 */

import postcssConfig from './postcss.config.js';

describe('postcss.config.js', () => {
  describe('Configuration Structure', () => {
    it('should export a default configuration object', () => {
      // Arrange & Act
      const config = postcssConfig;

      // Assert
      expect(config).toBeDefined();
      expect(typeof config).toBe('object');
    });

    it('should have a plugins property', () => {
      // Arrange & Act
      const config = postcssConfig;

      // Assert
      expect(config).toHaveProperty('plugins');
      expect(typeof config.plugins).toBe('object');
    });

    it('should not have null or undefined as the config', () => {
      // Arrange & Act
      const config = postcssConfig;

      // Assert
      expect(config).not.toBeNull();
      expect(config).not.toBeUndefined();
    });
  });

  describe('Plugins Configuration', () => {
    it('should include tailwindcss plugin', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(plugins).toHaveProperty('tailwindcss');
    });

    it('should include autoprefixer plugin', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(plugins).toHaveProperty('autoprefixer');
    });

    it('should have tailwindcss configured as an empty object', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(plugins.tailwindcss).toEqual({});
    });

    it('should have autoprefixer configured as an empty object', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(plugins.autoprefixer).toEqual({});
    });

    it('should have exactly 2 plugins configured', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;
      const pluginCount = Object.keys(plugins).length;

      // Assert
      expect(pluginCount).toBe(2);
    });

    it('should have plugins in the correct order (tailwindcss before autoprefixer)', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;
      const pluginNames = Object.keys(plugins);

      // Assert
      expect(pluginNames[0]).toBe('tailwindcss');
      expect(pluginNames[1]).toBe('autoprefixer');
    });
  });

  describe('Configuration Immutability', () => {
    it('should return the same configuration on multiple imports', () => {
      // Arrange
      const config1 = postcssConfig;
      const config2 = postcssConfig;

      // Act & Assert
      expect(config1).toBe(config2);
    });

    it('should have consistent plugin structure across accesses', () => {
      // Arrange
      const plugins1 = postcssConfig.plugins;
      const plugins2 = postcssConfig.plugins;

      // Act & Assert
      expect(plugins1).toBe(plugins2);
      expect(plugins1.tailwindcss).toEqual(plugins2.tailwindcss);
      expect(plugins1.autoprefixer).toEqual(plugins2.autoprefixer);
    });
  });

  describe('Edge Cases', () => {
    it('should not have any additional top-level properties', () => {
      // Arrange & Act
      const configKeys = Object.keys(postcssConfig);

      // Assert
      expect(configKeys).toEqual(['plugins']);
      expect(configKeys.length).toBe(1);
    });

    it('should not have nested plugins within tailwindcss', () => {
      // Arrange & Act
      const tailwindConfig = postcssConfig.plugins.tailwindcss;
      const tailwindKeys = Object.keys(tailwindConfig);

      // Assert
      expect(tailwindKeys.length).toBe(0);
    });

    it('should not have nested plugins within autoprefixer', () => {
      // Arrange & Act
      const autoprefixerConfig = postcssConfig.plugins.autoprefixer;
      const autoprefixerKeys = Object.keys(autoprefixerConfig);

      // Assert
      expect(autoprefixerKeys.length).toBe(0);
    });

    it('should be a plain object (not an instance of a class)', () => {
      // Arrange & Act
      const config = postcssConfig;

      // Assert
      expect(Object.getPrototypeOf(config)).toBe(Object.prototype);
    });

    it('should have plugins as a plain object', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(Object.getPrototypeOf(plugins)).toBe(Object.prototype);
    });
  });

  describe('Type Validation', () => {
    it('should have plugins property that is not an array', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(Array.isArray(plugins)).toBe(false);
    });

    it('should have plugins property that is not a function', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(typeof plugins).not.toBe('function');
    });

    it('should have tailwindcss value that is not null', () => {
      // Arrange & Act
      const { tailwindcss } = postcssConfig.plugins;

      // Assert
      expect(tailwindcss).not.toBeNull();
    });

    it('should have autoprefixer value that is not null', () => {
      // Arrange & Act
      const { autoprefixer } = postcssConfig.plugins;

      // Assert
      expect(autoprefixer).not.toBeNull();
    });
  });

  describe('Snapshot Testing', () => {
    it('should match the expected configuration snapshot', () => {
      // Arrange & Act
      const config = postcssConfig;

      // Assert
      expect(config).toMatchSnapshot();
    });

    it('should match the expected plugins snapshot', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert
      expect(plugins).toMatchSnapshot();
    });
  });

  describe('Configuration Validity for PostCSS', () => {
    it('should have a valid PostCSS configuration format', () => {
      // Arrange & Act
      const config = postcssConfig;

      // Assert - PostCSS expects an object with plugins property
      expect(config).toMatchObject({
        plugins: expect.any(Object)
      });
    });

    it('should have plugin values that are valid (object or function)', () => {
      // Arrange & Act
      const { plugins } = postcssConfig;

      // Assert - Each plugin should be an object (options) or could be a function
      Object.values(plugins).forEach(pluginConfig => {
        expect(
          typeof pluginConfig === 'object' || typeof pluginConfig === 'function'
        ).toBe(true);
      });
    });
  });
});