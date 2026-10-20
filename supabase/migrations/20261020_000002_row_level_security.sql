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
