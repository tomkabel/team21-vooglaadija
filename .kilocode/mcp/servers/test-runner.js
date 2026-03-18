#!/usr/bin/env node

/**
 * Cobalt Test Runner MCP Server
 * Provides tools for running tests and retrieving test results
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
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Test results cache
const testResultsCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

class TestRunnerServer {
  constructor() {
    this.server = new Server(
      {
        name: 'cobalt-test-runner',
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
            name: 'run_service_test',
            description: 'Run tests for a specific service or component',
            inputSchema: {
              type: 'object',
              properties: {
                service: {
                  type: 'string',
                  description: 'Service name to test (e.g., youtube, tiktok, api, web)',
                  enum: ['youtube', 'tiktok', 'twitter', 'reddit', 'bilibili', 'soundcloud', 'api', 'web', 'all']
                },
                testPattern: {
                  type: 'string',
                  description: 'Specific test pattern to match',
                  default: ''
                },
                coverage: {
                  type: 'boolean',
                  description: 'Generate coverage report',
                  default: false
                }
              },
              required: ['service']
            }
          },
          {
            name: 'get_test_results',
            description: 'Retrieve cached test results by ID',
            inputSchema: {
              type: 'object',
              properties: {
                resultId: {
                  type: 'string',
                  description: 'Test result ID from a previous run'
                },
                format: {
                  type: 'string',
                  description: 'Output format',
                  enum: ['summary', 'detailed', 'json'],
                  default: 'summary'
                }
              },
              required: ['resultId']
            }
          },
          {
            name: 'run_all_tests',
            description: 'Run all tests across the entire Cobalt project',
            inputSchema: {
              type: 'object',
              properties: {
                coverage: {
                  type: 'boolean',
                  description: 'Generate coverage report',
                  default: false
                },
                parallel: {
                  type: 'boolean',
                  description: 'Run tests in parallel',
                  default: true
                }
              }
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
          case 'run_service_test':
            return await this.runServiceTest(args);
          case 'get_test_results':
            return await this.getTestResults(args);
          case 'run_all_tests':
            return await this.runAllTests(args);
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

  async runServiceTest(args) {
    const { service, testPattern = '', coverage = false } = args;
    const resultId = `test-${service}-${Date.now()}`;

    // Determine test command based on service
    const testCommands = {
      youtube: { cmd: 'pnpm', args: ['--prefix', 'api', 'test', 'youtube'], cwd: process.cwd() },
      tiktok: { cmd: 'pnpm', args: ['--prefix', 'api', 'test', 'tiktok'], cwd: process.cwd() },
      twitter: { cmd: 'pnpm', args: ['--prefix', 'api', 'test', 'twitter'], cwd: process.cwd() },
      reddit: { cmd: 'pnpm', args: ['--prefix', 'api', 'test', 'reddit'], cwd: process.cwd() },
      bilibili: { cmd: 'pnpm', args: ['--prefix', 'api', 'test', 'bilibili'], cwd: process.cwd() },
      soundcloud: { cmd: 'pnpm', args: ['--prefix', 'api', 'test', 'soundcloud'], cwd: process.cwd() },
      api: { cmd: 'pnpm', args: ['--prefix', 'api', 'test'], cwd: process.cwd() },
      web: { cmd: 'pnpm', args: ['--prefix', 'web', 'test'], cwd: process.cwd() },
      all: { cmd: 'pnpm', args: ['test'], cwd: process.cwd() }
    };

    const testConfig = testCommands[service];
    if (!testConfig) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Unknown service: ${service}. Available services: ${Object.keys(testCommands).join(', ')}`
      );
    }

    // Add coverage flag if requested
    if (coverage) {
      testConfig.args.push('--coverage');
    }

    // Add test pattern if provided
    if (testPattern) {
      testConfig.args.push('--testNamePattern', testPattern);
    }

    // Execute test command
    const result = await this.executeCommand(testConfig.cmd, testConfig.args, testConfig.cwd);
    
    // Parse and cache results
    const parsedResult = this.parseTestResults(result.stdout, result.stderr, result.exitCode);
    parsedResult.resultId = resultId;
    parsedResult.service = service;
    parsedResult.timestamp = new Date().toISOString();
    parsedResult.coverage = coverage;

    testResultsCache.set(resultId, {
      data: parsedResult,
      timestamp: Date.now()
    });

    // Clean old cache entries
    this.cleanCache();

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            resultId: resultId,
            summary: parsedResult.summary,
            status: result.exitCode === 0 ? 'passed' : 'failed',
            duration: parsedResult.duration,
            testCount: parsedResult.testCount
          }, null, 2)
        }
      ]
    };
  }

  async getTestResults(args) {
    const { resultId, format = 'summary' } = args;

    const cached = testResultsCache.get(resultId);
    if (!cached) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Test results not found for ID: ${resultId}. Results are cached for 5 minutes.`
      );
    }

    const { data } = cached;

    if (format === 'json') {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data, null, 2)
          }
        ]
      };
    }

    if (format === 'detailed') {
      const output = this.formatDetailedResults(data);
      return {
        content: [
          {
            type: 'text',
            text: output
          }
        ]
      };
    }

    // Summary format
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            service: data.service,
            status: data.summary.failed > 0 ? 'failed' : 'passed',
            passed: data.summary.passed,
            failed: data.summary.failed,
            skipped: data.summary.skipped,
            duration: data.duration,
            timestamp: data.timestamp
          }, null, 2)
        }
      ]
    };
  }

  async runAllTests(args) {
    const { coverage = false, parallel = true } = args;
    const resultId = `test-all-${Date.now()}`;

    const testArgs = ['test'];
    if (coverage) testArgs.push('--coverage');
    if (!parallel) testArgs.push('--runInBand');

    const result = await this.executeCommand('pnpm', testArgs, process.cwd());
    
    const parsedResult = this.parseTestResults(result.stdout, result.stderr, result.exitCode);
    parsedResult.resultId = resultId;
    parsedResult.service = 'all';
    parsedResult.timestamp = new Date().toISOString();
    parsedResult.coverage = coverage;

    testResultsCache.set(resultId, {
      data: parsedResult,
      timestamp: Date.now()
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            resultId: resultId,
            summary: parsedResult.summary,
            status: result.exitCode === 0 ? 'passed' : 'failed',
            duration: parsedResult.duration,
            testCount: parsedResult.testCount,
            services: ['api', 'web']
          }, null, 2)
        }
      ]
    };
  }

  executeCommand(cmd, args, cwd) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      let stdout = '';
      let stderr = '';

      const child = spawn(cmd, args, {
        cwd,
        env: { ...process.env, FORCE_COLOR: '0' },
        shell: false
      });

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (exitCode) => {
        const duration = Date.now() - startTime;
        resolve({
          stdout,
          stderr,
          exitCode: exitCode || 0,
          duration
        });
      });

      child.on('error', (error) => {
        reject(new Error(`Failed to execute command: ${error.message}`));
      });
    });
  }

  parseTestResults(stdout, stderr, exitCode) {
    const result = {
      summary: {
        passed: 0,
        failed: 0,
        skipped: 0,
        total: 0
      },
      testCount: 0,
      duration: 0,
      failures: [],
      rawOutput: stdout + stderr
    };

    // Try to parse Jest results
    const jestMatch = stdout.match(/Tests:\s+(\d+)\s+passed,?\s*(?:(\d+)\s+failed,?)?\s*(?:(\d+)\s+skipped,?)?/);
    if (jestMatch) {
      result.summary.passed = parseInt(jestMatch[1]) || 0;
      result.summary.failed = parseInt(jestMatch[2]) || 0;
      result.summary.skipped = parseInt(jestMatch[3]) || 0;
      result.summary.total = result.summary.passed + result.summary.failed + result.summary.skipped;
      result.testCount = result.summary.total;
    }

    // Try to parse duration
    const durationMatch = stdout.match(/Time:\s+([\d.]+)\s*s/);
    if (durationMatch) {
      result.duration = parseFloat(durationMatch[1]) * 1000;
    }

    // Extract failure details
    if (result.summary.failed > 0) {
      const failureBlocks = stdout.split(/FAIL\s+/).slice(1);
      failureBlocks.forEach(block => {
        const lines = block.split('\n');
        const testFile = lines[0]?.trim();
        const errorMatch = block.match(/●\s+(.+?)\n/);
        if (errorMatch) {
          result.failures.push({
            test: errorMatch[1],
            file: testFile,
            error: block.substring(block.indexOf(errorMatch[0]) + errorMatch[0].length, block.indexOf('  ●') > -1 ? block.indexOf('  ●') : undefined).trim()
          });
        }
      });
    }

    return result;
  }

  formatDetailedResults(data) {
    let output = `Test Results for ${data.service}\n`;
    output += `================================\n\n`;
    output += `Timestamp: ${data.timestamp}\n`;
    output += `Duration: ${(data.duration / 1000).toFixed(2)}s\n`;
    output += `Status: ${data.summary.failed > 0 ? 'FAILED' : 'PASSED'}\n\n`;
    output += `Summary:\n`;
    output += `  Passed: ${data.summary.passed}\n`;
    output += `  Failed: ${data.summary.failed}\n`;
    output += `  Skipped: ${data.summary.skipped}\n`;
    output += `  Total: ${data.summary.total}\n\n`;

    if (data.failures.length > 0) {
      output += `Failures:\n`;
      data.failures.forEach((failure, index) => {
        output += `  ${index + 1}. ${failure.test}\n`;
        output += `     File: ${failure.file}\n`;
        output += `     Error: ${failure.error.substring(0, 200)}...\n\n`;
      });
    }

    return output;
  }

  cleanCache() {
    const now = Date.now();
    for (const [key, value] of testResultsCache.entries()) {
      if (now - value.timestamp > CACHE_TTL) {
        testResultsCache.delete(key);
      }
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Cobalt Test Runner MCP Server running on stdio');
  }
}

// Run the server
const server = new TestRunnerServer();
server.run().catch(console.error);
