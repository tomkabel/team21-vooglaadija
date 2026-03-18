#!/bin/bash

# =============================================================================
# Sprint 3 Setup Script - Core Features Implementation
# Repository: https://github.com/tomkabel/team21-vooglaadija
# Sprint: March 23-29, 2026
# Focus: Video Processing Pipeline, UI Components, Testing
# =============================================================================

set -e

REPO="tomkabel/team21-vooglaadija"
SPRINT_NAME="Sprint 3: Core Features Implementation"
MILESTONE_DATE="2026-03-29T23:59:59Z"

echo "🚀 Setting up Sprint 3 for $REPO"
echo "================================================"

if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated. Run: gh auth login"
    exit 1
fi

echo "✅ Authentication verified"
echo ""

# ============================================================
# STEP 1: Create Labels
# ============================================================
echo "🏷️  Creating labels..."

gh label create "sprint-3" --color "F9D0C4" --description "Sprint 3 work" -R "$REPO" 2>/dev/null || echo "Label sprint-3 already exists"
gh label create "epic" --color "0052CC" --description "Epic - large body of work" -R "$REPO" 2>/dev/null || echo "Label epic already exists"
gh label create "priority-critical" --color "B60205" --description "Blocks release" -R "$REPO" 2>/dev/null || echo "Label priority-critical already exists"
gh label create "priority-high" --color "D93F0B" --description "Important" -R "$REPO" 2>/dev/null || echo "Label priority-high already exists"
gh label create "priority-medium" --color "FBCA04" --description "Normal priority" -R "$REPO" 2>/dev/null || echo "Label priority-medium already exists"
gh label create "type-feature" --color "1D76DB" --description "New feature" -R "$REPO" 2>/dev/null || echo "Label type-feature already exists"
gh label create "type-testing" --color "84B6EB" --description "Testing" -R "$REPO" 2>/dev/null || echo "Label type-testing already exists"
gh label create "area-webcodecs" --color "5319E7" --description "WebCodecs API" -R "$REPO" 2>/dev/null || echo "Label area-webcodecs already exists"
gh label create "area-ui" --color "D93F0B" --description "UI/UX" -R "$REPO" 2>/dev/null || echo "Label area-ui already exists"
gh label create "area-testing" --color "C2E0C6" --description "Testing Infrastructure" -R "$REPO" 2>/dev/null || echo "Label area-testing already exists"

echo "✅ Labels created"
echo ""

# ============================================================
# STEP 2: Create Milestone
# ============================================================
echo "📅 Creating Sprint 3 milestone..."

MILESTONE_RESULT=$(gh api repos/$REPO/milestones \
  --method POST \
  --field title="$SPRINT_NAME" \
  --field state=open \
  --field description="Week of Mar 23-29: Video processing pipeline, UI components, testing framework. First working features." \
  --field due_on="$MILESTONE_DATE" 2>/dev/null || echo "exists")

if [ "$MILESTONE_RESULT" = "exists" ]; then
    echo "⚠️  Milestone may already exist"
else
    echo "✅ Milestone created"
fi
echo ""

# ============================================================
# STEP 3: Create Epic Issue
# ============================================================
echo "📋 Creating Sprint 3 Epic..."

EPIC_BODY='## Epic Goal
Implement core video processing features and establish a solid UI foundation. This is where the application starts coming to life.

## Success Criteria
- [ ] Video can be loaded and processed client-side
- [ ] Basic editing features work (trim, format selection)
- [ ] UI component library established
- [ ] Testing framework in place with >60% coverage
- [ ] Error handling implemented

## Sprint Capacity
- **Total Available:** 60 hours (2 devs × 5 days × 6 hrs)
- **Planned:** 48 hours (80% capacity)
- **Buffer:** 12 hours

## Stories
1. WebCodecs Video Decoder (8 pts)
2. Format Selection & Conversion (5 pts)
3. Trim/Cut Feature (5 pts)
4. UI Component Library (5 pts)
5. Testing Framework Setup (3 pts)

**Total: 26 points**

## Risks
| Risk | Probability | Mitigation |
|------|-------------|------------|
| Browser compatibility issues | High | Feature detection, fallbacks |
| Performance problems | Medium | Web Workers, optimization |
| WebCodecs API limitations | Medium | Document limitations |

## Dependencies
- Sprint 2: Architecture Foundation (completed)
- Browser support for WebCodecs (Chrome 94+, Edge 94+)'

gh issue create \
  --title="[EPIC] Sprint 3: Core Features Implementation" \
  --body "$EPIC_BODY" \
  --label="epic" \
  --label="sprint-3" \
  --label="priority-high" \
  -R "$REPO"

echo "✅ Epic created"
echo ""

# ============================================================
# STEP 4: Create Story Issues
# ============================================================

echo "📝 Creating Sprint 3 Stories..."
echo ""

# Story 1: WebCodecs Decoder
STORY1_BODY='## User Story
As a user, I want to load video files so I can process them in the browser.

## Acceptance Criteria

### Video Loading
- [ ] Support MP4, WebM, MOV containers
- [ ] File size limit: 2GB (configurable)
- [ ] Drag & drop file input
- [ ] Progress indicator during load
- [ ] Video metadata extraction (duration, resolution, codec)

### WebCodecs Integration
- [ ] VideoDecoder configured for common codecs (H.264, VP9, AV1)
- [ ] Hardware acceleration detection
- [ ] Decode video frames to Canvas
- [ ] Frame rate detection and display

### Error Handling
- [ ] Invalid file format message
- [ ] Codec not supported detection
- [ ] Corrupt file handling
- [ ] Graceful fallbacks

### Performance
- [ ] Decode first frame for thumbnail (<1s)
- [ ] Memory management (don'"'"'t hold all frames)
- [ ] Web Worker for decoding

## Technical Notes
```javascript
// Example decoder setup
const decoder = new VideoDecoder({
  output: handleFrame,
  error: handleError
});
```

## Browser Support
- Chrome 94+
- Edge 94+
- Firefox: Partial (behind flag)
- Safari: Not supported (use fallback message)

## Estimated Effort
**8 story points** (~16 hours)

## Dependencies
- Sprint 2: Svelte 5 setup
- Sprint 2: pnpm workspaces

## Definition of Done
- [ ] Videos load from file picker
- [ ] Metadata displays correctly
- [ ] Errors handled gracefully
- [ ] Works in Chrome/Edge
- [ ] Demo video processed'

gh issue create \
  --title="[Sprint 3] Implement WebCodecs video decoder" \
  --body "$STORY1_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-3" \
  --label="priority-high" \
  --label="type-feature" \
  --label="area-webcodecs" \
  -R "$REPO"

echo "✅ Story 1 created"

# Story 2: Format Selection
STORY2_BODY='## User Story
As a user, I want to select output format so I can convert videos to my preferred format.

## Acceptance Criteria

### Supported Formats
- [ ] MP4 (H.264 baseline)
- [ ] WebM (VP9)
- [ ] GIF (for short clips)
- [ ] MP3 (audio extraction)

### Format Selection UI
- [ ] Dropdown with format options
- [ ] Format descriptions (use case, quality, size)
- [ ] Quality presets (Low/Medium/High)
- [ ] Estimated output size preview

### Technical Implementation
- [ ] VideoEncoder configuration per format
- [ ] Codec selection based on format
- [ ] Bitrate configuration
- [ ] Container muxing (mp4box.js or similar)

### Validation
- [ ] Disable incompatible formats for input
- [ ] Warn about quality loss
- [ ] Validate codec support before processing

## Technical Notes
```javascript
const encoder = new VideoEncoder({
  output: handleEncodedChunk,
  error: handleError
});
await encoder.configure({
  codec: "vp09.00.10.08",
  width: 1920,
  height: 1080
});
```

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Story 1: Video decoder

## Definition of Done
- [ ] All formats selectable
- [ ] Conversion preview works
- [ ] Quality settings apply
- [ ] Error messages clear'

gh issue create \
  --title="[Sprint 3] Implement format selection and conversion" \
  --body "$STORY2_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-3" \
  --label="priority-high" \
  --label="type-feature" \
  --label="area-webcodecs" \
  -R "$REPO"

echo "✅ Story 2 created"

# Story 3: Trim Feature
STORY3_BODY='## User Story
As a user, I want to trim video length so I can extract specific segments.

## Acceptance Criteria

### Trim UI
- [ ] Dual-handle range slider
- [ ] Start/end time inputs (MM:SS.ms)
- [ ] Current time display
- [ ] Trim preview (play selected range)

### Frame Preview
- [ ] Thumbnail strip showing video frames
- [ ] Click to seek
- [ ] Hover for timestamp
- [ ] Update on trim change

### Technical Implementation
- [ ] Seek to specific frames
- [ ] Calculate trim boundaries
- [ ] Update processing range
- [ ] Maintain precision (frame-accurate)

### UX Enhancements
- [ ] Zoom timeline for precision
- [ ] Keyboard shortcuts (arrows, space)
- [ ] Undo/redo trim changes
- [ ] Reset to full video

## Technical Approach
Use Canvas to render frame thumbnails from decoded video. Store trim boundaries in state.

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Story 1: Video decoder

## Definition of Done
- [ ] Trim handles draggable
- [ ] Time inputs functional
- [ ] Preview plays trim range
- [ ] Frame thumbnails display
- [ ] Keyboard shortcuts work'

gh issue create \
  --title="[Sprint 3] Implement video trim/cut feature" \
  --body "$STORY3_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-3" \
  --label="priority-high" \
  --label="type-feature" \
  --label="area-ui" \
  -R "$REPO"

echo "✅ Story 3 created"

# Story 4: UI Component Library
STORY4_BODY='## User Story
As a developer, I need reusable UI components so the interface is consistent.

## Acceptance Criteria

### Component Library
- [ ] Button component (variants: primary, secondary, danger, ghost)
- [ ] Input component (text, number, file)
- [ ] Select/Dropdown component
- [ ] Slider component (single, range)
- [ ] Progress bar component
- [ ] Modal/Dialog component
- [ ] Toast/Notification component
- [ ] Loading/Spinner component

### Svelte 5 Patterns
- [ ] Use $state for reactive data
- [ ] Use $derived for computed values
- [ ] Use $props for component properties
- [ ] Use snippets for reusable markup
- [ ] Event handling with callbacks

### Styling
- [ ] CSS custom properties (variables)
- [ ] Dark/light theme support
- [ ] Responsive design (mobile-first)
- [ ] Accessibility (ARIA labels, keyboard nav)

### Documentation
- [ ] Storybook or component docs
- [ ] Usage examples
- [ ] Props documentation

## Components Location
```
packages/ui/
├── Button.svelte
├── Input.svelte
├── Select.svelte
├── Slider.svelte
├── Progress.svelte
├── Modal.svelte
├── Toast.svelte
└── index.ts
```

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Sprint 2: Svelte 5 setup

## Definition of Done
- [ ] All components functional
- [ ] Stories/documented
- [ ] Accessible
- [ ] Responsive
- [ ] Dark mode support'

gh issue create \
  --title="[Sprint 3] Create reusable UI component library" \
  --body "$STORY4_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-3" \
  --label="priority-high" \
  --label="type-feature" \
  --label="area-ui" \
  -R "$REPO"

echo "✅ Story 4 created"

# Story 5: Testing Framework
STORY5_BODY='## User Story
As a developer, I need automated testing so I can catch bugs early.

## Acceptance Criteria

### Test Setup
- [ ] Vitest configured for unit tests
- [ ] Playwright configured for E2E tests
- [ ] Test utilities and helpers
- [ ] Mock data generators

### Unit Tests (>60% coverage)
- [ ] Utility functions tested
- [ ] Component rendering tests
- [ ] State management tests
- [ ] Validation logic tests

### E2E Tests (Critical paths)
- [ ] File upload flow
- [ ] Format selection flow
- [ ] Trim feature flow
- [ ] Export/download flow

### CI Integration
- [ ] Tests run in GitHub Actions
- [ ] Coverage reports generated
- [ ] Failed tests block merge
- [ ] Coverage badge in README

### Test Data
- [ ] Sample video files (small, various formats)
- [ ] Mock API responses
- [ ] Test fixtures

## Test Structure
```
packages/
├── utils/
│   └── *.test.ts
├── ui/
│   └── *.test.svelte
└── web/
    └── e2e/
        └── *.spec.ts
```

## Estimated Effort
**3 story points** (~6 hours)

## Dependencies
- Sprint 2: CI/CD setup
- Stories 1-4 (for test targets)

## Definition of Done
- [ ] Tests run in CI
- [ ] >60% coverage
- [ ] Critical paths covered
- [ ] Coverage badge visible'

gh issue create \
  --title="[Sprint 3] Set up testing framework with >60% coverage" \
  --body "$STORY5_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-3" \
  --label="priority-medium" \
  --label="type-testing" \
  --label="area-testing" \
  -R "$REPO"

echo "✅ Story 5 created"

# ============================================================
# STEP 5: Summary
# ============================================================
echo ""
echo "================================================"
echo "🎉 Sprint 3 Setup Complete!"
echo "================================================"
echo ""
echo "Repository: https://github.com/$REPO"
echo "Milestone: $SPRINT_NAME"
echo "Due: March 29, 2026"
echo ""
echo "Created:"
echo "  • 1 Epic"
echo "  • 5 Stories (26 points)"
echo "  • 10 Labels"
echo "  • 1 Milestone"
echo ""
echo "Next Steps:"
echo "  1. View issues: gh issue list -R $REPO --milestone '$SPRINT_NAME'"
echo "  2. Set up GitHub Project board"
echo "  3. Conduct Sprint Planning"
echo "  4. Begin WebCodecs implementation"
echo ""
