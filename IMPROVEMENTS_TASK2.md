# Task 2 Entity Extraction Improvements

## Issues Identified

1. **Terminology Validator Over-Correction**:
   - Expanding common words like "of", "80", "C" as medical abbreviations
   - Need: Context-aware abbreviation expansion

2. **Spell Checker Over-Correction**:
   - Correcting valid English words like "has", "and", "for"
   - Need: Whitelist of common English words

3. **Entity Extraction Duplicates**:
   - Finding overlapping entities (e.g., "reports fever" and "fever")
   - Need: Better deduplication logic

## Proposed Fixes

1. Add common English word whitelist to spell checker
2. Add context-aware abbreviation expansion
3. Improve entity deduplication
4. Add confidence thresholds for corrections

## Expected Impact

- Precision: 0.40 → 0.70+ (fewer false positives)
- Recall: 0.67 → 0.75+ (better entity detection)
- F1-Score: 0.50 → 0.72+ (overall improvement)

