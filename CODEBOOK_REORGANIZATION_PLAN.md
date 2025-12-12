# Dhalgren Codebook Reorganization Plan

## Current Issues Identified

1. **Flat Structure**: Most codes are at the same level with minimal hierarchy
2. **Mixed Categories**: Codes mix entities (characters, places, objects) with processes and qualities
3. **Generic Codes**: Very broad codes like "SETTING", "CHARACTER", "DIALOGUE" are too vague
4. **Missing Specificity**: No character name codes (Kid, Tak, Denny, etc.)
5. **Poor Thematic Grouping**: Related codes are scattered
6. **Underutilized Hierarchy**: Parent_code field exists but only 4 codes use it

## Proposed Reorganization Structure

### I. SETTING & SPACE (Parent: None)
**Order: 0-19**
- BELLONA_CITY (0) - Specific city references
- ARCHITECTURE (1) - Buildings/structures
- SPATIAL_DISORIENTATION (2) - Spatial confusion
- URBAN_DECAY (3) - Ruins/decay
- FIRE_DESTRUCTION (4) - Fire/destruction
- THRESHOLD (5) - Doorways/borders
- LABYRINTH (6) - Maze-like elements
- UNDERWORLD_DESCENT (7) - Descent into dark
- TWILIGHT_DAWN (8) - Transitional times
- CARNIVAL (9) - Carnival atmosphere

### II. CHARACTERS (Parent: CHARACTER_ENTITY)
**Order: 20-39**

#### A. Character Names (Parent: CHARACTER_ENTITY)
- KID (20) - Protagonist
- TAK (21) - Character
- DENNY (22) - Character
- LOPP (23) - Character
- GEORGE (24) - Character
- [Other named characters as needed]

#### B. Character Roles (Parent: CHARACTER_ENTITY)
- TRICKSTER (25) - Trickster archetype
- ORACLE_PROPHET (26) - Prophetic figures
- MENTOR_GUIDE (27) - Guide/teacher figures
- HOMELESS_DRIFTER (28) - Drifter archetype

#### C. Character Identity (Parent: CHARACTER_ENTITY)
- OUTSIDER_STATUS (29) - Outside mainstream
- NAME_AMNESIA (30) - Identity/name issues
- IDENTITY_FLUID (31) - Fluid identities
- RACIAL_DYNAMICS (32) - Race/racial identity
- CLASS_PRIVILEGE (33) - Economic class

### III. OBJECTS & SYMBOLS (Parent: OBJECT_ENTITY)
**Order: 40-59**
- NOTEBOOK (40) - The notebook object
- ORCHID_CHAINS (41) - Orchid/chains imagery
- OPTICAL_CHAIN (42) - Prism/lens devices
- WEAPON (43) - Weapons as symbols
- LIGHT_SOURCE (44) - Lamps/fires/light
- REFLECTION_MIRROR (45) - Mirrors/reflections

### IV. SOCIAL STRUCTURES (Parent: SOCIAL_ENTITY)
**Order: 60-79**
- SCORPIONS_GANG (60) - The Scorpions
- COMMUNE_LIFE (61) - Communal living
- ALTERNATIVE_FAMILY (62) - Non-traditional families
- TRIBAL_IDENTITY (63) - Group identity
- ARTISTIC_CIRCLE (64) - Artists/poets community
- SOCIAL_COLLAPSE (65) - Social breakdown

### V. PROCESSES & ACTIONS (Parent: None)
**Order: 80-99**

#### A. Physical Movement
- WANDERING (80) - Aimless movement
- SEARCHING (81) - Seeking/looking
- SURVIVAL (82) - Surviving

#### B. Identity Processes
- SELF_CREATION (83) - Creating self
- TRANSFORMING (84) - Undergoing change
- REBIRTH_RENEWAL (85) - Transformation/rebirth

#### C. Social Processes
- MUTUAL_AID (86) - Helping/sharing
- RESISTING (87) - Opposing/rejecting

#### D. Creative Processes
- WRITING_PROCESS (88) - Writing poetry/journal
- CREATION_ACT (89) - Making art
- CREATING (90) - Making/building
- POETRY_PERFORMANCE (91) - Performing poetry

#### E. Cognitive Processes
- OBSERVING (92) - Watching/witnessing
- REMEMBERING (93) - Recalling past
- FRAGMENTING (94) - Breaking apart
- DISSOLVING (95) - Loss of boundaries

### VI. EMOTIONS (Parent: None)
**Order: 100-119**
- FEAR (100)
  - PARANOIA (101) - subcode
- ANGER (102)
- SADNESS (103)
  - ALIENATION (104) - subcode
  - DESPAIR (105) - subcode
  - SHAME (106) - subcode
- JOY (107)
  - ECSTASY (108) - subcode
- DISGUST (109)
- CONFUSION (110)
- ISOLATION (111)
- INTIMACY (112)

### VII. RELATIONSHIPS & DESIRE (Parent: None)
**Order: 120-139**
- QUEER_DESIRE (120) - Non-heteronormative desire
- POLYAMORY (121) - Multiple relationships
- SEXUAL_ENCOUNTER (122) - Sexual interactions
- GENDER_PLAY (123) - Gender performance
- DOMINANCE_SUBMISSION (124) - Power dynamics
- VIOLENCE_DESIRE (125) - Violence + desire

### VIII. REALITY & TIME (Parent: None)
**Order: 140-159**
- TEMPORAL_ANOMALY (140) - Time behaving strangely
- TEMPORAL_CONFUSION (141) - Unclear timeline
- REALITY_BREAK (142) - Reality breaking down
- MEMORY_LOSS (143) - Forgetting/lost memories

### IX. NARRATIVE STRUCTURE (Parent: None)
**Order: 160-179**
- CIRCULAR_STRUCTURE (160) - Narrative loops
- FRAGMENTATION (161) - Fragmented narrative
- METAFICTION (162) - Text referring to itself
- TYPOGRAPHIC_PLAY (163) - Unusual typography
- MULTIPLE_PERSPECTIVES (164) - Shifting viewpoints
- STREAM_CONSCIOUSNESS (165) - Stream of consciousness
- REPETITION_VARIATION (166) - Repeated scenes
- PROLEPSIS (167) - Flash-forwards
- ANALEPSIS (168) - Flashbacks
- UNRELIABLE_NARRATION (169) - Unreliable narrator
- READER_ADDRESS (170) - Direct address
- TEXTUAL_ARTIFACT (171) - Text as object
- HERO_JOURNEY (172) - Hero's journey elements
- TEMPORAL_SHIFT (173) - Time changes
- PERSPECTIVE_SHIFT (174) - Perspective changes

### X. NARRATIVE ELEMENTS (Parent: None)
**Order: 180-199**
- SETTING (180) - Time/place/environment
- CHARACTER (181) - Character introduction
- DIALOGUE (182) - Direct speech
- INTERIOR_MONOLOGUE (183) - Internal thoughts
- NARRATIVE_VOICE (184) - Narrator commentary
- SYMBOLISM (185) - Symbolic elements

### XI. SENSORY & PERCEPTUAL (Parent: None)
**Order: 200-219**
- SENSORY_DETAIL (200) - Rich sensory descriptions
- OPTICAL_DISTORTION (201) - Visual distortions

### XII. VALUES (Parent: None)
**Order: 220-239**
- AUTONOMY (220)
- COMMUNITY (221)
- ORDER (222)
- CHAOS (223)
- TRUTH (224)
- BEAUTY (225)
- POWER (226)
- JUSTICE (227)
- AESTHETIC_JUDGMENT (228) - Evaluating art

### XIII. SOCIAL DYNAMICS (Parent: None)
**Order: 240-249**
- EXPLOITATION (240) - Economic/social exploitation

## Implementation Notes

1. **Parent Codes to Create:**
   - CHARACTER_ENTITY (new parent for all character-related codes)
   - OBJECT_ENTITY (new parent for all object codes)
   - SOCIAL_ENTITY (new parent for social structure codes)

2. **Code Type Updates:**
   - Character name codes: type = "descriptive"
   - Character role codes: type = "descriptive" 
   - Process codes: type = "process" (already correct)
   - Emotion codes: type = "emotion" (already correct)
   - Structure codes: type = "structure" (already correct)
   - Values codes: type = "values" (already correct)

3. **Ordering Strategy:**
   - Major categories get ranges of 20 (0-19, 20-39, etc.)
   - Subcategories within ranges
   - Leaves room for expansion

4. **Generic Codes:**
   - Keep SETTING, CHARACTER, DIALOGUE but move to end as "catch-all" codes
   - These are useful for broad coding but shouldn't be primary

