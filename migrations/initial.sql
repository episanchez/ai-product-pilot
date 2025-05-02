-- Active pgvector extension pour le stockage des embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Table pour stocker les feedbacks
CREATE TABLE public.feedback (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT NOT NULL,
    file_path TEXT,
    content TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT,
    analysis JSONB,
    summary TEXT,
    stories_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table pour stocker les documents vectorisés
CREATE TABLE public.documents (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding VECTOR(1536)
);

-- Table pour stocker les user stories
CREATE TABLE public.stories (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    as_a TEXT NOT NULL,
    i_want TEXT NOT NULL,
    so_that TEXT NOT NULL,
    themes TEXT[] NOT NULL,
    acceptance_criteria TEXT[] NOT NULL,
    feedback_ids UUID[] NOT NULL,
    reach FLOAT NOT NULL,
    impact FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    effort FLOAT NOT NULL,
    rice_score FLOAT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ajout d'un index pour la recherche par thème
CREATE INDEX idx_stories_themes ON public.stories USING GIN (themes);

-- Ajout d'un index pour la recherche par feedback_id
CREATE INDEX idx_stories_feedback_ids ON public.stories USING GIN (feedback_ids);

-- Fonction pour trouver des documents similaires
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    filter JSONB DEFAULT NULL
)
RETURNS TABLE(
    id BIGINT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.content,
        d.metadata,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM
        documents d
    WHERE
        CASE
            WHEN filter IS NOT NULL THEN
                metadata @> filter
            ELSE
                TRUE
        END
    ORDER BY
        d.embedding <=> query_embedding
    LIMIT match_count;
END;$$;

-- Fonction pour extraire tous les thèmes uniques des stories
CREATE OR REPLACE FUNCTION get_unique_themes()
RETURNS TABLE(theme TEXT)
LANGUAGE plpgsql
AS $$BEGIN
    RETURN QUERY
    SELECT DISTINCT unnest(themes) AS theme
    FROM stories
    ORDER BY theme;
END;$$;

-- Déclencheur pour mettre à jour le timestamp updated_at
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;$$ LANGUAGE plpgsql;

CREATE TRIGGER update_feedback_timestamp
BEFORE UPDATE ON feedback
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

CREATE TRIGGER update_stories_timestamp
BEFORE UPDATE ON stories
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();

-- Déclencheur pour notifier les nouvelles stories en temps réel
CREATE OR REPLACE FUNCTION notify_story_changes()
RETURNS TRIGGER AS $$BEGIN
  PERFORM pg_notify(
    'stories',
    json_build_object(
      'type', TG_OP,
      'record', row_to_json(NEW)
    )::text
  );
  RETURN NEW;
END;$$ LANGUAGE plpgsql;

CREATE TRIGGER stories_changes
AFTER INSERT OR UPDATE ON stories
FOR EACH ROW
EXECUTE PROCEDURE notify_story_changes();

-- Politiques RLS (Row Level Security)
-- Activer RLS sur les tables
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE stories ENABLE ROW LEVEL SECURITY;

-- Créer des politiques par défaut (à adapter selon vos besoins de sécurité)
CREATE POLICY "Allow authenticated read access to feedback" ON feedback
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated read access to stories" ON stories
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Allow service role full access" ON feedback
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access to documents" ON documents
    USING (auth.role() = 'service_role');

CREATE POLICY "Allow service role full access to stories" ON stories
    USING (auth.role() = 'service_role');