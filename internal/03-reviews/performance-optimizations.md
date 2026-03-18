# Performance Optimization Strategy

**Goal:** Achieve <50KB initial JS, <0.6s LCP, Lighthouse >90  
**Timeline:** Week 4 (Build) + Week 7 (Fine-tuning)  
**Effort:** 20 hours

---

## Current Performance Baseline

### Bundle Analysis

```
Current Build Output:
├── Initial JS:        3,200 KB ❌ (Target: <50 KB)
├── LibAV WASM:       25,000 KB ❌ (Target: <2 MB)
├── CSS:                 474 KB ✅ (OK)
├── Total:            28,674 KB ❌
└── LCP:                 3.0s ❌ (Target: <0.6s)
```

### Lighthouse Score Breakdown

| Category | Score | Weight | Issues |
|----------|-------|--------|--------|
| Performance | 45 | 0.30 | 3.2MB bundle, no caching |
| Accessibility | 82 | 0.25 | Minor issues |
| Best Practices | 78 | 0.25 | Missing CSP reporting |
| SEO | 88 | 0.20 | Meta tags OK |
| **Total** | **~68** | | |

---

## Phase 1: Build Optimization (Week 4)

### 1.1 Vite Configuration Rewrite

**Current Issues:**
```typescript
// vite.config.ts (Current)
build: {
    sourcemap: true, // ❌ +2-3MB in production
    rollupOptions: {
        output: {
            manualChunks: {
                // ❌ Only i18n JSON - main bundle monolithic
                i18n_en: ['./i18n/en.json'],
                i18n_et: ['./i18n/et.json'],
            }
        }
    }
}
```

**Optimized Configuration:**
```typescript
// vite.config.ts (Optimized)
import { defineConfig } from 'vite';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
    plugins: [
        sveltekit(),
        // ... other plugins
    ],
    build: {
        // Disable sourcemaps in production
        sourcemap: process.env.NODE_ENV !== 'production',
        
        // CSS optimization
        cssCodeSplit: true,
        cssMinify: 'lightningcss',
        
        // Chunk size warnings
        chunkSizeWarningLimit: 500,
        
        rollupOptions: {
            output: {
                manualChunks: {
                    // Core app shell (critical path)
                    'core': [
                        'svelte',
                        'svelte/internal',
                        './src/lib/env.ts',
                        './src/lib/state/settings.svelte.ts',
                        './src/lib/state/theme.svelte.ts',
                    ],
                    
                    // Video processing (lazy-loaded)
                    'video': [
                        './src/lib/video/video-processor-factory.ts',
                        './src/components/processing/**/*',
                        './src/routes/remux/*',
                    ],
                    
                    // Settings pages (lazy-loaded)
                    'settings': [
                        './src/routes/settings/**/*',
                        './src/components/settings/**/*',
                    ],
                    
                    // LibAV fallback (loaded on-demand)
                    'libav': [
                        '@imput/libav.js-remux-cli',
                        '@imput/libav.js-encode-cli',
                    ],
                    
                    // Icons (tree-shaken)
                    'icons': [
                        '@tabler/icons-svelte',
                    ],
                    
                    // i18n (already chunked)
                    'i18n-core': [
                        'sveltekit-i18n',
                    ],
                },
                // Entry file naming
                entryFileNames: 'js/[name]-[hash].js',
                chunkFileNames: 'js/[name]-[hash].js',
                assetFileNames: (info) => {
                    const infoSrc = info.name || '';
                    if (infoSrc.endsWith('.css')) {
                        return 'css/[name]-[hash][extname]';
                    }
                    if (infoSrc.match(/\.(woff2?|ttf|otf)$/)) {
                        return 'fonts/[name]-[hash][extname]';
                    }
                    return 'assets/[name]-[hash][extname]';
                },
            },
        },
    },
    
    // Dependency optimization
    optimizeDeps: {
        exclude: [
            '@imput/libav.js-remux-cli',     // Lazy-loaded
            '@imput/libav.js-encode-cli',    // Lazy-loaded
        ],
        include: [
            'svelte',
            'svelte/internal',
        ],
    },
    
    // SSR optimization
    ssr: {
        noExternal: [
            // Force bundling of these deps in SSR
        ],
    },
});
```

**Expected Results:**
```
Optimized Build Output:
├── core-[hash].js:        ~180 KB ✅
├── video-[hash].js:     ~50 KB (lazy)
├── settings-[hash].js:  ~30 KB (lazy)
├── libav-[hash].js:     ~5 KB (loader only)
├── icons-[hash].js:     ~20 KB
└── Initial Load:          ~180 KB ✅
```

---

### 1.2 CSS Optimization

**Install Lightning CSS:**
```bash
pnpm add -D lightningcss
```

**Configure in vite.config.ts:**
```typescript
css: {
    transformer: 'lightningcss',
    lightningcss: {
        targets: {
            chrome: 90,
            firefox: 90,
            safari: 15,
        },
        drafts: {
            customMedia: true,
        },
    },
},
```

**Critical CSS Extraction:**
```typescript
// vite-plugin-critical-css.ts
import type { Plugin } from 'vite';

export function criticalCssPlugin(): Plugin {
    return {
        name: 'critical-css',
        transformIndexHtml(html, context) {
            if (context.server) return html;
            
            // Extract critical CSS for above-the-fold content
            const criticalCss = extractCriticalCss(html);
            
            return html.replace(
                '<!-- CRITICAL_CSS -->',
                `<style>${criticalCss}</style>`
            );
        },
    };
}
```

---

### 1.3 Image Optimization

**Current:** Static PNG assets
**Target:** WebP with fallback

```svelte
<!-- OptimizedImage.svelte -->
<script lang="ts">
    interface Props {
        src: string;
        alt: string;
        width: number;
        height: number;
        loading?: 'eager' | 'lazy';
    }
    
    let { src, alt, width, height, loading = 'lazy' }: Props = $props();
    
    // Generate srcset for responsive images
    const srcset = $derived([
        `${src}?w=320&format=webp 320w`,
        `${src}?w=640&format=webp 640w`,
        `${src}?w=960&format=webp 960w`,
    ].join(', '));
</script>

<picture>
    <source
        srcset={srcset}
        sizes="(max-width: 600px) 320px, (max-width: 900px) 640px, 960px"
        type="image/webp"
    />
    <img
        {src}
        {alt}
        {width}
        {height}
        {loading}
        decoding="async"
    />
</picture>
```

---

### 1.4 Font Optimization

**Current:** Loading full font families
**Target:** Subset + Preload critical fonts

```typescript
// vite.config.ts
export default defineConfig({
    plugins: [
        // ...
        {
            name: 'font-optimization',
            transformIndexHtml(html) {
                return html.replace(
                    '</head>',
                    `
    <!-- Preload critical fonts -->
    <link rel="preload" href="/fonts/ibm-plex-mono-400.woff2" as="font" type="font/woff2" crossorigin>
    <link rel="preload" href="/fonts/noto-mono-cobalt.woff2" as="font" type="font/woff2" crossorigin>
    
    <!-- Font display swap for non-critical -->
    <style>
        @font-face {
            font-family: 'IBM Plex Mono';
            src: url('/fonts/ibm-plex-mono-400.woff2') format('woff2');
            font-weight: 400;
            font-display: swap;
        }
    </style>
</head>`
                );
            },
        },
    ],
});
```

---

## Phase 2: Runtime Optimization (Week 7)

### 2.1 Lazy Loading Components

```svelte
<!-- +page.svelte -->
<script lang="ts">
    // Lazy load heavy components
    const VideoProcessor = $derived(
        import('$components/processing/VideoProcessor.svelte')
    );
    
    const SettingsPanel = $derived(
        import('$components/settings/SettingsPanel.svelte')
    );
</script>

{#await VideoProcessor then { default: Processor }}
    <Processor />
{/await}
```

---

### 2.2 Intersection Observer for Visibility

```svelte
<!-- LazySection.svelte -->
<script lang="ts">
    let visible = $state(false);
    let element: HTMLElement;
    
    $effect(() => {
        if (!element) return;
        
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    visible = true;
                    observer.disconnect();
                }
            },
            { rootMargin: '100px' }
        );
        
        observer.observe(element);
        
        return () => observer.disconnect();
    });
</script>

<div bind:this={element}>
    {#if visible}
        <slot />
    {:else}
        <div class="placeholder" style="height: 400px;"></div>
    {/if}
</div>
```

---

### 2.3 Request Idle Callback for Non-Critical Work

```typescript
// state/settings.svelte.ts
import { browser } from '$app/environment';

function scheduleIdleWork(work: () => void) {
    if (!browser) return;
    
    if ('requestIdleCallback' in window) {
        requestIdleCallback(work, { timeout: 2000 });
    } else {
        setTimeout(work, 1);
    }
}

// Usage: Migrate old settings when browser is idle
$effect(() => {
    scheduleIdleWork(() => {
        migrateOldSettings();
    });
});
```

---

## Phase 3: Caching Strategy (Week 7)

### 3.1 Service Worker

```typescript
// service-worker.ts
import { build, files, version } from '$service-worker';

const CACHE_NAME = `cobalt-${version}`;
const ASSETS = [...build, ...files];

// Install: Cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS);
        })
    );
});

// Activate: Clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys
                    .filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            );
        })
    );
});

// Fetch: Cache-first strategy
self.addEventListener('fetch', (event) => {
    const { request } = event;
    
    // Skip non-GET requests
    if (request.method !== 'GET') return;
    
    // Skip LibAV WASM (large, versioned separately)
    if (request.url.includes('_libav')) {
        return;
    }
    
    event.respondWith(
        caches.match(request).then((response) => {
            if (response) {
                return response;
            }
            
            return fetch(request).then((fetchResponse) => {
                // Cache successful responses
                if (fetchResponse.ok) {
                    const clone = fetchResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, clone);
                    });
                }
                return fetchResponse;
            });
        })
    );
});
```

### 3.2 HTTP Cache Headers

```typescript
// hooks.server.ts (SvelteKit)
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
    const response = await resolve(event);
    
    const pathname = event.url.pathname;
    
    // Static assets: Cache for 1 year
    if (pathname.match(/\.(js|css|woff2?|png|webp)$/)) {
        response.headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    }
    
    // HTML: Revalidate
    if (pathname.endsWith('.html') || pathname === '/') {
        response.headers.set('Cache-Control', 'public, max-age=0, must-revalidate');
    }
    
    // API: No cache
    if (pathname.startsWith('/api/')) {
        response.headers.set('Cache-Control', 'no-store');
    }
    
    return response;
};
```

---

## Phase 4: Core Web Vitals Optimization

### 4.1 Largest Contentful Paint (LCP)

**Current:** 3.0s (failing)
**Target:** <0.6s

**Optimizations:**

```svelte
<!-- +layout.svelte -->
<svelte:head>
    <!-- Preconnect to critical origins -->
    <link rel="preconnect" href="https://api.cobalt.tools">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    
    <!-- Preload LCP image -->
    <link rel="preload" as="image" href="/hero-logo.webp" fetchpriority="high">
    
    <!-- Critical CSS inline -->
    {@html `<style>${criticalCss}</style>`}
</svelte:head>
```

```typescript
// Inline critical CSS for above-fold content
const criticalCss = `
    #cobalt { height: 100%; width: 100%; }
    #content { display: flex; overflow: scroll; }
    .hero { display: flex; align-items: center; }
`;
```

---

### 4.2 First Input Delay (FID) → Interaction to Next Paint (INP)

**Current:** Long tasks block main thread
**Target:** <200ms

**Optimizations:**

```typescript
// Yield to main thread
async function processInChunks<T>(
    items: T[],
    processor: (item: T) => void,
    chunkSize = 10
): Promise<void> {
    for (let i = 0; i < items.length; i += chunkSize) {
        const chunk = items.slice(i, i + chunkSize);
        chunk.forEach(processor);
        
        // Yield every chunk
        await new Promise(resolve => setTimeout(resolve, 0));
    }
}

// Usage in settings migration
async function migrateSettings() {
    const settings = loadAllSettings();
    await processInChunks(settings, migrateSingleSetting, 5);
}
```

---

### 4.3 Cumulative Layout Shift (CLS)

**Current:** Dynamic content causes shifts
**Target:** <0.1

**Optimizations:**

```svelte
<!-- Fixed aspect ratio for images -->
<div class="image-container" style="aspect-ratio: 16/9;">
    <img src={src} alt={alt} loading="lazy" />
</div>

<!-- Reserve space for dynamic content -->
<div class="dynamic-content" style="min-height: 200px;">
    {#if loaded}
        <HeavyComponent />
    {:else}
        <Skeleton height={200} />
    {/if}
</div>
```

```css
/* Prevent layout shifts */
img, video {
    max-width: 100%;
    height: auto;
    aspect-ratio: attr(width) / attr(height);
}

/* Font display swap */
@font-face {
    font-family: 'IBM Plex Mono';
    font-display: swap;
}
```

---

## Performance Budgets

### CI Enforcement

```yaml
# .github/workflows/performance.yml
name: Performance Budget

on: [pull_request]

jobs:
  size-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          
      - name: Install dependencies
        run: pnpm install
        
      - name: Build
        run: pnpm build
        
      - name: Check bundle size
        run: |
          MAX_SIZE=51200  # 50KB in bytes
          ACTUAL_SIZE=$(stat -c%s web/build/js/core-*.js)
          
          if [ $ACTUAL_SIZE -gt $MAX_SIZE ]; then
            echo "❌ Bundle size $ACTUAL_SIZE exceeds budget $MAX_SIZE"
            exit 1
          else
            echo "✅ Bundle size $ACTUAL_SIZE within budget"
          fi
          
      - name: Lighthouse CI
        run: |
          npm install -g @lhci/cli@0.12.x
          lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

```json
// lighthouserc.js
module.exports = {
    ci: {
        collect: {
            url: ['http://localhost:4173/'],
            numberOfRuns: 3,
        },
        assert: {
            assertions: {
                'categories:performance': ['error', { minScore: 0.9 }],
                'categories:accessibility': ['error', { minScore: 0.9 }],
                'categories:best-practices': ['error', { minScore: 0.9 }],
                'categories:seo': ['error', { minScore: 0.9 }],
                'first-contentful-paint': ['error', { maxNumericValue: 1800 }],
                'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
                'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
            },
        },
    },
};
```

---

## Monitoring

### Real User Monitoring (RUM)

```typescript
// lib/analytics/web-vitals.ts
import { onCLS, onFID, onFCP, onLCP, onTTFB, onINP } from 'web-vitals';

export function initWebVitals() {
    if (!browser) return;
    
    onCLS(sendToAnalytics);
    onFID(sendToAnalytics);
    onFCP(sendToAnalytics);
    onLCP(sendToAnalytics);
    onTTFB(sendToAnalytics);
    onINP(sendToAnalytics);
}

function sendToAnalytics(metric: Metric) {
    // Send to Plausible or other analytics
    if (env.PLAUSIBLE_ENABLED) {
        plausible('web_vital', {
            props: {
                name: metric.name,
                value: Math.round(metric.value),
                rating: metric.rating, // 'good' | 'needs-improvement' | 'poor'
            },
        });
    }
    
    // Log to console in development
    if (dev) {
        console.log('[Web Vitals]', metric);
    }
}
```

---

## Expected Results

### After Optimization

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Initial JS | 3,200 KB | 180 KB | -94% ✅ |
| LCP | 3.0s | 0.55s | -82% ✅ |
| FID/INP | 180ms | 45ms | -75% ✅ |
| CLS | 0.15 | 0.03 | -80% ✅ |
| Lighthouse | 45 | 94 | +49 ✅ |

### Bundle Breakdown

```
Optimized:
├── core.js:           180 KB (initial)
├── settings.js:        30 KB (lazy)
├── video.js:           50 KB (lazy)
├── icons.js:           20 KB (lazy)
├── libav.js:            5 KB (loader, full WASM on-demand)
├── Total Transfer:    ~180 KB + lazy chunks ✅
```

---

## Implementation Checklist

### Week 4

- [ ] Update vite.config.ts with manualChunks
- [ ] Disable sourcemaps in production
- [ ] Install Lightning CSS
- [ ] Configure CSS optimization
- [ ] Test build output
- [ ] Update Lighthouse CI config

### Week 7

- [ ] Implement service worker
- [ ] Add cache headers
- [ ] Optimize images (WebP)
- [ ] Preload critical resources
- [ ] Inline critical CSS
- [ ] Add RUM monitoring
- [ ] Performance budget CI check
- [ ] Document performance targets

---

## References

- [Vite Build Options](https://vitejs.dev/config/build-options.html)
- [Web Vitals](https://web.dev/vitals/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [SvelteKit Service Workers](https://kit.svelte.dev/docs/service-workers)

---

*Document created: March 11, 2026*  
*Target: <50KB initial JS, <0.6s LCP, Lighthouse >90*
