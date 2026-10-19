---
name: poster-design
version: 2.5.0
description: |
  Master poster design and autonomous visual generation skill for Design Hub & Canva.
  Strictly locked to Facebook Portrait (4:5, 1080x1350 px) and Square (1:1, 1080x1080 px).
  Features dynamic text placement, freeform layout architectures, context-driven style selection,
  high-focus title highlighting, official contact standards, and strict brand logo integrity.
---

# POSTER DESIGN MASTER SKILL (v2.5.0)

## 1. STRICT ASPECT RATIO LOCK (MANDATORY FOR ALL GENERATIONS)

**ONLY TWO RATIOS ARE PERMITTED UNDER ANY CIRCUMSTANCES:**
1. **Facebook Portrait (4:5, 1080×1350 px) — PRIMARY & RECOMMENDED:**
   - Maximizes screen real estate on mobile Facebook & Instagram feeds.
   - Drives significantly higher Click-Through-Rates (CTR) and visual stopping power.
2. **Square Feed Standard (1:1, 1080×1080 px) — SECONDARY:**
   - Standard balanced Facebook feed tile.
*NEVER generate 9:16 vertical stories, 16:9 widescreen, or landscape formats unless specifically commanded by the user.*

---

## 2. OFFICIAL LOGOS & BRAND INTEGRITY INSTRUCTIONS

### A. Company Brand Logo (Design Hub): `designuhb-logo.png`
- Features a built-in crisp white outline, guaranteeing high contrast on any background (dark, light, or textured).
- **This is a finished artwork. NEVER redraw, recreate, restyle, or allow AI diffusion to draw any brand logo.**
- **No Background Plates:** Keep it 100% transparent. **DO NOT put a box, square, circle, badge, card, or shadow plate behind it.** The poster background must show through completely.
- **Positioning:**
  - **Standard (Styles 1, 2, 4, 5, 6, 7, 8, 9, 10, 11):** Place in the **TOP-LEFT** corner with 5.5% margin (60px from left, 68px from top on 1080x1350; 55px from left, 50px from top on 1024x1024).
  - **Pricing Cards (Style 3):** Place in the **BOTTOM-CENTER** floor area (14-16% width) to let the top spotlight center on Canva.
- **Size:** 14% to 15% of poster width (approx 150-160px on 1080px canvas).
- **Implementation:** Always composite programmatically using Python Pillow with Lanczos resampling. Before compositing, patch/smooth any AI placeholder artifact in the top-left corner so transparency is 100% clean.

### B. Official Product Logo (Canva): `canva-logo.png` & `canva-3d-logo.png`
- **Master 2D Logo:** `canva-logo.png`
  - Authentic Canva squircle badge featuring the signature gradient (top-left vibrant cyan `#00C4CC` transitioning through royal blue to bottom-right rich violet `#7D2AE8`) with the iconic white cursive Canva script.
- **Master 3D Logo Asset:** `canva-3d-logo.png`
  - A photorealistic, tangible 3D squircle tile with metallic extrusion depth, smooth rounded beveled edges, top specular rim highlight, and soft directional drop shadow.
  - **Usage:** Use `canva-3d-logo.png` whenever the poster calls for a 3D app icon, floating creative tile, or tactile surface token.
  - **Prompts:** When generating 3D Canva scenes via diffusion, always specify: *"a tactile 3D squircle tile featuring the official Canva gradient (vibrant cyan to purple-violet) with the iconic white cursive Canva script and realistic beveled depth and contact shadows."*

---

## 2.1 MANDATORY TITLE HIGHLIGHTING & FOCAL FOCUS ARCHITECTURE (CRITICAL)

> ⚡ **THE HEADLINE IS THE VISUAL GATEWAY: NEVER MAKE IT FLAT OR MONOCHROME**
> Viewers scroll feeds in under 0.5 seconds. The title MUST have unmissable focal power and depth.
> Across **EVERY SINGLE DESIGN STYLE (Styles 1 through 11)**, you MUST apply high-focus title highlighting using these 4 core design techniques:

### 1. Two-Tone Color Contrast Split:
- Split the title phrase across two distinct, complementary colors:
  - **Dark-Mode Backgrounds:** Primary words in crisp off-white (`#F8FAFC`) + Action/Key word in **Luminous Cyan (`#00F2FE`)**, **Neon Emerald (`#10B981`)**, or **Golden Amber (`#F59E0B`)**.
  - **Light-Mode Backgrounds:** Primary words in deep charcoal navy (`#0F172A`) + Action/Key word in **Royal Blue (`#0052FF`)** or **Vibrant Electric Violet (`#7D2AE8`)**.

### 2. Accent Keyword Badges & Pill Containers:
- Frame high-impact keywords (e.g. `Canva Pro`, `১ TB ক্লাউড`, `প্রিমিয়াম`, `আল্টিমেট`) inside an illuminated pill container, frosted glass ticket, or dashed-border cutout badge with 1px luminous border.

### 3. Typographic Scale & Weight Hierarchy:
- The highlighted keyword must be **1.3x to 1.8x larger** than secondary text, rendered in bold condensed modern sans-serif typography.

### 4. Style-by-Style Title Highlighting Matrix (All 11 Styles):
- **Style 1 (Clean Studio Character):** Deep charcoal bold header (`ডিজাইন হবে`) + Electric cyan/amber pill tag (`[ একদম সহজ ]`).
- **Style 2 (Atmospheric Dark Mode 3D):** Crisp white title with key action phrase in luminous cyan-to-purple gradient glow (`#00F2FE` -> `#7D2AE8`).
- **Style 3 (Glassmorphism Pricing Tiles):** Frosted headline with golden amber `#F59E0B` glow on value hook (`ULTIMATE VALUE`).
- **Style 4 (Hand Holding Miniature Capsule):** Tall ivory condensed lettering with warm amber keyword highlight on micro-offer.
- **Style 5 (Poetic Conceptual Art):** Minimalist uppercase title with focal noun styled like luminous colored glass.
- **Style 6 (Real Model & Orbiting 3D Tiles):** Vibrant two-tone split with gradient pill badge around subscription tier.
- **Style 7 (Split-Bento & Feature Stack):** Large high-contrast brand headline with glowing 3D star token and electric purple keyword emphasis.
- **Style 8 (Commercial Hardware Showcase):** Two-tone inquiry title (`ডিজাইন করতে` in white, `হিমশিম খাচ্ছেন ?` in vibrant red/cyan) with bright category tag pill.
- **Style 9 (Modern Tech Desk & 3D Glass Token):** Clean dark emerald title with primary software name in contrasting two-tone split (`CANVA PRO` in dark emerald, `& 1TB CLOUD` with electric highlight).
- **Style 10 (3D Hardcover Book & Cyber Schema):** Two-tone cyber headline (`ডাটাবেজ শেখো` in crisp white, `ঘর গোছানোর মতো` in luminous cyan `#22D3EE`).
- **Style 11 (3D Robot Mascot & Server Tower):** Bold royal blue & charcoal title split (`CANVA PRO` in deep navy, `& 1TB CLOUD` in vivid royal blue `#0052FF`).

---

## 2.2 OFFICIAL STANDARDIZED CONTACT FOOTER (FOR EVERY STYLE)

> 📞 **UNIFORM CONTACT DETAILS ON ALL POSTERS & GENERATIONS:**
> Whenever generating, prompting, or compositing bottom contact bars, you MUST use these verified company contact credentials:

- **Hotline Phone:** `01571425035` (cleanly formatted: `01571425035` or `01571-425035`)
- **Official Website:** `designhub.com.bd`
- **Facebook Page:** `<facebook logo>/DesignHub` (display as `[f] /DesignHub` or `fb.com/DesignHub`)
- **Standard Capsule Footer Layout:**
  `Hotline: 01571425035   •   Web: designhub.com.bd   •   fb.com/DesignHub`

---

## 3. FREEFORM LAYOUT & DYNAMIC TEXT PLACEMENT (CRITICAL)

> ⚠️ **CRITICAL GOLDEN RULE: REFERENCES ARE BLUEPRINTS, NEVER IMG2IMG INPUTS**
> - **DO NOT pass reference images into `ImagePaths` when generating posters via diffusion.**
> - Passing a reference image into diffusion forces the AI to inpaint/trace over the original image, which results in dirty artifacts, half-copied competitor logos, and distorted low-quality patches.
> - **Always generate 100% BRAND NEW, ORIGINAL ARTWORK from pure text prompts** inspired by the reference's layout geometry, lighting, and visual DNA.
> - **Always composite the official `designuhb-logo.png` programmatically** with Python Pillow (Lanczos resampling) in the top-left corner onto a clean background.
> - **REFERENCES ARE INSPIRATIONS, NOT RIGID CAGES:** Dynamically vary character expressions, camera angles, color accents, and props while honoring the core geometry.

### Supported Layout Geometries (Rotate Dynamically):

1. **Geometry A: Horizontal Top Headline & Bottom Glass Dock (Ref: `dynamic_horizontal_promo_1080x1350.jpg`)**
   - **Top:** Bold, condensed headline with two-tone highlight centered across the top with a floating 3D Canva tile.
   - **Center:** Hero 3D character or artistic subject centered, interacting with floating 3D tools.
   - **Bottom:** Sleek horizontal frosted-glass dock card containing the price offer (`50 TK / 3 MONTHS`), trust guarantee (`ACCESS FIRST | PAY LATER`), and glowing CTA pill.

2. **Geometry B: Reverse Split-Screen (Copy on Left, Character on Right)**
   - **Left:** Bold highlighted headline, benefit bullets, dashed discount coupon box, and CTA button stacked on the left side.
   - **Right:** 3D character positioned on the right side, leaning or gesturing toward the offer on the left.

3. **Geometry C: Asymmetrical Diagonal Flow (Z-Pattern / Triangle)**
   - **Top-Left:** Highlighted headline and value hook.
   - **Mid-Right:** Floating 3D Canva tile or feature showcase with glowing particles.
   - **Bottom-Left / Bottom-Center:** 3D character seated or holding a floating price pill badge.
   - **Bottom-Right:** Floating glass coupon card with CTA.

4. **Geometry D: Typographic Depth Backdrop (Hero Overlapping Giant Typography)**
   - **Background:** Huge, architectural outline or frosted typography spanning the background.
   - **Foreground:** 3D character in front, naturally overlapping the lettering to create deep 3D dimensional immersion.
   - **Floating Elements:** Highlighted price badge and micro CTA pills hovering near the character.

5. **Geometry E: Centered Gallery Minimalist (Ref: `canva_conceptual_promo_1080x1350.jpg`)**
   - **Upper Two-Thirds:** Clean, fine-art physical metaphor (e.g. pencil + 3D Canva token -> glowing glass ribbon transformation).
   - **Lower Third:** Centered ivory condensed headline with highlighted focal keyword, paired with a distinct golden-amber pill badge highlighting the price (`Starts from [ 25tk ] today`).

6. **Geometry F: 3-Card Floor Spotlight (Ref: `design3.jpg`)**
   - **Top-Center:** Glowing 3D Canva badge with condensed highlighted headline above.
   - **Center:** Three floating frosted glass pricing cards with elevated center hero card.
   - **Bottom-Center:** Clean floor area with centered Design Hub brand logo.

7. **Geometry G: Commercial Hardware Centerpiece & Dual Pill Hotline Footer (Ref: `designs/design-8_reference/reference.jpg`)**
   - **Top-Right:** Bold two-tone Bengali inquiry headline (`...খুঁজছেন ?`) with category highlight pill.
   - **Center:** Photorealistic tangible hardware / device mockup (tablet, live workstation) on rich wooden surface with circling neon energy beam.
   - **Left:** Square dashed-border callout coupon badge (`[ ফ্রি ট্রায়াল করুন ]` or `[ মাত্র ২৫ টাকা ]`).
   - **Bottom:** Sleek contrast footer bar: `Hotline: 01571425035 • Web: designhub.com.bd • fb.com/DesignHub`.

8. **Geometry H: Open Laptop Desk, Tactile 3D Glass Token & Big Taka Pill (Ref: `designs/design-9_reference/reference.jpg`)**
   - **Atmosphere:** Split ivory cream surface with sweeping emerald/forest green architectural arch.
   - **Right:** Slim modern laptop open on desk displaying live software UI.
   - **Foreground Center:** Tangible glossy 3D glass squircle token with beveled metallic depth and brand emblem resting on desk.
   - **Top-Left:** Bold dark emerald headline with two-tone split (`CANVA PRO & 1TB CLOUD`) and white pill tags.
   - **Bottom-Left:** Prominent dark emerald price block with yellow accent tag (`ONLY`), stark-white `৳ 25`, and pill CTA button (`Order Now >`).

9. **Geometry I: 3D Hardcover Book, Isometric Metaphor & Neon Schema Grid (Ref: `designs/design-10_reference/reference.jpg`)**
   - **Atmosphere:** Deep atmospheric obsidian navy backdrop with faint tech silhouettes.
   - **Top:** Two-tone Bengali headline (`ডাটাবেজ শেখো` in crisp white + `ঘর গোছানোর মতো` in vibrant cyan `#22D3EE`) with chapter/page specs line.
   - **Center-Right:** Photorealistic upright 3D hardcover book mockup with intricate isometric narrative cover art.
   - **Left:** Floating frosted SQL/tech schema cards with PK/FK pills and glowing neon cyan relational connector paths.
   - **Lower-Left:** Dynamic cyan arrow pointer price badge (`[ মাত্র ৳১১১ ]` or `[ মাত্র ২৫ টাকা ]`).
   - **Bottom:** Rounded dark CTA button with neon cyan perimeter glow.

10. **Geometry J: 3D Robot Mascot, Server Tower & Giant Blue Price Pill (Ref: `designs/design-11_reference/canva_pro_robot_server_design11_master.jpg`)**
    - **Atmosphere:** High-key crisp white and ice-blue tech studio with subtle circuit trace corner brackets.
    - **Top-Left:** High-contrast two-tone headline (`CANVA PRO` in deep navy + `& 1TB CLOUD` in electric royal blue `#0052FF`).
    - **Center-Right:** Shiny 3D enterprise server tower with glowing blue drive bays and a charming 3D white-and-blue robot mascot gesturing towards it.
    - **Floating Center:** Tactile 3D squircle tile of the official Canva gradient.
    - **Lower-Left:** Massive royal blue price container with oversized white price numbers (`৳ 25`), sub-pill (`শুরু মাত্র`), and `— value for money —`.
    - **Upper-Right:** Stack of 3 rounded white feature cards (`🔒 100% Private`, `📂 1 TB Cloud Storage`, `⚡ Zero Expire Hassle`).
    - **Bottom:** Clean rounded capsule footer: `Hotline: 01571425035 • Web: designhub.com.bd • fb.com/DesignHub`.

---

## 4. AUTONOMOUS CONTEXT-TO-STYLE DECISION MATRIX

When given a campaign topic or context, autonomously pick both the **Style Archetype** and a matching **Layout Geometry**:

| Campaign Context & Marketing Goal | Style Archetype | Recommended Layout Geometry | Reference Benchmark |
|---|---|---|---|
| **Direct Sales, Tier Comparison, Flash Discounts, Plan Upgrades** | **Style 3: Ultra-Premium Glassmorphism Pricing Tiles** | Geometry F (3-Card Floor Spotlight) | `design3.jpg` |
| **Creative Empowerment, Thought Leadership, Brand Storytelling, Artistic Metaphor** | **Style 5: Poetic Conceptual Art & Physical Metaphor** | Geometry E (Centered Gallery Minimalist) | `canva_conceptual_promo_1080x1350.jpg` |
| **Feature Launches, All-in-One Capabilities, Pro Designers, Modern Tech Appeal** | **Style 2: Atmospheric Dark Mode & Floating Elements** | Geometry A (Top Headline & Bottom Dock) OR Geometry C (Diagonal Flow) | `dynamic_horizontal_promo_1080x1350.jpg` & `design2.jpg` |
| **Beginners, Student Deals, High-Trust Offers ('Access First, Pay Later'), Friendly Walkthrough** | **Style 1: Clean & Bright Studio Character** | Geometry B (Reverse Split) OR Classic Split with varied character & prop | `design1.jpg` |
| **Curiosity Campaigns, Secret Tools, Gift Bundles, Micro-World Reveals** | **Style 4: Hand Holding Miniature Glass Capsule** | Geometry E (Centered Hand & Capsule) with Bottom Floating Pill Offer | `DESIGN-4` |
| **Direct Subscription Promo, Mobile App Checkout, All-in-One AI Suite, bKash Offers** | **Style 6: Real Model & Floating 3D Feature Badges** | Geometry G (Phone in Hand with Orbiting 3D Tiles & Hero Model) | `design-6_reference` |
| **All-in-One Pro SaaS Perks, Multi-Feature Breakdown, High-Trust Bengali Audience** | **Style 7: Premium SaaS Split-Bento & Feature Stack Grid** | Geometry H (Split-Bento Hero Card & Vertical Feature Stack) | `design-7_reference` |
| **B2B / B2C Hardware, Retail SaaS, High-Impact Commercial Launches** | **Style 8: Commercial Hardware Centerpiece & Dual Pill Hotline Footer** | Geometry G (Commercial Hardware Centerpiece & Dual Pill Footer) | `designs/design-8_reference/` |
| **SaaS Subscriptions, AI Tech Subscriptions, Premium Laptop Mockups, Taka Pricing Highlights** | **Style 9: Modern Tech Desk, Laptop Mockup & 3D Glass Token** | Geometry H (Open Laptop Desk, Tactile 3D Glass Token & Big Taka Pill) | `designs/design-9_reference/` |
| **Tech Books, Programming Guides, Masterclasses, E-books, Course Launches & Technical Metaphors** | **Style 10: 3D Hardcover Book, Isometric Metaphor & Cyber Relational Schema** | Geometry I (3D Hardcover Book, Isometric Metaphor & Neon Schema Grid) | `designs/design-10_reference/` |
| **Cloud Infrastructure, Server Packages, Tech Bundles & Robot Mascot Promos** | **Style 11: 3D Tech Mascot, Server Tower & Giant Blue Price Pill** | Geometry J (3D Robot Mascot, Server Tower & Giant Blue Price Pill) | `designs/design-11_reference/` |

---

## 5. DYNAMIC PRICE HIGHLIGHTING, CORE VALUE PILLARS & COPY RULES

- **Highlight the Price (CRITICAL RULE - SHOW PRICE UNIQUELY):**
  Bangladeshi consumers respond strongly to clear, unmissable pricing. The price must NEVER blend into body copy or look like ordinary typography:
  - **Unique Floating Container:** Frame the price inside a distinct ticket/pill element (e.g. crisp stark-white rounded pill with 3D soft drop shadow against rich gradients, or illuminated neon badge against dark backgrounds).
  - **Color & Weight Separation:** Use high-contrast brand colors (deep royal violet `#7D2AE8`, electric blue `#0062FF`, or warm amber `#F59E0B`) in bold, prominent Bengali/English numerals (`[ মাত্র ২৫ টাকা ]` or `[ মাত্র ৫০ টাকা ]`).
  - **Instant Visual Hook:** The price pill should be the single most eye-catching badge on the card, immediately communicating unbeatable value.

### 🛡️ MANDATORY 5 CORE VALUE PROPOSITIONS (MUST BE EMPHASIZED)
Whenever designing posters, feature badges, or promotional copy, you MUST incorporate or choose from these 5 flagship pillars:

1. **🔒 Security & Privacy (সম্পূর্ণ নিরাপদ ও প্রাইভেট):**
   - **English Micro-copy:** `100% Private & Protected — Others cannot view your designs`
   - **Bengali Micro-copy:** `১০০% নিরাপদ ও প্রাইভেট — আপনার ডিজাইন অন্য কেউ দেখতে পারবে না`
2. **⚡ No Hassle (মেয়াদ শেষ হওয়ার আগে টিম এক্সপায়ার হওয়ার কোনো সুযোগ নেই):**
   - **English Micro-copy:** `Zero Expire Hassle — No chance of team expiring before due date`
   - **Bengali Micro-copy:** `নো টিম এক্সপায়ার হ্যাসেল — মেয়াদ শেষ হওয়ার আগে টিম বন্ধ হওয়ার কোনো সুযোগ নেই`
3. **🔄 Extend Policy (ডিজাইন আজীবন সুরক্ষিত রাখার সহজ এক্সটেন্ড পলিসি):**
   - **English Micro-copy:** `Flexible Extend Policy — Seamless renewals keep your designs permanently secure`
   - **Bengali Micro-copy:** `সহজ এক্সটেন্ড পলিসি — যেকোনো সময় মেয়াদ বাড়িয়ে নিন, ডিজাইন থাকবে আজীবন সুরক্ষিত`
4. **📂 1 TB Cloud Storage (১ TB বিশাল ক্লাউড স্টোরেজ):**
   - **English Micro-copy:** `1 TB Cloud Storage — Huge cloud backup for Brand Kit & media`
   - **Bengali Micro-copy:** `১ TB ক্লাউড স্টোরেজ — আনলিমিটেড ডিজাইন ও মিডিয়া ব্যাকআপ`
5. **✨ 100M+ Premium Designs & Assets (১০০M+ প্রিমিয়াম রিসোর্স):**
   - **English Micro-copy:** `100M+ Premium Templates, Photos, Videos & Fonts`
   - **Bengali Micro-copy:** `১০০M+ প্রিমিয়াম টেমপ্লেট, ছবি, ভিডিও ও ফন্টস আনলকড`

---

## 5.1 STRICT BENGALI TYPOGRAPHY, SPELLING & LIGATURE INTEGRITY

Bengali copy must be authentic, natural, grammatically flawless, and double-checked:
- **Spelling Verification Matrix:**
  - ✅ **ঝামেলা / ঝামেলামুক্ত** (NOT 'ঝামেলাহীন' or broken conjuncts)
  - ✅ **হ্যাসেল** (NOT 'হেসেল' or 'হাসেল')
  - ✅ **সুরক্ষিত** (NOT 'সুরখিত')
  - ✅ **মেয়াদ** (NOT 'মেয়াদ' with missing aakar)
  - ✅ **অফিসিয়াল / অফিসিয়াল** (NOT 'অফিশিয়াল')
  - ✅ **প্রাইভেট** (NOT 'প্রাইবেট')
  - ✅ **ক্লাউড স্টোরেজ** (NOT 'ক্লাউড স্তোরেজ')
  - ✅ **সাবস্ক্রিপশন** (NOT 'সাবস্ক্রিপ্সন')
  - ✅ **প্রিমিয়াম** (NOT 'প্রিমিয়াম' inconsistently; maintain standard modern Bangla)
- **Zero Broken Ligatures:** Ensure Unicode conjuncts (`ক্ষ`, `জ্ঞ`, `ষ্ক`, `স্থ`, `ন্ত`, `ন্ড`) are rendered cleanly without detached hasant signs.
- **Tone:** Professional, engaging, clear, and trustworthy for the Bangladeshi creative community.

---

## 6. MODULAR PROMPT GENERATION TEMPLATES (1080x1350 & 1080x1080)

### TEMPLATE A: Dynamic Horizontal Promo (Top Headline + Bottom Dock)
```
Generate a 1080x1350 portrait ultra-clean modern digital art poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Deep obsidian navy with subtle smooth vignette and soft rim lighting.
Top: Bold condensed headline 'CREATE WITHOUT LIMITS' with two-tone split ('CREATE' in off-white, 'WITHOUT LIMITS' in glowing cyan #00F2FE). Floating beside it is a tactile 3D squircle tile of the official Canva logo (cyan to purple gradient with white script) with realistic beveled depth.
Center: A stylish 3D character designer holding a glowing digital stylus, surrounded by floating 3D creative assets (swatches, typography).
Bottom: A sleek horizontal frosted-glass dock card with 1px glowing border containing bold amber text '50 TK / 3 MONTHS', secondary trust line 'ACCESS FIRST | PAY LATER', and contact line 'Hotline: 01571425035 • fb.com/DesignHub'.
Top-left corner is completely clear and empty for direct brand logo overlay.
```

### TEMPLATE B: Reverse Split-Screen Studio Promo (Copy on Left, Hero on Right)
```
Generate a 1080x1350 portrait clean, bright, professional social media promo poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Soft morning ivory-white studio gradient with gentle floor shadows.
Left Side: Official 3D Canva squircle tile with title 'CANVA PRO' (charcoal text with 'PRO' in electric cyan pill badge). Dashed coupon box with highlighted amber price '[PRICE/DURATION]'. 3 bullet points with colored icons detailing key benefits. Rounded solid CTA button.
Right Side: Charming 3D character sitting casually on a glossy branded pedestal, pointing towards the offer on the left.
Bottom: Sleek white capsule footer with 'Hotline: 01571425035 • Web: designhub.com.bd • fb.com/DesignHub'.
Top-left corner is completely clear and empty for direct brand logo overlay.
```

### TEMPLATE C: Poetic Conceptual Art (Physical Tool to Glowing Glass Transformation)
```
Generate a 1080x1350 portrait museum-grade conceptual art poster celebrating creative empowerment.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Matte deep Prussian-blue wall with soft directional studio shadows and warm ambient glow.
Bottom Surface: A yellow wooden pencil lies beside a tactile, physical 3D squircle token of the official Canva logo with realistic contact shadows.
Metaphor: From the sharp tool tip, a single continuous drawn line sweeps upward in a graceful S-curve, gradually morphing into a fluid luminous ribbon of translucent frosted colored glass (glowing cyan and warm amber).
Below: Tall ivory condensed headline 'ANYONE CAN CREATE' with 'CREATE' in luminous glass styling. Centered amber pill badge with 'Starts from 25tk today'.
Bottom: Subtle footer 'Hotline: 01571425035 • fb.com/DesignHub'.
Top-left corner is reserved clean for direct Design Hub brand logo placement.
```

### TEMPLATE D: Style 8 (Commercial Hardware Centerpiece & Dual Pill Hotline Footer)
```
Generate a 1080x1350 portrait high-impact commercial tech advertisement poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Polished dark wooden/slate studio counter with soft directional studio spotlight and subtle warm rim lighting. Top-left corner is completely clear and empty for brand logo overlay.
Top-Right: Bold high-contrast two-tone Bengali inquiry headline 'ডিজাইন করতে হিমশিম খাচ্ছেন ?' ('ডিজাইন করতে' in crisp white, 'হিমশিম খাচ্ছেন ?' in vivid luminous red/cyan accent tag).
Center: A photorealistic tangible 3D workstation setup (slim tablet with Magic Keyboard displaying vibrant Canva interface, accompanied by an Apple Pencil prop), with a sleek luminous neon energy beam circling the device.
Left: Square dashed-border callout coupon badge with bold price '[ মাত্র ২৫ টাকা ]' and 'ইনস্ট্যান্ট এক্টিভেশন'.
Bottom: High-trust dark horizontal footer bar containing clean white text 'Hotline: 01571425035 • Web: designhub.com.bd • fb.com/DesignHub'.
3D Octane render, photorealistic product lighting, razor-sharp vector typography, commercial agency finish.
```

### TEMPLATE E: Style 9 (Modern Tech Desk, Laptop Mockup & 3D Glass Token)
```
Generate a 1080x1350 portrait ultra-premium minimalist tech workspace promo poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Split architectural studio backdrop: soft ivory cream matte desk on the left, paired with an elegant sweeping architectural curve in deep forest/emerald green on the right with soft rim lighting. Top-left corner kept completely empty for brand logo overlay.
Top-Left: Tagline 'SMARTER IDEAS EVERYDAY' in refined sans-serif, above bold high-focus title 'CANVA PRO & 1TB CLOUD' ('CANVA PRO' in dark emerald, '& 1TB CLOUD' in electric cyan highlight). Floating pill tags: '⚡ 100M+ Assets', '✨ Magic Studio AI', '📄 1TB Storage'.
Center-Right: Sleek modern silver laptop (MacBook Pro) open at a 3/4 perspective angle displaying the colorful Canva Pro web editor on its display.
Foreground Center: A tangible, photorealistic rounded glass squircle app token (emerald green glass with beveled reflections and white cursive Canva script) resting proudly on the desk in front of the laptop.
Lower-Left: Large rounded dark emerald container with yellow 'ONLY' accent tag, stark-white '৳ 25' price, and 'PER MONTH' subtitle, paired with rounded pill button 'Order Now >'.
Bottom: Clean contact pill 'Hotline: 01571425035 • fb.com/DesignHub'.
Hyper-clean Apple-grade product photography, pristine shadows, museum-grade aesthetic.
```

### TEMPLATE F: Style 10 (3D Hardcover Book, Isometric Metaphor & Cyber Relational Schema)
```
Generate a 1080x1350 portrait deep cyber educational masterclass promo poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Atmospheric obsidian navy to charcoal studio with faint server rack silhouettes and glowing cyan floor grid lines. Top-left corner clean for brand logo overlay.
Top: High-contrast two-tone headline: 'ডিজাইন শেখো' in crisp white, 'ঘর গোছানোর মতো' in glowing cyan (#22D3EE), with subtitle line 'সম্পূর্ণ গাইডলাইন • একদম শুরু থেকে'.
Center-Right: A thick, photorealistic 3D upright hardcover book mockup with tangible embossed spine, textured dust jacket, and realistic contact shadow. Book cover artwork features an intricate miniature 3D isometric designer's creative workshop with warm internal lighting.
Center-Left: Floating translucent holographic cards ('Templates', 'Brand Kit', 'Magic AI') with glowing neon cyan relational connection paths.
Lower-Left: Dynamic cyan arrow pointer pill badge highlighting the price '[ মাত্র ২৫ টাকা ]'.
Bottom: Rounded dark button with neon cyan perimeter glow and footer line 'Hotline: 01571425035 • fb.com/DesignHub'.
High-tech cinematic atmosphere, 3D Octane lighting, stunning depth of field.
```

### TEMPLATE G: Style 11 (3D Robot Mascot, Server Tower & Giant Blue Price Pill)
```
Generate a 1080x1350 portrait clean, high-key commercial tech cloud and design subscription poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Pristine, high-key white and ice-blue tech studio background with minimalist subtle circuit trace accents in top corners. Top-left corner is completely clear, open and empty for brand logo overlay.
Top-Left: High-contrast two-tone title 'CANVA PRO & 1TB CLOUD' ('CANVA PRO' in deep charcoal navy, '& 1TB CLOUD' in vivid royal blue #0052FF), with subline '100M+ Assets & Magic Studio AI'.
Center-Right: A sleek, photorealistic 3D enterprise server tower with glowing blue LED drive bays and brushed chrome metallic finish. Standing beside it on an illuminated circular floor pedestal is an adorable, friendly 3D Pixar/Disney-style white and royal-blue robot mascot with digital smiling cyan LED eyes, happily gesturing and pointing towards the offer. Floating near the server is a tactile 3D squircle tile featuring the official Canva gradient.
Upper-Right: Vertical stack of 3 rounded white micro-cards with royal blue icons:
- '🔒 100% Private (No Others Can View)'
- '📂 1 TB Cloud Storage'
- '⚡ Zero Expire Hassle'
Lower-Left: A massive rounded royal blue price card featuring bold white numerals '৳ 25', white sub-pill 'শুরু মাত্র', and trust line '— value for money —'.
Bottom: Sleek white rounded capsule pill footer bar reading: 'Hotline: 01571425035 • Web: designhub.com.bd • fb.com/DesignHub'.
3D Octane render, photorealistic product studio lighting, razor-sharp typography, ultra-clean commercial advertising aesthetic.
```

---

## 7. ORGANIZED FOLDER STRUCTURE (`designs/` DIRECTORY)

All reference designs and finished posters are categorized into dedicated folders under `designs/`:

```
designs/
├── design1_studio_character/         # Clean daylight studio character + dashed coupon offers
│   ├── reference.jpg
│   ├── make_ideas_happen_motivation.jpg
│   └── README.md
├── design2_dark_mode_3d/             # Atmospheric dark mode + floating 3D creative assets
│   ├── reference.jpg
│   ├── dynamic_horizontal_promo_1080x1350.jpg
│   ├── autonomous_campaign_promo_1080x1350.jpg
│   └── README.md
├── design3_glassmorphism_pricing/    # 3-Card spotlight glassmorphism SaaS pricing
│   ├── reference.jpg
│   └── README.md
├── design4_conceptual_art/           # Poetic physical-to-glass transformation conceptual art
│   ├── reference.jpg
│   ├── canva_conceptual_promo_1080x1350.jpg
│   └── README.md
├── design5_national_observance/      # Non-commercial commemorative vector art for national days
│   ├── reference.png
│   ├── national_revolution_and_solidarity_day_celebration.jpg
│   └── README.md
├── design-6_reference/               # Real photographic model + smartphone + orbiting 3D tiles
│   ├── reference.jpg
│   ├── canva_pro_mobile_promo_1080x1350.jpg
│   └── README.md
├── design-7_reference/               # Premium SaaS Split-Bento & Feature Stack Grid
│   ├── reference.jpg
│   ├── canva_pro_bento_promo_1080x1350.jpg
│   └── README.md
├── design-8_reference/               # Commercial Hardware Centerpiece & Dual Pill Hotline Footer
│   ├── reference.jpg
│   └── README.md
├── design-9_reference/               # Modern Tech Desk, Laptop Mockup & 3D Glass Token
│   ├── reference.jpg
│   └── README.md
├── design-10_reference/              # 3D Hardcover Book, Isometric Metaphor & Cyber Relational Schema
│   ├── reference.jpg
│   └── README.md
└── design-11_reference/              # 3D Tech Mascot, Server Tower & Giant Blue Price Pill
    ├── reference.jpg
    ├── canva_pro_robot_server_design11_master.jpg
    └── README.md
```

**Rule for Future Generations:**
- When generating a new poster based on a design reference, save the finished poster into its matching `designs/<category>/` folder.
- Root files are kept as master references and assets (`canva-logo.png`, `canva-3d-logo.png`, `designuhb-logo.png`).
