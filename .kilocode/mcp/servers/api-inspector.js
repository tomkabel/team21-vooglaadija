#!/usr/bin/env node

/**
 * Cobalt API Inspector MCP Server
 * Provides tools for inspecting and validating API services
 * 
 * DEPENDENCY: Requires @modelcontextprotocol/sdk installed at project root
 * Install: pnpm add -D @modelcontextprotocol/sdk
 * Or run: ./.kilocode/setup-mcp.sh
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Server configuration
const CONFIG_PATH = path.join(process.cwd(), 'api', 'src', 'services');

class ApiInspectorServer {
  constructor() {
    this.server = new Server(
      {
        name: 'cobalt-api-inspector',
        version: '1.0.0'
      },
      {
        capabilities: {
          tools: {}
        }
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'list_services',
            description: 'List all available API services in the Cobalt project',
            inputSchema: {
              type: 'object',
              properties: {
                includeInternal: {
                  type: 'boolean',
                  description: 'Include internal utility services',
                  default: false
                }
              }
            }
          },
          {
            name: 'get_service_info',
            description: 'Get detailed information about a specific service',
            inputSchema: {
              type: 'object',
              properties: {
                serviceName: {
                  type: 'string',
                  description: 'Name of the service to inspect'
                }
              },
              required: ['serviceName']
            }
          },
          {
            name: 'validate_url',
            description: 'Validate a URL format and check if it matches Cobalt URL patterns',
            inputSchema: {
              type: 'object',
              properties: {
                url: {
                  type: 'string',
                  description: 'URL to validate'
                },
                serviceType: {
                  type: 'string',
                  description: 'Expected service type (youtube, tiktok, etc.)',
                  enum: ['youtube', 'tiktok', 'twitter', 'reddit', 'bilibili', 'soundcloud']
                }
              },
              required: ['url']
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'list_services':
            return await this.listServices(args);
          case 'get_service_info':
            return await this.getServiceInfo(args);
          case 'validate_url':
            return await this.validateUrl(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async listServices(args = {}) {
    const services = [
      { name: 'youtube', description: 'YouTube video and audio downloader', status: 'active' },
      { name: 'tiktok', description: 'TikTok video downloader', status: 'active' },
      { name: 'twitter', description: 'Twitter/X media downloader', status: 'active' },
      { name: 'reddit', description: 'Reddit media downloader', status: 'active' },
      { name: 'bilibili', description: 'Bilibili video downloader', status: 'active' },
      { name: 'soundcloud', description: 'SoundCloud audio downloader', status: 'active' }
    ];

    if (!args.includeInternal) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ services: services.filter(s => s.status === 'active') }, null, 2)
          }
        ]
      };
    }

    const internalServices = [
      { name: 'stream', description: 'Stream processing utilities', status: 'internal' },
      { name: 'cache', description: 'Caching service', status: 'internal' },
      { name: 'rate-limiter', description: 'Rate limiting service', status: 'internal' }
    ];

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ 
            services: [...services, ...internalServices] 
          }, null, 2)
        }
      ]
    };
  }

  async getServiceInfo(args) {
    const { serviceName } = args;
    
    const serviceInfo = {
      youtube: {
        name: 'YouTube',
        description: 'Download videos and audio from YouTube',
        endpoints: ['/api/youtube', '/api/youtube/audio'],
        formats: ['mp4', 'webm', 'mp3', 'm4a'],
        quality: ['best', 'worst', '1080p', '720p', '480p'],
        requiresAuth: false
      },
      tiktok: {
        name: 'TikTok',
        description: 'Download videos from TikTok without watermark',
        endpoints: ['/api/tiktok', '/api/tiktok/nowatermark'],
        formats: ['mp4'],
        quality: ['best', 'worst'],
        requiresAuth: false
      },
      twitter: {
        name: 'Twitter/X',
        description: 'Download media from Twitter/X posts',
        endpoints: ['/api/twitter'],
        formats: ['mp4', 'jpg', 'png'],
        quality: ['best', 'worst'],
        requiresAuth: false
      },
      reddit: {
        name: 'Reddit',
        description: 'Download media from Reddit posts',
        endpoints: ['/api/reddit'],
        formats: ['mp4', 'gif', 'jpg', 'png'],
        quality: ['best', 'worst'],
        requiresAuth: false
      },
      bilibili: {
        name: 'Bilibili',
        description: 'Download videos from Bilibili',
        endpoints: ['/api/bilibili'],
        formats: ['mp4', 'flv'],
        quality: ['best', 'worst', '1080p', '720p', '480p'],
        requiresAuth: false
      },
      soundcloud: {
        name: 'SoundCloud',
        description: 'Download audio from SoundCloud',
        endpoints: ['/api/soundcloud'],
        formats: ['mp3', 'ogg', 'flac'],
        quality: ['best', 'worst'],
        requiresAuth: false
      }
    };

    const info = serviceInfo[serviceName.toLowerCase()];
    
    if (!info) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Service "${serviceName}" not found. Available services: ${Object.keys(serviceInfo).join(', ')}`
      );
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(info, null, 2)
        }
      ]
    };
  }

  async validateUrl(args) {
    const { url, serviceType } = args;
    
    const patterns = {
      youtube: /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/,
      tiktok: /^https?:\/\/(www\.)?tiktok\.com\/.+/,
      twitter: /^https?:\/\/(www\.)?(twitter\.com|x\.com)\/.+/,
      reddit: /^https?:\/\/(www\.)?reddit\.com\/.+/,
      bilibili: /^https?:\/\/(www\.)?bilibili\.com\/.+/,
      soundcloud: /^https?:\/\/(www\.)?soundcloud\.com\/.+/
    };

    // Basic URL validation
    let isValidUrl = false;
    try {
      new URL(url);
      isValidUrl = true;
    } catch {
      isValidUrl = false;
    }

    if (!isValidUrl) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              valid: false,
              error: 'Invalid URL format'
            }, null, 2)
          }
        ]
      };
    }

    // Service-specific validation
    const detectedServices = [];
    for (const [service, pattern] of Object.entries(patterns)) {
      if (pattern.test(url)) {
        detectedServices.push(service);
      }
    }

    const result = {
      valid: true,
      url: url,
      detectedServices: detectedServices,
      matchesExpectedService: serviceType ? detectedServices.includes(serviceType) : null
    };

    if (serviceType && !detectedServices.includes(serviceType)) {
      result.warning = `URL does not match expected service type "${serviceType}". Detected: ${detectedServices.join(', ') || 'unknown'}`;
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Cobalt API Inspector MCP Server running on stdio');
  }
}

// Run the server
const server = new ApiInspectorServer();
server.run().catch(console.error);
