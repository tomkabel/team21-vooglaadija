# 🚀 @here Team 21 - Vooglaadija otsib tegijaid!

## 📋 Mis on Vooglaadija?

**Vooglaadija** on minimalistlik, kasutajasõbralik meedia allalaadimisteenus – *"kleebi URL, saa fail, unusta kõik"* – kuid toodetud täiesti **production-ready** vormis.

Meie olemasolev monorepo (Node.js Express backend + Svelte frontend) on juba tehniliselt tugev, kuid nüüd migreerime see **AWS ECS Fargate'ile** ja lisame sügavalt integreeritud **monitooringu** ning **automatiseeritud CI/CD** võimalused.

---

## 🎯 Mis oleme täpselt kursuse käsitlusel?

Kõik tehnoloogiad johtuvad otse **tarkvarainseneri kursuse teemade**:

| Teema | Meie rakendus |
|-------|---------------|
| **Frontend & Backend** | SvelteKit (frontend) + Express.js (backend) |
| **Database** | PostgreSQL + Prisma (anonüümne statistika) |
| **CI/CD, Docker** | GitHub Actions + multi-stage Docker build |
| **AWS cloud** | ECS Fargate, RDS, ElastiCache, CloudFront |
| **Performance** | Node.js clustering, Redis cache, CDN |
| **Profiling** | OpenTelemetry, Jaeger tracing |
| **Monitoring** | Prometheus metrikad + Grafana dashboards |
| **Security** | OWASP, rate limiting, JWT, CORS, secret management |
| **Architecture** | Microservices, event-driven, circuit breaker |

---

## 🔧 **Mis lisame?** (ja miks?)

### ✅ **Redise** – juba töös
- Rate limiting klastriülene
- Tunnelite metaandmete jagamine
- Asünkroonne töötlusjärjekord

### ➕ **PostgreSQL + Prisma**
- **Mida salvestame?** Ainult **anonüümne statistika**:
  - Milliseid teenuseid kui palju kasutatakse
  - õnnestunud/ebaõnnestunud allalaadimised (ilma URL'ideta)
  - Süsteemi operatorile: kas süsteem töötab korralikult?
- **Mida EI salvestata:** kasutajakonto, IP-aadressid, allalaadimisajalugu

### 📊 **OpenTelemetry + Jaeger**
- Distributed tracing kogu request flow'ile
- Performance bottleneck'ide leidmine
- Error rate'i analüüs

### 📈 **Prometheus + Grafana**
- Reaalajas metrikad: request rate, latency, error rate
- Custom dashboardid klastrite ülevaateks
- Alerting võimalused

### 🛡️ **API Gateway + Circuit Breaker**
- Rate limiting (lisaks Redisele)
- Fail-fast kaitse allika defekti korral
- Request routing ja load balancing

---

## 👥 **Kes meid vajame?**

Me otsime **tõsiseid kaastöötajaid**, kes tahavad ** praktilisi kogemusi** saada järgmistelt aladelt:

### 🔧 **DevOps / Infrastruktuuri spetsialist**
- Terraform/CloudFormation (AWS)
- ECS Fargate seadistamine
- CI/CD pipeline'i tugevdamine
- Secrets management (AWS Secrets Manager)

### ⚡ **Node.js performance expert**
- Clustering ja memory management
- Profiling (clinic.js, 0x)
- Garbage collection tuning

### 📊 **Database & Monitoring spetsialist**
- PostgreSQL/Prisma optimiseerimine
- Prometheus metrics design
- Grafana dashboardid

### 🔒 **Security enthusiast**
- OWASP Top 10 rakendamine
- JWT turvalisus
- API rate limiting strateegiad

---

## 🏆 **Miks just meiega?**

1. **Praktiline kogemus** – tegemist on **täielikult töötava** rakendusega, mitte teoreetilise prototüübiga
2. **Kõik teemad katetud** – saad oma käed kogu DevOps/Cloud stack'iga
3. **Reaalsed AWS ressursid** – kasutame õigeid pilveteenuseid, mitte locally emuleeritud
4. **Professionaalsed standardid** – koodikvaliteet, testing, documentation
5. **Eetiline raamistik** – **ei ole piraatlusvahend**! Automatiseerime ainult DevTools-iga võimalikku

---

## ⚖️ **Oluline eetiline märkus**

*"Projekt ei põhjusta piraatlust. Kasutajad saavad ainult allalaadida avalikult kättesaadavat sisu – täpselt sama, mida saaks teha käsitsi brauseri DevTools'iga. Me ei mööda autoriõigusi, ei puhasta tasumise seina, ei eggi piraatlussofti. Autoreid ja tootjaid austame – just seepärast töötab süsteem ainult seadmete, mis on avalikult kättesaadavad."*

---

## 📞 **Kuidas liituda?**

1. Võta ühendust **Discordis**: 
   - `#team-21-vooglaadija` kanal
   - Tag: **@TA Tom Kristian Abel**

2. Vaata koodi: https://github.com/imputnet/cobalt

3. Vali endale **area of expertise** ja tee **issue** või **PR**

4. Kõik muudatused lähevad:
   - ✅ Automaatsete testide läbi
   - ✅ Code review't
   - ✅ CI/CD pipeline'isse

5. Tere tulemast despite teie taust – olen avatud **kõikidele**, kes **usklevad projekti eetilisse raamistusse** ja tahavad **tegelikult ära teha**!

---

### 🎯 **Projekt on spetsiaalselt selle kursuse jaoks loodud**

See on **mitte ainult** "mingi olemasolev app", vaid **õpperaamistik**, kus igaüks saa oma ** kompetansid näidata**. 

**Tule ja tee see meie projektiks!** 🚀

---
*Vooglaadija – kleebi URL, saa fail, unusta. Teeme seda õigesti.*
