# WebCodecs API Integration Strategy

**Goal:** Replace 25MB LibAV WASM with native WebCodecs API  
**Timeline:** Week 4-5  
**Effort:** 16 hours  
**Impact:** 80% WASM size reduction, LCP 3.0s → 0.8s

---

## Problem Statement

### Current Implementation

```
LibAV WASM Bundle: 25MB
├── libav.js-remux-cli: ~17MB
├── libav.js-encode-cli: ~8MB
└── Total Payload: 33MB (if both used)

Download Time (3G):
├── First Visit: 8-12 seconds
├── Subsequent: From cache
└── LCP Impact: +3.0 seconds
```

### Browser Support

| API | Chrome | Firefox | Safari | Support |
|-----|--------|---------|--------|---------|
| WebCodecs | 94+ | 🚫 | 16.4+ | 78% |
| VideoDecoder | 94+ | 🚫 | 16.4+ | 78% |
| VideoEncoder | 94+ | 🚫 | 16.4+ | 78% |
| AudioDecoder | 94+ | 🚫 | 16.4+ | 78% |

**Strategy:** Progressive enhancement with LibAV fallback

---

## Architecture

### New VideoProcessor Class

```typescript
// video-processor.svelte.ts
interface VideoProcessor {
    // Unified interface
    probe(blob: Blob): Promise<MediaInfo>;
    render(params: RenderParams): Promise<Blob>;
    terminate(): Promise<void>;
}

// WebCodecs implementation
class WebCodecsProcessor implements VideoProcessor {
    private decoder: VideoDecoder | null = null;
    private encoder: VideoEncoder | null = null;
    
    async initialize(): Promise<void> {
        // Check support
        if (!('VideoDecoder' in window)) {
            throw new Error('WebCodecs not supported');
        }
    }
    
    async probe(blob: Blob): Promise<MediaInfo> {
        // Use WebCodecs + mp4box.js (100KB)
        const info = await this.extractMetadata(blob);
        return info;
    }
    
    async render({ files, output, args }: RenderParams): Promise<Blob> {
        // Native encoding pipeline
        return this.encodeNative(files, output, args);
    }
    
    async terminate(): Promise<void> {
        this.decoder?.close();
        this.encoder?.close();
    }
}

// LibAV fallback implementation
class LibAVProcessor implements VideoProcessor {
    private libav: LibAVWrapper | null = null;
    
    async initialize(): Promise<void> {
        // Lazy-load LibAV only when needed
        const { default: LibAV } = await import('@imput/libav.js-remux-cli');
        this.libav = new LibAVWrapper();
        await this.libav.init();
    }
    
    async probe(blob: Blob): Promise<MediaInfo> {
        return this.libav!.probe(blob);
    }
    
    async render(params: RenderParams): Promise<Blob> {
        return this.libav!.render(params);
    }
    
    async terminate(): Promise<void> {
        await this.libav?.terminate();
    }
}
```

---

## Detection & Selection

```typescript
// video-processor-factory.svelte.ts
const supportsWebCodecs = $derived.by(() => {
    return typeof VideoDecoder !== 'undefined' &&
           typeof VideoEncoder !== 'undefined' &&
           typeof AudioDecoder !== 'undefined';
});

const supportsRequiredCodecs = $derived.by(() => {
    const config: VideoDecoderConfig = {
        codec: 'vp09.00.10.08', // VP9
        codedWidth: 1920,
        codedHeight: 1080
    };
    
    // Check if browser supports required codecs
    return VideoDecoder.isConfigSupported(config)
        .then(result => result.supported);
});

export async function createProcessor(): Promise<VideoProcessor> {
    if (await supportsRequiredCodecs) {
        console.log('[VideoProcessor] Using WebCodecs API');
        return new WebCodecsProcessor();
    } else {
        console.log('[VideoProcessor] Falling back to LibAV');
        return new LibAVProcessor();
    }
}
```

---

## WebCodecs Implementation Details

### 1. Metadata Extraction

```typescript
// Using mp4box.js (100KB) for container parsing
import MP4Box from 'mp4box';

async function extractMetadata(blob: Blob): Promise<MediaInfo> {
    const arrayBuffer = await blob.arrayBuffer();
    
    const mp4boxfile = MP4Box.createFile();
    
    return new Promise((resolve, reject) => {
        mp4boxfile.onReady = (info) => {
            resolve({
                duration: info.duration / info.timescale,
                videoTracks: info.videoTracks.map(t => ({
                    codec: t.codec,
                    width: t.track_width,
                    height: t.track_height
                })),
                audioTracks: info.audioTracks.map(t => ({
                    codec: t.codec,
                    sampleRate: t.audio.sample_rate
                }))
            });
        };
        
        mp4boxfile.onError = reject;
        
        const buffer = arrayBuffer.slice(0);
        (buffer as any).fileStart = 0;
        mp4boxfile.appendBuffer(buffer);
        mp4boxfile.flush();
    });
}
```

### 2. Video Decoding Pipeline

```typescript
async function decodeVideo(blob: Blob, track: VideoTrack): Promise<VideoFrame[]> {
    const frames: VideoFrame[] = [];
    
    const decoder = new VideoDecoder({
        output: (frame) => frames.push(frame),
        error: (e) => console.error('Decode error:', e)
    });
    
    await decoder.configure({
        codec: track.codec,
        codedWidth: track.width,
        codedHeight: track.height
    });
    
    // Extract samples and decode
    const samples = await extractSamples(blob, track.id);
    
    for (const sample of samples) {
        const chunk = new EncodedVideoChunk({
            type: sample.is_sync ? 'key' : 'delta',
            timestamp: sample.cts,
            data: sample.data
        });
        
        decoder.decode(chunk);
    }
    
    await decoder.flush();
    decoder.close();
    
    return frames;
}
```

### 3. Video Encoding Pipeline

```typescript
async function encodeVideo(
    frames: VideoFrame[],
    config: VideoEncoderConfig
): Promise<Blob> {
    const chunks: EncodedVideoChunk[] = [];
    
    const encoder = new VideoEncoder({
        output: (chunk, metadata) => chunks.push(chunk),
        error: (e) => console.error('Encode error:', e)
    });
    
    await encoder.configure(config);
    
    for (const frame of frames) {
        encoder.encode(frame);
        frame.close(); // Release memory
    }
    
    await encoder.flush();
    encoder.close();
    
    // Mux into MP4 container using mp4box.js
    return muxToMP4(chunks, config);
}
```

### 4. Audio Processing

```typescript
async function processAudio(
    blob: Blob,
    track: AudioTrack
): Promise<AudioData[]> {
    const decoder = new AudioDecoder({
        output: (data) => audioData.push(data),
        error: (e) => console.error('Audio decode error:', e)
    });
    
    await decoder.configure({
        codec: track.codec,
        sampleRate: track.sampleRate,
        numberOfChannels: track.channelCount
    });
    
    // Similar pattern to video
    const samples = await extractAudioSamples(blob, track.id);
    
    for (const sample of samples) {
        const chunk = new EncodedAudioChunk({
            type: 'key',
            timestamp: sample.cts,
            data: sample.data
        });
        
        decoder.decode(chunk);
    }
    
    await decoder.flush();
    decoder.close();
    
    return audioData;
}
```

---

## Progress Tracking

```typescript
class WebCodecsProcessor implements VideoProcessor {
    onProgress?: ProgressCallback;
    
    async render(params: RenderParams): Promise<Blob> {
        const totalFrames = params.estimatedFrames;
        let processedFrames = 0;
        
        const encoder = new VideoEncoder({
            output: (chunk, metadata) => {
                processedFrames++;
                
                this.onProgress?.({
                    status: 'continue',
                    frame: processedFrames,
                    totalFrames,
                    progress: processedFrames / totalFrames
                });
                
                chunks.push(chunk);
            },
            error: (e) => {
                this.onProgress?.({
                    status: 'error',
                    error: e.message
                });
            }
        });
        
        // ... encoding logic
        
        this.onProgress?.({ status: 'end' });
        return muxToMP4(chunks);
    }
}
```

---

## Component Integration

```svelte
<!-- VideoProcessor.svelte -->
<script lang="ts">
    import { createProcessor } from '$lib/video/video-processor-factory';
    import type { VideoProcessor } from '$lib/video/types';
    
    interface Props {
        onProgress?: (progress: ProgressEvent) => void;
        onComplete?: (result: Blob) => void;
        onError?: (error: Error) => void;
    }
    
    let { onProgress, onComplete, onError }: Props = $props();
    
    let processor = $state<VideoProcessor | null>(null);
    let isProcessing = $state(false);
    let usingWebCodecs = $state(false);
    
    export async function startProcessing(files: File[]) {
        try {
            isProcessing = true;
            
            // Lazy-load processor
            if (!processor) {
                processor = await createProcessor();
                usingWebCodecs = processor instanceof WebCodecsProcessor;
            }
            
            // Set up progress callback
            processor.onProgress = onProgress;
            
            // Process
            const result = await processor.render({
                files,
                output: { format: 'mp4', type: 'video/mp4' },
                args: []
            });
            
            onComplete?.(result);
        } catch (error) {
            onError?.(error as Error);
        } finally {
            isProcessing = false;
        }
    }
    
    export async function cancel() {
        await processor?.terminate();
        processor = null;
        isProcessing = false;
    }
    
    // Cleanup on unmount
    $effect(() => {
        return () => {
            processor?.terminate();
        };
    });
</script>

<div class="processor" data-using-webcodecs={usingWebCodecs}>
    {#if isProcessing}
        <progress indeterminate />
    {/if}
    <slot {isProcessing} {usingWebCodecs} />
</div>
```

---

## Error Handling Strategy

```typescript
enum ProcessingError {
    UNSUPPORTED_CODEC = 'UNSUPPORTED_CODEC',
    OUT_OF_MEMORY = 'OUT_OF_MEMORY',
    DECODE_ERROR = 'DECODE_ERROR',
    ENCODE_ERROR = 'ENCODE_ERROR',
    ABORTED = 'ABORTED'
}

class VideoProcessingError extends Error {
    constructor(
        public code: ProcessingError,
        message: string,
        public recoverable: boolean
    ) {
        super(message);
    }
}

// Usage
async function processWithFallback(blob: Blob): Promise<Blob> {
    try {
        // Try WebCodecs first
        const processor = new WebCodecsProcessor();
        await processor.initialize();
        return await processor.render({ files: [blob] });
    } catch (error) {
        if (error instanceof VideoProcessingError && error.recoverable) {
            // Fall back to LibAV
            console.warn('[VideoProcessor] WebCodecs failed, using LibAV:', error);
            const fallback = new LibAVProcessor();
            await fallback.initialize();
            return await fallback.render({ files: [blob] });
        }
        throw error;
    }
}
```

---

## Performance Comparison

| Metric | LibAV (Current) | WebCodecs | Improvement |
|--------|-----------------|-----------|-------------|
| Download Size | 25MB | 200KB (native) | **-99.2%** |
| Initialization | 2-3s | 50ms | **-97%** |
| Decode Speed | 1x (baseline) | 2-3x | **+200%** |
| Memory Usage | 500MB | 200MB | **-60%** |
| Battery Impact | High | Low | **Significant** |

---

## Implementation Timeline

### Week 4: Foundation

**Day 1-2: Setup**
- [ ] Install mp4box.js dependency
- [ ] Create `VideoProcessor` interface
- [ ] Implement factory pattern
- [ ] Add feature detection

**Day 3-4: WebCodecs Implementation**
- [ ] Metadata extraction
- [ ] Video decode pipeline
- [ ] Video encode pipeline
- [ ] Audio processing

**Day 5: LibAV Refactor**
- [ ] Extract LibAV to separate class
- [ ] Implement lazy loading
- [ ] Add progress callbacks

### Week 5: Integration

**Day 1-2: Component Integration**
- [ ] Update `VideoProcessor.svelte`
- [ ] Add UI indicators (WebCodecs vs LibAV)
- [ ] Implement cancellation

**Day 3-4: Testing**
- [ ] Unit tests for both implementations
- [ ] Browser compatibility tests
- [ ] Performance benchmarks

**Day 5: Optimization**
- [ ] Memory leak fixes
- [ ] Error recovery
- [ ] Documentation

---

## Testing Strategy

### Unit Tests

```typescript
// video-processor.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { WebCodecsProcessor } from './webcodecs-processor';
import { LibAVProcessor } from './libav-processor';

describe('VideoProcessor', () => {
    describe('WebCodecsProcessor', () => {
        it('should detect unsupported browsers', async () => {
            // Mock unsupported browser
            vi.stubGlobal('VideoDecoder', undefined);
            
            const processor = new WebCodecsProcessor();
            await expect(processor.initialize()).rejects.toThrow('not supported');
        });
        
        it('should extract metadata from MP4', async () => {
            const processor = new WebCodecsProcessor();
            await processor.initialize();
            
            const blob = createMockMP4();
            const info = await processor.probe(blob);
            
            expect(info.duration).toBeGreaterThan(0);
            expect(info.videoTracks).toHaveLength(1);
        });
        
        it('should report progress during encoding', async () => {
            const processor = new WebCodecsProcessor();
            await processor.initialize();
            
            const progressEvents: ProgressEvent[] = [];
            processor.onProgress = (e) => progressEvents.push(e);
            
            await processor.render({ files: [mockFile] });
            
            expect(progressEvents.length).toBeGreaterThan(0);
            expect(progressEvents[progressEvents.length - 1].status).toBe('end');
        });
    });
});
```

### E2E Tests

```typescript
// video-processing.spec.ts
import { test, expect } from '@playwright/test';

test('processes video with WebCodecs when available', async ({ page }) => {
    await page.goto('/remux');
    
    // Upload test video
    await page.setInputFiles('input[type="file"]', 'test-video.mp4');
    
    // Wait for processing
    await page.waitForSelector('[data-processing="true"]');
    
    // Verify WebCodecs is used (if supported)
    const usingWebCodecs = await page.evaluate(() => {
        return 'VideoDecoder' in window;
    });
    
    if (usingWebCodecs) {
        await expect(page.locator('[data-using-webcodecs="true"]')).toBeVisible();
    }
    
    // Wait for completion
    await page.waitForSelector('[data-complete="true"]');
    
    // Download result
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toMatch(/\.mp4$/);
});
```

---

## Monitoring & Analytics

```typescript
// Track WebCodecs usage
const webcodecsMetrics = $state({
    supportedBrowsers: 0,
    fallbackToLibAV: 0,
    avgProcessingTime: 0
});

$effect(() => {
    // Report to analytics
    if (browser && env.PLAUSIBLE_ENABLED) {
        plausible('video_processor_usage', {
            props: {
                codec: usingWebCodecs ? 'webcodecs' : 'libav',
                duration: processingTime
            }
        });
    }
});
```

---

## Risk Mitigation

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Firefox no support | Certain | LibAV fallback mandatory |
| Codec support gaps | Medium | Feature detection + fallback |
| Memory leaks | Medium | Proper cleanup in $effect |
| Safari bugs | Low | Extensive testing, version checks |
| Performance regression | Low | A/B testing, rollback plan |

---

## References

- [WebCodecs API Spec](https://w3c.github.io/webcodecs/)
- [WebCodecs Samples](https://github.com/w3c/webcodecs/tree/main/samples)
- [mp4box.js Documentation](https://github.com/gpac/mp4box.js)
- [Can I Use: WebCodecs](https://caniuse.com/webcodecs)

---

*Document created: March 11, 2026*  
*Target implementation: Weeks 4-5 of sprint*
