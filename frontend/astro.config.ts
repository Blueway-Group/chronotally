// Copyright (c) 2026 Blueway Consulting LLC.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

// @ts-check
import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';
import tailwindcss from '@tailwindcss/vite';
import commonSiteConfig from '../../../sites/common_site_config.json' assert { type: 'json' };
import type { HttpProxy, ProxyOptions } from 'vite';
import mcp from 'astro-mcp'
const webserver_port = commonSiteConfig.webserver_port;

// https://astro.build/config
export default defineConfig({
  output: 'static',
  integrations: [vue(), mcp()],
  base: '/chronotally',
  outDir: '../chronotally/public/frontend',
  build: {
    assetsPrefix: '/assets/chronotally/frontend',
  },
  server: {
    port: 8080,
    host: true
  },
  vite: {
    plugins: [tailwindcss()],
    server: {
      allowedHosts: ["frappe.remotehost", "frappe.localhost"],
      proxy: {
        '^/(app|login|api|assets|files|private)': {
          target: `http://127.0.0.1:${webserver_port}`,
          changeOrigin: true,
          configure: (proxy: HttpProxy.Server, _options: ProxyOptions) => {
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              const hostHeader = req.headers.host || '127.0.0.1';
              const site_name = hostHeader.includes(':') ? hostHeader.split(':')[0] : hostHeader;
              proxyReq.setHeader('Host', `${site_name}:${webserver_port}`);
            });
          }
        }
      }
    }
  }
});
