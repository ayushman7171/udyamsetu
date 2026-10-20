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


-- =============================================================================
-- Migration 000002: Row Level Security (RLS) & Security Policies
-- Enforces row-level isolation for profiles, messages, notifications, and features.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Helper Functions (SECURITY DEFINER to prevent recursion in RLS policies)
-- -----------------------------------------------------------------------------

-- Checks if a user is an enrolled participant in a given conversation
CREATE OR REPLACE FUNCTION public.is_conversation_participant(conv_id_param BIGINT, user_id_param UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.conversation_participants
        WHERE conversation_id = conv_id_param AND user_id = user_id_param
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Checks if there is an active block between two users
CREATE OR REPLACE FUNCTION public.is_user_blocked(user_a UUID, user_b UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.user_blocks
        WHERE (blocker_id = user_a AND blocked_id = user_b)
           OR (blocker_id = user_b AND blocked_id = user_a)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- Enable RLS on All Tables
-- -----------------------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collaborations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collaboration_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collaborative_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discussions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- 1. Profiles Policies
-- -----------------------------------------------------------------------------
-- Public can read all profiles (sensitive fields masked via public_profiles view)
CREATE POLICY "profiles_select_public"
ON public.profiles FOR SELECT
USING (true);

-- Users can only insert their own profile
CREATE POLICY "profiles_insert_owner"
ON public.profiles FOR INSERT
WITH CHECK (auth.uid() = id);

-- Users can only update their own profile
CREATE POLICY "profiles_update_owner"
ON public.profiles FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Users can only delete their own profile
CREATE POLICY "profiles_delete_owner"
ON public.profiles FOR DELETE
USING (auth.uid() = id);

-- -----------------------------------------------------------------------------
-- 2. Products Policies
-- -----------------------------------------------------------------------------
-- Products are publicly viewable
CREATE POLICY "products_select_public"
ON public.products FOR SELECT
USING (true);

-- Only verified entrepreneurs can insert products
CREATE POLICY "products_insert_owner"
ON public.products FOR INSERT
WITH CHECK (
    auth.uid() = owner_id AND
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = auth.uid() AND account_type = 'entrepreneur'
    )
);

-- Only the product owner can update or delete
CREATE POLICY "products_update_owner"
ON public.products FOR UPDATE
USING (auth.uid() = owner_id)
WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "products_delete_owner"
ON public.products FOR DELETE
USING (auth.uid() = owner_id);

-- -----------------------------------------------------------------------------
-- 3. Posts Policies (Feed)
-- -----------------------------------------------------------------------------
CREATE POLICY "posts_select_public"
ON public.posts FOR SELECT
USING (true);

CREATE POLICY "posts_insert_author"
ON public.posts FOR INSERT
WITH CHECK (auth.uid() = author_id);

CREATE POLICY "posts_update_author"
ON public.posts FOR UPDATE
USING (auth.uid() = author_id)
WITH CHECK (auth.uid() = author_id);

CREATE POLICY "posts_delete_author"
ON public.posts FOR DELETE
USING (auth.uid() = author_id);

-- -----------------------------------------------------------------------------
-- 4. Post Likes Policies
-- -----------------------------------------------------------------------------
CREATE POLICY "post_likes_select_public"
ON public.post_likes FOR SELECT
USING (true);

CREATE POLICY "post_likes_insert_user"
ON public.post_likes FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "post_likes_delete_user"
ON public.post_likes FOR DELETE
USING (auth.uid() = user_id);

-- -----------------------------------------------------------------------------
-- 5. Collaborations Policies
-- -----------------------------------------------------------------------------
CREATE POLICY "collaborations_select_public"
ON public.collaborations FOR SELECT
USING (true);

-- Only entrepreneurs can post collaboration opportunities
CREATE POLICY "collaborations_insert_entrepreneur"
ON public.collaborations FOR INSERT
WITH CHECK (
    auth.uid() = author_id AND
    EXISTS (
        SELECT 1 FROM public.profiles 
        WHERE id = auth.uid() AND account_type = 'entrepreneur'
    )
);

CREATE POLICY "collaborations_update_author"
ON public.collaborations FOR UPDATE
USING (auth.uid() = author_id)
WITH CHECK (auth.uid() = author_id);

CREATE POLICY "collaborations_delete_author"
ON public.collaborations FOR DELETE
USING (auth.uid() = author_id);

-- -----------------------------------------------------------------------------
-- 6. Collaboration Requests Policies
-- -----------------------------------------------------------------------------
-- Only the sender or recipient can view proposals
CREATE POLICY "collab_requests_select_parties"
ON public.collaboration_requests FOR SELECT
USING (auth.uid() = sender_id OR auth.uid() = receiver_id);

-- Authenticated sender can propose (no self-proposals)
CREATE POLICY "collab_requests_insert_sender"
ON public.collaboration_requests FOR INSERT
WITH CHECK (auth.uid() = sender_id AND sender_id != receiver_id);

-- Only the receiver can accept or reject
CREATE POLICY "collab_requests_update_receiver"
ON public.collaboration_requests FOR UPDATE
USING (auth.uid() = receiver_id)
WITH CHECK (auth.uid() = receiver_id);

CREATE POLICY "collab_requests_delete_sender"
ON public.collaboration_requests FOR DELETE
USING (auth.uid() = sender_id);

-- -----------------------------------------------------------------------------
-- 7. Collaborative Projects Policies
-- -----------------------------------------------------------------------------
-- Only project partners can view
CREATE POLICY "collab_projects_select_partners"
ON public.collaborative_projects FOR SELECT
USING (auth.uid() = partner1_id OR auth.uid() = partner2_id);

CREATE POLICY "collab_projects_insert_partners"
ON public.collaborative_projects FOR INSERT
WITH CHECK (auth.uid() = partner1_id OR auth.uid() = partner2_id);

CREATE POLICY "collab_projects_update_partners"
ON public.collaborative_projects FOR UPDATE
USING (auth.uid() = partner1_id OR auth.uid() = partner2_id)
WITH CHECK (auth.uid() = partner1_id OR auth.uid() = partner2_id);

-- -----------------------------------------------------------------------------
-- 8. Discussions & Comments Policies
-- -----------------------------------------------------------------------------
CREATE POLICY "discussions_select_public"
ON public.discussions FOR SELECT
USING (true);

CREATE POLICY "discussions_insert_author"
ON public.discussions FOR INSERT
WITH CHECK (auth.uid() = author_id);

CREATE POLICY "discussions_update_author"
ON public.discussions FOR UPDATE
USING (auth.uid() = author_id)
WITH CHECK (auth.uid() = author_id);

CREATE POLICY "discussions_delete_author"
ON public.discussions FOR DELETE
USING (auth.uid() = author_id);

CREATE POLICY "comments_select_public"
ON public.comments FOR SELECT
USING (true);

CREATE POLICY "comments_insert_author"
ON public.comments FOR INSERT
WITH CHECK (auth.uid() = author_id);

CREATE POLICY "comments_delete_author"
ON public.comments FOR DELETE
USING (auth.uid() = author_id);

-- -----------------------------------------------------------------------------
-- 9. Articles Policies (Learn & Share)
-- -----------------------------------------------------------------------------
CREATE POLICY "articles_select_public"
ON public.articles FOR SELECT
USING (true);

-- -----------------------------------------------------------------------------
-- 10. Connections Policies
-- -----------------------------------------------------------------------------
CREATE POLICY "connections_select_parties"
ON public.connections FOR SELECT
USING (auth.uid() = user_id_1 OR auth.uid() = user_id_2);

CREATE POLICY "connections_insert_initiator"
ON public.connections FOR INSERT
WITH CHECK (auth.uid() = user_id_1 AND user_id_1 != user_id_2);

CREATE POLICY "connections_delete_parties"
ON public.connections FOR DELETE
USING (auth.uid() = user_id_1 OR auth.uid() = user_id_2);

-- -----------------------------------------------------------------------------
-- 11. Conversations Policies
-- -----------------------------------------------------------------------------
-- Visible only to users enrolled as participants in the conversation
CREATE POLICY "conversations_select_participants"
ON public.conversations FOR SELECT
USING (public.is_conversation_participant(id, auth.uid()));

CREATE POLICY "conversations_insert_creator"
ON public.conversations FOR INSERT
WITH CHECK (auth.uid() = created_by);

-- -----------------------------------------------------------------------------
-- 12. Conversation Participants Policies
-- -----------------------------------------------------------------------------
CREATE POLICY "participants_select_members"
ON public.conversation_participants FOR SELECT
USING (
    user_id = auth.uid() OR
    public.is_conversation_participant(conversation_id, auth.uid())
);

CREATE POLICY "participants_insert_creator"
ON public.conversation_participants FOR INSERT
WITH CHECK (
    user_id = auth.uid() OR
    EXISTS (
        SELECT 1 FROM public.conversations c 
        WHERE c.id = conversation_id AND c.created_by = auth.uid()
    )
);

CREATE POLICY "participants_update_self"
ON public.conversation_participants FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- -----------------------------------------------------------------------------
-- 13. Messages Policies (Strict Isolation & Block Enforcement)
-- -----------------------------------------------------------------------------
CREATE POLICY "messages_select_participants"
ON public.messages FOR SELECT
USING (
    public.is_conversation_participant(conversation_id, auth.uid()) AND
    NOT public.is_user_blocked(auth.uid(), sender_id)
);

CREATE POLICY "messages_insert_participants"
ON public.messages FOR INSERT
WITH CHECK (
    auth.uid() = sender_id AND
    public.is_conversation_participant(conversation_id, auth.uid()) AND
    NOT EXISTS (
        SELECT 1 FROM public.conversation_participants cp
        WHERE cp.conversation_id = messages.conversation_id
          AND cp.user_id != auth.uid()
          AND public.is_user_blocked(auth.uid(), cp.user_id)
    )
);

-- -----------------------------------------------------------------------------
-- 14. User Blocks Policies
-- -----------------------------------------------------------------------------
CREATE POLICY "user_blocks_select_blocker"
ON public.user_blocks FOR SELECT
USING (auth.uid() = blocker_id);

CREATE POLICY "user_blocks_insert_blocker"
ON public.user_blocks FOR INSERT
WITH CHECK (auth.uid() = blocker_id AND blocker_id != blocked_id);

CREATE POLICY "user_blocks_delete_blocker"
ON public.user_blocks FOR DELETE
USING (auth.uid() = blocker_id);

-- -----------------------------------------------------------------------------
-- 15. In-App Notifications Policies
-- -----------------------------------------------------------------------------
-- Strict recipient isolation: nobody can read another user's notifications
CREATE POLICY "notifications_select_recipient"
ON public.notifications FOR SELECT
USING (auth.uid() = recipient_id);

-- Authenticated actors can insert notifications for other users
CREATE POLICY "notifications_insert_actor"
ON public.notifications FOR INSERT
WITH CHECK (auth.uid() = actor_id AND actor_id != recipient_id);

-- Only recipient can mark as read
CREATE POLICY "notifications_update_recipient"
ON public.notifications FOR UPDATE
USING (auth.uid() = recipient_id)
WITH CHECK (auth.uid() = recipient_id);

-- Only recipient can delete
CREATE POLICY "notifications_delete_recipient"
ON public.notifications FOR DELETE
USING (auth.uid() = recipient_id);


-- =============================================================================
-- Migration 000003: Auth Lifecycle Triggers & Helper RPC Functions
-- Automatically links auth.users registrations to public.profiles and exposes secure RPCs.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. Automatic Profile Provisioning on Supabase Auth Signup
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    user_name TEXT;
    user_account_type TEXT;
    user_slug TEXT;
    clean_slug TEXT;
    counter INT := 0;
BEGIN
    user_name := COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1));
    user_account_type := COALESCE(NEW.raw_user_meta_data->>'account_type', 'entrepreneur');
    
    -- Generate initial slug from user_id in metadata or name
    IF NEW.raw_user_meta_data->>'user_id' IS NOT NULL AND NEW.raw_user_meta_data->>'user_id' <> '' THEN
        user_slug := NEW.raw_user_meta_data->>'user_id';
    ELSIF NEW.raw_user_meta_data->>'slug' IS NOT NULL AND NEW.raw_user_meta_data->>'slug' <> '' THEN
        user_slug := NEW.raw_user_meta_data->>'slug';
    ELSE
        clean_slug := lower(regexp_replace(user_name, '[^a-zA-Z0-9]+', '-', 'g'));
        clean_slug := trim(both '-' from clean_slug);
        IF clean_slug = '' THEN
            clean_slug := 'user';
        END IF;
        user_slug := clean_slug || '-' || substr(NEW.id::text, 1, 6);
    END IF;

    -- Ensure unique slug
    WHILE EXISTS (SELECT 1 FROM public.profiles WHERE slug = user_slug) LOOP
        counter := counter + 1;
        user_slug := clean_slug || '-' || counter;
    END LOOP;

    INSERT INTO public.profiles (
        id,
        slug,
        name,
        email,
        account_type,
        business_name,
        category,
        location,
        state,
        district,
        subdistrict_or_town,
        pincode,
        address_landmark,
        location_display_preference,
        preferred_language,
        avatar,
        quote,
        description,
        full_story,
        looking_for,
        skills,
        website,
        phone,
        verified
    )
    VALUES (
        NEW.id,
        user_slug,
        user_name,
        NEW.email,
        user_account_type,
        COALESCE(NEW.raw_user_meta_data->>'business_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'category', ''),
        COALESCE(NEW.raw_user_meta_data->>'location', ''),
        COALESCE(NEW.raw_user_meta_data->>'state', ''),
        COALESCE(NEW.raw_user_meta_data->>'district', ''),
        COALESCE(NEW.raw_user_meta_data->>'subdistrict_or_town', ''),
        COALESCE(NEW.raw_user_meta_data->>'pincode', ''),
        COALESCE(NEW.raw_user_meta_data->>'address_landmark', ''),
        COALESCE(NEW.raw_user_meta_data->>'location_display_preference', 'district_state'),
        COALESCE(NEW.raw_user_meta_data->>'preferred_language', 'en'),
        COALESCE(NEW.raw_user_meta_data->>'avatar', 'assets/images/digital_rahul.jpg'),
        COALESCE(NEW.raw_user_meta_data->>'quote', ''),
        COALESCE(NEW.raw_user_meta_data->>'description', ''),
        COALESCE(NEW.raw_user_meta_data->>'full_story', ''),
        COALESCE((NEW.raw_user_meta_data->'looking_for')::jsonb, '[]'::jsonb),
        COALESCE((NEW.raw_user_meta_data->'skills')::jsonb, '[]'::jsonb),
        COALESCE(NEW.raw_user_meta_data->>'website', ''),
        COALESCE(NEW.raw_user_meta_data->>'phone', ''),
        COALESCE((NEW.raw_user_meta_data->>'verified')::boolean, FALSE)
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        name = COALESCE(NULLIF(EXCLUDED.name, ''), public.profiles.name);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger fired after an auth user is inserted
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- -----------------------------------------------------------------------------
-- 2. Helper RPC: Get or Create Direct Conversation
-- Guarantees a unique 1-on-1 conversation without duplicate rooms.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_or_create_direct_conversation(target_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    cur_user_id UUID;
    low_uid TEXT;
    high_uid TEXT;
    computed_direct_key TEXT;
    found_conv_id BIGINT;
    found_conv_code TEXT;
BEGIN
    cur_user_id := auth.uid();
    IF cur_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required';
    END IF;

    IF cur_user_id = target_user_id THEN
        RAISE EXCEPTION 'Cannot create conversation with self';
    END IF;

    -- Block check
    IF public.is_user_blocked(cur_user_id, target_user_id) THEN
        RAISE EXCEPTION 'Communication unavailable due to block restrictions';
    END IF;

    IF cur_user_id::text < target_user_id::text THEN
        low_uid := cur_user_id::text;
        high_uid := target_user_id::text;
    ELSE
        low_uid := target_user_id::text;
        high_uid := cur_user_id::text;
    END IF;
    computed_direct_key := 'direct:' || low_uid || ':' || high_uid;

    -- Search existing
    SELECT id, conv_id INTO found_conv_id, found_conv_code
    FROM public.conversations
    WHERE direct_key = computed_direct_key;

    IF found_conv_id IS NULL THEN
        found_conv_code := 'conv-' || substr(md5(random()::text || clock_timestamp()::text), 1, 12);
        INSERT INTO public.conversations (conv_id, conv_type, direct_key, created_by)
        VALUES (found_conv_code, 'direct', computed_direct_key, cur_user_id)
        RETURNING id INTO found_conv_id;

        INSERT INTO public.conversation_participants (conversation_id, conv_id, user_id, role)
        VALUES 
            (found_conv_id, found_conv_code, cur_user_id, 'creator'),
            (found_conv_id, found_conv_code, target_user_id, 'member')
        ON CONFLICT (conversation_id, user_id) DO NOTHING;
    END IF;

    RETURN jsonb_build_object(
        'id', found_conv_id,
        'conv_id', found_conv_code
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- 3. Helper RPC: Unread Notifications Count
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_unread_notifications_count()
RETURNS INTEGER AS $$
DECLARE
    cur_user_id UUID;
    unread_total INTEGER;
BEGIN
    cur_user_id := auth.uid();
    IF cur_user_id IS NULL THEN
        RETURN 0;
    END IF;

    SELECT COUNT(*) INTO unread_total
    FROM public.notifications
    WHERE recipient_id = cur_user_id AND is_read = FALSE;

    RETURN unread_total;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- 4. Helper RPC: Mark Single Notification Read
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.mark_notification_read(notif_id_param BIGINT)
RETURNS BOOLEAN AS $$
DECLARE
    cur_user_id UUID;
BEGIN
    cur_user_id := auth.uid();
    IF cur_user_id IS NULL THEN
        RETURN FALSE;
    END IF;

    UPDATE public.notifications
    SET is_read = TRUE
    WHERE id = notif_id_param AND recipient_id = cur_user_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- -----------------------------------------------------------------------------
-- 5. Helper RPC: Mark All Notifications Read
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.mark_all_notifications_read()
RETURNS INTEGER AS $$
DECLARE
    cur_user_id UUID;
    affected_rows INTEGER;
BEGIN
    cur_user_id := auth.uid();
    IF cur_user_id IS NULL THEN
        RETURN 0;
    END IF;

    UPDATE public.notifications
    SET is_read = TRUE
    WHERE recipient_id = cur_user_id AND is_read = FALSE;

    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RETURN affected_rows;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
