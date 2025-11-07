# Library Functions vs Wrapper Functions

## How Google Apps Script Libraries Work

### Option 1: Using Library Functions Directly (with prefix)

**Technically possible, but has limitations:**

```excel
=CBBData.GET_PLAYERS_FULL(A1)
```

**Requirements:**
- Library must be added with identifier `CBBData`
- Function must be public (not private)
- Library must be in Development mode or specific version

**Limitations:**
- ❌ Functions won't appear in Google Sheets autocomplete
- ❌ No `@customfunction` tag support (autocomplete doesn't work)
- ❌ More verbose syntax
- ❌ Can be unreliable depending on library setup

### Option 2: Using Wrapper Functions (recommended)

**The recommended approach:**

```excel
=GET_PLAYERS_FULL(A1)
```

**Requirements:**
- Library must be added with identifier `CBBData`
- Wrapper functions must be in **your spreadsheet's Apps Script** (not the library)
- Copy `LibraryWrappers.gs` to your spreadsheet's Apps Script editor

**Benefits:**
- ✅ Functions appear in Google Sheets autocomplete
- ✅ Cleaner syntax (no prefix needed)
- ✅ `@customfunction` tag works properly
- ✅ Better user experience
- ✅ More reliable

## The Reality

**You're correct!** For the best experience and to make functions work reliably in Google Sheets cells, you **need the wrapper functions** in your spreadsheet's Apps Script.

### Why Wrappers Are Needed

1. **Custom Functions**: Google Sheets only recognizes `@customfunction` tags in the **spreadsheet's own script**, not in libraries
2. **Autocomplete**: Functions only appear in autocomplete if they're defined in the spreadsheet's script
3. **Reliability**: Direct library calls can be unreliable; wrappers provide a stable interface

### The Workflow

1. **Library** (`google-apps-script-cbbd.js`): Contains the actual function logic
2. **Wrappers** (`LibraryWrappers.gs`): Thin wrappers that call the library functions
3. **Spreadsheet**: Has both the library (added) AND the wrappers (copied into its Apps Script)

## How It Works

```
User types: =GET_PLAYERS_FULL(A1)
     ↓
Wrapper in spreadsheet: GET_PLAYERS_FULL() calls CBBData.GET_PLAYERS_FULL()
     ↓
Library function: CBBData.GET_PLAYERS_FULL() executes the actual logic
     ↓
Returns result to spreadsheet
```

## Summary

- **Direct library calls** (`=CBBData.FUNCTION()`) might work but are unreliable
- **Wrapper functions** (`=FUNCTION()`) are the recommended, reliable approach
- **You need both**: Library added + Wrappers copied to spreadsheet
- **Updates**: When you push library updates, wrappers automatically get the new functionality

## Best Practice

Always use wrapper functions for:
- ✅ Custom functions in Google Sheets
- ✅ Autocomplete support
- ✅ Clean syntax
- ✅ Reliable execution

