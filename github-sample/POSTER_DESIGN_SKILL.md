---
name: poster-design
version: 2.3.0
description: |
  Master poster design and autonomous visual generation skill for Design Hub & Canva.
  Strictly locked to Facebook Portrait (4:5, 1080x1350 px) and Square (1:1, 1080x1080 px).
  Features dynamic text placement, freeform layout architectures, context-driven style selection, and strict brand logo integrity.
---

# POSTER DESIGN MASTER SKILL (v2.3.0)

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
  - **Standard (Styles 1, 2, 4, 5 & Dynamic Layouts):** Place in the **TOP-LEFT** corner with 5.5% margin (60px from left, 68px from top on 1080x1350).
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

## 3. FREEFORM LAYOUT & DYNAMIC TEXT PLACEMENT (CRITICAL)

> **REFERENCES ARE INSPIRATIONS, NOT RIGID CAGES.**
> Never treat the reference designs (`design1`, `design2`, `design3`) as static constant templates.
> **DO NOT** lock text and characters into the exact same left/right split every time.
> Dynamically vary text placement, typographic hierarchy, character positioning, and offer containers across generations to create fresh, viral engagement.

### Supported Layout Geometries (Rotate Dynamically):

1. **Geometry A: Horizontal Top Headline & Bottom Glass Dock (Ref: `dynamic_horizontal_promo_1080x1350.jpg`)**
   - **Top:** Bold, condensed headline centered across the top (`CREATE WITHOUT LIMITS` or `DESIGN LIKE A PRO`) with a floating 3D Canva tile.
   - **Center:** Hero 3D character or artistic subject centered, interacting with floating 3D tools (stylus, color swatches, typography glyphs).
   - **Bottom:** Sleek horizontal frosted-glass dock card containing the price offer (`50 TK / 3 MONTHS`), trust guarantee (`ACCESS FIRST | PAY LATER`), and glowing CTA pill (`GET ACCESS`).
   - **Advantage:** Maximum cinematic visual symmetry, extremely clean mobile feed presentation.

2. **Geometry B: Reverse Split-Screen (Copy on Left, Character on Right)**
   - **Left:** Bold headline, benefit bullets, dashed discount coupon box, and CTA button stacked on the left side.
   - **Right:** 3D character positioned on the right side, leaning or gesturing toward the offer on the left.
   - **Advantage:** Directly flips the traditional split screen, preventing layout fatigue.

3. **Geometry C: Asymmetrical Diagonal Flow (Z-Pattern / Triangle)**
   - **Top-Left:** Headline and value hook.
   - **Mid-Right:** Floating 3D Canva tile or feature showcase with glowing particles.
   - **Bottom-Left / Bottom-Center:** 3D character seated or holding a floating price pill badge.
   - **Bottom-Right:** Floating glass coupon card with CTA.
   - **Advantage:** Dynamic visual energy that guides the viewer's eye across the entire canvas.

4. **Geometry D: Typographic Depth Backdrop (Hero Overlapping Giant Typography)**
   - **Background:** Huge, architectural outline or frosted typography (e.g. `CANVA`, `CREATE`, `PRO`) spanning the background.
   - **Foreground:** 3D character in front, naturally overlapping the lettering to create deep 3D dimensional immersion.
   - **Floating Elements:** Highlighted price badge (e.g. `Starts from [ 25tk ]`) and micro CTA pills hovering near the character.

5. **Geometry E: Centered Gallery Minimalist (Ref: `canva_conceptual_promo_1080x1350.jpg`)**
   - **Upper Two-Thirds:** Clean, fine-art physical metaphor (e.g. pencil + 3D Canva token -> glowing glass ribbon transformation).
   - **Lower Third:** Centered ivory condensed headline (`ANYONE CAN CREATE`), paired with a distinct golden-amber pill badge highlighting the price (`Starts from [ 25tk ] today`).
   - **Advantage:** Museum-grade luxury and intellectual sophistication.

6. **Geometry F: 3-Card Floor Spotlight (Ref: `design3.jpg`)**
   - **Top-Center:** Glowing 3D Canva badge with condensed headline above.
   - **Center:** Three floating frosted glass pricing cards with elevated center hero card.
   - **Bottom-Center:** Clean floor area with centered Design Hub brand logo.

7. **Geometry G: Real Model with Phone & Orbiting 3D Tiles (Ref: `design-6_reference`)**
   - **Top:** Dual brand logos with neon portal ambient glow.
   - **Center-Left:** Smartphone held forward with live Canva interface, surrounded by 4 tactile 3D squircle tiles.
   - **Center-Right:** Charismatic photographic model engaging the viewer.
   - **Bottom:** Glowing neon price pill badge and Messenger CTA.

8. **Geometry H: Split-Bento Hero Card & Vertical Feature Stack (Ref: `design-7_reference`)**
   - **Top:** Bold brand headline + Bengali subheadline with floating 3D spark/diamond token.
   - **Center-Left (Hero Card):** Large vibrant gradient squircle card with 3D product token and massive perk typography (`UNLIMITED` / `100M+`).
   - **Center-Left Unique Price Inset:** Stark white floating ticket/pill container with soft drop shadow and bold contrasting typography (`[ মাত্র ৫০ টাকা ]`), completely distinct from all body copy.
   - **Center-Right (Feature Stack):** 5-6 sleek horizontal white cards with colored icons, English feature title, and Bengali description.
   - **Bottom:** Full-width 4-badge security trust bar + Messenger CTA pill.

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

---

## 5. DYNAMIC PRICE HIGHLIGHTING & COPY RULES

- **Highlight the Price (CRITICAL RULE - SHOW PRICE UNIQUELY):**
  Bangladeshi consumers respond strongly to clear, unmissable pricing. The price must NEVER blend into body copy or look like ordinary typography:
  - **Unique Floating Container:** Frame the price inside a distinct ticket/pill element (e.g. crisp stark-white rounded pill with 3D soft drop shadow against rich gradients, or illuminated neon badge against dark backgrounds).
  - **Color & Weight Separation:** Use high-contrast brand colors (deep royal violet `#7D2AE8`, electric blue `#0062FF`, or warm amber `#F59E0B`) in bold, prominent Bengali/English numerals (`[ মাত্র ৫০ টাকা ]` or `[ মাত্র ৯৯ টাকা ]`).
  - **Instant Visual Hook:** The price pill should be the single most eye-catching badge on the card, immediately communicating unbeatable value.
  - Use high-contrast amber/gold pill badges (e.g. `[ 25tk ]` or `[ 50 TK / 3 MONTHS ]`).
  - Use warm amber `#F59E0B` or vibrant emerald `#10B981` accents against dark obsidian backgrounds.
  - In light backgrounds, use bold brand-colored pills or clean dashed coupon cutouts.
- **Value Trust Hooks:** Always pair pricing with high-trust micro-copy:
  - `Access First | Pay Later`
  - `Official Canva Pro Access`
  - `Instant Activation Guarantee`
  - `24/7 Support by Design Hub`

---

## 6. MODULAR PROMPT GENERATION TEMPLATES (1080x1350 & 1080x1080)

### TEMPLATE A: Dynamic Horizontal Promo (Top Headline + Bottom Dock)
```
Generate a 1080x1350 portrait ultra-clean modern digital art poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Deep obsidian navy with subtle smooth vignette and soft rim lighting.
Top: Bold condensed headline 'CREATE WITHOUT LIMITS' in clean off-white lettering. Floating beside it is a tactile 3D squircle tile of the official Canva logo (cyan to purple-violet gradient with white script) with realistic beveled depth and soft glow.
Center: A stylish 3D character [DESCRIBE CHARACTER: e.g. female designer with glasses and cozy black shirt holding a glowing digital stylus], surrounded by floating 3D creative assets [e.g. glowing typography 'Aa', color swatch deck, neon sparkles].
Bottom: A sleek, horizontal frosted-glass dock card with 1px glowing border containing bold amber text '50 TK / 3 MONTHS', secondary trust line 'ACCESS FIRST | PAY LATER', and a rounded glowing CTA button 'GET ACCESS'.
Top-left corner is completely clear and empty for direct brand logo overlay.
```

### TEMPLATE B: Reverse Split-Screen Studio Promo (Copy on Left, Hero on Right)
```
Generate a 1080x1350 portrait clean, bright, professional social media promo poster.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Soft morning ivory-white studio gradient with gentle floor shadows.
Left Side: Official 3D Canva squircle tile (cyan to purple gradient with white script) with title 'CANVA PRO'. Dashed coupon box with highlighted amber price '[PRICE/DURATION]'. 3 bullet points with colored icons detailing [KEY BENEFITS]. Rounded solid CTA button '[BUTTON TEXT]'.
Right Side: Charming 3D character [DESCRIBE CHARACTER & POSE] sitting casually on a glossy branded prop or cylindrical pedestal, pointing towards the offer on the left.
Top-left corner is completely clear and empty for direct brand logo overlay.
```

### TEMPLATE C: Poetic Conceptual Art (Physical Tool to Glowing Glass Transformation)
```
Generate a 1080x1350 portrait museum-grade conceptual art poster celebrating creative empowerment.
Aspect Ratio: Exactly 4:5 vertical (1080x1350 px).
Background: Matte deep [PRUSSIAN-BLUE / FOREST-GREEN / GRAPHITE] wall with soft directional studio shadows and warm ambient glow.
Bottom Surface: An ordinary [YELLOW WOODEN PENCIL / FOUNTAIN PEN / STYLUS] lies beside a tactile, physical 3D squircle token of the official Canva logo (cyan-to-violet gradient with white script) with realistic contact shadows.
Metaphor: From the sharp tool tip, a single continuous drawn line sweeps upward in a graceful S-curve, gradually morphing into a fluid luminous ribbon of translucent frosted colored glass (glowing cyan and warm amber), ending at the top in an intricate glowing origami [FLOWER / CRANE / PRISM] gently guided by an adult hand.
Below: Tall ivory condensed headline 'ANYONE CAN CREATE'. Centered amber pill badge with 'Starts from 25tk today' highlighting '25tk'.
Top-left corner is reserved clean for direct Design Hub brand logo placement.
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
│   ├── var2_pill_badge.jpg
│   └── README.md
├── design5_national_observance/      # Non-commercial commemorative vector art for national days
│   ├── reference.png
│   ├── national_revolution_and_solidarity_day_celebration.jpg
│   └── README.md
├── design-6_reference/               # Real photographic model + smartphone + orbiting 3D tiles
│   ├── reference.jpg
│   ├── canva_pro_mobile_promo_1080x1350.jpg
│   └── README.md
└── design-7_reference/               # Premium SaaS Split-Bento & Feature Stack Grid
    ├── reference.jpg
    ├── canva_pro_bento_promo_1080x1350.jpg
    └── README.md
```

**Rule for Future Generations:**
- When generating a new poster based on a design reference, save the finished poster into its matching `designs/<category>/` folder.
- Root files are kept as master references and assets (`canva-logo.png`, `canva-3d-logo.png`, `designuhb-logo.png`).

