---
name: observance-posters
version: 2.0.0
description: |
  Master guide and autonomous visual generator for national days, independence celebrations,
  cultural festivities, and observance day posters for Design Hub.
  Strictly locked to Facebook Portrait (4:5, 1080x1350 px) and Square (1:1, 1080x1080 px).
  Zero commercial selling/pricing. Features dynamic element placement, diverse vector art styles,
  respectful historical resonance, and strict brand logo integrity.
---

# NATIONAL & OBSERVANCE DAY POSTER SKILL (v2.0.0)

## 1. PURPOSE & CORE PRINCIPLES

This skill governs the autonomous creation of **non-commercial commemorative posters** celebrating national holidays, historical milestones, cultural festivals, and international observance days (e.g. Independence Day, Victory Day, National Revolution and Solidarity Day, Language Movement Day, Pahela Baishakh, World Teachers' Day, etc.).

### Critical Distinctions from Commercial Posters:
1. **ZERO Commercial Selling:**
   - **DO NOT** mention Canva Pro, subscription prices, discounts, coupons, dashed promo boxes, or sales CTAs.
   - The sole goal is **brand goodwill, national pride, cultural solidarity, and patriotic resonance**.
2. **Strict Aspect Ratio Lock:**
   - **Facebook Portrait (4:5, 1080×1350 px) — PRIMARY:** Maximum mobile feed real estate.
   - **Square Feed Standard (1:1, 1080×1080 px) — SECONDARY.**
   - Never generate 9:16 vertical stories or wide banners unless explicitly commanded.
3. **Naming Convention:**
   - Always name generated files as:
     `-<the main caption in the photo>_<context>.jpg`
     Examples:
     - `national_revolution_and_solidarity_day_celebration.jpg`
     - `victory_day_celebration.jpg`
     - `international_mother_language_day_observance.jpg`

---

## 2. DIVERSE VECTOR ART STYLES (CYCLE DYNAMICALLY)

Do not limit designs to a single vector formula. Select the art style that best elevates the specific occasion:

### Style A: Modern Layered Paper-Cut & Flat Vector (Ref: `independence-day-sample-poster.png`)
- **Visuals:** Crisp contour lines, smooth subtle vector gradients, clean layered paper-cut drop shadows, cheerful and relatable vector characters.
- **Lighting:** Warm sunrise, crisp morning sky, diffused festive radiance.
- **Best For:** National Day festivities, Independence Day parades, Pahela Baishakh, youth & cultural celebrations.

### Style B: Dynamic Graphic Novel & Heroic Cel-Shading
- **Visuals:** Bold ink outlines, heroic comic angles, expressive cross-hatching, energetic wind-swept flags, high-contrast dynamic shadows.
- **Lighting:** Dramatic golden hour, heroic rim lighting, backlit silhouettes.
- **Best For:** National Revolution & Solidarity Day, Victory Day, Armed Forces Day, historical uprisings.

### Style C: Retro Silk-Screen / Revolutionary Woodblock Print
- **Visuals:** Authentic vintage screenprint aesthetic, subtle halftone dots, bold geometric shapes, tactile woodcut line work.
- **Palette:** Limited striking 3-4 color palette (deep forest green, crimson red, aged cream/parchment, charcoal).
- **Best For:** Historical retrospectives, labor movement, solidarity commemorations, patriotic heritage.

### Style D: Minimalist Line Art & Duotone / Tricolor Elegance
- **Visuals:** Sophisticated continuous vector line art, expansive negative space, delicate geometric accents, luxurious understated composition.
- **Palette:** Rich off-white or deep slate canvas with pure emerald green, ruby red, and gold metallic accents.
- **Best For:** International Mother Language Day (Ekushey February), Martyred Intellectuals Day, solemn memorials.

### Style E: Vibrant Watercolor & Gouache Illustrated Vector
- **Visuals:** Soft painterly blends, loose fluid brushstrokes with clean vector typography overlays, emotional organic textures.
- **Palette:** Warm dawn amber, lush riverine greens, vivid floral watercolors.
- **Best For:** Pahela Baishakh, World Environment Day, Women's Day, World Poetry Day.

---

## 3. FREEFORM COMPOSITION & ELEMENT PLACEMENT ARCHITECTURES

Never force elements into a constant geometric layout. Rotate across these 6 distinct composition architectures:

### Architecture 1: Asymmetrical Diagonal Dynamic (Ref: `national_revolution_and_solidarity_day_celebration.jpg`)
- **Bottom-Left:** Strong stylized hand or youth raising the national flag high into the sky.
- **Bottom-Center:** Cheerful, dignified citizens / soldiers standing in solidarity.
- **Top-Right:** Bold stacked headline badges and clean calendar block (`07/11 2026`).
- **Background:** Soft architectural monument silhouette, flying doves, and floating water lilies (*Shapla*).

### Architecture 2: Symmetrical Heroic Arch & Monumental Center
- **Center Stage:** The national monument (e.g. *Jatiya Smriti Soudho* or *Shaheed Minar*) or a heroic trio of citizens/soldiers standing tall in center frame.
- **Top Center:** Arched or bold centered headline spanning the skyline.
- **Bottom Center:** Elegant ribbon banner or clean gold date badge flanked by laurel wreaths or floral offerings.
- **Flanks:** Symmetrical fluttering flags or ceremonial torch glows.

### Architecture 3: Heroic Horizon & Panoramic March
- **Lower Third:** A panoramic silhouette or cel-shaded crowd of diverse citizens (students, farmers, workers, soldiers) marching forward with fluttering flags toward a radiant sunrise.
- **Upper Two-Thirds:** Expansive open sky featuring massive, confident commemorative typography and flying doves of liberty.
- **Placement:** Date badge anchored either top-right or lower-right horizon.

### Architecture 4: Typographic Focal Art (Characters Interacting with Giant Lettering)
- **Visual Focus:** Giant, artistic architectural letters (e.g. `1971`, `VICTORY`, `BIJOY`, `21`, `EKUSHEY`) dominating the canvas center.
- **Character Integration:** Stylized vector figures standing, leaning, or placing flowers on and around the oversized letters.
- **Perimeter:** Minimalist date badge and commemorative motto framing the top or bottom.

### Architecture 5: Prestigious Medal / Circular Emblem Seal
- **Center:** An intricate, circular vector medallion or sun-wheel emblem framing the national flag or iconic monument, surrounded by traditional floral patterns (*Alpana* or *Shapla*).
- **Top:** Elegant serif or modern sans-serif commemorative headline.
- **Bottom:** Polished commemorative plaque containing the date, day, and core value motto (`SOVEREIGNTY • UNITY • FREEDOM`).

### Architecture 6: Historical-to-Modern Split Progression
- **Left Side:** Sepia/monochrome expressive vector illustrations depicting the historical struggle (1952, 1971, or 1975).
- **Right Side:** Vibrant full-color modern vector scene of today’s smiling youth building a progressive, sovereign nation.
- **Connecting Element:** A continuous flowing national flag or river ribbon uniting both eras.

---

## 4. BRAND LOGO INTEGRITY (`designuhb-logo.png`)

- **Placement:** Always composite [`designuhb-logo.png`](file:///Users/sunny/work/designHub-bot/designuhb-logo.png) in the **TOP-LEFT** corner with 5.5% margin (60px from left, 68px from top on 1080x1350 canvas).
- **100% Background Transparency:** The company logo must be completely transparent. **NEVER** place a white box, dark plate, card, or pill behind it. The sky or background artwork must flow through seamlessly.
- **Composite Programmatically:** Use Python Pillow with Lanczos resampling. Ensure the top-left background in the AI generation is kept clean and uniform before compositing.

---

## 5. EXPANDED OBSERVANCE & CULTURAL CALENDAR

| Observance / National Day | Core Date | Key Visual Symbols & Characters | Recommended Style & Architecture | Primary Palette |
|---|---|---|---|---|
| **National Revolution & Solidarity Day** | November 7 | Sipahi-Janata (Soldier & Youth) united, raised Bangladesh Flag, Jatiya Smriti Soudho, Shapla flowers, Doves | Style B (Heroic Cel-Shading) + Architecture 1 or 3 | Bottle green, crimson, olive, sky-blue |
| **Victory Day (Bijoy Dibosh)** | December 16 | Cheering freedom fighters, victorious youth with flag, Jatiya Smriti Soudho, golden paddy fields, sunrise rays | Style A (Layered Flat) + Architecture 2 (Monumental) | Lush green, radiant red, sunburst gold |
| **Independence Day (Shadhinota Dibosh)** | March 26 | Resolute raised fists with flags, flying birds of freedom, historical silhouettes, blooming water lilies | Style C (Silk-Screen) + Architecture 1 (Diagonal) | Crisp sky-blue, emerald green, vibrant red |
| **International Mother Language Day** | February 21 | Shaheed Minar floral tributes, Bengali typography alphabets (অ, আ, ক, খ) floating, barefoot mourning procession | Style D (Minimalist Line) + Architecture 4 (Typographic) | Pure black, ivory white, crimson red, marigold |
| **Pahela Baishakh (Bengali New Year)** | April 14 | Mangal Shobhajatra masks (tiger, owl, sun), traditional dhol/flute, alpana floor art, festive couple in red & white | Style E (Watercolor Vector) + Architecture 5 (Emblem) | Vermillion red, sunny yellow, terracotta |
| **Armed Forces Day** | November 21 | Tri-service symbols (Army, Navy, Air Force silhouettes), defense jets, naval ship silhouette, national flag | Style B (Heroic Cel-Shading) + Architecture 2 (Symmetrical) | Steel blue, olive drab, deep navy, gold |
| **World Teachers' Day** | October 5 | Inspiring 3D/vector teacher with students, open books, glowing lightbulbs of wisdom, graduation caps | Style A (Clean Vector) + Architecture 1 (Diagonal) | Warm cream, royal blue, inspiring yellow |
| **International Women's Day** | March 8 | Diverse empowered women standing united, purple ribbons, blooming flowers, forward-looking gazes | Style E (Watercolor) or Style D + Architecture 3 | Purple, lilac, warm peach, emerald |

---

## 6. MODULAR PROMPT GENERATION TEMPLATES

### TEMPLATE A: Dynamic Asymmetrical Observance (Flag & Figures)
```
Generate a 1080x1350 portrait high-quality commemorative national observance poster in modern [VECTOR ART STYLE: Layered Flat / Heroic Cel-Shading].
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Soft [MORNING SKY-BLUE / SUNRISE GOLDEN] gradient with gentle translucent clouds, warm sunrise rays, and soaring white doves of peace.
Subject & Composition:
- [DESCRIBE HERO ELEMENTS: e.g. Raised proudly from the bottom-left is a strong stylized vector hand holding aloft the official National Flag of Bangladesh waving gracefully in the wind].
- [DESCRIBE FIGURES: e.g. Next to the flag are cheerful stylized vector figures depicting national solidarity: a proud patriotic soldier in olive uniform standing shoulder-to-shoulder with a smiling youth in casual attire, looking forward with unity].
- Background: Elegant semi-transparent silhouette of the iconic [LANDMARK: e.g. National Martyrs' Memorial Jatiya Smriti Soudho] and floating water lily (Shapla) motifs.
Typography & Layout:
- Bold, stacked commemorative headline in modern block badges: '[EVENT TITLE LINE 1]' and '[EVENT TITLE LINE 2]' in contrasting vibrant colors.
- Subtitle: '[DIGNIFIED THEME / MOTTO]'.
- Clean modern calendar date badge: '[DATE / MONTH]' with '[YEAR]' and '[DAY LABEL]'.
- Commemorative pill tag: '[VALUE 1] • [VALUE 2] • [VALUE 3]'.
Top-left corner is completely clear and empty for direct brand logo overlay.
Zero commercial selling, zero product promos. Celebratory, patriotic, clean vector art.
```

### TEMPLATE B: Monumental Symmetrical Centerpiece
```
Generate a 1080x1350 portrait majestic commemorative poster in [VECTOR ART STYLE].
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Center: A magnificent, dignified stylized vector depiction of [NATIONAL MONUMENT / FREEDOM MEMORIAL] rising in the center under an ethereal dawn sky with sunburst rays.
Foreground: A respectful gathering of stylized citizens holding small national flags, with floral tributes (red roses and water lilies) adorning the marble plaza.
Top: Centered arched bold commemorative typography '[EVENT TITLE]' in deep bottle-green and crimson red.
Bottom: Clean polished ribbon banner displaying the official date '[DATE, MONTH, YEAR]' and national motto '[MOTTO]'.
Top-left corner is reserved clean for direct Design Hub brand logo placement.
Zero commercial selling, zero product promos.
```

---

## 7. DEDICATED FOLDER LOCATION (`designs/design5_national_observance/`)

All commemorative national day and observance posters are filed in:
`designs/design5_national_observance/`

```
designs/design5_national_observance/
├── reference.png                                              # Festive vector reference
├── national_revolution_and_solidarity_day_celebration.jpg     # Nov 7 commemoration
└── README.md                                                  # Category guide & file index
```

**Rule for Future Generations:**
- Save all generated national and cultural observance posters into `designs/design5_national_observance/`.
- Ensure strict adherence to `-<caption >_<context>.jpg` naming and 1080×1350 resolution.

