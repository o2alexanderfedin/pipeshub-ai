<objective>
Analyze PipesHub's external service dependencies and prepare discussion points on which services should connect externally vs run locally in Docker.

This analysis will help make architectural decisions about:
- Cost optimization (local vs cloud services)
- Performance considerations (latency, throughput)
- Security implications (data leaving local environment)
- Operational complexity (service management)
</objective>

<context>
PipesHub is a document indexing and retrieval platform that integrates with various enterprise services.

## Services Deployed Locally (Docker)
- MongoDB (document storage)
- Redis (cache/message broker)
- ArangoDB (graph/document database)
- Qdrant (vector search)
- Kafka + Zookeeper (message broker)
- etcd (configuration/credentials)
- Node.js backend, Python connectors, Python indexing
- Frontend (React)

## External Services Referenced
**AI/ML Providers:** OpenAI, Anthropic, Azure OpenAI, Groq, Cohere, Mistral, Gemini, Fireworks, Together.ai, xAI, AWS Bedrock, Ollama (local option)

**Enterprise Connectors:** Google Workspace (Drive, Gmail, Calendar, Docs), Microsoft 365 (OneDrive, Outlook, Teams, SharePoint), Slack, Notion, Jira, Confluence, Dropbox, ServiceNow

**Cloud Storage:** AWS S3, Azure Blob Storage

**Document Processing:** Azure Document Intelligence (optional, local alternatives exist)
</context>

<analysis_requirements>
For each category of external service, evaluate:

1. **AI/ML Model Providers**
   - Which providers are essential vs optional?
   - Cost comparison: local Ollama vs cloud APIs
   - Performance/quality tradeoffs
   - Recommendation: local, cloud, or hybrid approach

2. **Enterprise Connectors**
   - These MUST connect externally (they're SaaS platforms)
   - Authentication considerations (OAuth, API tokens)
   - Rate limiting and quota management
   - Data residency/compliance implications

3. **Cloud Storage (S3/Azure)**
   - When to use local storage vs cloud?
   - Backup and disaster recovery considerations
   - Cost vs convenience tradeoffs

4. **Document Processing**
   - Azure Document Intelligence vs local OCR
   - Processing capacity and scaling needs

5. **Ollama Configuration**
   - Currently expects host.docker.internal:11434
   - Should this be included in docker-compose?
   - GPU requirements and alternatives
</analysis_requirements>

<discussion_points>
Prepare answers to these questions:

1. **Minimum viable external dependencies**: What's the minimum set of external services needed to run PipesHub productively?

2. **Cost optimization**: Which cloud services could be replaced with local alternatives without significant quality loss?

3. **Security posture**: Which services should definitely remain local to avoid data leaving the environment?

4. **Scaling considerations**: Which services would become bottlenecks if kept local during scaling?

5. **Ollama deployment**: Should Ollama be added to docker-compose with GPU support, or kept as external dependency?

6. **Hybrid recommendations**: What's the ideal split between local and external services for:
   - Development environment
   - Small production (single server)
   - Large production (distributed)
</discussion_points>

<output_format>
Create a comprehensive analysis document with:

1. Executive summary (2-3 paragraphs)
2. Service-by-service analysis table
3. Recommended configurations for different deployment scenarios
4. Trade-off matrix (cost, performance, security, complexity)
5. Decision checklist for users

Save analysis to: `./analyses/external-service-requirements.md`
</output_format>

<success_criteria>
- All service categories analyzed with clear recommendations
- Trade-offs clearly articulated
- Actionable guidance for different deployment scenarios
- Security considerations explicitly addressed
- Cost implications estimated where possible
</success_criteria>
