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
        NULLIF(NEW.raw_user_meta_data->>'avatar', ''),
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
