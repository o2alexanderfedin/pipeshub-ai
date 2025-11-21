<objective>
Finalize the setup guide `./docs/setup-guide-local-anthropic.md` to be deployment-ready by:

1. Populating actual .env values from the codebase's .env.example files
2. Fixing the embedding model name to full path: `sentence-transformers/all-MiniLM-L6-v2`
3. Adding Playwright automation scripts for any web-based configuration steps
4. Ensuring the guide is complete and actionable for immediate deployment

This is critical - the guide must be absolutely ready for a demo tomorrow.
</objective>

<research>
First, examine these files to understand the actual .env structure:

1. `./.env.example` (root level)
2. `./backend/.env.example`
3. `./deployment/docker-compose/*.yml` - for any env vars defined there

Extract all environment variables and their default/example values.
</research>

<requirements>
## 1. Environment Variables
- Extract ALL environment variables from .env.example files
- Populate the guide's .env template with actual values
- Include clear comments for each variable explaining its purpose
- Mark which values are required vs optional
- For the Anthropic API key, use placeholder `your-anthropic-api-key-here`

## 2. Fix Embedding Model Name
- Change `all-MiniLM-L6-v2` to `sentence-transformers/all-MiniLM-L6-v2`
- This is the full HuggingFace model path required by Sentence Transformers

## 3. Playwright Automation
For any configuration that requires web UI interaction, create Playwright scripts:

- Add a section "Automated Configuration with Playwright"
- Include installable Playwright script(s) for:
  - Initial admin setup if needed
  - AI provider configuration in PipesHub UI
  - Any other web-based settings
- Scripts should be copy-paste ready
- Include npm/npx commands to run them

## 4. Deployment Readiness
Ensure the guide includes:
- Exact docker-compose command to use
- How to verify all services started correctly
- First-time setup steps after containers are running
- How to access the web UI and complete initial configuration
</requirements>

<playwright_script_template>
Create scripts like this:

```javascript
// scripts/configure-pipeshub.js
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  // Navigate to PipesHub UI
  await page.goto('http://localhost:3000');

  // Configuration steps...

  await browser.close();
})();
```

Include instructions to run:
```bash
npx playwright install chromium
node scripts/configure-pipeshub.js
```
</playwright_script_template>

<output>
Modify in place: `./docs/setup-guide-local-anthropic.md`

Optionally create: `./scripts/configure-pipeshub.js` (if Playwright automation is needed)
</output>

<verification>
After completing, verify:
- All environment variables have actual values (not placeholders except API key)
- Embedding model shows `sentence-transformers/all-MiniLM-L6-v2`
- .env template is complete and copy-paste ready
- Playwright scripts (if created) have proper syntax
- Guide can be followed start-to-finish without guessing
</verification>

<success_criteria>
- Guide is 100% deployment-ready
- .env values sourced from actual .env.example files
- Embedding model name is fully qualified
- Web configuration steps are automated with Playwright
- Someone can follow this guide tomorrow and successfully deploy PipesHub
</success_criteria>
