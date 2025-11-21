<objective>
Create a comprehensive setup guide for PipesHub that configures:
- All infrastructure services running locally via Docker
- Anthropic (Claude) as the LLM provider
- Local Ollama for embeddings (cost-effective alternative)

This guide will enable a user to deploy PipesHub with maximum data privacy (all processing local) while using Anthropic's Claude for high-quality LLM responses.
</objective>

<research>
Examine the codebase to understand:

1. Docker deployment configuration:
   - `./deployment/docker-compose/docker-compose.dev.yml` or `docker-compose.prod.yml`
   - What services are included and their dependencies

2. Environment configuration:
   - `.env.example` files (root and backend)
   - What variables control AI provider selection
   - How Anthropic API key is configured

3. AI model configuration:
   - Where LLM and embedding models are specified
   - How to set Anthropic as the LLM provider
   - How to configure Ollama for embeddings

4. Frontend/UI configuration:
   - How users select AI providers in the interface
   - Any admin settings that need configuration
</research>

<guide_requirements>
Create a setup guide that includes:

## 1. Prerequisites Section
- System requirements (RAM, CPU, disk space)
- Docker and Docker Compose versions
- Ollama installation instructions
- Anthropic API key acquisition

## 2. Quick Start Steps
Numbered, copy-paste ready commands for:
1. Clone/download the repository
2. Configure environment variables
3. Start Docker services
4. Verify services are running
5. Access the web interface
6. Configure AI providers in UI

## 3. Configuration Details
For each configuration area:
- **Environment Variables**: List all relevant variables with descriptions
- **Anthropic Setup**: API key, model selection (claude-3-opus, claude-3-sonnet, etc.)
- **Ollama Setup**: Installation, model download (mxbai-embed-large), endpoint configuration
- **Docker Services**: Brief description of each service's purpose

## 4. Verification Checklist
- How to verify each service is running
- How to test LLM connectivity
- How to test embedding generation
- Expected behavior in the UI

## 5. Troubleshooting
Common issues and solutions:
- Docker networking issues
- Ollama connection failures
- Anthropic API errors
- Port conflicts

## 6. Security Notes
- API key handling best practices
- Network exposure considerations
- Data privacy benefits of this configuration
</guide_requirements>

<output_format>
Create a well-structured Markdown document with:
- Clear section headers
- Code blocks for all commands and configurations
- Tables for environment variables
- Callout boxes for important notes/warnings

Save to: `./docs/setup-guide-local-anthropic.md`
</output_format>

<verification>
Before completing, verify:
- All configuration file paths are accurate
- Environment variable names match the actual codebase
- Docker service names are correct
- The guide is complete and actionable
</verification>

<success_criteria>
- Guide can be followed by someone with basic Docker knowledge
- All commands are copy-paste ready
- Configuration is specific to Anthropic + local services
- Troubleshooting covers common failure modes
</success_criteria>
