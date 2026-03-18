# Svelte 5 Migration Guide

**Target:** Migrate 9 store files + 34 components from Svelte 4 to Svelte 5 Runes  
**Timeline:** Weeks 2-3 of sprint  
**Effort:** 30 hours

---

## Overview

Svelte 5 introduces **Runes**, a new way to declare reactive state that replaces Svelte 4's reactive statements and stores. This guide provides step-by-step migration patterns for the Cobalt codebase.

### Why Migrate?

| Aspect | Svelte 4 | Svelte 5 | Impact |
|--------|----------|----------|--------|
| Bundle Size | Baseline | -15-20% | Smaller downloads |
| Runtime Perf | Good | Excellent | Faster updates |
| Type Safety | Okay | Native | Better DX |
| Reactivity | Coarse | Fine-grained | Only changed parts update |

---

## Migration Patterns

### Pattern 1: writable() → $state()

**Before (Svelte 4):**
```typescript
// store.ts
import { writable } from 'svelte/store';

export const count = writable(0);

export function increment() {
    count.update(n => n + 1);
}

// Component.svelte
<script>
    import { count, increment } from './store';
</script>

<button on:click={increment}>
    Count: {$count}
</button>
```

**After (Svelte 5):**
```typescript
// store.ts
export const count = $state(0);

export function increment() {
    count++; // Direct mutation!
}

// Component.svelte
<script>
    import { count, increment } from './store';
</script>

<button onclick={increment}>
    Count: {count}
</button>
```

**Key Changes:**
- Remove `import { writable }`
- Replace `$count` with `count` in template
- Direct mutation instead of `.update()`

---

### Pattern 2: readable() → $state() + $effect()

**Before:**
```typescript
import { readable } from 'svelte/store';

export const time = readable(new Date(), (set) => {
    const interval = setInterval(() => {
        set(new Date());
    }, 1000);
    
    return () => clearInterval(interval);
});
```

**After:**
```typescript
export const time = $state(new Date());

$effect(() => {
    const interval = setInterval(() => {
        time = new Date(); // Direct assignment
    }, 1000);
    
    return () => clearInterval(interval); // Cleanup
});
```

**Key Changes:**
- `$state()` for the value
- `$effect()` for side effects
- Cleanup function returned from `$effect()`

---

### Pattern 3: derived() → $derived()

**Before:**
```typescript
import { derived } from 'svelte/store';
import { settings } from './settings';

export const theme = derived(
    settings,
    $settings => $settings.theme || 'auto'
);

export const isDark = derived(
    [theme, systemPreference],
    ([$theme, $system]) => {
        if ($theme === 'dark') return true;
        if ($theme === 'light') return false;
        return $system === 'dark';
    }
);
```

**After:**
```typescript
import { settings } from './settings';

// Single derived value
export const theme = $derived(settings.theme || 'auto');

// Multiple dependencies
export const isDark = $derived.by(() => {
    if (theme === 'dark') return true;
    if (theme === 'light') return false;
    return systemPreference === 'dark';
});
```

**Key Changes:**
- `$derived` for simple expressions
- `$derived.by()` for complex logic
- Access values directly, no `$` prefix

---

### Pattern 4: Store with External Updates

**Current (settings.ts - Most Complex):**
```typescript
import { derived, readable, type Updater } from 'svelte/store';

let update: (_: Updater<PartialSettings>) => void;

export const storedSettings = readable<PartialSettings>(
    loadFromStorage(),
    (_, _update) => { update = _update }
);

export default derived(storedSettings, $s => mergeWithDefaults($s));

export function updateSetting(partial: PartialSettings) {
    update(current => {
        const updated = writeToStorage(merge(current, partial));
        return updated;
    });
}
```

**Migrated:**
```typescript
// settings.ts
const storedSettings = $state<PartialSettings>(loadFromStorage());

// Auto-persist on changes
$effect(() => {
    localStorage.setItem('settings', JSON.stringify(storedSettings));
    updatePlausiblePreference(storedSettings);
});

// Exported derived full settings
export const settings = $derived(mergeWithDefaults(storedSettings));

// Direct mutation function
export function updateSetting(partial: PartialSettings) {
    Object.assign(storedSettings, partial, { 
        schemaVersion: defaultSettings.schemaVersion 
    });
}

export function resetSettings() {
    Object.assign(storedSettings, {});
    localStorage.removeItem('settings');
}
```

**Key Changes:**
- `$state()` holds the raw data
- `$effect()` handles side effects (persistence)
- `$derived()` creates computed view
- `Object.assign()` for partial updates

---

### Pattern 5: Component Props

**Before:**
```svelte
<script lang="ts">
    export let items: NavItem[];
    export let collapsed = false;
    export let theme: Theme = 'auto';
    
    $: filteredItems = items.filter(i => i.visible);
</script>
```

**After:**
```svelte
<script lang="ts">
    interface Props {
        items: NavItem[];
        collapsed?: boolean;
        theme?: Theme;
    }
    
    let { items, collapsed = false, theme = 'auto' }: Props = $props();
    
    const filteredItems = $derived(items.filter(i => i.visible));
</script>
```

**Key Changes:**
- `interface Props` for type safety
- `$props()` destructuring with defaults
- `$derived()` for computed values
- No more `export let`

---

### Pattern 6: Event Handlers

**Before:**
```svelte
<button on:click={handleClick}>
    Click me
</button>

<input on:input={e => value = e.target.value} />
```

**After:**
```svelte
<button onclick={handleClick}>
    Click me
</button>

<input oninput={e => value = e.currentTarget.value} />
```

**Key Changes:**
- `on:click` → `onclick` (no colon)
- `e.target` → `e.currentTarget` (better typing)

---

### Pattern 7: Reactive Statements

**Before:**
```svelte
<script>
    $: reduceMotion = $settings.accessibility.reduceMotion || device.prefers.reducedMotion;
    $: reduceTransparency = $settings.accessibility.reduceTransparency || device.prefers.reducedTransparency;
    
    $: if (browser) {
        document.body.classList.toggle('reduce-motion', reduceMotion);
    }
</script>
```

**After:**
```svelte
<script>
    const preferences = $derived({
        reduceMotion: settings.accessibility.reduceMotion || device.prefers.reducedMotion,
        reduceTransparency: settings.accessibility.reduceTransparency || device.prefers.reducedTransparency
    });
    
    $effect(() => {
        if (browser) {
            document.body.classList.toggle('reduce-motion', preferences.reduceMotion);
        }
    });
</script>
```

**Key Changes:**
- Multiple `$:` → single `$derived` object
- Side effects → `$effect()`
- Dependencies tracked automatically

---

### Pattern 8: Store Subscriptions in Components

**Before:**
```svelte
<script>
    import { settings } from '$lib/state/settings';
    import { theme } from '$lib/state/theme';
    
    $: themeColor = $theme === 'dark' ? '#000' : '#fff';
</script>

<div style="color: {themeColor}">
    {$settings.general.language}
</div>
```

**After:**
```svelte
<script>
    import { settings } from '$lib/state/settings';
    import { themeState } from '$lib/state/theme';
    
    const themeColor = $derived(themeState.theme === 'dark' ? '#000' : '#fff');
</script>

<div style="color: {themeColor}">
    {settings.general.language}
</div>
```

**Key Changes:**
- No `$` prefix on reactive values
- `$derived()` for computed template values

---

## File-by-File Migration Plan

### Week 2: Store Migration (Priority Order)

#### 1. `omnibox.ts` (5 lines) - START HERE
**Complexity:** Trivial  
**Effort:** 30 minutes

```typescript
// Before
import { writable } from 'svelte/store';
export const omnibox = writable(false);

// After
export const omnibox = $state(false);
```

**Learning:** Simplest migration, good for team practice.

---

#### 2. `dialogs.ts` (23 lines)
**Complexity:** Low  
**Effort:** 1 hour

```typescript
// Before
import { writable } from 'svelte/store';
export const dialogs = writable({ about: false, settings: false, donate: false });

// After
export const dialogs = $state({ about: false, settings: false, donate: false });

export function openDialog(name: keyof typeof dialogs) {
    dialogs[name] = true;
}

export function closeDialog(name: keyof typeof dialogs) {
    dialogs[name] = false;
}

export function closeAllDialogs() {
    Object.keys(dialogs).forEach(key => {
        dialogs[key as keyof typeof dialogs] = false;
    });
}
```

---

#### 3. `queue-visibility.ts` (11 lines)
**Complexity:** Low  
**Effort:** 30 minutes

```typescript
// Before
import { writable } from 'svelte/store';
export const queueVisible = writable(false);

// After
export const queueVisible = $state(false);
```

---

#### 4. `server-info.ts` (4 lines)
**Complexity:** Trivial  
**Effort:** 15 minutes

```typescript
// Before
import { writable } from 'svelte/store';
export const serverInfo = writable<ServerInfo | null>(null);

// After
export const serverInfo = $state<ServerInfo | null>(null);
```

---

#### 5. `turnstile.ts` (17 lines)
**Complexity:** Medium  
**Effort:** 1 hour

**Security-sensitive:** Requires careful testing

```typescript
// Before
import { derived, writable } from 'svelte/store';
export const turnstileEnabled = writable(false);
export const turnstileCreated = writable(false);
export const turnstileVisible = derived(
    [turnstileEnabled, turnstileCreated],
    ([$enabled, $created]) => $enabled && !$created
);

// After
export const turnstileEnabled = $state(false);
export const turnstileCreated = $state(false);
export const turnstileVisible = $derived(turnstileEnabled && !turnstileCreated);
```

---

#### 6. `theme.ts` (53 lines)
**Complexity:** Medium  
**Effort:** 2 hours

**Critical:** Used in root layout

```typescript
// Before (simplified)
import { derived, writable } from 'svelte/store';
export const themeOverride = writable<Theme | null>(null);
export const currentTheme = derived(
    [themeOverride, systemPreference],
    ([$override, $system]) => $override || $system || 'auto'
);
export const statusBarColors = derived(
    currentTheme,
    $theme => ({ /* colors */ })
);

// After
const themeOverride = $state<Theme | null>(null);

export const currentTheme = $derived(
    themeOverride || systemPreference || 'auto'
);

export const statusBarColors = $derived(
    getStatusBarColors(currentTheme)
);

export function setThemeOverride(theme: Theme | null) {
    themeOverride = theme;
}
```

---

#### 7. `settings.ts` (94 lines)
**Complexity:** High  
**Effort:** 4 hours

**Most Critical Store**

See Pattern 4 above for full migration.

**Testing Requirements:**
- [ ] Settings persist to localStorage
- [ ] Migration from old schema versions works
- [ ] Plausible analytics respect privacy settings
- [ ] Reset functionality clears storage

---

### Week 3: Component Migration

#### Priority Order

1. **Leaf Components** (no dependencies)
   - Turnstile.svelte
   - NotchSticker.svelte
   - UpdateNotification.svelte

2. **Container Components**
   - DialogHolder.svelte
   - ProcessingQueue.svelte

3. **Layout Components**
   - Sidebar.svelte
   - +layout.svelte (root)

4. **Page Components**
   - settings/* (all settings pages)
   - +page.svelte (home)

---

## Common Migration Pitfalls

### Pitfall 1: Mutating $state() Outside Component

**Wrong:**
```typescript
// store.ts
export const count = $state(0);

// elsewhere.ts
count = 5; // ❌ Error: Cannot mutate $state outside component
```

**Right:**
```typescript
// store.ts
let count = $state(0);

export function getCount() { return count; }
export function setCount(n: number) { count = n; }

// elsewhere.ts
import { setCount } from './store';
setCount(5); // ✅ Works
```

---

### Pitfall 2: Using $state() in Non-.svelte Files

**Wrong:**
```typescript
// utils.ts (not a .svelte file)
export const value = $state(0); // ❌ Runtime error
```

**Right:**
```typescript
// utils.svelte.ts (note: .svelte.ts extension)
export const value = $state(0); // ✅ Works in Svelte 5
```

**Note:** Rename `store.ts` → `store.svelte.ts` for Svelte 5 runes.

---

### Pitfall 3: Forgetting .svelte.ts Extension

**File naming convention:**
- `store.ts` → `store.svelte.ts`
- `helpers.ts` with runes → `helpers.svelte.ts`
- Regular utilities → keep `.ts`

---

### Pitfall 4: Accessing State Before Initialization

**Wrong:**
```svelte
<script>
    let value = $state(0);
    console.log(value); // ✅ OK
    
    // Later...
    const doubled = $derived(value * 2);
    console.log(doubled); // ⚠️ May be undefined initially
</script>
```

**Right:**
```svelte
<script>
    let value = $state(0);
    const doubled = $derived(value * 2);
    
    $effect(() => {
        console.log(doubled); // ✅ Safe in $effect
    });
</script>
```

---

## Testing Migration

### Unit Test Pattern

```typescript
// settings.svelte.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { settings, updateSetting, resetSettings } from './settings.svelte';

describe('Settings Store', () => {
    beforeEach(() => {
        localStorage.clear();
        resetSettings();
    });

    it('should have default values', () => {
        expect(settings.privacy.disableAnalytics).toBe(false);
    });

    it('should update values reactively', () => {
        updateSetting({ privacy: { disableAnalytics: true } });
        expect(settings.privacy.disableAnalytics).toBe(true);
    });

    it('should persist to localStorage', () => {
        updateSetting({ general: { language: 'et' } });
        const stored = JSON.parse(localStorage.getItem('settings')!);
        expect(stored.general.language).toBe('et');
    });
});
```

### Component Test Pattern

```typescript
// Sidebar.svelte.test.ts
import { render, screen, fireEvent } from '@testing-library/svelte';
import Sidebar from './Sidebar.svelte';

describe('Sidebar', () => {
    it('should toggle collapse state', async () => {
        render(Sidebar, { items: [] });
        
        const toggle = screen.getByLabelText('Toggle sidebar');
        await fireEvent.click(toggle);
        
        expect(screen.getByRole('navigation')).toHaveClass('collapsed');
    });
});
```

---

## Migration Checklist

### Per-File Checklist

- [ ] Rename `.ts` → `.svelte.ts` if using runes
- [ ] Remove `import { writable, readable, derived } from 'svelte/store'`
- [ ] Replace `writable()` with `$state()`
- [ ] Replace `readable()` with `$state()` + `$effect()`
- [ ] Replace `derived()` with `$derived()` or `$derived.by()`
- [ ] Remove `$` prefix from store subscriptions
- [ ] Update component props to use `$props()`
- [ ] Change `on:event` to `onevent`
- [ ] Run `svelte-check` for type errors
- [ ] Run unit tests
- [ ] Manual browser testing

---

## Effort Estimation

| Task | Complexity | Effort | Risk |
|------|------------|--------|------|
| omnibox.ts | Trivial | 0.5h | Low |
| server-info.ts | Trivial | 0.5h | Low |
| queue-visibility.ts | Low | 0.5h | Low |
| dialogs.ts | Low | 1h | Low |
| turnstile.ts | Medium | 1h | Medium |
| theme.ts | Medium | 2h | Medium |
| settings.ts | High | 4h | High |
| 22 Components | Medium | 15h | Medium |
| Testing | - | 5h | Low |
| **TOTAL** | | **30h** | |

---

## References

- [Svelte 5 Runes Documentation](https://svelte.dev/docs/runes)
- [Svelte 5 Migration Guide](https://svelte.dev/docs/faq#how-do-i-migrate-from-svelte-4-to-svelte-5)
- [Svelte 5 REPL](https://svelte-5-preview.vercel.app/)

---

*Document created: March 11, 2026*  
*For issues, reference original files in `/web/src/lib/state/`*
