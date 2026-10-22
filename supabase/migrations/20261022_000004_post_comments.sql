-- =============================================================================
-- Migration 000004: Post Comments Table & RLS Policies
-- Allows users to view and post comments on feed posts (stories, opportunities, questions).
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.post_comments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    text TEXT NOT NULL CHECK (char_length(text) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_post_comments_post_id ON public.post_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_author ON public.post_comments(author_id);
CREATE INDEX IF NOT EXISTS idx_post_comments_created ON public.post_comments(created_at ASC);

-- Trigger to maintain post comments_count automatically
CREATE OR REPLACE FUNCTION public.update_post_comments_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE public.posts SET comments_count = comments_count + 1 WHERE id = NEW.post_id;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE public.posts SET comments_count = GREATEST(comments_count - 1, 0) WHERE id = OLD.post_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_post_comments_counter ON public.post_comments;
CREATE TRIGGER trigger_post_comments_counter
AFTER INSERT OR DELETE ON public.post_comments
FOR EACH ROW EXECUTE FUNCTION public.update_post_comments_count();

-- Enable Row Level Security (RLS)
ALTER TABLE public.post_comments ENABLE ROW LEVEL SECURITY;

-- 1. Anyone can view comments on public posts
CREATE POLICY "post_comments_select_public"
ON public.post_comments FOR SELECT
USING (true);

-- 2. Authenticated users can insert their own comments
CREATE POLICY "post_comments_insert_author"
ON public.post_comments FOR INSERT
WITH CHECK (auth.uid() = author_id);

-- 3. Users can delete their own comments
CREATE POLICY "post_comments_delete_author"
ON public.post_comments FOR DELETE
USING (auth.uid() = author_id);
