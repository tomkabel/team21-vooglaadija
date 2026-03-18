# Template: Adding a New Media Service

Use this template when implementing support for a new media platform in Cobalt.

## Pre-Implementation Checklist

- [ ] Research platform's media URLs and page structure
- [ ] Identify URL patterns (posts, videos, stories, etc.)
- [ ] Check if platform requires authentication/cookies
- [ ] Test if content has region restrictions
- [ ] Verify rate limits and respect robots.txt

## Implementation Steps

### 1. Add URL Patterns

Edit `api/src/processing/service-patterns.js`:

```javascript
export const testers = {
    // ... existing testers

    "newservice": pattern =>
        pattern.postId?.length <= 20 ||
        pattern.shortLink?.length <= 10,
}
```

Add to `api/src/processing/url.js` (if needed for URL normalization):

```javascript
const patterns = {
    // ... existing patterns
    
    "newservice": [
        /newservice\.com\/(?:p|post)\/([a-zA-Z0-9_-]{1,20})/,
        /newservice\.com\/s\/([a-zA-Z0-9_-]{1,10})/
    ],
}
```

### 2. Create Service Module

Create `api/src/processing/services/newservice.js`:

```javascript
import Cookie from "../cookie/cookie.js";
import { genericUserAgent } from "../../config.js";
import { updateCookie } from "../cookie/manager.js";

export default async function(obj) {
    const cookie = new Cookie({});
    
    // Handle short links if present
    let postId = obj.postId;
    if (!postId && obj.shortLink) {
        // Resolve short link
        const res = await fetch(`https://newservice.com/s/${obj.shortLink}`, {
            redirect: "manual",
            headers: { "user-agent": genericUserAgent }
        });
        // Extract postId from redirect or response
    }
    
    if (!postId) return { error: "fetch.short_link" };
    
    // Fetch content page
    const res = await fetch(`https://newservice.com/post/${postId}`, {
        headers: {
            "user-agent": genericUserAgent,
            cookie,
        }
    });
    updateCookie(cookie, res.headers);
    
    const html = await res.text();
    
    // Extract metadata from HTML/JSON
    let metadata;
    try {
        // Parse JSON data from script tag
        const json = html
            .split('<script type="application/json">')[1]
            .split('</script>')[0];
        metadata = JSON.parse(json);
    } catch {
        return { error: "fetch.fail" };
    }
    
    // Check for unavailable content
    if (!metadata?.post) {
        return { error: "fetch.empty" };
    }
    
    if (metadata.post.isDeleted) {
        return { error: "content.post.unavailable" };
    }
    
    // Extract media URLs
    const filenameBase = `newservice_${metadata.post.author}_${postId}`;
    
    // Video handling
    if (!obj.isAudioOnly && metadata.post.videoUrl) {
        return {
            urls: metadata.post.videoUrl,
            filename: `${filenameBase}.mp4`,
            headers: { cookie }
        };
    }
    
    // Audio handling
    if (metadata.post.audioUrl) {
        return {
            urls: metadata.post.audioUrl,
            audioFilename: `${filenameBase}_audio`,
            isAudioOnly: true,
            bestAudio: "m4a",  // or mp3, opus
            headers: { cookie }
        };
    }
    
    // Gallery/photo handling
    if (metadata.post.images?.length) {
        const picker = metadata.post.images.map((img, i) => ({
            type: "photo",
            url: img.url
        }));
        
        return {
            picker,
            urls: metadata.post.audioUrl,  // Optional background audio
            audioFilename: `${filenameBase}_audio`,
            isAudioOnly: true,
            bestAudio: "m4a",
            headers: { cookie }
        };
    }
    
    return { error: "fetch.empty" };
}
```

### 3. Wire Up Service

Edit `api/src/processing/match.js`:

```javascript
// Add import at top
import newservice from "./services/newservice.js";

// Add case in switch statement
switch (host) {
    // ... existing cases
    
    case "newservice":
        r = await newservice({
            postId: patternMatch.postId,
            shortLink: patternMatch.shortLink,
            isAudioOnly,
            // ... other params
        }, {
            dispatcher
        });
        break;
}
```

### 4. Add Service Alias (Optional)

Edit `api/src/processing/service-alias.js`:

```javascript
const friendlyNames = {
    // ... existing aliases
    "newservice": "NewService",
};
```

### 5. Testing

Create test cases in `api/src/util/test.js` or test manually:

```bash
cd api
npm start

# Test in another terminal
curl -X POST http://localhost:9000/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://newservice.com/post/abc123"}'
```

## Response Format Reference

### Video Response
```javascript
{
  urls: "https://...",              // Single URL or array of URLs
  filename: "newservice_user_id.mp4",
  headers: { cookie },              // Cookie for auth if needed
  subtitles: "https://...",         // Optional subtitle URL
  fileMetadata: {                   // Optional metadata
    title: "...",
    artist: "..."
  }
}
```

### Audio Response
```javascript
{
  urls: "https://...",
  audioFilename: "newservice_user_id_audio",
  isAudioOnly: true,
  bestAudio: "m4a",                 // "m4a" | "mp3" | "opus"
  fileMetadata: {                   // Optional ID3 metadata
    title: "...",
    artist: "...",
    album: "...",
    date: "..."
  },
  cover: "https://..."              // Optional album art
}
```

### Gallery Response
```javascript
{
  picker: [
    { type: "photo", url: "https://..." },
    { type: "photo", url: "https://..." }
  ],
  urls: "https://...",              // Optional audio for slideshow
  audioFilename: "...",
  isAudioOnly: true,
  bestAudio: "m4a",
  headers: { cookie }
}
```

## Error Codes Reference

| Code | Usage |
|------|-------|
| `fetch.fail` | Network error or parsing failure |
| `fetch.empty` | No media found in content |
| `fetch.short_link` | Could not resolve short URL |
| `content.too_long` | Exceeds duration limit |
| `content.region` | Region-blocked content |
| `content.paid` | Subscription/paid content |
| `content.post.unavailable` | Deleted or private post |
| `content.post.age` | Age-restricted content |
| `link.unsupported` | URL pattern not matched |

## Best Practices

1. **Cookie Management**: Always use `Cookie` class and `updateCookie()`
2. **Error Handling**: Return specific error codes, don't throw
3. **Rate Limiting**: Be respectful of platform resources
4. **Short Links**: Resolve and re-extract pattern matches
5. **User Agents**: Use `genericUserAgent` from config
6. **Audio Formats**: Set `bestAudio` to "m4a", "mp3", or "opus"
7. **Metadata**: Include `fileMetadata` for audio tracks when available
8. **Testing**: Test with various content types (video, audio, photos)

## Common Patterns

### Extracting JSON from HTML
```javascript
const json = html
    .split('<script id="__DATA__" type="application/json">')[1]
    .split('</script>')[0];
const data = JSON.parse(json);
```

### Handling Short Links
```javascript
const html = await fetch(shortUrl, {
    redirect: "manual",
    headers: { "user-agent": genericUserAgent }
}).then(r => r.text());

// Extract full URL from redirect or page content
const fullUrl = html.match(/href="(https:\/\/[^"]+)"/)[1];
```

### Caching Client IDs
```javascript
const cached = { version: '', id: '' };

async function getClientId() {
    if (cached.id) return cached.id;
    // Fetch and cache
    cached.id = await fetchClientId();
    return cached.id;
}
```
