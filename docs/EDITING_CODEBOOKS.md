# How to Edit Codebooks in the Admin Panel

## Accessing the Admin Panel

1. Go to `/admin/` on your site
2. Log in with your superuser account
3. Navigate to **Literary Analysis** section

## Editing a Codebook

### Method 1: Edit Codebook with Inline Codes (Recommended)

1. Go to **Codebook Templates** in the admin
2. Click on the codebook you want to edit (e.g., "Dhalgren - Complete Analysis")
3. You'll see an inline editor at the bottom showing all codes
4. **To add a new code:**
   - Scroll to the bottom of the inline codes section
   - Click "Add another Code"
   - Fill in:
     - **Code name**: e.g., "NEW_CODE_NAME"
     - **Code type**: Choose from Descriptive, Process, Emotion, Values, or Structure
     - **Definition**: What this code captures
     - **Parent code**: (Optional) Select a parent code to create hierarchy
     - **Order**: Number controlling display order (lower = appears first)
   - Click "Save"
   
5. **To edit an existing code:**
   - Find the code in the inline list
   - Modify any field (name, type, definition, parent, order)
   - Click "Save"
   
6. **To delete a code:**
   - Find the code in the inline list
   - Check the "Delete" checkbox next to it
   - Click "Save"

### Method 2: Edit Individual Codes

1. Go to **Codes** in the admin
2. Use the search/filter to find codes from your codebook
3. Click on a code name to edit it
4. Make your changes and click "Save"
5. To delete: Click "Delete" button at the bottom

## Important Fields

- **Code name**: Unique identifier (e.g., "URBAN_DECAY", "KID")
- **Code type**: 
  - `descriptive`: Describes what is (characters, places, objects)
  - `process`: Describes what happens (actions, transformations)
  - `emotion`: Emotional states
  - `values`: Values and beliefs
  - `structure`: Narrative structure elements
- **Definition**: What this code captures (important for clarity)
- **Parent code**: Creates hierarchy (e.g., PARANOIA under FEAR)
- **Order**: Controls display order in coding interface (0 = first)

## Best Practices

1. **Use consistent naming**: UPPER_SNAKE_CASE for code names
2. **Set logical order**: Group related codes together with similar order numbers
3. **Use parent codes**: Create hierarchies for related codes (e.g., character roles under CHARACTER_ENTITY)
4. **Write clear definitions**: Helps you remember what each code means
5. **Don't delete codes in use**: If a code is already applied to segments, deleting it will remove those applications

## Example: Adding a New Character Code

1. Go to Codebook Templates → "Dhalgren - Complete Analysis"
2. Scroll to Codes section
3. Click "Add another Code"
4. Fill in:
   - Code name: `NEW_CHARACTER`
   - Code type: `descriptive`
   - Definition: `Description of the new character`
   - Parent code: Select `CHARACTER_ENTITY` (if it exists)
   - Order: `34` (after other character codes)
5. Click "Save"

## Example: Creating a Subcode

1. First, ensure the parent code exists (e.g., "FEAR")
2. Add a new code:
   - Code name: `TERROR`
   - Code type: `emotion`
   - Definition: `Extreme fear`
   - Parent code: Select `FEAR`
   - Order: `101` (after FEAR which is 100)
3. Click "Save"

## Troubleshooting

- **Can't see codes inline?** Make sure you're editing an existing codebook, not creating a new one
- **Code not appearing in coding interface?** Check the `order` field - codes are sorted by order
- **Can't set parent code?** The parent code must exist and be in the same codebook
- **Changes not showing?** Try refreshing the page or clearing your browser cache

