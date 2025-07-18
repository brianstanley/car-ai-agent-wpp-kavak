CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number TEXT UNIQUE NOT NULL,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    goals TEXT,
    background TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instruction TEXT,
    application_mode TEXT DEFAULT 'assistant',
    persona_id UUID REFERENCES personas(id),
    tools JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    started_at TIMESTAMP DEFAULT now(),
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE conversations_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_session_id UUID NOT NULL REFERENCES chat_sessions(id),
    role TEXT CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    embedding VECTOR(1536),
    embedded BOOLEAN DEFAULT FALSE
);

CREATE TABLE summaries_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_session_id UUID NOT NULL REFERENCES chat_sessions(id),
    text TEXT NOT NULL,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    embedding VECTOR(1536)
);

CREATE INDEX idx_users_phone_number               ON users(phone_number);
CREATE INDEX idx_chat_sessions_user_id            ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_agent_id           ON chat_sessions(agent_id);
CREATE INDEX idx_conversation_memory_chat_session_id ON conversations_memory(chat_session_id);
CREATE INDEX idx_conversation_memory_created_at   ON conversations_memory(created_at);
CREATE INDEX idx_summaries_memory_chat_session_id ON summaries_memory(chat_session_id);
CREATE INDEX idx_agents_persona_id                ON agents(persona_id);
