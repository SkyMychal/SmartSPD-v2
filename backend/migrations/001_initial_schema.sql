-- SmartSPD v2 Initial Database Schema
-- Multi-tenant PostgreSQL database for TPA operations

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Create TPAs table (root tenant table)
CREATE TABLE tpas (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'United States',
    
    -- Configuration
    is_active BOOLEAN NOT NULL DEFAULT true,
    settings JSONB DEFAULT '{}',
    branding JSONB DEFAULT '{}',
    
    -- Subscription
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    max_users INTEGER DEFAULT 10,
    max_health_plans INTEGER DEFAULT 5,
    max_documents INTEGER DEFAULT 100,
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for TPAs
CREATE INDEX idx_tpas_slug ON tpas(slug);
CREATE INDEX idx_tpas_is_active ON tpas(is_active);

-- Create users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    
    -- Basic info
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    
    -- Authentication
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    
    -- Role and permissions
    role VARCHAR(50) NOT NULL DEFAULT 'cs_agent',
    permissions JSONB DEFAULT '[]',
    
    -- Profile
    phone VARCHAR(50),
    department VARCHAR(100),
    title VARCHAR(100),
    
    -- Session management
    last_login_at TIMESTAMP WITHOUT TIME ZONE,
    login_count INTEGER DEFAULT 0,
    
    -- MFA
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_secret VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for users
CREATE INDEX idx_users_tpa_id ON users(tpa_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE UNIQUE INDEX idx_users_tpa_email ON users(tpa_id, email);

-- Create health_plans table
CREATE TABLE health_plans (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    
    -- Basic info
    name VARCHAR(255) NOT NULL,
    plan_number VARCHAR(100) NOT NULL,
    plan_year INTEGER NOT NULL,
    effective_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    termination_date TIMESTAMP WITHOUT TIME ZONE,
    
    -- Plan details
    plan_type VARCHAR(50),
    description TEXT,
    
    -- Coverage amounts
    deductible_individual DECIMAL(10,2),
    deductible_family DECIMAL(10,2),
    out_of_pocket_max_individual DECIMAL(10,2),
    out_of_pocket_max_family DECIMAL(10,2),
    
    -- Copays
    primary_care_copay DECIMAL(10,2),
    specialist_copay DECIMAL(10,2),
    urgent_care_copay DECIMAL(10,2),
    emergency_room_copay DECIMAL(10,2),
    
    -- Coinsurance
    in_network_coinsurance DECIMAL(5,2),
    out_of_network_coinsurance DECIMAL(5,2),
    
    -- Prescription
    rx_generic_copay DECIMAL(10,2),
    rx_brand_copay DECIMAL(10,2),
    rx_specialty_copay DECIMAL(10,2),
    
    -- Additional data
    benefits_summary JSONB,
    exclusions JSONB,
    network_info JSONB,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    processing_status VARCHAR(50) DEFAULT 'pending',
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for health_plans
CREATE INDEX idx_health_plans_tpa_id ON health_plans(tpa_id);
CREATE INDEX idx_health_plans_plan_number ON health_plans(plan_number);
CREATE INDEX idx_health_plans_is_active ON health_plans(is_active);
CREATE INDEX idx_health_plans_effective_date ON health_plans(effective_date);

-- Create documents table
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    health_plan_id VARCHAR(36) REFERENCES health_plans(id) ON DELETE CASCADE,
    uploaded_by VARCHAR(36) NOT NULL REFERENCES users(id),
    
    -- File info
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(64),
    
    -- Document metadata
    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0',
    
    -- Processing
    processing_status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    processing_error TEXT,
    processing_log JSONB,
    extracted_metadata JSONB,
    page_count INTEGER,
    
    -- Access
    is_public BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for documents
CREATE INDEX idx_documents_tpa_id ON documents(tpa_id);
CREATE INDEX idx_documents_health_plan_id ON documents(health_plan_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_hash ON documents(file_hash);

-- Create document_chunks table
CREATE TABLE document_chunks (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    document_id VARCHAR(36) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64),
    
    -- Chunk metadata
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    section_title VARCHAR(255),
    chunk_type VARCHAR(50),
    
    -- Vector data
    embedding JSONB,
    embedding_model VARCHAR(100),
    
    -- Semantic metadata
    keywords JSONB,
    entities JSONB,
    topics JSONB,
    
    -- Quality scores
    relevance_score DECIMAL(5,4),
    confidence_score DECIMAL(5,4),
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for document_chunks
CREATE INDEX idx_document_chunks_tpa_id ON document_chunks(tpa_id);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_content_hash ON document_chunks(content_hash);
CREATE INDEX idx_document_chunks_content_trgm ON document_chunks USING GIN (content gin_trgm_ops);

-- Create conversations table
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    health_plan_id VARCHAR(36) REFERENCES health_plans(id),
    
    -- Basic info
    title VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    
    -- Context
    session_id VARCHAR(100),
    context JSONB,
    
    -- Metrics
    total_messages INTEGER DEFAULT 0,
    avg_response_time DECIMAL(10,3),
    satisfaction_rating INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for conversations
CREATE INDEX idx_conversations_tpa_id ON conversations(tpa_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_status ON conversations(status);

-- Create messages table
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Content
    content TEXT NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    
    -- Metadata
    query_intent VARCHAR(100),
    query_complexity VARCHAR(50),
    
    -- AI response data
    confidence_score DECIMAL(5,4),
    source_documents JSONB,
    reasoning TEXT,
    
    -- Performance
    response_time DECIMAL(10,3),
    token_count INTEGER,
    
    -- Feedback
    user_rating INTEGER,
    user_feedback TEXT,
    was_helpful BOOLEAN,
    
    -- Processing
    model_used VARCHAR(100),
    processing_log JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for messages
CREATE INDEX idx_messages_tpa_id ON messages(tpa_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_type ON messages(message_type);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Create query_analytics table
CREATE TABLE query_analytics (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    user_id VARCHAR(36) REFERENCES users(id),
    conversation_id VARCHAR(36) REFERENCES conversations(id),
    
    -- Query info
    query_text VARCHAR(1000) NOT NULL,
    query_hash VARCHAR(64),
    query_intent VARCHAR(100),
    query_complexity VARCHAR(50),
    
    -- Performance
    response_time DECIMAL(10,3) NOT NULL,
    confidence_score DECIMAL(5,4),
    token_count INTEGER,
    
    -- Results
    documents_retrieved INTEGER,
    sources_cited INTEGER,
    
    -- Feedback
    user_rating INTEGER,
    was_helpful BOOLEAN,
    feedback_text VARCHAR(500),
    
    -- Context
    health_plan_name VARCHAR(255),
    user_role VARCHAR(50),
    session_info JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for query_analytics
CREATE INDEX idx_query_analytics_tpa_id ON query_analytics(tpa_id);
CREATE INDEX idx_query_analytics_query_hash ON query_analytics(query_hash);
CREATE INDEX idx_query_analytics_created_at ON query_analytics(created_at);

-- Create user_activity table
CREATE TABLE user_activity (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Activity date
    activity_date DATE NOT NULL,
    
    -- Usage metrics
    queries_count INTEGER DEFAULT 0,
    conversations_count INTEGER DEFAULT 0,
    documents_accessed INTEGER DEFAULT 0,
    active_time_minutes INTEGER DEFAULT 0,
    
    -- Performance metrics
    avg_response_time DECIMAL(10,3),
    avg_confidence_score DECIMAL(5,4),
    success_rate DECIMAL(5,4),
    
    -- Satisfaction
    avg_rating DECIMAL(3,2),
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for user_activity
CREATE INDEX idx_user_activity_tpa_id ON user_activity(tpa_id);
CREATE INDEX idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX idx_user_activity_date ON user_activity(activity_date);
CREATE UNIQUE INDEX idx_user_activity_unique ON user_activity(tpa_id, user_id, activity_date);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    tpa_id VARCHAR(36) NOT NULL REFERENCES tpas(id) ON DELETE CASCADE,
    user_id VARCHAR(36) REFERENCES users(id),
    
    -- Action details
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(36),
    
    -- Context
    description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'low',
    
    -- Request details
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    request_path VARCHAR(500),
    request_method VARCHAR(10),
    
    -- Data changes
    old_values JSONB,
    new_values JSONB,
    
    -- Additional metadata
    metadata JSONB,
    
    -- Status
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for audit_logs
CREATE INDEX idx_audit_logs_tpa_id ON audit_logs(tpa_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_tpas_updated_at BEFORE UPDATE ON tpas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_plans_updated_at BEFORE UPDATE ON health_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_chunks_updated_at BEFORE UPDATE ON document_chunks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_query_analytics_updated_at BEFORE UPDATE ON query_analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_activity_updated_at BEFORE UPDATE ON user_activity FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_audit_logs_updated_at BEFORE UPDATE ON audit_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();