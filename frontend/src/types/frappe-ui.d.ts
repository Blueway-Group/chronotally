// Copyright (c) 2026 Enerlinq. All rights reserved.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

// Type declarations for frappe-ui/vite plugin
declare module 'frappe-ui/vite' {
  import { Plugin } from 'vite';
  
  interface FrappeUIOptions {
    frappeProxy?: boolean | any;
    lucideIcons?: boolean | any;
    jinjaBootData?: boolean | any;
    buildConfig?: boolean | any;
    frappeTypes?: boolean | any;
  }
  
  function frappeuiPlugin(options?: FrappeUIOptions): Plugin[];
  export default frappeuiPlugin;
}
