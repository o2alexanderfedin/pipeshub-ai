<objective>
Fix the frontend bug in PipesHub's connector management page that renders an icon for every indexed record (~21,000 files), causing thousands of duplicate network requests for the same `filesystem.svg` icon.

This is causing the connector management page to be unusable - it hangs while making thousands of identical HTTP requests.
</objective>

<context>
- PipesHub is a data connector platform with React frontend
- The connector management page displays connector status and indexed records
- When Local Filesystem connector indexes ~21,000 files, the page attempts to render an icon for each record
- Network tab shows thousands of duplicate requests for `filesystem.svg`
- This appears to be a frontend rendering issue, not a backend problem

@frontend/src - Examine the connector management components
</context>

<research>
First, locate and understand the bug:

1. Find the connector management page component
2. Identify where record icons are rendered
3. Determine if it's rendering icons per-record instead of per-connector
4. Check for missing virtualization, pagination, or icon caching
</research>

<requirements>
Fix the icon rendering issue by implementing one or more of:

1. **Icon deduplication**: Use a single icon per connector type, not per record
2. **Virtualization**: Only render visible rows (react-window, react-virtualized)
3. **Pagination**: Don't render all 21,000 records at once
4. **Icon caching**: Cache loaded SVGs to prevent duplicate requests

The page should:
- Load within 2-3 seconds even with 21,000+ records
- Not make duplicate network requests for the same icon
- Remain responsive and scrollable
</requirements>

<implementation>
1. Identify the exact component causing the issue
2. Determine root cause (icon per record? no virtualization? no pagination?)
3. Implement the simplest fix that solves the problem
4. Test with large dataset (21,000+ records)

Avoid:
- Over-engineering - fix the immediate bug
- Breaking existing functionality
- Major architectural changes unless absolutely necessary
</implementation>

<output>
Modify existing frontend files to fix the bug.
Document what was changed and why in your response.
</output>

<verification>
Before declaring complete:
1. Build the frontend without errors
2. Test connector management page loads quickly
3. Verify network tab shows minimal icon requests (1 per connector type, not per record)
4. Confirm page remains responsive with 21,000+ indexed records
</verification>

<success_criteria>
- Connector management page loads in < 5 seconds
- No duplicate network requests for icons
- Page is responsive and scrollable
- Existing functionality preserved
</success_criteria>
