<objective>
Update the system requirements in `./docs/setup-guide-local-anthropic.md` to reflect minimal hardware for a laptop demo.

This is for a demo tomorrow on limited hardware - requirements must be realistic for a low-spec laptop.
</objective>

<context>
File to modify: `./docs/setup-guide-local-anthropic.md`

Target hardware: Minimal laptop for demo purposes
</context>

<new_requirements>
Update the Prerequisites/System Requirements section with these values:

- **RAM**: 8 GB (was likely 16-32 GB)
- **CPU**: 2 cores (was likely 4+)
- **Disk Space**: 30 GB (was likely 50+ GB)

Also update any other references to hardware requirements throughout the document to be consistent with these minimums.

If there are notes about "recommended" vs "minimum" requirements, make these the minimum and remove or lower the recommended values accordingly.
</new_requirements>

<output>
Modify the file in place: `./docs/setup-guide-local-anthropic.md`
</output>

<verification>
After editing, verify:
- RAM requirement shows 8 GB
- CPU requirement shows 2 cores
- Disk space requirement shows 30 GB
- No contradicting higher requirements elsewhere in doc
</verification>

<success_criteria>
- All hardware requirements updated to minimal values
- Document remains coherent
- No conflicting requirements in different sections
</success_criteria>
