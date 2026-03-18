# Vooglaadija Fork-Plan
## Kursuse Projekt: Noorem-Tarkvaraarendajast Vanemarendajaks

---

## Ülevaade

**Projekti nimi:** Vooglaadija  
**Alus:** cobalt.tools (imputnet/cobalt) fork  
**Kursus:** Noorem-Tarkvaraarendajast Vanemarendajaks  
**Alguskuupäev:** 17.03.2026  
**Lõppkuupäev:** 10.05.2026 (8 nädalat)

---

## Projekti Kirjeldus

Vooglaadija on veebipõhine meedia-allalaadija, mis võimaldab kasutajatel alla laadida videosid ja helifaile populaarsetest platvormidest (YouTube, TikTok, Instagram, Twitter/X jne).

### Põhifunktsionaalsus
- URL-i sisestamine ja meedia allalaadimine
- Toetatud platvormid: YouTube, TikTok, Instagram, Twitter/X, Reddit, SoundCloud, Vimeo, VK, Bilibili jt
- Video- ja heliformaatide valik
- Kvaliteedi seaded
- CAPTCHA kaitse (Turnstile)
- API võtme autentimine

---

## Arhitektuur

### Olemasolev Struktuur
```
vooglaadija/
├── api/                    # Backend (Node.js + Express)
│   ├── src/
│   │   ├── core/          # API tuum (api.js, env.js)
│   │   ├── processing/    # URL parsimine, teenused (YouTube, TikTok jne)
│   │   ├── security/      # JWT, API võtmed, Turnstile
│   │   ├── store/         # Redis/Mälu rate limiting
│   │   ├── stream/        # FFmpeg, HLS, proxy
│   │   └── util/          # Testid, abifunktsioonid
│   └── package.json
├── web/                    # Frontend (SvelteKit + TypeScript)
│   ├── src/
│   │   ├── components/    # Svelte komponendid
│   │   ├── lib/           # API klient, seaded, state
│   │   └── routes/        # Leheküljed
│   └── package.json
├── packages/               # Jagatud paketid
│   ├── api-client/        # TypeScript API klient
│   └── version-info/      # Versiooniinfo
└── docs/                   # Dokumentatsioon
```

### Tehnoloogiad
- **Backend:** Node.js 18+, Express, Undici (HTTP klient), Zod (valideerimine)
- **Frontend:** SvelteKit, TypeScript, Vite
- **Andmebaas:** Redis (valikuline, rate limiting)
- **Container:** Docker, Docker Compose
- **CI/CD:** GitHub Actions
- **Turvalisus:** JWT, API võtmed, Turnstile CAPTCHA

---

## Arendusplaan (Sprintid)

### Sprint 2: 17.03 - 22.03 (Praegune)
**Eesmärk:** Arhitektuur paigas, esimesed endpointid/ekraanivaated

#### Ülesanded:
- [ ] **Projekti ülesseadmine**
  - Fork'i kinnitamine ja repositooriumi seadistamine
  - Tiimi õiguste haldamine
  - Development environment'i seadistamine
  
- [ ] **Backend põhi**
  - API struktuuri mõistmine ja dokumenteerimine
  - Esimesed endpointid: `GET /` (server info), `POST /` (meedia töötlemine)
  - Rate limiting seadistamine (mälu-põhine)
  
- [ ] **Frontend põhi**
  - SvelteKit projekti ülesehituse mõistmine
  - Põhiliste komponentide ülevaade
  - Esimesed vaated: avaleht, seaded
  
- [ ] **Dokumentatsiooni algus**
  - README.md kohandamine
  - API dokumentatsiooni uuendamine
  - Paigaldusjuhend

**Definition of Done:**
- Backend käivitub lokaalselt (`pnpm start` api kaustas)
- Frontend käivitub lokaalselt (`pnpm dev` web kaustas)
- API vastab päringutele
- Frontend suhtleb API-ga

**Hinnanguline aeg:** 6-8h inimese kohta

---

### Sprint 3: 23.03 - 29.03
**Eesmärk:** Põhifunktsionaalsus, põhiline kasutusjuht

#### Ülesanded:
- [ ] **Meedia allalaadimine**
  - URL parsimise lõplik implementatsioon
  - YouTube tugi (kõige populaarsem)
  - TikTok tugi
  - Instagram tugi
  
- [ ] **Frontendi kasutajaliides**
  - URL sisestusväli
  - Laadimise progress
  - Allalaadimise nupp
  - Formaadi valik (MP3, MP4, jne)
  
- [ ] **Veatöötlus**
  - Vigased URL-id
  - Mitte-toetatud platvormid
  - Võrgu vead
  
- [ ] **Testimise algus**
  - Ühiktestid backendis (Zod schema testid)
  - Manuaalsed testid frontendis

**Definition of Done:**
- Kasutaja saab sisestada URL-i ja alla laadida meediat
- Veatöötlus näitab arusaadavaid veateateid
- Vähemalt 3 platvormi toetatud (YouTube, TikTok, Instagram)

**Hinnanguline aeg:** 8-10h inimese kohta

---

### Sprint 4: 30.03 - 05.04
**Eesmärk:** Rakendus/teenus avalikult kättesaadav, CI/CD

#### Ülesanded:
- [ ] **Avalikult kättesaadav deployment**
  - Veebiserver seadistamine (nt Vercel, Netlify, või oma server)
  - API server deployment (nt Railway, Render, Fly.io, või oma server)
  - Domeeni seadistamine (valikuline)
  
- [ ] **CI/CD pipeline**
  - GitHub Actions workflow'd
  - Automaatne testimine PR-ides
  - Automaatne deployment main harule
  
- [ ] **Docker täiustused**
  - Docker Compose konfiguratsioon
  - Keskkonnamuutujate haldus
  
- [ ] **Jõudlus ja optimeerimine**
  - Võrgu päringute optimeerimine
  - Frontend bundle size
  - Puhverdamine (caching)

**Definition of Done:**
- Rakendus on ligipääsetav avalikult internetis
- Iga commit main harule deploy'itakse automaatselt
- CI/CD pipeline jookseb edukalt

**Hinnanguline aega:** 6-8h inimese kohta

---

### Sprint 5: 06.04 - 12.04
**Eesmärk:** Testimine, videopresentatsioon

#### Ülesanded:
- [ ] **Testimise täiustamine**
  - Backend testide laiendamine
  - Frontend testid (Playwright/Cypress)
  - Integratsioonitestid
  
- [ ] **Turvalisuse kontroll**
  - API võtmete haldus
  - Rate limiting testimine
  - CAPTCHA töö kontroll
  
- [ ] **Videopresentatsioon**
  - 2-3 minutiline demo video
  - Projekti tutvustus
  - Funktsionaalsuse näitamine
  
- [ ] **Bugide parandamine**
  - Sprint 1-4 leitud bugide parandus

**Definition of Done:**
- Testide katvus > 60%
- Video esitamiseks valmis
- Kriitilised bugid parandatud

**Hinnanguline aeg:** 8-10h inimese kohta

---

### Sprint 6: 20.04 - 26.04 (Pärast vaheaega)
**Eesmärk:** Error handling, UX/UI viimistlemine

#### Ülesanded:
- [ ] **Veatöötluse täiustamine**
  - Ühtne veahaldussüsteem
  - Kasutajasõbralikud veateated
  - Vealogimine
  
- [ ] **UX/UI täiustused**
  - Mobiilivaate optimeerimine
  - Laadimise indikaatorid
  - Animatsioonid
  - Teavitused (toast notifications)
  
- [ ] **Lisafunktsionaalsus**
  - Queue (järjekord) mitme faili allalaadimiseks
  - Ajalugu (viimased allalaadimised)
  - Seadete salvestamine
  
- [ ] **Ligipääsetavus (a11y)**
  - Klaviatuuri navigeerimine
  - Ekraanilugeja tugi
  - Kontrastid

**Definition of Done:**
- Veateated on kasutajasõbralikud
- Mobiilivaade töötab hästi
- WCAG 2.1 AA nõuded täidetud (põhimõtteliselt)

**Hinnanguline aeg:** 8-10h inimese kohta

---

### Sprint 7: 27.04 - 03.05
**Eesmärk:** Dokumentatsioon, reliis, esimene ettekanne

#### Ülesanded:
- [ ] **Dokumentatsioon**
  - API dokumentatsiooni täiendamine
  - Paigaldusjuhend
  - Arendusjuhend (CONTRIBUTING.md)
  - Arhitektuuri dokumentatsioon
  
- [ ] **Reliis**
  - Versioonimine (semver)
  - Changelog
  - GitHub Release
  
- [ ] **Ettekande ettevalmistus**
  - Slaidid
  - Demo stsenaarium
  - Koodi näited
  
- [ ] **Tagasiside kogumine**
  - Esialgne demo
  - Mentorilt tagasiside
  - Tiimisisesed review'd

**Definition of Done:**
- Dokumentatsioon on täielik
- Reliis on loodud
- Ettekanne on valmis

**Hinnanguline aeg:** 6-8h inimese kohta

---

### Sprint 8: 04.05 - 10.05
**Eesmärk:** Refleksioon, ettekande ettevalmistus

#### Ülesanded:
- [ ] **Refleksioon**
  - Projektikogemuse analüüs
  - Õpitu ülevaade
  - Mis töötas hästi, mis mitte
  
- [ ] **Lõplik ettekanne**
  - Ettekande proovid
  - Slaidide viimistlemine
  - Demo ettevalmistus
  
- [ ] **Projekti lõpetamine**
  - Viimased bugiparandused
  - Dokumentatsiooni viimased täiendused
  - Koodi puhastus
  
- [ ] **Tulevikuplaanid**
  - Võimalikud edasiarendused
  - Hooldusplaan

**Definition of Done:**
- Ettekanne on proovitud
- Projekt on esitlemiseks valmis
- Tagasiside on kogutud

**Hinnanguline aeg:** 4-6h inimese kohta

---

## Tehnilised Nõuded (Kursuse Nõuded)

| Nõue | Olemas | Plaan |
|------|--------|-------|
| Backend | ✅ Express.js API | Laiendada endpointe |
| Frontend | ✅ SvelteKit | Täiustada UI/UX |
| Andmebaas | ⚠️ Redis (valikuline) | Lisada püsiv andmebaas (valikuline) |
| REST API | ✅ On olemas | Dokumenteerida |
| CI/CD pipeline | ⚠️ Osaliselt | Täiustada deployment |
| Avalikult kättesaadav | ❌ | Sprint 4 |
| Testitud | ⚠️ Osaliselt | Sprint 5 |
| Turvalisus | ✅ JWT, API võtmed, Rate limiting | Sprint 5 kontroll |

---

## Võimalikud Täiendused (Kui Aega Üle Jääb)

### Funktsionaalsus
- [ ] Rohkem platvorme (Spotify, Apple Music, Bandcamp)
- [ ] Playlistide allalaadimine
- [ ] Metadata redigeerimine
- [ ] Subtiitrite allalaadimine
- [ ] Batch allalaadimine
- [ ] Brauseri laiendus

### Tehniline
- [ ] GraphQL API
- [ ] WebSocket reaalajas uuendused
- [ ] Mikroteenuste arhitektuur
- [ ] Kubernetes deployment
- [ ] Prometheus/Grafana monitooring

### Kasutajakogemus
- [ ] Kasutajakontod
- [ ] Allalaadimiste ajalugu
- [ ] Lemmikud
- [ ] Otsing
- [ ] Mobiilirakendus (PWA)

---

## Rollid ja Vastutused

### Tiimiliikmed
- **Developer 1:** Backend, API, Turvalisus
- **Developer 2:** Frontend, UI/UX, Testimine
- **Developer 3:** DevOps, CI/CD, Dokumentatsioon

### Mentor
- Code review
- Arhitektuuri nõustamine
- Planeerimise ja retro tulemuste ülevaatus

---

## Git Töövoog

1. **Harud:**
   - `main` - tootmiseks
   - `develop` - arenduseks (valikuline)
   - `feature/nimi` - funktsionaalsused
   - `bugfix/nimi` - bugiparandused

2. **Pull Requestid:**
   - Iga funktsionaalsus oma PR-is
   - Code review enne merge'imist
   - CI peab läbima

3. **Commit sõnumid:**
   - Selged ja kirjeldavad
   - Viide issue/ülesande numbrile

---

## Aja Planeerimine

| Sprint | Planeeritud | Tegelik | Märkused |
|--------|-------------|---------|----------|
| 2 | 6-8h | - | Arhitektuur |
| 3 | 8-10h | - | Põhifunktsionaalsus |
| 4 | 6-8h | - | Deployment |
| 5 | 8-10h | - | Testimine, video |
| 6 | 8-10h | - | UX/UI |
| 7 | 6-8h | - | Dokumentatsioon |
| 8 | 4-6h | - | Refleksioon |
| **Kokku** | **46-60h** | - | - |

---

## Riskid ja Lahendused

| Risk | Tõenäosus | Mõju | Lahendus |
|------|-----------|------|----------|
| API muutused (YouTube) | Kõrge | Kõrge | Regulaarsed uuendused, fallback'id |
| Rate limiting blokeerimine | Keskmine | Keskmine | Proxy rotation, viivitused |
| Deployment probleemid | Keskmine | Kõrge | Varajane testing, mitu keskkonda |
| Ajanappus | Keskmine | Keskmine | Prioriteedid, MVP fookus |
| Tiimiliikme puudumine | Madal | Kõrge | Teadmiste jagamine, dokumentatsioon |

---

## Edukriteeriumid

1. **Miinimum (Hinne 3):**
   - Põhifunktsionaalsus töötab
   - Rakendus on avalikult kättesaadav
   - Testid on olemas
   - Dokumentatsioon on olemas

2. **Hea (Hinne 4):**
   - Kõik miinimum nõuded
   - Mitme platvormi tugi
   - Hea veatöötlus
   - CI/CD pipeline

3. **Suurepärane (Hinne 5):**
   - Kõik eelnev
   - Rohkem kui 5 platvormi
   - Täielik testimine
   - Lõppkasutajale valmis toode
   - Lõpuesitlus on professionaalne

---

## Kasulikud Lingid

- **Cobalt API docs:** `/docs/api.md`
- **Cobalt env variables:** `/docs/api-env-variables.md`
- **Run instance:** `/docs/run-an-instance.md`
- **Protect instance:** `/docs/protect-an-instance.md`
- **GitHub Actions:** `/.github/workflows/`

---

## Märkused

See plaan on elav dokument. Iga sprinti lõpus (retro) uuendatakse plaani vastavalt tegelikule olukorrale ja tagasisidele.

**Viimati uuendatud:** 17.03.2026  
**Järgmine uuendus:** 22.03.2026 (pärast Sprint 2)
