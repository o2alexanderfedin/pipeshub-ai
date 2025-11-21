<objective>
Fully deploy PipesHub following the setup guide at `./docs/setup-guide-local-anthropic.md`.

This will get PipesHub running locally with:
- All Docker services started
- Anthropic as the LLM provider
- Sentence Transformers for embeddings
- Automated UI configuration via Playwright
</objective>

<context>
Setup guide: `./docs/setup-guide-local-anthropic.md`
Playwright script: `./scripts/configure-pipeshub.js`
Anthropic API Key: `YOUR_ANTHROPIC_API_KEY`
</context>

<deployment_steps>
Execute these steps in order:

## 1. Read the Setup Guide
Read `./docs/setup-guide-local-anthropic.md` to understand the complete .env template and deployment process.

## 2. Create .env File
Create `./deployment/docker-compose/.env` with:
- All environment variables from the guide
- The provided Anthropic API key
- Secure generated passwords for databases (use openssl rand -base64 32)

## 3. Start Docker Services
```bash
cd deployment/docker-compose
docker compose -f docker-compose.prod.yml up -d
```

## 4. Verify Services
Wait for all services to be healthy:
```bash
docker compose -f docker-compose.prod.yml ps
```

Check that these services are running:
- MongoDB
- Redis
- ArangoDB
- Qdrant
- Kafka
- Zookeeper
- etcd
- pipeshub-ai (main application)

## 5. Wait for Application Readiness
The application needs time to initialize. Check logs:
```bash
docker compose -f docker-compose.prod.yml logs -f pipeshub-ai
```

Wait until you see the application is ready to accept connections.

## 6. Configure AI Providers
Run the Playwright script to configure Anthropic and embeddings:
```bash
cd ../..
npm install playwright
npx playwright install chromium
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY node scripts/configure-pipeshub.js
```

## 7. Final Verification
- Access http://localhost:3000 in browser
- Verify login works
- Verify AI model settings show Anthropic configured
</deployment_steps>

<error_handling>
If any step fails:
- Check Docker logs: `docker compose logs [service-name]`
- Ensure ports are not in use: 3000, 8001, 8088, 8091, 27017, 6379, 8529, 6333, 9092, 2181, 2379
- If Playwright fails, take a screenshot and report the error
</error_handling>

<verification>
Deployment is successful when:
- All Docker containers show "healthy" or "running"
- http://localhost:3000 is accessible
- Playwright script completes without errors
- AI models are configured in the UI
</verification>

<success_criteria>
- PipesHub is fully running and accessible
- Anthropic is configured as LLM provider
- Sentence Transformers embeddings are configured
- User can interact with the application
</success_criteria>
