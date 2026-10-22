-- =============================================================================
-- ThriveHub Supabase Migration: Profile Images & Storage Configuration
-- Safe, idempotent SQL script for profiles schema and storage bucket policies.
-- =============================================================================

-- 1. Add Dedicated Profile Columns
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS business_logo_url TEXT DEFAULT '';

ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS cover_image_url TEXT DEFAULT '';

-- 2. Update Public Profiles View to Expose Image Fields
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
    business_logo_url,
    cover_image_url,
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

-- 3. Create Public Storage Bucket for Profiles
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'profiles',
    'profiles',
    true,
    5242880, -- 5 MB
    ARRAY['image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET 
    public = true,
    file_size_limit = 5242880,
    allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'image/webp'];

-- 4. Storage Row-Level Security Policies (profiles bucket)
-- Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy 1: Public read access for profile images
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Public profiles images view'
    ) THEN
        CREATE POLICY "Public profiles images view"
        ON storage.objects FOR SELECT
        USING (bucket_id = 'profiles');
    END IF;
END $$;

-- Policy 2: Authenticated user upload only to own user folder: {userId}/...
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Users upload own profile images'
    ) THEN
        CREATE POLICY "Users upload own profile images"
        ON storage.objects FOR INSERT
        TO authenticated
        WITH CHECK (
            bucket_id = 'profiles' 
            AND (storage.foldername(name))[1] = auth.uid()::text
        );
    END IF;
END $$;

-- Policy 3: Authenticated user update only own profile images
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Users update own profile images'
    ) THEN
        CREATE POLICY "Users update own profile images"
        ON storage.objects FOR UPDATE
        TO authenticated
        USING (
            bucket_id = 'profiles' 
            AND (storage.foldername(name))[1] = auth.uid()::text
        )
        WITH CHECK (
            bucket_id = 'profiles' 
            AND (storage.foldername(name))[1] = auth.uid()::text
        );
    END IF;
END $$;

-- Policy 4: Authenticated user delete only own profile images
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'objects' AND schemaname = 'storage' AND policyname = 'Users delete own profile images'
    ) THEN
        CREATE POLICY "Users delete own profile images"
        ON storage.objects FOR DELETE
        TO authenticated
        USING (
            bucket_id = 'profiles' 
            AND (storage.foldername(name))[1] = auth.uid()::text
        );
    END IF;
END $$;
