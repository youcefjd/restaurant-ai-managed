import axios from 'axios';

// Mock axios before importing the module
jest.mock('axios', () => {
  const mockAxiosInstance = {
    interceptors: {
      request: {
        use: jest.fn(),
      },
      response: {
        use: jest.fn(),
      },
    },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
  };

  return {
    create: jest.fn(() => mockAxiosInstance),
    default: {
      create: jest.fn(() => mockAxiosInstance),
    },
  };
});

// Mock import.meta.env
const mockEnv = {
  VITE_API_BASE_URL: 'http://test-api.com',
  DEV: false,
};

// Store original import.meta
const originalImportMeta = global.importMeta;

beforeAll(() => {
  // Setup import.meta mock
  Object.defineProperty(global, 'import', {
    value: { meta: { env: mockEnv } },
    writable: true,
  });
});

afterAll(() => {
  if (originalImportMeta) {
    Object.defineProperty(global, 'import', {
      value: originalImportMeta,
      writable: true,
    });
  }
});

describe('API Client', () => {
  let mockAxiosInstance;
  let requestInterceptorSuccess;
  let requestInterceptorError;
  let responseInterceptorSuccess;
  let responseInterceptorError;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    console.log = jest.fn();
    console.error = jest.fn();

    // Get the mock instance
    mockAxiosInstance = axios.create();

    // Capture interceptor callbacks
    mockAxiosInstance.interceptors.request.use.mockImplementation((success, error) => {
      requestInterceptorSuccess = success;
      requestInterceptorError = error;
    });

    mockAxiosInstance.interceptors.response.use.mockImplementation((success, error) => {
      responseInterceptorSuccess = success;
      responseInterceptorError = error;
    });
  });

  describe('axios.create configuration', () => {
    it('should create axios instance with correct base configuration', () => {
      // Re-import to trigger axios.create
      jest.isolateModules(() => {
        require('./client');
      });

      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          timeout: 30000,
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
        })
      );
    });

    it('should use default baseURL when VITE_API_BASE_URL is not set', () => {
      const originalUrl = mockEnv.VITE_API_BASE_URL;
      mockEnv.VITE_API_BASE_URL = '';

      jest.isolateModules(() => {
        require('./client');
      });

      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
        })
      );

      mockEnv.VITE_API_BASE_URL = originalUrl;
    });

    it('should register request and response interceptors', () => {
      jest.isolateModules(() => {
        require('./client');
      });

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('Request Interceptor', () => {
    beforeEach(() => {
      jest.isolateModules(() => {
        require('./client');
      });
    });

    describe('Success Handler', () => {
      it('should add Authorization header when auth token exists in localStorage', () => {
        // Arrange
        const mockTOKEN_REDACTED;
        localStorage.setItem('authToken', mockToken);
        const config = {
          headers: {},
          method: 'get',
          url: '/api/test',
        };

        // Act
        const result = requestInterceptorSuccess(config);

        // Assert
        expect(result.headers.Authorization).toBe(`Bearer ${mockToken}`);
      });

      it('should not add Authorization header when no auth token exists', () => {
        // Arrange
        const config = {
          headers: {},
          method: 'get',
          url: '/api/test',
        };

        // Act
        const result = requestInterceptorSuccess(config);

        // Assert
        expect(result.headers.Authorization).toBeUndefined();
      });

      it('should return config unchanged except for auth header', () => {
        // Arrange
        const config = {
          headers: { 'Custom-Header': 'value' },
          method: 'post',
          url: '/api/users',
          data: { name: 'test' },
          params: { page: 1 },
        };

        // Act
        const result = requestInterceptorSuccess(config);

        // Assert
        expect(result.method).toBe('post');
        expect(result.url).toBe('/api/users');
        expect(result.data).toEqual({ name: 'test' });
        expect(result.params).toEqual({ page: 1 });
        expect(result.headers['Custom-Header']).toBe('value');
      });

      it('should log request in development mode', () => {
        // Arrange
        mockEnv.DEV = true;
        const config = {
          headers: {},
          method: 'get',
          url: '/api/test',
          params: { id: 1 },
          data: null,
        };

        // Act
        requestInterceptorSuccess(config);

        // Assert
        expect(console.log).toHaveBeenCalledWith(
          '[API Request] GET /api/test',
          expect.objectContaining({
            params: { id: 1 },
            data: null,
          })
        );

        mockEnv.DEV = false;
      });

      it('should not log request in production mode', () => {
        // Arrange
        mockEnv.DEV = false;
        const config = {
          headers: {},
          method: 'get',
          url: '/api/test',
        };

        // Act
        requestInterceptorSuccess(config);

        // Assert
        expect(console.log).not.toHaveBeenCalled();
      });

      it('should handle undefined method gracefully', () => {
        // Arrange
        mockEnv.DEV = true;
        const config = {
          headers: {},
          url: '/api/test',
        };

        // Act
        const result = requestInterceptorSuccess(config);

        // Assert
        expect(result).toBeDefined();

        mockEnv.DEV = false;
      });
    });

    describe('Error Handler', () => {
      it('should log error and reject promise', async () => {
        // Arrange
        const error = new Error('Network error');

        // Act & Assert
        await expect(requestInterceptorError(error)).rejects.toThrow('Network error');
        expect(console.error).toHaveBeenCalledWith('[API Request Error]', error);
      });

      it('should preserve error object when rejecting', async () => {
        // Arrange
        const error = new Error('Custom error');
        error.code = 'NETWORK_ERROR';

        // Act
        try {
          await requestInterceptorError(error);
        } catch (e) {
          // Assert
          expect(e).toBe(error);
          expect(e.code).toBe('NETWORK_ERROR');
        }
      });
    });
  });

  describe('Response Interceptor', () => {
    beforeEach(() => {
      jest.isolateModules(() => {
        require('./client');
      });
    });

    describe('Success Handler', () => {
      it('should return response unchanged', () => {
        // Arrange
        const response = {
          status: 200,
          data: { id: 1, name: 'Test' },
          config: {
            method: 'get',
            url: '/api/test',
          },
        };

        // Act
        const result = responseInterceptorSuccess(response);

        // Assert
        expect(result).toBe(response);
      });

      it('should log response in development mode', () => {
        // Arrange
        mockEnv.DEV = true;
        const response = {
          status: 200,
          data: { success: true },
          config: {
            method: 'post',
            url: '/api/users',
          },
        };

        // Act
        responseInterceptorSuccess(response);

        // Assert
        expect(console.log).toHaveBeenCalledWith(
          '[API Response] POST /api/users',
          expect.objectContaining({
            status: 200,
            data: { success: true },
          })
        );

        mockEnv.DEV = false;
      });

      it('should not log response in production mode', () => {
        // Arrange
        mockEnv.DEV = false;
        const response = {
          status: 200,
          data: {},
          config: {
            method: 'get',
            url: '/api/test',
          },
        };

        // Act
        responseInterceptorSuccess(response);

        // Assert
        expect(console.log).not.toHaveBeenCalled();
      });
    });

    describe('Error Handler', () => {
      describe('400 Bad Request', () => {
        it('should return error with detail message from response', async () => {
          // Arrange
          const error = {
            response: {
              status: 400,
              data: { detail: 'Email is required' },
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('Email is required');
            expect(e.status).toBe(400);
          }
        });

        it('should return default message when no detail provided', async () => {
          // Arrange
          const error = {
            response: {
              status: 400,
              data: {},
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('Invalid request. Please check your input.');
          }
        });
      });

      describe('401 Unauthorized', () => {
        it('should return authentication error message', async () => {
          // Arrange
          localStorage.setItem('authToken', 'old-token');
          const error = {
            response: {
              status: 401,
              data: {},
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('Authentication required. Please log in.');
            expect(e.status).toBe(401);
          }
        });

        it('should clear auth token from localStorage', async () => {
          // Arrange
          localStorage.setItem('authToken', 'old-token');
          const error = {
            response: {
              status: 401,
              data: {},
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(localStorage.getItem('authToken')).toBeNull();
          }
        });
      });

      describe('403 Forbidden', () => {
        it('should return permission error message', async () => {
          // Arrange
          const error = {
            response: {
              status: 403,
              data: {},
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('You do not have permission to perform this action.');
            expect(e.status).toBe(403);
          }
        });
      });

      describe('404 Not Found', () => {
        it('should return detail message from response', async () => {
          // Arrange
          const error = {
            response: {
              status: 404,
              data: { detail: 'User not found' },
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('User not found');
          }
        });

        it('should return default message when no detail provided', async () => {
          // Arrange
          const error = {
            response: {
              status: 404,
              data: {},
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('The requested resource was not found.');
          }
        });
      });

      describe('422 Validation Error', () => {
        it('should format validation errors array from FastAPI', async () => {
          // Arrange
          const error = {
            response: {
              status: 422,
              data: {
                detail: [
                  { loc: ['body', 'email'], msg: 'invalid email format' },
                  { loc: ['body', 'password'], msg: 'too short' },
                ],
              },
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('body.email: invalid email format, body.PASSWORD_REDACTED short');
          }
        });

        it('should handle validation error without loc', async () => {
          // Arrange
          const error = {
            response: {
              status: 422,
              data: {
                detail: [{ msg: 'validation failed' }],
              },
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toContain('validation failed');
          }
        });

        it('should return default message when detail is not an array', async () => {
          // Arrange
          const error = {
            response: {
              status: 422,
              data: { detail: 'Some string error' },
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('Validation error. Please check your input.');
          }
        });

        it('should return default message when detail is missing', async () => {
          // Arrange
          const error = {
            response: {
              status: 422,
              data: {},
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('Validation error. Please check your input.');
          }
        });
      });

      describe('429 Too Many Requests', () => {
        it('should return rate limit error message', async () => {
          // Arrange
          const error = {
            response: {
              status: 429,
              data: {},
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('Too many requests. Please try again later.');
            expect(e.status).toBe(429);
          }
        });
      });

      describe('500 Internal Server Error', () => {
        it('should return default error message for unhandled status codes', async () => {
          // Arrange
          const error = {
            response: {
              status: 500,
              data: { error: 'Internal server error' },
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.status).toBe(500);
            expect(e.data).toEqual({ error: 'Internal server error' });
          }
        });
      });

      describe('Network Errors (no response)', () => {
        it('should handle network errors without response', async () => {
          // Arrange
          const error = new Error('Network Error');

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.message).toBe('An unexpected error occurred');
            expect(e.status).toBeNull();
            expect(e.data).toBeNull();
          }
        });

        it('should handle timeout errors', async () => {
          // Arrange
          const error = {
            code: 'ECONNABORTED',
            message: 'timeout of 30000ms exceeded',
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e.status).toBeNull();
          }
        });
      });

      describe('Error Response Structure', () => {
        it('should include status, message, and data in error response', async () => {
          // Arrange
          const error = {
            response: {
              status: 400,
              data: { detail: 'Bad request', extra: 'info' },
            },
          };

          // Act
          try {
            await responseInterceptorError(error);
          } catch (e) {
            // Assert
            expect(e).toHaveProperty('message');
            expect(e).toHaveProperty('status');
            expect(e).toHaveProperty('data');
            expect(e.data).toEqual({ detail: 'Bad request', extra: 'info' });
          }
        });
      });
    });
  });

  describe('Edge Cases', () => {
    beforeEach(() => {
      jest.isolateModules(() => {
        require('./client');
      });
    });

    it('should handle empty localStorage gracefully', () => {
      // Arrange
      localStorage.clear();
      const config = { headers: {} };

      // Act
      const result = requestInterceptorSuccess(config);

      // Assert
      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should handle null auth token', () => {
      // Arrange
      localStorage.setItem('authToken', '');
      const config = { headers: {} };

      // Act
      const result = requestInterceptorSuccess(config);

      // Assert
      expect(result.headers.Authorization).toBeUndefined();
    });

    it('should handle response with empty data', () => {
      // Arrange
      const response = {
        status: 204,
        data: null,
        config: { method: 'delete', url: '/api/test' },
      };

      // Act
      const result = responseInterceptorSuccess(response);

      // Assert
      expect(result.data).toBeNull();
    });

    it('should handle validation error with empty array', async () => {
      // Arrange
      const error = {
        response: {
          status: 422,
          data: { detail: [] },
        },
      };

      // Act
      try {
        await responseInterceptorError(error);
      } catch (e) {
        // Assert
        expect(e.message).toBe('');
      }
    });

    it('should handle validation error with single item', async () => {
      // Arrange
      const error = {
        response: {
          status: 422,
          data: {
            detail: [{ loc: ['query', 'page'], msg: 'must be positive' }],
          },
        },
      };

      // Act
      try {
        await responseInterceptorError(error);
      } catch (e) {
        // Assert
        expect(e.message).toBe('query.page: must be positive');
      }
    });
  });
});

describe('API Client Export', () => {
  it('should export apiClient as default', () => {
    jest.isolateModules(() => {
      const clientModule = require('./client');
      expect(clientModule.default).toBeDefined();
    });
  });
});