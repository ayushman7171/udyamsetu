// =============================================================================
// ThriveHub Supabase API Client
// Direct PostgREST & Auth adapter for all platform features.
// =============================================================================

window.UdyamAPI = {
  // ---------------------------------------------------------------------------
  // 1. Entrepreneurs Directory
  // ---------------------------------------------------------------------------
  async getEntrepreneurs(filters = {}) {
    if (!window.supabaseClient) return [];
    let query = window.supabaseClient
      .from("public_profiles")
      .select("*")
      .eq("account_type", "entrepreneur")
      .order("created_at", { ascending: false });

    if (filters.state) {
      query = query.eq("state", filters.state);
    }
    if (filters.category) {
      query = query.eq("category", filters.category);
    }
    if (filters.search) {
      const term = `%${filters.search.trim()}%`;
      query = query.or(`name.ilike.${term},business_name.ilike.${term},description.ilike.${term},category.ilike.${term}`);
    }

    const { data, error } = await query;
    if (error) {
      console.error("Error fetching entrepreneurs:", error);
      return [];
    }
    return data || [];
  },

  // ---------------------------------------------------------------------------
  // 2. Entrepreneur Detail & Profile
  // ---------------------------------------------------------------------------
  async getEntrepreneurDetail(slugOrId) {
    if (!window.supabaseClient || !slugOrId) return null;

    // Try finding by slug first, then by UUID id
    let query = window.supabaseClient.from("public_profiles").select("*");
    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(slugOrId);
    if (isUUID) {
      query = query.eq("id", slugOrId);
    } else {
      query = query.eq("slug", slugOrId);
    }

    const { data: user, error } = await query.maybeSingle();
    if (error || !user) return null;

    // Fetch related products
    const { data: products } = await window.supabaseClient
      .from("products")
      .select("*")
      .eq("owner_id", user.id)
      .order("created_at", { ascending: false });

    // Fetch collaborations authored by this user
    const { data: collabs } = await window.supabaseClient
      .from("collaborations")
      .select("*")
      .eq("author_id", user.id)
      .order("created_at", { ascending: false });

    // Check if connected with current viewer
    let isConnected = false;
    let isSelf = false;
    const curUser = await window.UdyamAuth.getUser();
    if (curUser) {
      isSelf = (curUser.id === user.id);
      if (!isSelf) {
        const { data: conn } = await window.supabaseClient
          .from("connections")
          .select("id")
          .or(`and(user_id_1.eq.${curUser.id},user_id_2.eq.${user.id}),and(user_id_1.eq.${user.id},user_id_2.eq.${curUser.id})`)
          .maybeSingle();
        isConnected = !!conn;
      }
    }

    return {
      ...user,
      products: products || [],
      collaborations: collabs || [],
      is_connected: isConnected,
      is_self: isSelf
    };
  },

  // ---------------------------------------------------------------------------
  // 3. Products Management
  // ---------------------------------------------------------------------------
  async addProduct(product) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    const { data, error } = await window.supabaseClient
      .from("products")
      .insert({
        owner_id: curUser.id,
        name: product.name,
        price: product.price,
        image: product.image || "assets/images/hero_entrepreneur.jpg"
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async deleteProduct(productId) {
    const { error } = await window.supabaseClient
      .from("products")
      .delete()
      .eq("id", productId);
    if (error) throw error;
    return true;
  },

  // ---------------------------------------------------------------------------
  // 4. Community Feed & Posts
  // ---------------------------------------------------------------------------
  async getFeedPosts() {
    if (!window.supabaseClient) return [];
    const { data, error } = await window.supabaseClient
      .from("posts")
      .select(`
        *,
        author:profiles(id, slug, name, category, location, avatar),
        post_likes(user_id)
      `)
      .order("created_at", { ascending: false });

    if (error) {
      console.error("Error loading feed posts:", error);
      return [];
    }

    const curUser = await window.UdyamAuth.getUser();
    const curUid = curUser ? curUser.id : null;

    return (data || []).map(p => {
      const author = p.author || {};
      const likes = p.post_likes || [];
      const userLiked = curUid ? likes.some(l => l.user_id === curUid) : false;
      return {
        id: p.id,
        author_id: p.author_id,
        author_name: author.name || "Community Member",
        author_category: author.category || "",
        author_location: author.location || "India",
        author_avatar: author.avatar || "assets/images/digital_rahul.jpg",
        content: p.content,
        post_type: p.post_type,
        tag: p.tag,
        likes: p.likes_count || likes.length || 0,
        likes_count: p.likes_count || likes.length || 0,
        comments_count: (() => {
          let cc = p.comments_count || 0;
          if (typeof localStorage !== "undefined") {
            try {
              const cached = JSON.parse(localStorage.getItem(`udyam_post_comments_${p.id}`) || "[]");
              if (Array.isArray(cached) && cached.length > cc) cc = cached.length;
            } catch (_) {}
          }
          return cc;
        })(),
        created_at: p.created_at,
        is_liked: userLiked,
        has_liked: userLiked
      };
    });
  },

  async createFeedPost(content, postType = "story", tag = "") {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    const { data, error } = await window.supabaseClient
      .from("posts")
      .insert({
        author_id: curUser.id,
        content: content.trim(),
        post_type: postType,
        tag: tag || null
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async togglePostLike(postId) {
    if (!window.supabaseClient || !window.UdyamAuth) {
      // Fallback to local Flask endpoint if running locally
      try {
        const resp = await fetch(`/api/posts/${postId}/like`, { method: "POST" });
        if (resp.ok) return await resp.json();
      } catch (_) {}
      throw new Error("Supabase client is not available");
    }

    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    // Check existing like
    const { data: existing, error: checkErr } = await window.supabaseClient
      .from("post_likes")
      .select("id")
      .eq("post_id", postId)
      .eq("user_id", curUser.id)
      .maybeSingle();

    if (checkErr) {
      console.warn("post_likes check error:", checkErr);
      try {
        const resp = await fetch(`/api/posts/${postId}/like`, { method: "POST" });
        if (resp.ok) return await resp.json();
      } catch (_) {}
      throw checkErr;
    }

    let liked = false;
    if (existing) {
      const { error: delErr } = await window.supabaseClient
        .from("post_likes")
        .delete()
        .eq("post_id", postId)
        .eq("user_id", curUser.id);
      if (delErr) throw delErr;
      liked = false;
    } else {
      const { error: insErr } = await window.supabaseClient
        .from("post_likes")
        .insert({
          post_id: postId,
          user_id: curUser.id
        });
      if (insErr) throw insErr;
      liked = true;
    }

    // Query accurate count
    let currentLikes = null;
    try {
      const { count, error: countErr } = await window.supabaseClient
        .from("post_likes")
        .select("id", { count: "exact", head: true })
        .eq("post_id", postId);
      if (!countErr && typeof count === "number") {
        currentLikes = count;
      }
    } catch (_) {}

    if (currentLikes === null) {
      const { data: postData } = await window.supabaseClient
        .from("posts")
        .select("likes_count")
        .eq("id", postId)
        .maybeSingle();
      if (postData && typeof postData.likes_count === "number") {
        currentLikes = postData.likes_count;
      }
    }

    return { success: true, liked: liked, likes: currentLikes };
  },

  async getPostComments(postId) {
    if (!postId) return [];

    // 1. Try querying post_comments table in Supabase
    if (window.supabaseClient) {
      try {
        const { data, error } = await window.supabaseClient
          .from("post_comments")
          .select(`
            id,
            post_id,
            text,
            created_at,
            author:profiles(id, name, avatar)
          `)
          .eq("post_id", postId)
          .order("created_at", { ascending: true });

        if (!error && Array.isArray(data)) {
          return data.map(c => ({
            id: c.id,
            post_id: c.post_id,
            text: c.text,
            created_at: c.created_at,
            author_name: c.author?.name || "Member",
            author_avatar: c.author?.avatar || "assets/images/digital_rahul.jpg"
          }));
        }
      } catch (err) {
        console.warn("Could not query post_comments from Supabase:", err);
      }
    }

    // 2. Fallback to localStorage cache
    if (typeof localStorage !== "undefined") {
      try {
        const cached = localStorage.getItem(`udyam_post_comments_${postId}`);
        if (cached) {
          const parsed = JSON.parse(cached);
          if (Array.isArray(parsed) && parsed.length > 0) return parsed;
        }
      } catch (_) {}
    }

    // 3. Fallback to local Flask API if running
    try {
      const r = await fetch(`/api/posts/${postId}/comments`);
      if (r.ok) {
        const res = await r.json();
        if (res && Array.isArray(res.comments)) return res.comments;
      }
    } catch (_) {}

    return [];
  },

  async createPostComment(postId, text) {
    const curUser = window.UdyamAuth ? await window.UdyamAuth.getUser() : null;
    if (!curUser) throw new Error("Authentication required. Please log in.");
    const cleanText = (text || "").trim();
    if (!cleanText) throw new Error("Please write a comment first.");

    let commentData = null;

    // 1. Try Supabase post_comments table
    if (window.supabaseClient) {
      try {
        const { data, error } = await window.supabaseClient
          .from("post_comments")
          .insert({
            post_id: postId,
            author_id: curUser.id,
            text: cleanText
          })
          .select(`
            id,
            post_id,
            text,
            created_at,
            author:profiles(id, name, avatar)
          `)
          .single();

        if (!error && data) {
          commentData = {
            id: data.id,
            post_id: data.post_id,
            text: data.text,
            created_at: data.created_at,
            author_name: data.author?.name || curUser.user_metadata?.name || curUser.email?.split("@")[0] || "You",
            author_avatar: data.author?.avatar || curUser.user_metadata?.avatar || "assets/images/digital_rahul.jpg"
          };
        }
      } catch (err) {
        console.warn("Supabase post_comments insert failed:", err);
      }
    }

    // 2. Fallback if post_comments table not yet available on Supabase
    if (!commentData) {
      let authorName = curUser.user_metadata?.name || curUser.email?.split("@")[0] || "You";
      let authorAvatar = curUser.user_metadata?.avatar || "assets/images/digital_rahul.jpg";

      if (window.UdyamAuth && typeof window.UdyamAuth.getProfile === "function") {
        try {
          const prof = await window.UdyamAuth.getProfile(curUser.id);
          if (prof) {
            authorName = prof.name || authorName;
            authorAvatar = prof.avatar || authorAvatar;
          }
        } catch (_) {}
      }

      commentData = {
        id: Date.now(),
        post_id: postId,
        text: cleanText,
        created_at: new Date().toISOString(),
        author_name: authorName,
        author_avatar: authorAvatar
      };

      // Also try Flask endpoint if running locally
      try {
        await fetch(`/api/posts/${postId}/comments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: cleanText })
        });
      } catch (_) {}
    }

    // 3. Always store in localStorage so comments persist across reloads
    if (typeof localStorage !== "undefined") {
      try {
        const key = `udyam_post_comments_${postId}`;
        const existing = JSON.parse(localStorage.getItem(key) || "[]");
        existing.push(commentData);
        localStorage.setItem(key, JSON.stringify(existing));
      } catch (_) {}
    }

    return commentData;
  },

  // ---------------------------------------------------------------------------
  // 5. Collaborations & Proposals
  // ---------------------------------------------------------------------------
  async getCollaborations() {
    if (!window.supabaseClient) return [];
    const { data, error } = await window.supabaseClient
      .from("collaborations")
      .select(`
        *,
        author:profiles(id, slug, name, avatar)
      `)
      .order("created_at", { ascending: false });

    if (error) {
      console.error("Error loading collaborations:", error);
      return [];
    }

    return (data || []).map(c => ({
      ...c,
      author_name: c.author ? c.author.name : "Entrepreneur",
      author_avatar: c.author ? c.author.avatar : "assets/images/crafts_banner.jpg"
    }));
  },

  async createCollaboration(collab) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    const collabId = "collab-" + Date.now();
    const { data, error } = await window.supabaseClient
      .from("collaborations")
      .insert({
        collab_id: collabId,
        author_id: curUser.id,
        title: collab.title,
        subtitle: collab.subtitle || "",
        full_description: collab.full_description,
        category: collab.category,
        collab_type: collab.collab_type || "Seeking Partners",
        tag: collab.tag || "",
        location: collab.location || "",
        thumb: collab.thumb || "assets/images/crafts_banner.jpg"
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  },

  async proposeCollaboration(collabId, receiverId, message) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    const { data, error } = await window.supabaseClient
      .from("collaboration_requests")
      .insert({
        collab_id: collabId,
        sender_id: curUser.id,
        receiver_id: receiverId,
        message: message.trim(),
        status: "pending"
      })
      .select()
      .single();

    if (error) throw error;

    // Create notification for receiver
    await window.supabaseClient.from("notifications").insert({
      recipient_id: receiverId,
      actor_id: curUser.id,
      event_type: "collab_request_received",
      title: "New Collaboration Proposal",
      message: message.trim(),
      reference_type: "collaboration_request",
      reference_id: String(data.id),
      link_url: "collaborations.html"
    });

    return data;
  },

  async getCollaborationRequests() {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) return { sent: [], received: [] };

    const { data, error } = await window.supabaseClient
      .from("collaboration_requests")
      .select(`
        *,
        sender:profiles!collaboration_requests_sender_id_fkey(id, slug, name, avatar),
        receiver:profiles!collaboration_requests_receiver_id_fkey(id, slug, name, avatar),
        collab:collaborations(title)
      `)
      .or(`sender_id.eq.${curUser.id},receiver_id.eq.${curUser.id}`)
      .order("created_at", { ascending: false });

    if (error) return { sent: [], received: [] };

    const sent = [];
    const received = [];

    (data || []).forEach(r => {
      const item = {
        id: r.id,
        collab_id: r.collab_id,
        collab_title: r.collab ? r.collab.title : "Collaboration Opportunity",
        sender_id: r.sender_id,
        sender_name: r.sender ? r.sender.name : "Partner",
        sender_avatar: r.sender ? r.sender.avatar : "assets/images/digital_rahul.jpg",
        receiver_id: r.receiver_id,
        receiver_name: r.receiver ? r.receiver.name : "Partner",
        message: r.message,
        status: r.status,
        created_at: r.created_at
      };
      if (r.sender_id === curUser.id) sent.push(item);
      else received.push(item);
    });

    return { sent, received };
  },

  async respondToCollaborationRequest(requestId, action) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    const newStatus = action === "accept" ? "accepted" : "rejected";

    const { data: req, error } = await window.supabaseClient
      .from("collaboration_requests")
      .update({ status: newStatus })
      .eq("id", requestId)
      .eq("receiver_id", curUser.id)
      .select(`*, collab:collaborations(title)`)
      .single();

    if (error) throw error;

    if (newStatus === "accepted") {
      // Create collaborative project
      const projTitle = req.collab ? req.collab.title : "Joint Collaboration Project";
      const { data: proj } = await window.supabaseClient
        .from("collaborative_projects")
        .insert({
          title: projTitle,
          description: req.message,
          category: "General",
          partner1_id: req.receiver_id,
          partner2_id: req.sender_id,
          status: "Active"
        })
        .select()
        .single();

      // Create collaboration chat room
      if (proj) {
        const collabConvId = "conv-collab-" + proj.id;
        const { data: conv } = await window.supabaseClient
          .from("conversations")
          .insert({
            conv_id: collabConvId,
            conv_type: "collaboration",
            title: projTitle,
            project_id: proj.id,
            collab_id: req.collab_id,
            created_by: curUser.id
          })
          .select()
          .single();

        if (conv) {
          await window.supabaseClient.from("conversation_participants").insert([
            { conversation_id: conv.id, conv_id: collabConvId, user_id: req.receiver_id, role: "creator" },
            { conversation_id: conv.id, conv_id: collabConvId, user_id: req.sender_id, role: "member" }
          ]);

          // Initial system message
          await window.supabaseClient.from("messages").insert({
            msg_id: "msg-" + Date.now(),
            conversation_id: conv.id,
            conv_id: collabConvId,
            sender_id: curUser.id,
            body: `Collaboration project '${projTitle}' accepted and started.`,
            message_type: "system"
          });
        }
      }

      // Notify the sender
      await window.supabaseClient.from("notifications").insert({
        recipient_id: req.sender_id,
        actor_id: curUser.id,
        event_type: "collab_request_accepted",
        title: "Proposal Accepted",
        message: `Your collaboration proposal was accepted!`,
        reference_type: "collaboration_request",
        reference_id: String(req.id),
        link_url: "messages.html"
      });
    }

    return req;
  },

  async getCollaborativeProjects() {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) return [];

    const { data, error } = await window.supabaseClient
      .from("collaborative_projects")
      .select(`
        *,
        partner1:profiles!collaborative_projects_partner1_id_fkey(name, avatar),
        partner2:profiles!collaborative_projects_partner2_id_fkey(name, avatar)
      `)
      .or(`partner1_id.eq.${curUser.id},partner2_id.eq.${curUser.id}`)
      .order("created_at", { ascending: false });

    if (error) return [];
    return data || [];
  },

  // ---------------------------------------------------------------------------
  // 6. Discussions & Comments
  // ---------------------------------------------------------------------------
  async getDiscussions() {
    if (!window.supabaseClient) return [];
    const { data, error } = await window.supabaseClient
      .from("discussions")
      .select(`
        *,
        author:profiles(id, slug, name, category, location, avatar),
        comments(id)
      `)
      .order("created_at", { ascending: false });

    if (error) return [];
    return (data || []).map(d => ({
      ...d,
      author_name: d.author ? d.author.name : "Community Member",
      author_category: d.author ? d.author.category : "",
      author_location: d.author ? d.author.location : "India",
      author_avatar: d.author ? d.author.avatar : "assets/images/digital_rahul.jpg",
      comments_count: (d.comments || []).length
    }));
  },

  async getDiscussionDetail(discId) {
    if (!window.supabaseClient || !discId) return null;

    const { data: disc, error } = await window.supabaseClient
      .from("discussions")
      .select(`
        *,
        author:profiles(id, slug, name, category, location, avatar)
      `)
      .eq("disc_id", discId)
      .maybeSingle();

    if (error || !disc) return null;

    // Fetch comments
    const { data: comments } = await window.supabaseClient
      .from("comments")
      .select(`
        *,
        author:profiles(id, slug, name, avatar)
      `)
      .eq("disc_id", discId)
      .order("created_at", { ascending: true });

    return {
      ...disc,
      author_name: disc.author ? disc.author.name : "Community Member",
      author_category: disc.author ? disc.author.category : "",
      author_location: disc.author ? disc.author.location : "India",
      author_avatar: disc.author ? disc.author.avatar : "assets/images/digital_rahul.jpg",
      comments: (comments || []).map(c => ({
        id: c.id,
        text: c.text,
        created_at: c.created_at,
        time_ago: new Date(c.created_at).toLocaleDateString(),
        author_name: c.author ? c.author.name : "Community Member",
        author_avatar: c.author ? c.author.avatar : "assets/images/digital_rahul.jpg"
      }))
    };
  },

  async createComment(discId, text) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    const { data, error } = await window.supabaseClient
      .from("comments")
      .insert({
        disc_id: discId,
        author_id: curUser.id,
        text: text.trim()
      })
      .select(`*, author:profiles(id, name, avatar)`)
      .single();

    if (error) throw error;
    return {
      id: data.id,
      text: data.text,
      created_at: data.created_at,
      author_name: data.author ? data.author.name : "You",
      author_avatar: data.author ? data.author.avatar : "assets/images/digital_rahul.jpg"
    };
  },

  // ---------------------------------------------------------------------------
  // 7. Messaging System
  // ---------------------------------------------------------------------------
  async getConversations() {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) return [];

    // Find all conversation IDs where user is a participant
    const { data: participations } = await window.supabaseClient
      .from("conversation_participants")
      .select("conversation_id, last_read_at")
      .eq("user_id", curUser.id);

    if (!participations || participations.length === 0) return [];
    const convIds = participations.map(p => p.conversation_id);

    const { data: convs, error } = await window.supabaseClient
      .from("conversations")
      .select(`
        *,
        participants:conversation_participants(
          user_id,
          role,
          profile:profiles(id, slug, name, avatar)
        ),
        messages(id, body, created_at, sender_id)
      `)
      .in("id", convIds)
      .order("updated_at", { ascending: false });

    if (error) return [];

    return (convs || []).map(c => {
      // Find other participant for direct chats
      const otherPart = (c.participants || []).find(p => p.user_id !== curUser.id);
      const otherProf = otherPart ? otherPart.profile : null;

      // Find last message
      const msgs = (c.messages || []).sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      const lastMsg = msgs[msgs.length - 1] || null;

      return {
        id: c.id,
        conv_id: c.conv_id,
        conv_type: c.conv_type,
        title: c.conv_type === "direct" ? (otherProf ? otherProf.name : "Direct Conversation") : (c.title || "Project Conversation"),
        avatar: c.conv_type === "direct" ? (otherProf ? otherProf.avatar : "assets/images/digital_rahul.jpg") : "assets/images/crafts_banner.jpg",
        partner_id: otherProf ? otherProf.id : null,
        partner_slug: otherProf ? otherProf.slug : null,
        last_message: lastMsg ? lastMsg.body : "No messages yet",
        updated_at: c.updated_at
      };
    });
  },

  async getMessages(convId) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) return [];

    const { data, error } = await window.supabaseClient
      .from("messages")
      .select(`
        *,
        sender:profiles(id, name, avatar)
      `)
      .eq("conv_id", convId)
      .order("created_at", { ascending: true });

    if (error) return [];

    return (data || []).map(m => ({
      id: m.id,
      msg_id: m.msg_id,
      sender_id: m.sender_id,
      sender_name: m.sender ? m.sender.name : "Member",
      sender_avatar: m.sender ? m.sender.avatar : "assets/images/digital_rahul.jpg",
      body: m.body,
      message_type: m.message_type,
      created_at: m.created_at,
      is_self: m.sender_id === curUser.id
    }));
  },

  async sendMessage(convId, body) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) throw new Error("Authentication required");

    // Fetch conversation record to get numeric ID
    const { data: conv } = await window.supabaseClient
      .from("conversations")
      .select("id")
      .eq("conv_id", convId)
      .single();

    if (!conv) throw new Error("Conversation not found");

    const msgId = "msg-" + Date.now();
    const { data, error } = await window.supabaseClient
      .from("messages")
      .insert({
        msg_id: msgId,
        conversation_id: conv.id,
        conv_id: convId,
        sender_id: curUser.id,
        body: body.trim(),
        message_type: "text"
      })
      .select()
      .single();

    if (error) throw error;

    // Update conversation timestamp
    await window.supabaseClient
      .from("conversations")
      .update({ updated_at: new Date().toISOString() })
      .eq("id", conv.id);

    return data;
  },

  // ---------------------------------------------------------------------------
  // 8. Notifications
  // ---------------------------------------------------------------------------
  async getNotifications() {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) return [];

    const { data, error } = await window.supabaseClient
      .from("notifications")
      .select(`
        *,
        actor:profiles!notifications_actor_id_fkey(name, avatar)
      `)
      .eq("recipient_id", curUser.id)
      .order("created_at", { ascending: false });

    if (error) return [];

    return (data || []).map(n => ({
      id: n.id,
      event_type: n.event_type,
      title: n.title,
      message: n.message,
      link_url: n.link_url,
      is_read: n.is_read,
      created_at: n.created_at,
      actor_name: n.actor ? n.actor.name : "ThriveHub",
      actor_avatar: n.actor ? n.actor.avatar : "assets/images/digital_rahul.jpg"
    }));
  },

  async markNotificationRead(notifId) {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) return;

    await window.supabaseClient
      .from("notifications")
      .update({ is_read: true })
      .eq("id", notifId)
      .eq("recipient_id", curUser.id);
  },

  async markAllNotificationsRead() {
    const curUser = await window.UdyamAuth.getUser();
    if (!curUser) return;

    await window.supabaseClient
      .from("notifications")
      .update({ is_read: true })
      .eq("recipient_id", curUser.id);
  },

  // ---------------------------------------------------------------------------
  // 9. Articles (Learn & Share)
  // ---------------------------------------------------------------------------
  async getArticles() {
    if (!window.supabaseClient) return [];
    const { data, error } = await window.supabaseClient
      .from("articles")
      .select("*")
      .order("created_at", { ascending: false });

    if (error) return [];
    return data || [];
  },

  // ---------------------------------------------------------------------------
  // 10. Profile Image Storage & Upload Helper
  // ---------------------------------------------------------------------------
  async uploadProfileImage(file, imageType = "avatar") {
    if (!file) throw new Error("No file provided");
    const validTypes = ["avatar", "business_logo", "cover"];
    if (!validTypes.includes(imageType)) {
      throw new Error("Invalid image type");
    }

    // Validate size (5 MB limit)
    const MAX_SIZE = 5 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      throw new Error("File size exceeds 5 MB limit");
    }

    // Validate format
    const allowedMime = ["image/jpeg", "image/png", "image/webp"];
    if (!allowedMime.includes(file.type)) {
      throw new Error("Invalid format. Only JPEG, PNG, and WebP are allowed.");
    }

    // If Supabase Auth session is active, attempt Supabase Storage
    if (window.supabaseClient && window.UdyamAuth) {
      const curUser = await window.UdyamAuth.getUser();
      if (curUser) {
        const ext = file.name.split(".").pop().toLowerCase() || "jpg";
        const cleanName = `${Date.now()}_${Math.random().toString(36).substring(2, 8)}.${ext}`;
        const filePath = `${curUser.id}/${imageType}/${cleanName}`;

        const { data, error } = await window.supabaseClient.storage
          .from("profiles")
          .upload(filePath, file, {
            cacheControl: "3600",
            upsert: true
          });

        if (!error && data) {
          const { data: { publicUrl } } = window.supabaseClient.storage
            .from("profiles")
            .getPublicUrl(filePath);
          return { success: true, url: publicUrl, imageType };
        }
      }
    }

    // Fallback to Flask backend /api/upload
    if (!window.CSRF_TOKEN) {
      try {
        const cRes = await fetch("/api/csrf-token");
        const cData = await cRes.json();
        if (cData && cData.csrf_token) {
          window.CSRF_TOKEN = cData.csrf_token;
        }
      } catch (e) {}
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("image_type", imageType);

    const headers = {};
    if (window.CSRF_TOKEN) {
      headers["X-CSRF-Token"] = window.CSRF_TOKEN;
    }

    const response = await fetch("/api/upload", {
      method: "POST",
      headers,
      credentials: "same-origin",
      body: formData
    });

    const res = await response.json();
    if (!response.ok || !res.success) {
      throw new Error(res.error || "Image upload failed");
    }
    return { success: true, url: res.url, imageType };
  }
};

window.ThriveHubAPI = window.UdyamAPI;

