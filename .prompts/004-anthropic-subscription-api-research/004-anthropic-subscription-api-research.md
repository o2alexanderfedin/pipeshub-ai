# Research: Enabling Anthropic Subscription Pricing for Standard API

<objective>
Research how to enable subscription-based pricing (10x cheaper rates) when using the standard Anthropic API (not Claude Code CLI, not Agentic API). The goal is to determine if there are special API keys, headers, authentication methods, or account settings needed to access subscription pricing.

This is critical for cost optimization - subscription rates are 10x cheaper than pay-as-you-go.
</objective>

<context>
- **Current setup**: Using standard Anthropic API with `sk-ant-api-...` key
- **Current usage**: High volume - indexing 1,725 files, making frequent API calls
- **Problem**: May be hitting rate limits and paying pay-as-you-go rates
- **Goal**: Enable subscription pricing to reduce costs by 10x

The user knows subscription pricing exists and is cheaper, but doesn't know HOW to enable it for the standard API.
</context>

<requirements>

## Primary Questions

1. **Is subscription pricing automatic or opt-in?**
   - Does it activate automatically when you subscribe?
   - Or do you need special API keys or configuration?

2. **Are there different API keys for subscription vs pay-as-you-go?**
   - Do subscription customers get different key formats?
   - Do headers change (e.g., `anthropic-version`, special billing headers)?

3. **How to verify you're using subscription pricing?**
   - Is there a way to check if current API key is subscription-tier?
   - Can you see pricing tier in API responses or usage dashboard?

4. **Account configuration needed?**
   - Do you need to upgrade account to subscription tier first?
   - Is there a Console setting or billing page to enable it?

## Research Sources

**Primary sources** (check these first):
- Anthropic official documentation: https://docs.anthropic.com/
- Anthropic Console billing/pricing page
- API reference for authentication: https://docs.anthropic.com/en/api/
- Anthropic pricing page: https://www.anthropic.com/pricing

**Search queries**:
- "anthropic api subscription pricing how to enable"
- "anthropic subscription api key"
- "anthropic api billing tiers"
- "anthropic pay as you go vs subscription"

**Verification method**:
- Check current API key format
- Look for billing tier indicators in Console
- Test if there's a /pricing or /account endpoint

## Expected Output Structure

Organize findings as:

### Subscription Pricing Activation
[How to enable subscription pricing - step by step]

### API Key Differences
[Any differences in API keys between pay-as-you-go and subscription]

### Verification Methods
[How to confirm you're using subscription pricing]

### Current Status
[Analysis of current setup - are we on subscription or pay-as-you-go?]

### Action Items
[Concrete steps to enable subscription if not already active]

</requirements>

<output>
Save comprehensive research to: `.prompts/004-anthropic-subscription-api-research/anthropic-subscription-api-research.md`

Include:
- Clear explanation of subscription pricing activation
- Step-by-step instructions if configuration is needed
- Verification methods to confirm subscription is active
- Any code examples for checking billing tier programmatically

Create SUMMARY.md with:
- **One-liner**: How to enable Anthropic subscription pricing
- **Key Findings**: The concrete answer - how to activate it
- **Decisions Needed**: If manual steps are required
- **Blockers**: Any prerequisites (e.g., must contact sales, minimum commitment)
- **Next Step**: Immediate action to enable subscription pricing

<metadata>
- `<confidence>`: High/Medium/Low based on official documentation
- `<dependencies>`: Account access, billing permissions
- `<open_questions>`: Any uncertainties about activation process
- `<assumptions>`: Assumptions about current account type
</metadata>
</output>

<verification>
Before finalizing, verify:
- [ ] Checked official Anthropic documentation
- [ ] Searched for subscription pricing docs
- [ ] Reviewed Console billing/account pages
- [ ] Confirmed API key format requirements
- [ ] Identified verification method
- [ ] Provided actionable next steps
</verification>

<success_criteria>
- Clear answer on HOW to enable subscription pricing
- Verification method to confirm it's active
- Step-by-step instructions if manual activation needed
- Current status assessment (are we already on subscription or not?)
</success_criteria>
