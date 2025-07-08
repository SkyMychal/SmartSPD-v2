# SmartSPD v2 - AI-Powered Health Plan Assistant

**Powered by Onyx AI**

## Overview

SmartSPD is an enterprise-grade AI assistant designed specifically for TPA (Third Party Administrator) customer service operations. It enables customer service agents to provide instant, accurate answers to health plan member questions by leveraging AI-powered document processing and knowledge graphs.

## Key Features

- **Intelligent Document Processing**: Automated parsing of SPD (Summary Plan Description) PDFs and BPS (Benefit Plan Specification) Excel files
- **Knowledge Graph Integration**: Complex benefit relationships and plan hierarchies for accurate responses
- **Multi-Tenant Architecture**: Complete TPA isolation with custom branding and configuration
- **Real-Time Chat Interface**: Agent-focused UI for seamless customer service workflows
- **Advanced Analytics**: Comprehensive dashboards for performance monitoring and business intelligence
- **Enterprise Security**: HIPAA-compliant with role-based access control and audit logging

## Architecture

- **Backend**: FastAPI (Python) with async support
- **Frontend**: Next.js 14 with TypeScript
- **Database**: PostgreSQL with multi-tenant schema
- **Vector Database**: Pinecone for semantic search
- **Knowledge Graph**: Neo4j for benefit relationships
- **AI**: OpenAI/Azure OpenAI integration
- **Caching**: Redis for performance optimization

## Getting Started

See the setup instructions in each component:
- [Backend Setup](./backend/README.md)
- [Frontend Setup](./frontend/README.md)

## License

Proprietary - BeneSense AI / Onyx AI