# Block Containers Persistence Fix Plan

## Objective

Create a concrete, executable plan for fixing the block_containers persistence issue based on research findings. The plan must address the root cause, define the implementation approach, establish verification criteria, and provide rollback procedures to safely restore content extraction to full working state.

**Why this matters**: Research has identified why block_containers is not persisting to ArangoDB. Now we need a clear, actionable roadmap to implement the fix, verify it works end-to-end, and complete the validation workflow that was blocked at Phase 2. The goal is to achieve "done-done-done" state where content extraction works completely from file read through database persistence to query retrieval.

## Context

### Research Input

**@.prompts/004-block-containers-persistence-research/block-containers-persistence-research.md**
- Use root cause findings from research phase
- Reference specific code locations and evidence
- Build on architectural understanding discovered
- Address the exact persistence failure mechanism identified

### Blocked Validation

**@.prompts/003-content-extraction-validation-do/SUMMARY.md**
- Phase 2 validation blocked at database query step
- 12 test records created with content in logs but not database
- Need to resume: Phase 2 validation → Phase 3 comprehensive testing → Phase 4 final verification
- Original goal: Validate all 17 tests and achieve done-done-done

### Implementation Context

**@.prompts/009-connector-missing-content-fix/**
- Content extraction code working correctly
- block_containers populated in memory
- Problem is purely in persistence layer

**@.prompts/010-connector-missing-content-test/**
- 17 comprehensive tests waiting to run
- Test files exist at `/data/pipeshub/test-files/`
- Cannot execute until content persists correctly

## Requirements

### Plan Scope

Create a **complete, actionable plan** covering:

#### 1. Root Cause Resolution

Based on research findings:
- **If serialization bug**: Fix Pydantic model_dump() or batch_upsert_records()
- **If schema issue**: Update ArangoDB collection schema
- **If architectural**: Implement proper content storage (separate collection, indexing service, etc.)
- **If configuration**: Update persistence settings or field inclusion lists

**Must include**:
- Exact code changes needed (file paths, line numbers, before/after)
- Configuration changes required
- Database schema updates (if needed)
- Migration strategy for existing records

#### 2. Implementation Strategy

**Code Changes**:
- Which files to modify
- Exact functions/methods to update
- Before/after code snippets
- Type safety considerations
- Error handling additions

**Testing Approach**:
- Unit tests to create/update
- Integration tests needed
- Verification queries to run
- Sample data to test with

**Deployment Process**:
- Docker rebuild required (Yes/No)
- Container restart needed (Yes/No)
- Database migration steps
- Configuration updates

#### 3. Verification Plan

**Immediate Verification** (after fix):
- Query to confirm block_containers persists
- Sample record inspection
- Field validation checklist
- Content quality check

**Comprehensive Validation** (resume Phase 2):
- All 12 test files have content
- Content is queryable from ArangoDB
- Content matches source files
- All file types handled correctly

**Full Testing** (Phase 3):
- Execute remaining tests from 17-test suite
- Edge cases, large files, Unicode
- Performance validation

#### 4. Rollback Procedures

**If fix fails**:
- Immediate recovery steps
- How to restore previous state
- Data integrity checks
- Fallback options

**Contingencies**:
- If schema change breaks existing queries
- If serialization causes performance issues
- If alternative storage needs different architecture

#### 5. Risk Management

**Potential risks**:
- Breaking existing record queries
- Performance degradation from large content
- Schema migration failures
- Data loss during updates

**Mitigation strategies**:
- Backup before changes
- Staged rollout approach
- Performance benchmarks
- Validation at each step

### Plan Structure

Organize as **sequential phases** with clear dependencies:

**Phase 0: Pre-Implementation Preparation**
- Backup current database state
- Document current behavior
- Prepare test environment
- Review research findings

**Phase 1: Core Fix Implementation**
- Make identified code changes
- Update configurations
- Rebuild and deploy
- Initial smoke test

**Phase 2: Immediate Verification**
- Trigger new sync
- Query for content
- Validate persistence
- Confirm fix works

**Phase 3: Comprehensive Validation** (Resume original Phase 2)
- Verify all 12 test records
- Content quality checks
- Query functionality
- Multiple file types

**Phase 4: Full Testing** (Original Phase 3)
- Execute 9 critical tests
- Edge cases
- Performance validation
- Integration tests

**Phase 5: Final Sign-Off** (Original Phase 4)
- End-to-end verification
- Documentation updates
- Done-done-done confirmation

### Decision Framework

For each decision point, provide:

**Decision Template**:
```xml
<decision id="decision-id">
<question>[What needs to be decided?]</question>
<context>[Why this decision matters]</context>
<options>
  <option id="A">
    <description>[Approach A]</description>
    <pros>[Benefits]</pros>
    <cons>[Drawbacks]</cons>
    <effort>[Time/complexity estimate]</effort>
    <risk>[Risk level: Low/Medium/High]</risk>
  </option>
  <option id="B">
    [Same structure]
  </option>
</options>
<recommendation>[Preferred option]</recommendation>
<rationale>[Why recommended]</rationale>
<approval_needed>Yes/No</approval_needed>
</decision>
```

**Common Decisions**:
- Modify existing serialization vs. create custom serializer
- Update schema vs. use existing schema differently
- Fix in persistence layer vs. fix in model layer
- Store in ArangoDB vs. alternative storage
- Migrate existing records vs. only fix new ones

## Output Specification

Save your plan to: `.prompts/005-block-containers-persistence-plan/block-containers-persistence-plan.md`

### Required Structure

```xml
# Block Containers Persistence Fix Plan

## Executive Summary

[One paragraph: fix approach, estimated time, key decisions, success criteria]

**Root Cause Addressed**: [From research]

**Fix Strategy**: [High-level approach]

**Estimated Time**: [Total hours]

**Critical Decisions**: [Key choices that need approval]

## Prerequisites

<phase id="phase-0" name="Pre-Implementation">
<objective>[Prepare for fix implementation]</objective>

<tasks>
1. [Task 1]: [Acceptance criteria]
2. [Task 2]: [Acceptance criteria]
</tasks>

<success_criteria>
- [Criterion 1]: [How to verify]
- [Criterion 2]: [How to verify]
</success_criteria>

<estimated_time>[X minutes/hours]</estimated_time>

<dependencies>
- [What must be done first]
</dependencies>

<risks>
- [Risk]: [Mitigation]
</risks>
</phase>

## Phase 1: Core Fix Implementation

<phase id="phase-1" name="Fix Implementation">
<objective>[Implement the identified fix]</objective>

<code_changes>
### File 1: [path/to/file.py]

**Location**: Lines [X-Y]

**Current Code**:
```python
[Code that's broken]
```

**Updated Code**:
```python
[Fixed code]
```

**Rationale**: [Why this change fixes the issue]

### File 2: [Another file if needed]

[Same structure]
</code_changes>

<configuration_changes>
### [Config file or setting]

**Current**:
```
[Current config]
```

**Updated**:
```
[New config]
```

**Reason**: [Why needed]
</configuration_changes>

<database_changes>
### Schema Update (if needed)

**Collection**: records

**Current Schema**:
```json
[Current]
```

**Updated Schema**:
```json
[Updated]
```

**Migration**:
```aql
[AQL migration query if needed]
```
</database_changes>

<deployment_steps>
1. [Step 1]: [Exact command]
2. [Step 2]: [Exact command]
3. [Step 3]: [Expected output]
</deployment_steps>

<success_criteria>
- Code changes applied: ✅/❌
- Container rebuilt: ✅/❌
- Service restarted: ✅/❌
- No errors in logs: ✅/❌
</success_criteria>

<estimated_time>[X minutes/hours]</estimated_time>

<rollback_procedure>
If this phase fails:
1. [Immediate action]
2. [Restore previous version]
3. [Verify rollback succeeded]
</rollback_procedure>
</phase>

## Phase 2: Immediate Verification

<phase id="phase-2" name="Immediate Verification">
<objective>[Confirm fix works with simple test]</objective>

<verification_steps>
### Step 1: Trigger Content Sync

**Action**:
```bash
[Command to trigger sync or create test record]
```

**Expected Result**: [What should happen]

### Step 2: Query for Content

**Query**:
```sql
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
  AND CONTAINS(doc.externalRecordId, "test-files/basic/sample.txt")
RETURN {
  recordName: doc.recordName,
  hasBlockContainers: doc.block_containers != null,
  blockCount: LENGTH(doc.block_containers.blocks),
  contentPreview: doc.block_containers.blocks[0].data
}
```

**Expected Result**:
```json
{
  "recordName": "sample.txt",
  "hasBlockContainers": true,
  "blockCount": 1,
  "contentPreview": "This is a sample text file..."
}
```

### Step 3: Validate Content Quality

**Checks**:
- [ ] block_containers field exists
- [ ] blocks array has entries
- [ ] data field contains actual file content
- [ ] Content matches source file
- [ ] No truncation or corruption
</verification_steps>

<success_criteria>
- Query returns block_containers: ✅
- Content preview shows actual text: ✅
- Block count > 0: ✅
- Content matches file: ✅
</success_criteria>

<estimated_time>[X minutes]</estimated_time>

<failure_handling>
If verification fails:
1. Check logs for errors
2. Verify serialization in code
3. Test with Python shell manually
4. [Additional debugging steps]
</failure_handling>
</phase>

## Phase 3: Comprehensive Validation

<phase id="phase-3" name="Resume Original Phase 2">
<objective>[Validate all 12 test files have content]</objective>

<validation_tasks>
### Task 1: Verify All Test Records

**Query**:
```sql
FOR doc IN records
FILTER doc.connectorName == "LOCAL_FILESYSTEM"
  AND CONTAINS(doc.externalRecordId, "test-files")
COLLECT hasContent = (doc.block_containers != null)
WITH COUNT INTO count
RETURN { hasContent, count }
```

**Expected**: `{ hasContent: true, count: 12 }`

### Task 2: File Type Coverage

**Check**: Each file type has content

| File Type | File | Has Content | ✅/❌ |
|-----------|------|-------------|-------|
| TypeScript | calculator.ts | Required | |
| Python | analyzer.py | Required | |
| JSON | config.json | Required | |
| CSS | styles.css | Required | |
| Markdown | README.md | Required | |
| Text | sample.txt | Required | |
| YAML | design.yaml | Required | |
| Large | large-file.md | Required | |
| Empty | empty.txt | Required | |
| Unicode | unicode.md | Required | |

### Task 3: Content Quality Validation

For each file type:
1. Retrieve content from database
2. Compare with source file
3. Verify encoding preserved
4. Check for truncation
</validation_tasks>

<success_criteria>
- All 12 records have block_containers: ✅
- All content matches source files: ✅
- Unicode properly preserved: ✅
- Large files handled correctly: ✅
- Empty files handled gracefully: ✅
</success_criteria>

<estimated_time>[X minutes]</estimated_time>
</phase>

## Phase 4: Full Testing Suite

<phase id="phase-4" name="Execute Comprehensive Tests">
<objective>[Run 9 critical tests from original test plan]</objective>

<test_execution>
**Tests from**: `.prompts/010-connector-missing-content-test/TEST-COMMANDS.md`

### Smoke Tests (Must Pass)
1. Test 1: Basic content extraction
2. Test 2: Multiple file types
3. Test 3: Large file handling

### Functional Tests
4. Test 4: Unicode preservation
5. Test 5: Binary file handling
6. Test 6: Empty file handling
7. Test 7: File extension accuracy

### Integration Tests
8. Test 8: Search functionality
9. Test 9: Content indexing
</test_execution>

<success_criteria>
- All 9 tests pass: ✅
- No regressions in existing functionality: ✅
- Performance acceptable: ✅
</success_criteria>

<estimated_time>[X minutes/hours]</estimated_time>
</phase>

## Phase 5: Final Sign-Off

<phase id="phase-5" name="Done-Done-Done Confirmation">
<objective>[Final validation and documentation]</objective>

<final_checks>
1. **End-to-End Test**: Upload new file → sync → query → verify content
2. **Performance**: Measure query response times
3. **Documentation**: Update relevant docs
4. **Known Issues**: Document any limitations
</final_checks>

<sign_off_criteria>
- ✅ Content extraction working end-to-end
- ✅ Database persistence confirmed
- ✅ Queries return content successfully
- ✅ All critical tests passing
- ✅ No known blockers
- ✅ System production-ready
</sign_off_criteria>

<estimated_time>[X minutes]</estimated_time>
</phase>

## Decisions Required

<decision id="decision-1">
[Use decision template from requirements]
</decision>

<decision id="decision-2">
[Additional decisions]
</decision>

## Risk Management

### Risk 1: [Risk description]

**Probability**: Low/Medium/High

**Impact**: Low/Medium/High

**Mitigation**:
- [Preventive action 1]
- [Preventive action 2]

**Contingency**:
- [What to do if it happens]

### Risk 2: [Next risk]

[Same structure]

## Rollback Plan

### Trigger Conditions

Rollback if:
- Fix causes errors in existing functionality
- Performance degrades unacceptably
- Data corruption detected
- Unable to verify fix works

### Rollback Procedure

**Step 1: Stop Services**
```bash
[Command]
```

**Step 2: Restore Code**
```bash
[Git revert or restore command]
```

**Step 3: Restore Database** (if schema changed)
```bash
[Restore schema or data]
```

**Step 4: Restart Services**
```bash
[Restart commands]
```

**Step 5: Verify Rollback**
```bash
[Verification commands]
```

## Timeline

**Total Estimated Time**: [X hours]

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Preparation | [X min] | None |
| Phase 1: Implementation | [X min] | Phase 0 |
| Phase 2: Immediate Verification | [X min] | Phase 1 |
| Phase 3: Comprehensive Validation | [X min] | Phase 2 |
| Phase 4: Full Testing | [X min] | Phase 3 |
| Phase 5: Sign-Off | [X min] | Phase 4 |

**Critical Path**: [Phases that determine minimum time]

**Parallel Opportunities**: [Tasks that can run concurrently]

## Success Metrics

**Minimum for Success**:
- block_containers field persists to ArangoDB
- At least 1 test record queryable with content
- Content matches source file
- No errors in persistence path

**Complete Success** (Done-Done-Done):
- All 12 test files have persisted content
- All 9 critical tests pass
- Content queryable and usable
- Performance acceptable
- System production-ready
- Original validation workflow complete

## Metadata

<confidence>High/Medium/Low - Confidence this plan will succeed</confidence>

<dependencies>
**From Research**:
- [Root cause from research]
- [Architectural understanding from research]

**External**:
- Docker access for rebuild
- ArangoDB write access
- Ability to restart services
</dependencies>

<open_questions>
- [Question 1 requiring answer before execution]
- [Question 2 requiring clarification]
</open_questions>

<assumptions>
- [Assumption 1 from research is correct]
- [Assumption 2 about system behavior]
</assumptions>

<blockers>
- [Any external impediments preventing execution]

OR

None - ready to execute
</blockers>

<next_steps>
1. [First action after plan approval - usually execute Phase 0]
2. [Second action]
</next_steps>
```

## SUMMARY.md Requirement

Create `.prompts/005-block-containers-persistence-plan/SUMMARY.md`:

**One-liner**: [Substantive description of fix approach - e.g., "5-phase plan to fix Pydantic serialization, validate 12 test files, and complete comprehensive testing"]

**Version**: v1

**Fix Strategy**: [Core approach to solving the problem]

**Key Decisions**:
- [Most important choice in the plan]
- [Second most important]

**Phases**: [Number] phases, [Total estimated time]

**Phases Overview**:
- **Phase 0** ([time]): [Brief description]
- **Phase 1** ([time]): [Brief description]
- **Phase 2** ([time]): [Brief description]
- **Phase 3** ([time]): [Brief description]
- **Phase 4** ([time]): [Brief description]

**Risks**:
- [Top risk and mitigation]

**Decisions Needed**:
- [What requires user approval before proceeding]

**Blockers**:
- [External impediments, if any]

**Next Step**:
- [First concrete action to execute the plan]

## Success Criteria

**Minimum Requirements**:
- ✅ All phases defined with clear objectives
- ✅ Exact code changes specified (file paths, line numbers, before/after)
- ✅ Each phase has measurable success criteria
- ✅ Dependencies between phases explicitly stated
- ✅ Rollback procedure for each risky phase
- ✅ Timeline estimates provided
- ✅ Decision points identified with options and recommendations
- ✅ Builds on research findings
- ✅ SUMMARY.md created with substantive one-liner
- ✅ Plan leads to "done-done-done" state

**Quality Standards**:
- Phases are sequential and logically ordered
- Code changes are specific and actionable
- Success criteria are objectively measurable
- Recommendations have clear rationale based on research
- No ambiguous steps (all are executable)
- Time estimates are realistic
- Risks are specific with concrete mitigations
- Rollback plan is complete and tested mentally

## Execution Notes

- **Input**: Research findings from previous prompt
- **Time Estimate**: 1-2 hours to create comprehensive plan
- **Approach**: Build on root cause analysis, don't re-investigate
- **Focus**: Actionable steps, specific code changes, clear verification

Begin planning now and save output to the specified location.
