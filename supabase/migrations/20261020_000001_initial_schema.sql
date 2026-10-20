-- =============================================================================
-- Migration 000001: Initial UdyamSetu PostgreSQL Schema
-- Normalizes existing SQLite tables to PostgreSQL types, constraints, and indexes.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Utility function for automatically updating updated_at timestamps
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- 1. Profiles Table (1:1 with auth.users)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL CHECK (char_length(name) >= 2),
    email TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'entrepreneur' CHECK (account_type IN ('entrepreneur', 'community')),
    business_name TEXT DEFAULT '',
    category TEXT DEFAULT '',
    location TEXT DEFAULT '',
    state TEXT DEFAULT '',
    district TEXT DEFAULT '',
    subdistrict_or_town TEXT DEFAULT '',
    pincode TEXT DEFAULT '' CHECK (pincode = '' OR pincode ~ '^[1-9][0-9]{5}$'),
    address_landmark TEXT DEFAULT '',
    location_display_preference TEXT NOT NULL DEFAULT 'district_state' CHECK (location_display_preference IN ('district_state', 'state_only', 'exact')),
    preferred_language TEXT NOT NULL DEFAULT 'en',
    avatar TEXT NOT NULL DEFAULT 'assets/images/digital_rahul.jpg',
    quote TEXT DEFAULT '',
    description TEXT DEFAULT '',
    full_story TEXT DEFAULT '',
    looking_for JSONB NOT NULL DEFAULT '[]'::jsonb,
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    website TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trigger_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_profiles_slug ON public.profiles(slug);
CREATE INDEX IF NOT EXISTS idx_profiles_account_type ON public.profiles(account_type);
CREATE INDEX IF NOT EXISTS idx_profiles_state ON public.profiles(state);
CREATE INDEX IF NOT EXISTS idx_profiles_category ON public.profiles(category);
CREATE INDEX IF NOT EXISTS idx_profiles_verified ON public.profiles(verified);

-- -----------------------------------------------------------------------------
-- 2. Public Profiles Privacy View
-- Hides private street landmark and pincode from non-owners to match privacy model.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.public_profiles WITH (security_invoker = true) AS
SELECT 
    id,
    slug,
    name,
    CASE WHEN auth.uid() = id THEN email ELSE '' END AS email,
    account_type,
    business_name,
    category,
    CASE 
        WHEN location_display_preference = 'state_only' AND state <> '' THEN state
        WHEN location_display_preference = 'exact' AND subdistrict_or_town <> '' THEN 
            subdistrict_or_town || ', ' || district || ', ' || state
        WHEN district <> '' AND state <> '' THEN district || ', ' || state
        ELSE location
    END AS location,
    state,
    district,
    subdistrict_or_town,
    CASE WHEN auth.uid() = id THEN pincode ELSE '' END AS pincode,
    CASE WHEN auth.uid() = id THEN address_landmark ELSE '' END AS address_landmark,
    location_display_preference,
    preferred_language,
    avatar,
    quote,
    description,
    full_story,
    looking_for,
    skills,
    website,
    CASE WHEN auth.uid() = id THEN phone ELSE '' END AS phone,
    verified,
    created_at,
    updated_at
FROM public.profiles;

-- -----------------------------------------------------------------------------
-- 3. Products Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.products (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (char_length(name) > 0),
    price TEXT NOT NULL,
    image TEXT NOT NULL DEFAULT 'assets/images/hero_entrepreneur.jpg',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_owner_id ON public.products(owner_id);

-- -----------------------------------------------------------------------------
-- 4. Posts Table (Community Feed)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.posts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL CHECK (char_length(content) > 0),
    post_type TEXT NOT NULL DEFAULT 'story' CHECK (post_type IN ('story', 'question', 'opportunity')),
    tag TEXT,
    likes_count INTEGER NOT NULL DEFAULT 0,
    comments_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trigger_posts_updated_at
BEFORE UPDATE ON public.posts
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_posts_author_id ON public.posts(author_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_post_type ON public.posts(post_type);

-- -----------------------------------------------------------------------------
-- 5. Post Likes Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.post_likes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_post_likes_post_id ON public.post_likes(post_id);
CREATE INDEX IF NOT EXISTS idx_post_likes_user_id ON public.post_likes(user_id);

-- Trigger to maintain post likes_count automatically
CREATE OR REPLACE FUNCTION public.update_post_likes_count()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        UPDATE public.posts SET likes_count = likes_count + 1 WHERE id = NEW.post_id;
    ELSIF (TG_OP = 'DELETE') THEN
        UPDATE public.posts SET likes_count = GREATEST(likes_count - 1, 0) WHERE id = OLD.post_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_post_likes_counter
AFTER INSERT OR DELETE ON public.post_likes
FOR EACH ROW EXECUTE FUNCTION public.update_post_likes_count();

-- -----------------------------------------------------------------------------
-- 6. Collaborations Table (Opportunities)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.collaborations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    collab_id TEXT UNIQUE NOT NULL,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (char_length(title) > 0),
    subtitle TEXT DEFAULT '',
    full_description TEXT NOT NULL,
    category TEXT NOT NULL,
    collab_type TEXT NOT NULL DEFAULT 'Seeking Partners',
    tag TEXT DEFAULT '',
    location TEXT DEFAULT '',
    thumb TEXT DEFAULT 'assets/images/crafts_banner.jpg',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trigger_collaborations_updated_at
BEFORE UPDATE ON public.collaborations
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_collaborations_collab_id ON public.collaborations(collab_id);
CREATE INDEX IF NOT EXISTS idx_collaborations_author ON public.collaborations(author_id);
CREATE INDEX IF NOT EXISTS idx_collaborations_category ON public.collaborations(category);
CREATE INDEX IF NOT EXISTS idx_collaborations_created ON public.collaborations(created_at DESC);

-- -----------------------------------------------------------------------------
-- 7. Collaboration Requests (Proposals)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.collaboration_requests (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    collab_id TEXT REFERENCES public.collaborations(collab_id) ON DELETE SET NULL,
    sender_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    message TEXT NOT NULL CHECK (char_length(message) > 0),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (sender_id != receiver_id)
);

CREATE TRIGGER trigger_collab_requests_updated_at
BEFORE UPDATE ON public.collaboration_requests
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_collab_requests_sender ON public.collaboration_requests(sender_id);
CREATE INDEX IF NOT EXISTS idx_collab_requests_receiver ON public.collaboration_requests(receiver_id);
CREATE INDEX IF NOT EXISTS idx_collab_requests_status ON public.collaboration_requests(status);

-- -----------------------------------------------------------------------------
-- 8. Collaborative Projects
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.collaborative_projects (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL CHECK (char_length(title) > 0),
    description TEXT DEFAULT '',
    category TEXT DEFAULT '',
    partner1_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    partner2_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Completed', 'Paused')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (partner1_id != partner2_id)
);

CREATE TRIGGER trigger_collab_projects_updated_at
BEFORE UPDATE ON public.collaborative_projects
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_collab_projects_p1 ON public.collaborative_projects(partner1_id);
CREATE INDEX IF NOT EXISTS idx_collab_projects_p2 ON public.collaborative_projects(partner2_id);

-- -----------------------------------------------------------------------------
-- 9. Discussions Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.discussions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    disc_id TEXT UNIQUE NOT NULL,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK (char_length(title) > 0),
    body TEXT NOT NULL CHECK (char_length(body) > 0),
    tag TEXT DEFAULT 'Question',
    likes INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trigger_discussions_updated_at
BEFORE UPDATE ON public.discussions
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_discussions_disc_id ON public.discussions(disc_id);
CREATE INDEX IF NOT EXISTS idx_discussions_author ON public.discussions(author_id);
CREATE INDEX IF NOT EXISTS idx_discussions_created ON public.discussions(created_at DESC);

-- -----------------------------------------------------------------------------
-- 10. Comments Table (Discussion Replies)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.comments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    disc_id TEXT NOT NULL REFERENCES public.discussions(disc_id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    text TEXT NOT NULL CHECK (char_length(text) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comments_disc_id ON public.comments(disc_id);
CREATE INDEX IF NOT EXISTS idx_comments_author ON public.comments(author_id);
CREATE INDEX IF NOT EXISTS idx_comments_created ON public.comments(created_at ASC);

-- -----------------------------------------------------------------------------
-- 11. Articles Table (Learn & Share)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.articles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    author_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    date_str TEXT NOT NULL,
    image TEXT NOT NULL,
    summary TEXT NOT NULL,
    lessons JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_articles_article_id ON public.articles(article_id);
CREATE INDEX IF NOT EXISTS idx_articles_category ON public.articles(category);

-- -----------------------------------------------------------------------------
-- 12. Connections Table (Peer Network)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.connections (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id_1 UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    user_id_2 UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'connected' CHECK (status IN ('connected', 'pending', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id_1, user_id_2),
    CHECK (user_id_1 != user_id_2)
);

CREATE INDEX IF NOT EXISTS idx_connections_u1 ON public.connections(user_id_1);
CREATE INDEX IF NOT EXISTS idx_connections_u2 ON public.connections(user_id_2);

-- -----------------------------------------------------------------------------
-- 13. Conversations Table (Messaging)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.conversations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conv_id TEXT UNIQUE NOT NULL,
    conv_type TEXT NOT NULL DEFAULT 'direct' CHECK (conv_type IN ('direct', 'collaboration')),
    title TEXT DEFAULT '',
    direct_key TEXT UNIQUE,
    project_id BIGINT UNIQUE REFERENCES public.collaborative_projects(id) ON DELETE SET NULL,
    collab_id TEXT REFERENCES public.collaborations(collab_id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER trigger_conversations_updated_at
BEFORE UPDATE ON public.conversations
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE INDEX IF NOT EXISTS idx_conversations_conv_id ON public.conversations(conv_id);
CREATE INDEX IF NOT EXISTS idx_conversations_direct_key ON public.conversations(direct_key);
CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON public.conversations(project_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON public.conversations(updated_at DESC);

-- -----------------------------------------------------------------------------
-- 14. Conversation Participants Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.conversation_participants (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    conv_id TEXT NOT NULL REFERENCES public.conversations(conv_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('creator', 'member')),
    last_read_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(conversation_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_participants_user ON public.conversation_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_participants_conv ON public.conversation_participants(conversation_id);

-- -----------------------------------------------------------------------------
-- 15. Messages Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.messages (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    msg_id TEXT UNIQUE NOT NULL,
    conversation_id BIGINT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    conv_id TEXT NOT NULL REFERENCES public.conversations(conv_id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    body TEXT NOT NULL CHECK (char_length(body) > 0),
    message_type TEXT NOT NULL DEFAULT 'text' CHECK (message_type IN ('text', 'system')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conv ON public.messages(conversation_id, id ASC);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON public.messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON public.messages(created_at ASC);

-- -----------------------------------------------------------------------------
-- 16. User Blocks Table (Abuse Prevention)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.user_blocks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    blocker_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    blocked_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    reason TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(blocker_id, blocked_id),
    CHECK (blocker_id != blocked_id)
);

CREATE INDEX IF NOT EXISTS idx_user_blocks_pair ON public.user_blocks(blocker_id, blocked_id);

-- -----------------------------------------------------------------------------
-- 17. In-App Notifications Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.notifications (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recipient_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    title TEXT DEFAULT '',
    message TEXT NOT NULL,
    reference_type TEXT DEFAULT '',
    reference_id TEXT DEFAULT '',
    link_url TEXT DEFAULT '',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    dedup_key TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON public.notifications(recipient_id, is_read, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_dedup ON public.notifications(dedup_key);
