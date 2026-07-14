CREATE TABLE articles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('media', 'social')),
    author TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    sentiment TEXT NOT NULL CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    negative_score SMALLINT CHECK (negative_score BETWEEN 1 AND 5),
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    tags TEXT[] NOT NULL DEFAULT '{}',
    likes INTEGER NOT NULL DEFAULT 0 CHECK (likes >= 0),
    comments INTEGER NOT NULL DEFAULT 0 CHECK (comments >= 0),
    shares INTEGER NOT NULL DEFAULT 0 CHECK (shares >= 0),
    favorites INTEGER NOT NULL DEFAULT 0 CHECK (favorites >= 0)
);

CREATE INDEX articles_published_at_idx ON articles (published_at);
CREATE INDEX articles_tags_idx ON articles USING GIN (tags);
