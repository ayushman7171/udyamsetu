// =============================================================================
// UdyamSetu Supabase Client & Authentication Helper
// Vanilla JavaScript integration for Supabase Auth and PostgREST.
// =============================================================================

(function () {
  if (!window.SUPABASE_CONFIG || !window.SUPABASE_CONFIG.url) {
    console.error("UdyamSetu: SUPABASE_CONFIG missing. Load js/supabase-config.js first.");
    return;
  }

  // Check if supabase global exists from CDN
  if (typeof window.supabase === "undefined" || !window.supabase.createClient) {
    console.warn("UdyamSetu: @supabase/supabase-js library not loaded yet.");
    return;
  }

  const { url, publishableKey } = window.SUPABASE_CONFIG;

  // Initialize Supabase Client
  window.supabaseClient = window.supabase.createClient(url, publishableKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storageKey: "udyamsetu_supabase_auth"
    }
  });

  // Global Auth Helper Methods
  window.UdyamAuth = {
    // Get current authenticated user
    async getUser() {
      try {
        const { data: { user }, error } = await window.supabaseClient.auth.getUser();
        if (error || !user) return null;
        return user;
      } catch (e) {
        return null;
      }
    },

    // Get active session
    async getSession() {
      try {
        const { data: { session }, error } = await window.supabaseClient.auth.getSession();
        if (error || !session) return null;
        return session;
      } catch (e) {
        return null;
      }
    },

    // Fetch user profile from public.profiles or public_profiles view
    async getProfile(userId) {
      if (!userId) return null;
      try {
        const { data, error } = await window.supabaseClient
          .from("public_profiles")
          .select("*")
          .eq("id", userId)
          .maybeSingle();
        if (error) {
          // Fallback to profiles table if view not queried
          const { data: fallback } = await window.supabaseClient
            .from("profiles")
            .select("*")
            .eq("id", userId)
            .maybeSingle();
          return fallback || null;
        }
        return data;
      } catch (e) {
        return null;
      }
    },

    // Fetch profile by slug (e.g., 'asha-devi')
    async getProfileBySlug(slug) {
      if (!slug) return null;
      try {
        const { data, error } = await window.supabaseClient
          .from("public_profiles")
          .select("*")
          .eq("slug", slug)
          .maybeSingle();
        if (error) {
          const { data: fallback } = await window.supabaseClient
            .from("profiles")
            .select("*")
            .eq("slug", slug)
            .maybeSingle();
          return fallback || null;
        }
        return data;
      } catch (e) {
        return null;
      }
    },

    // Sign in with email and password
    async signIn(email, password) {
      const { data, error } = await window.supabaseClient.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password: password
      });
      if (error) throw error;
      return data;
    },

    // Sign up new user with profile metadata
    async signUp(email, password, metadata = {}) {
      const { data, error } = await window.supabaseClient.auth.signUp({
        email: email.trim().toLowerCase(),
        password: password,
        options: {
          data: metadata
        }
      });
      if (error) throw error;
      return data;
    },

    // Sign out
    async signOut() {
      const { error } = await window.supabaseClient.auth.signOut();
      if (error) throw error;
    },

    // Request password reset email
    async resetPassword(email) {
      const redirectUrl = window.location.origin + "/register.html?mode=update-password";
      const { data, error } = await window.supabaseClient.auth.resetPasswordForEmail(email.trim().toLowerCase(), {
        redirectTo: redirectUrl
      });
      if (error) throw error;
      return data;
    },

    // Update password (when authenticated or in recovery mode)
    async updatePassword(newPassword) {
      const { data, error } = await window.supabaseClient.auth.updateUser({
        password: newPassword
      });
      if (error) throw error;
      return data;
    }
  };
})();
