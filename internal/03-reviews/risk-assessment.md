# Risk Assessment

**Project:** Cobalt Web Frontend Refactoring  
**Date:** March 11, 2026  
**Scope:** 8-week sprint execution

---

## Executive Summary

| Risk Level | Count | Mitigation Status |
|------------|-------|-------------------|
| Critical (P0) | 4 | 3 mitigated, 1 monitoring |
| High (P1) | 6 | All mitigated |
| Medium (P2) | 8 | 6 mitigated, 2 accepted |
| Low (P3) | 12 | 8 mitigated, 4 accepted |

**Overall Risk Level:** MEDIUM - Manageable with planned mitigations

---

## Critical Risks (P0)

### R1: WebCodecs API Browser Incompatibility

**Risk:** Firefox and older browsers don't support WebCodecs API  
**Impact:** HIGH - 22% of users cannot use video processing  
**Probability:** CERTAIN (Firefox has no support)  
**Status:** ⚠️ MITIGATION REQUIRED

**Mitigation Strategy:**
1. Feature detection before loading any video processor
2. Automatic LibAV fallback for unsupported browsers
3. Clear UI indication of which engine is being used
4. Performance metrics to track fallback usage

**Implementation:**
```typescript
// video-processor-factory.ts
const supportsWebCodecs = typeof VideoDecoder !== 'undefined' &&
                          typeof VideoEncoder !== 'undefined';

export async function createProcessor(): Promise<VideoProcessor> {
    if (supportsWebCodecs) {
        try {
            return new WebCodecsProcessor();
        } catch (e) {
            console.warn('WebCodecs failed, falling back:', e);
        }
    }
    return new LibAVProcessor(); // Guaranteed fallback
}
```

**Fallback Coverage:**
- Firefox 100% → LibAV
- Safari <16.4 → LibAV  
- Chrome <94 → LibAV
- All mobile → LibAV (WebCodecs mobile support limited)

**Monitoring:**
- Track fallback rate in analytics
- Alert if >30% fallback (indicates implementation bug)

---

### R2: Store Migration Breaks Reactivity

**Risk:** Svelte 4 → Svelte 5 store migration causes reactive bugs  
**Impact:** CRITICAL - App may not function  
**Probability:** LOW - Well-documented patterns  
**Status:** ✅ MITIGATED

**Mitigation Strategy:**
1. Comprehensive unit tests before migration
2. Gradual rollout (1 store at a time)
3. Feature flags for rollback
4. Automated regression testing

**Test Requirements:**
```typescript
// settings.svelte.test.ts
// Must pass before and after migration
describe('Settings Store Reactivity', () => {
    it('should update when settings change', async () => {
        const component = render(SettingsPage);
        updateSetting({ language: 'et' });
        await waitFor(() => {
            expect(screen.getByText('Eesti')).toBeInTheDocument();
        });
    });
    
    it('should persist across reloads', () => {
        updateSetting({ theme: 'dark' });
        expect(localStorage.getItem('settings')).toContain('dark');
    });
});
```

**Rollback Plan:**
```bash
# If issues detected
$ git revert HEAD --no-edit
$ pnpm build
$ pnpm deploy:rollback
```

---

### R3: LibAV WASM Size Causes Timeout

**Risk:** 25MB LibAV WASM download times out on slow connections  
**Impact:** HIGH - Users cannot process videos  
**Probability:** MEDIUM - 3G connections  
**Status:** ⚠️ PARTIALLY MITIGATED

**Current State:**
- 25MB download on 3G = 60-90 seconds
- Many users will abandon

**Mitigation Strategy:**
1. WebCodecs for supported browsers (80% of traffic)
2. Lazy-load LibAV only when needed
3. Show progress indicator with ETA
4. Offer "retry" on timeout

**Lazy Loading:**
```typescript
// Only load LibAV when user starts processing
async function startProcessing() {
    if (!libavLoaded) {
        showProgress('Loading video processor...');
        const { default: LibAV } = await import('@imput/libav.js-remux-cli');
        libav = new LibAVWrapper();
        await libav.init();
        libavLoaded = true;
    }
    // ... processing
}
```

**Monitoring:**
- Track download completion rate
- Alert if <90% completion

---

### R4: Bundle Size Regression After Build Optimization

**Risk:** Manual chunking causes unexpected size increase  
**Impact:** HIGH - Fails <50KB target  
**Probability:** LOW - Vite chunking is reliable  
**Status:** ✅ MITIGATED

**Mitigation Strategy:**
1. CI performance budget check
2. Bundle analyzer in build pipeline
3. Weekly size audits

**CI Check:**
```yaml
# .github/workflows/size.yml
- name: Bundle Size Check
  run: |
    MAX_SIZE=51200  # 50KB
    ACTUAL_SIZE=$(stat -c%s web/build/js/core-*.js)
    
    if [ $ACTUAL_SIZE -gt $MAX_SIZE ]; then
      echo "❌ Bundle $ACTUAL_SIZE exceeds $MAX_SIZE"
      exit 1
    fi
```

---

## High Risks (P1)

### R5: Mentor Approval Delays

**Risk:** ADR documents not approved within 24-hour SLA  
**Impact:** MEDIUM - Delays critical path  
**Probability:** MEDIUM - Academic schedules  
**Status:** ✅ MITIGATED

**Mitigation:**
1. Submit ADRs Week 1 Day 1
2. Buffer time in Week 2
3. Parallel work possible (dev environment, tests)
4. Escalation path defined

---

### R6: Team Member Unavailability

**Risk:** Team member sick/available during sprint  
**Impact:** MEDIUM - Reduces capacity  
**Probability:** MEDIUM - 8-week duration  
**Status:** ✅ MITIGATED

**Mitigation:**
1. Cross-training on all components
2. Detailed documentation
3. Task handoff procedures
4. Buffer capacity (87h planned, 120h available)

---

### R7: Testing Infrastructure Setup Complexity

**Risk:** Vitest + @testing-library/svelte integration issues  
**Impact:** MEDIUM - Delays Week 5  
**Probability:** LOW - Mature tools  
**Status:** ✅ MITIGATED

**Mitigation:**
1. Proof-of-concept in Week 2
2. Fallback to Playwright-only testing
3. Community support (Svelte Discord)

---

### R8: Tailwind CSS Migration Breaks Styling

**Risk:** 474 lines of custom CSS don't translate cleanly  
**Impact:** MEDIUM - Visual regressions  
**Probability:** MEDIUM - Complex selectors  
**Status:** ✅ MITIGATED

**Mitigation:**
1. Visual regression testing (Chromatic)
2. Gradual migration (component by component)
3. Keep old CSS as backup
4. Design review before merge

---

### R9: WebCodecs Codec Support Gaps

**Risk:** Browser supports WebCodecs but not specific codec  
**Impact:** MEDIUM - Video fails to process  
**Probability:** MEDIUM - Codec fragmentation  
**Status:** ✅ MITIGATED

**Mitigation:**
```typescript
// Check codec support before use
async function supportsCodec(codec: string): Promise<boolean> {
    try {
        const result = await VideoDecoder.isConfigSupported({ codec });
        return result.supported;
    } catch {
        return false;
    }
}

// Usage
if (!await supportsCodec('vp09.00.10.08')) {
    return new LibAVProcessor(); // Fallback
}
```

---

### R10: Security Vulnerability in Dependencies

**Risk:** LibAV or other dependency has CVE  
**Impact:** HIGH - Security breach possible  
**Probability:** LOW - Monitored dependencies  
**Status:** ✅ MITIGATED

**Mitigation:**
1. Dependabot alerts enabled
2. Weekly dependency audit
3. OWASP dependency check in CI
4. Pin to specific versions

---

## Medium Risks (P2)

### R11: Svelte 5 Bug in Production

**Risk:** Undiscovered Svelte 5 bug affects users  
**Impact:** MEDIUM - Feature broken  
**Probability:** LOW - Svelte 5 is stable  
**Status:** ⚠️ ACCEPTED

**Mitigation:**
- Use latest stable version (5.0.0+)
- Monitor Svelte GitHub issues
- Quick rollback capability

---

### R12: CI/CD Pipeline Failure

**Risk:** GitHub Actions or deployment fails  
**Impact:** MEDIUM - Cannot deploy  
**Probability:** LOW - Mature infrastructure  
**Status:** ✅ MITIGATED

**Mitigation:**
1. Local build verification
2. Staging environment
3. Manual deployment fallback

---

### R13: Accessibility Regression

**Risk:** Migration breaks screen reader support  
**Impact:** MEDIUM - Excludes users  
**Probability:** LOW - A11y testing in place  
**Status:** ✅ MITIGATED

**Mitigation:**
1. axe-core testing in CI
2. Manual screen reader testing
3. Accessibility audit Week 7

---

### R14: Internationalization Issues

**Risk:** i18n keys break or translations missing  
**Impact:** LOW - UI text issues  
**Probability:** LOW - Static translations  
**Status:** ✅ MITIGATED

**Mitigation:**
1. Type-safe i18n keys
2. Fallback to English
3. Translation validation in CI

---

## Risk Matrix Visualization

```
Impact
   │
 H │ R1( WebCodecs)    R10( Security)
   │ R3( LibAV Size)   R5( Mentor)
   │ R4( Bundle Size)
   │
 M │ R8( Tailwind)     R6( Team)
   │ R9( Codec Gap)    R7( Testing)
   │
 L │                   R11-14
   │
   └──────────────────────────────
     L    M    H    C    Probability
```

---

## Risk Response Strategy

### Avoid
- **R2 (Reactivity bugs):** Comprehensive testing
- **R10 (Security):** Dependency monitoring

### Mitigate
- **R1 (WebCodecs):** Fallback implementation
- **R3 (LibAV size):** Lazy loading
- **R4 (Bundle size):** CI budget checks
- **R5-9:** Process and tooling

### Transfer
- None applicable

### Accept
- **R11-14:** Low impact/probability, monitoring

---

## Contingency Plans

### If WebCodecs Fails (>50% fallback rate)
1. Investigate root cause
2. Prioritize LibAV optimization
3. Consider WASM streaming/partial loading
4. Extend Week 5-6 timeline

### If Store Migration Breaks
1. Immediate rollback
2. Hotfix to main
3. Root cause analysis
4. Revised migration approach

### If Performance Targets Not Met
1. Additional optimization sprint
2. Feature cuts (non-critical)
3. CDN optimization
4. Extend timeline by 1 week

---

## Risk Owner Assignments

| Risk | Owner | Review Date |
|------|-------|-------------|
| R1 | Senior Frontend Dev | Weekly |
| R2 | Technical Lead | Daily (Week 2-3) |
| R3 | Performance Lead | Weekly |
| R4 | DevOps | Per-PR |
| R5 | Project Manager | Weekly |
| R6 | Project Manager | Daily standup |
| R7 | QA Lead | Week 5 |
| R8 | UI Lead | Week 6 |
| R9 | Senior Frontend Dev | Week 4-5 |
| R10 | Security Lead | Weekly |

---

## Review Schedule

- **Daily:** Standup risk mention
- **Weekly:** Sprint review risk assessment
- **Bi-weekly:** Full risk register review
- **As-needed:** Risk trigger events

---

*Document created: March 11, 2026*  
*Next review: March 18, 2026 (End of Week 1)*
