import sqlite3
import json
import os
import sys
import shutil
import datetime
from werkzeug.security import generate_password_hash

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "udyamsetu.db")

def get_db_path():
    return os.environ.get("UDYAMSETU_DB_PATH") or DEFAULT_DB_PATH

DB_PATH = DEFAULT_DB_PATH

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def backup_db(db_path=None):
    """Creates a timestamped backup of the current database file."""
    target_path = db_path or get_db_path()
    if not os.path.exists(target_path):
        return None
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = os.path.dirname(target_path)
    base_name = os.path.basename(target_path).replace(".db", "")
    backup_filename = f"{base_name}_backup_{timestamp}.db"
    backup_filepath = os.path.join(base_dir, backup_filename)
    shutil.copy2(target_path, backup_filepath)
    return backup_filepath

def init_db(reset=False):
    db_path = get_db_path()
    if reset and os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        account_type TEXT DEFAULT 'entrepreneur',
        business_name TEXT DEFAULT '',
        category TEXT DEFAULT '',
        location TEXT DEFAULT '',
        state TEXT DEFAULT '',
        district TEXT DEFAULT '',
        subdistrict_or_town TEXT DEFAULT '',
        pincode TEXT DEFAULT '',
        address_landmark TEXT DEFAULT '',
        location_display_preference TEXT DEFAULT 'district_state',
        preferred_language TEXT DEFAULT 'en',
        avatar TEXT DEFAULT 'assets/images/digital_rahul.jpg',
        quote TEXT DEFAULT '',
        description TEXT DEFAULT '',
        full_story TEXT DEFAULT '',
        looking_for TEXT DEFAULT '[]',
        skills TEXT DEFAULT '[]',
        website TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        verified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Safe Automatic Schema Migration for existing databases
    cursor.execute("PRAGMA table_info(users);")
    existing_cols = {row["name"] for row in cursor.fetchall()}

    columns_to_add = [
        ("account_type", "TEXT DEFAULT 'entrepreneur'"),
        ("state", "TEXT DEFAULT ''"),
        ("district", "TEXT DEFAULT ''"),
        ("subdistrict_or_town", "TEXT DEFAULT ''"),
        ("pincode", "TEXT DEFAULT ''"),
        ("address_landmark", "TEXT DEFAULT ''"),
        ("location_display_preference", "TEXT DEFAULT 'district_state'"),
        ("preferred_language", "TEXT DEFAULT 'en'"),
        ("business_logo_url", "TEXT DEFAULT ''"),
        ("cover_image_url", "TEXT DEFAULT ''")
    ]

    for col_name, col_def in columns_to_add:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def};")

    # Ensure existing records have entrepreneur account_type and default preferred_language
    cursor.execute("UPDATE users SET account_type = 'entrepreneur' WHERE account_type IS NULL OR account_type = '';")
    cursor.execute("UPDATE users SET preferred_language = 'en' WHERE preferred_language IS NULL OR preferred_language = '';")

    # Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        price TEXT NOT NULL,
        image TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Posts Table (Dashboard & Feed)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_id TEXT NOT NULL,
        content TEXT NOT NULL,
        post_type TEXT DEFAULT 'story',
        tag TEXT,
        likes INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Post Likes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS post_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(post_id, user_id),
        FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Collaborations Table (Opportunities)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collaborations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collab_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        subtitle TEXT,
        full_description TEXT NOT NULL,
        category TEXT NOT NULL,
        collab_type TEXT NOT NULL,
        tag TEXT,
        location TEXT,
        author_id TEXT NOT NULL,
        thumb TEXT,
        time_ago TEXT DEFAULT 'Just now',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Collaboration Requests Table (Proposals between users)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collaboration_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collab_id TEXT,
        sender_id TEXT NOT NULL,
        receiver_id TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (collab_id) REFERENCES collaborations(collab_id) ON DELETE SET NULL,
        FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Collaborative Projects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS collaborative_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        partner1_id TEXT NOT NULL,
        partner2_id TEXT NOT NULL,
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (partner1_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (partner2_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Discussions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discussions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disc_id TEXT UNIQUE NOT NULL,
        author_id TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        tag TEXT DEFAULT 'Question',
        likes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Comments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disc_id TEXT NOT NULL,
        author_id TEXT NOT NULL,
        text TEXT NOT NULL,
        time_ago TEXT DEFAULT 'Just now',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (disc_id) REFERENCES discussions(disc_id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Articles Table (Learn & Share)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        author_id TEXT NOT NULL,
        date_str TEXT NOT NULL,
        image TEXT NOT NULL,
        summary TEXT NOT NULL,
        lessons TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Connections Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id_1 TEXT NOT NULL,
        user_id_2 TEXT NOT NULL,
        status TEXT DEFAULT 'connected',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id_1, user_id_2)
    );
    """)

    # ---------------------------------------------------------
    # Messaging System Tables (Phase 2)
    # ---------------------------------------------------------

    # Conversations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conv_id TEXT UNIQUE NOT NULL,
        conv_type TEXT NOT NULL DEFAULT 'direct', -- 'direct' or 'collaboration'
        title TEXT DEFAULT '',
        direct_key TEXT UNIQUE, -- e.g. "direct:{min_uid}:{max_uid}" for 1-on-1 direct conversations; NULL for collaboration
        project_id INTEGER UNIQUE DEFAULT NULL, -- links to collaborative_projects(id); UNIQUE prevents duplicate collaboration chats
        collab_id TEXT DEFAULT NULL, -- links to collaborations(collab_id)
        created_by TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES collaborative_projects(id) ON DELETE SET NULL,
        FOREIGN KEY (collab_id) REFERENCES collaborations(collab_id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Conversation Participants Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversation_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        conv_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT DEFAULT 'member', -- 'creator' or 'member'
        last_read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(conversation_id, user_id),
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
        FOREIGN KEY (conv_id) REFERENCES conversations(conv_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        msg_id TEXT UNIQUE NOT NULL,
        conversation_id INTEGER NOT NULL,
        conv_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        body TEXT NOT NULL,
        message_type TEXT DEFAULT 'text', -- 'text' or 'system'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
        FOREIGN KEY (conv_id) REFERENCES conversations(conv_id) ON DELETE CASCADE,
        FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # User Blocks Table (Abuse Prevention)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        blocker_id TEXT NOT NULL,
        blocked_id TEXT NOT NULL,
        reason TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(blocker_id, blocked_id),
        FOREIGN KEY (blocker_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (blocked_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Performance & Lookup Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_direct_key ON conversations(direct_key);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_participants_user ON conversation_participants(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_participants_conv ON conversation_participants(conversation_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON messages(conversation_id, id ASC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_blocks_pair ON user_blocks(blocker_id, blocked_id);")

    # ---------------------------------------------------------
    # In-App Notification System Tables
    # ---------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id TEXT NOT NULL,
        actor_id TEXT,
        event_type TEXT NOT NULL,
        title TEXT DEFAULT '',
        message TEXT NOT NULL,
        reference_type TEXT DEFAULT '',
        reference_id TEXT DEFAULT '',
        link_url TEXT DEFAULT '',
        is_read INTEGER DEFAULT 0,
        dedup_key TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipient_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (actor_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_id, is_read, created_at DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_dedup ON notifications(dedup_key);")

    conn.commit()

    # Seed Initial Data if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        seed_database(conn)

    # Seed Initial Messaging Data if conversations table is empty
    cursor.execute("SELECT COUNT(*) FROM conversations;")
    if cursor.fetchone()[0] == 0:
        seed_messaging_data(conn)

    # Seed Initial Notification Data if notifications table is empty
    cursor.execute("SELECT COUNT(*) FROM notifications;")
    if cursor.fetchone()[0] == 0:
        seed_notifications_data(conn)

    conn.close()

def create_notification(cursor, recipient_id: str, event_type: str, message: str,
                        actor_id: str = None, title: str = "", reference_type: str = "",
                        reference_id: str = "", link_url: str = "", dedup_key: str = None):
    """
    Inserts an in-app notification idempotently inside the current cursor/transaction.
    - If recipient_id == actor_id, skips notification (no self-notifications).
    - If dedup_key is provided and already exists, uses INSERT OR IGNORE to prevent duplicates.
    - Returns the notification id if inserted, or None.
    """
    if not recipient_id or recipient_id == actor_id:
        return None

    try:
        cursor.execute("""
        INSERT OR IGNORE INTO notifications (
            recipient_id, actor_id, event_type, title, message,
            reference_type, reference_id, link_url, is_read, dedup_key
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (
            recipient_id,
            actor_id,
            event_type,
            title or "",
            message,
            reference_type or "",
            str(reference_id) if reference_id is not None else "",
            link_url or "",
            dedup_key
        ))
        return cursor.lastrowid
    except Exception:
        return None

def make_direct_key(user1_id: str, user2_id: str) -> str:
    """Returns a deterministic unique key for a direct 1-on-1 conversation."""
    low = min(user1_id, user2_id)
    high = max(user1_id, user2_id)
    return f"direct:{low}:{high}"

def seed_notifications_data(conn):
    """Seed initial realistic notifications for demo accounts."""
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id IN ('asha-devi', 'ramesh-kumar', 'rahul-sharma', 'meera-patil', 'green-harvest', 'lakshmi-narayan');")
    found_users = {row["user_id"] for row in cursor.fetchall()}
    if "ramesh-kumar" not in found_users or "asha-devi" not in found_users:
        return

    sample_notifs = [
        (
            "ramesh-kumar", "asha-devi", "new_message",
            "New message from Asha Devi",
            "Namaste Ramesh ji! I saw your Malnad organic spices in the directory. We are assembling handcrafted moonj...",
            "conversation", "conv-asha-ramesh", "messages.html?conversation=conv-asha-ramesh",
            0, "seed-notif-1"
        ),
        (
            "rahul-sharma", "asha-devi", "collab_request_accepted",
            "Partnership Accepted by Asha Devi",
            "Asha Devi accepted your collaboration proposal for 'Handicrafts Digital Catalog & Karigar Showcase'!",
            "collaboration_request", "2", "messages.html?conversation=conv-collab-1",
            0, "seed-notif-2"
        ),
        (
            "meera-patil", "rahul-sharma", "collab_request_received",
            "Partnership Request from Rahul Sharma",
            "Rahul Sharma sent a collaboration proposal for your snack packaging.",
            "collaboration_request", "1", "collaborations.html",
            0, "seed-notif-3"
        ),
        (
            "asha-devi", "ramesh-kumar", "new_connection",
            "New connection with Ramesh Kumar",
            "Ramesh Kumar connected with you on ThriveHub.",
            "user", "ramesh-kumar", "profile.html?id=ramesh-kumar",
            1, "seed-notif-4"
        ),
        (
            "green-harvest", "ramesh-kumar", "collab_request_accepted",
            "Partnership Confirmed with Ramesh Kumar",
            "Ramesh Kumar accepted your partnership for Organic Spice Synergy!",
            "collaboration_request", "3", "messages.html?conversation=conv-collab-2",
            0, "seed-notif-5"
        ),
        (
            "lakshmi-narayan", "meera-patil", "new_message",
            "New message from Meera Patil",
            "Hello Lakshmi ji, saw your post about banana fiber padded pouches...",
            "conversation", "conv-meera-lakshmi", "messages.html?conversation=conv-meera-lakshmi",
            0, "seed-notif-6"
        )
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO notifications (
        recipient_id, actor_id, event_type, title, message,
        reference_type, reference_id, link_url, is_read, dedup_key
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sample_notifs)
    conn.commit()

def seed_messaging_data(conn):
    """Seed initial realistic conversations between existing demo accounts."""
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE user_id IN ('asha-devi', 'ramesh-kumar', 'rahul-sharma', 'meera-patil', 'green-harvest', 'lakshmi-narayan');")
    found_users = {row["user_id"] for row in cursor.fetchall()}
    if "asha-devi" not in found_users or "ramesh-kumar" not in found_users:
        return

    # 1. Direct Conversation between Asha Devi and Ramesh Kumar
    direct_key_1 = make_direct_key("asha-devi", "ramesh-kumar")
    conv_id_1 = "conv-asha-ramesh"
    cursor.execute("""
    INSERT OR IGNORE INTO conversations (conv_id, conv_type, direct_key, created_by, updated_at)
    VALUES (?, 'direct', ?, 'asha-devi', CURRENT_TIMESTAMP);
    """, (conv_id_1, direct_key_1))

    cursor.execute("SELECT id FROM conversations WHERE conv_id = ?;", (conv_id_1,))
    conv_row_1 = cursor.fetchone()
    if conv_row_1:
        c_id = conv_row_1["id"]
        cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, 'asha-devi', 'creator');", (c_id, conv_id_1))
        cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, 'ramesh-kumar', 'member');", (c_id, conv_id_1))

        sample_msgs_1 = [
            ("msg-seed-1", c_id, conv_id_1, "asha-devi", "Namaste Ramesh ji! I saw your Malnad organic spices in the directory. We are assembling handcrafted moonj gift hampers for the upcoming festive exhibition and would love to include your aromatic cardamom and pepper.", "text"),
            ("msg-seed-2", c_id, conv_id_1, "ramesh-kumar", "Namaste Asha ji! That sounds like a wonderful synergy between traditional craft and organic agriculture. Our cardamom is fresh from harvest and PGS-certified. I can dispatch a sample pack to Varanasi tomorrow.", "text"),
            ("msg-seed-3", c_id, conv_id_1, "asha-devi", "That would be fantastic! Please send samples of green cardamom and crushed black pepper. Looking forward to our collaboration.", "text")
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
        VALUES (?, ?, ?, ?, ?, ?);
        """, sample_msgs_1)

    # 2. Direct Conversation between Meera Patil and Lakshmi Narayan
    if "meera-patil" in found_users and "lakshmi-narayan" in found_users:
        direct_key_2 = make_direct_key("meera-patil", "lakshmi-narayan")
        conv_id_2 = "conv-meera-lakshmi"
        cursor.execute("""
        INSERT OR IGNORE INTO conversations (conv_id, conv_type, direct_key, created_by, updated_at)
        VALUES (?, 'direct', ?, 'meera-patil', CURRENT_TIMESTAMP);
        """, (conv_id_2, direct_key_2))

        cursor.execute("SELECT id FROM conversations WHERE conv_id = ?;", (conv_id_2,))
        conv_row_2 = cursor.fetchone()
        if conv_row_2:
            c2_id = conv_row_2["id"]
            cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, 'meera-patil', 'creator');", (c2_id, conv_id_2))
            cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, 'lakshmi-narayan', 'member');", (c2_id, conv_id_2))

            sample_msgs_2 = [
                ("msg-seed-4", c2_id, conv_id_2, "meera-patil", "Hello Lakshmi ji, saw your post about banana fiber padded pouches. Could you share details on whether they are oil-resistant for traditional roasted snacks?", "text"),
                ("msg-seed-5", c2_id, conv_id_2, "lakshmi-narayan", "Namaste Meera ji! Yes, we have developed a vegetable-starch inner lining that is 100% compostable and grease-resistant. I will send 10 trial mailers to Satara.", "text"),
                ("msg-seed-6", c2_id, conv_id_2, "meera-patil", "That is exactly what we were searching for. Thank you so much!", "text")
            ]
            cursor.executemany("""
            INSERT OR IGNORE INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
            VALUES (?, ?, ?, ?, ?, ?);
            """, sample_msgs_2)

    # 3. Collaboration Project Conversations
    cursor.execute("SELECT id, title, partner1_id, partner2_id FROM collaborative_projects ORDER BY id ASC;")
    projects = cursor.fetchall()
    for proj in projects:
        p_id = proj["id"]
        collab_conv_id = f"conv-collab-{p_id}"
        cursor.execute("""
        INSERT OR IGNORE INTO conversations (conv_id, conv_type, title, project_id, created_by, updated_at)
        VALUES (?, 'collaboration', ?, ?, ?, CURRENT_TIMESTAMP);
        """, (collab_conv_id, proj["title"], p_id, proj["partner1_id"]))

        cursor.execute("SELECT id FROM conversations WHERE conv_id = ?;", (collab_conv_id,))
        collab_row = cursor.fetchone()
        if collab_row:
            cc_id = collab_row["id"]
            cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'creator');", (cc_id, collab_conv_id, proj["partner1_id"]))
            cursor.execute("INSERT OR IGNORE INTO conversation_participants (conversation_id, conv_id, user_id, role) VALUES (?, ?, ?, 'member');", (cc_id, collab_conv_id, proj["partner2_id"]))

            if p_id == 1:
                collab_msgs = [
                    (f"msg-seed-collab-{p_id}-1", cc_id, collab_conv_id, proj["partner1_id"], f"Collaboration project '{proj['title']}' active. Coordinate your joint deliverables here.", "system"),
                    (f"msg-seed-collab-{p_id}-2", cc_id, collab_conv_id, proj["partner2_id"], "Rahul ji, I have uploaded the high-resolution photography files for the first 15 moonj baskets.", "text"),
                    (f"msg-seed-collab-{p_id}-3", cc_id, collab_conv_id, proj["partner1_id"], "Excellent! The catalog layout and bilingual story tags are ready for review.", "text")
                ]
            else:
                collab_msgs = [
                    (f"msg-seed-collab-{p_id}-1", cc_id, collab_conv_id, proj["partner1_id"], f"Collaboration project '{proj['title']}' active. Coordinate your joint deliverables here.", "system"),
                    (f"msg-seed-collab-{p_id}-2", cc_id, collab_conv_id, proj["partner2_id"], "Namaste Green Harvest team! We have sorted 50kg of premium grade whole black pepper for our joint spice packs.", "text"),
                    (f"msg-seed-collab-{p_id}-3", cc_id, collab_conv_id, proj["partner1_id"], "Wonderful Ramesh ji! We are designing the combination tins with both farm origin stories highlighted.", "text")
                ]
            cursor.executemany("""
            INSERT OR IGNORE INTO messages (msg_id, conversation_id, conv_id, sender_id, body, message_type)
            VALUES (?, ?, ?, ?, ?, ?);
            """, collab_msgs)

    conn.commit()

def seed_database(conn):
    cursor = conn.cursor()
    default_hash = generate_password_hash("password123")

    # 10 Fictional Entrepreneurs across Indian states, categories, and locations + 2 Community Members
    users = [
        (
            "asha-devi", "Asha Devi", "asha@udyamsetu.in", default_hash,
            "entrepreneur", "Asha Rural Handicrafts", "Handicrafts", "Varanasi, Uttar Pradesh",
            "Uttar Pradesh", "Varanasi", "Rameshwar", "221002", "Behind Village Panchayat Hall", "district_state",
            "en", "assets/images/artisan_asha.jpg",
            "Preserving traditional craftsmanship while creating sustainable rural livelihoods. [Demo Profile]",
            "Handmade bags, home decor and traditional crafts. Looking for marketing and distribution partners.",
            "We create handmade bags, home decor and traditional crafts using local natural materials like moonj grass, cane, and clay. Our enterprise empowers over 45 rural women with sustainable dignified livelihoods, taking local indigenous craft to national and export exhibitions. [Demo Profile]",
            json.dumps(["Marketing partners", "Distributors", "E-commerce support"]),
            json.dumps(["Moonj Weaving", "Terracotta Pottery", "Natural Dyes"]),
            "https://ashacrafts.example.com", "+91 98765 43210",
            1
        ),
        (
            "ramesh-kumar", "Ramesh Kumar", "ramesh@udyamsetu.in", default_hash,
            "entrepreneur", "Malnad Organic Spices", "Agriculture", "Chikkamagaluru, Karnataka",
            "Karnataka", "Chikkamagaluru", "Mudigere", "577132", "Western Ghats Valley Estate", "district_state",
            "en", "assets/images/ramesh_kumar.jpg",
            "Connecting Western Ghats spice growers with national conscious markets. [Demo Profile]",
            "Organic turmeric, cardamom, and black pepper grown in the Western Ghats foothills.",
            "Family farming legacy now modernized into an organic farmer producer cluster cultivating high-grade GI turmeric, black pepper, and aromatic cardamom with PGS certification. [Demo Profile]",
            json.dumps(["Interstate buyers", "Wholesale partners", "FSSAI compliance guidance"]),
            json.dumps(["Organic Spices", "Direct Sourcing", "Quality Testing"]),
            "https://malnadspices.example.com", "+91 98765 99001",
            1
        ),
        (
            "meera-patil", "Meera Patil", "meera@udyamsetu.in", default_hash,
            "entrepreneur", "Meera's Traditional Foods", "Food Products", "Satara, Maharashtra",
            "Maharashtra", "Satara", "Wai", "412803", "Ganpati Ali Farm Complex", "district_state",
            "en", "assets/images/meera_patil.jpg",
            "Authentic Maharashtrian kitchen recipes prepared with local wholesome grains. [Demo Profile]",
            "Traditional Maharashtrian dry snacks, cold-stone pounded masalas, and healthy millet cookies.",
            "Founded in Satara district, we prepare small-batch stone-ground spices, spicy roasted poha chivda, and multigrain laddus made from organic jaggery. [Demo Profile]",
            json.dumps(["Eco-friendly packaging", "Urban retailers", "Courier partners"]),
            json.dumps(["Food Processing", "Traditional Spices", "FSSAI Standards"]),
            "https://meeratraditional.example.com", "+91 98765 77889",
            1
        ),
        (
            "rahul-sharma", "Rahul Sharma", "rahul@udyamsetu.in", default_hash,
            "entrepreneur", "Gramin Digital Studio", "Digital Services", "Jodhpur, Rajasthan",
            "Rajasthan", "Jodhpur", "Mandore", "342004", "Gram Seva Kendra Building", "district_state",
            "en", "assets/images/digital_rahul.jpg",
            "Empowering rural micro-enterprises with practical digital skills and clean branding. [Demo Profile]",
            "Website development, product photography and digital marketing for small businesses.",
            "Providing localized digital branding, catalog photography, social media assistance, and WhatsApp store setup for rural self-help groups and grassroots entrepreneurs across western India. [Demo Profile]",
            json.dumps(["Artisan clusters", "Agri-FPOs", "Rural cooperatives"]),
            json.dumps(["Photography", "Websites", "Social Media Marketing"]),
            "https://graminstudio.example.com", "+91 98765 66778",
            1
        ),
        (
            "suresh-yadav", "Suresh Yadav", "suresh@udyamsetu.in", default_hash,
            "entrepreneur", "Yadav Natural Apiaries", "Organic Products", "Muzaffarpur, Bihar",
            "Bihar", "Muzaffarpur", "Kanti", "843109", "Near Litchi Research Orchards", "district_state",
            "en", "assets/images/suresh_yadav.jpg",
            "Pure unpasteurized raw honey harvested ethically from orchard blossoms. [Demo Profile]",
            "Raw unpasteurized honey, organic beekeeping kits, and seasonal herbal extracts.",
            "We run a network of 400 beehives across Muzaffarpur and Samastipur, producing seasonal litchi honey and raw mustard flora honey without artificial additives. [Demo Profile]",
            json.dumps(["Distributors", "Eco-packaging jars", "Interstate transport"]),
            json.dumps(["Beekeeping", "Honey Extraction", "Packaging Quality"]),
            "https://yadavhoney.example.com", "+91 98765 88990",
            0
        ),
        (
            "ananya-sharma", "Ananya Sharma", "ananya@udyamsetu.in", default_hash,
            "entrepreneur", "Ananya Handlooms & Natural Dyes", "Rural Textiles", "Jaipur, Rajasthan",
            "Rajasthan", "Jaipur", "Amer", "302028", "Near Old Amber Post Office", "district_state",
            "en", "assets/images/hero_entrepreneur.jpg",
            "Connecting rural weavers with modern design and natural plant dyes. [Demo Profile]",
            "Specializing in handloom khadi, natural vegetable dyeing, and fair-wage women's clusters.",
            "Working with women weavers in rural Rajasthan to modernize traditional motifs, formulate natural indigo dyes, and bring heritage handloom textiles to conscious urban markets. [Demo Profile]",
            json.dumps(["Handloom clusters", "Export partners", "Designers"]),
            json.dumps(["E-commerce", "Weaving Design", "Natural Dyeing"]),
            "https://ananyahandlooms.example.com", "+91 98765 11223",
            1
        ),
        (
            "green-harvest", "Green Harvest Producer Co.", "contact@greenharvest.in", default_hash,
            "entrepreneur", "Green Harvest Organic Collective", "Agriculture", "Hoshangabad, Madhya Pradesh",
            "Madhya Pradesh", "Hoshangabad", "Pipariya", "461775", "Station Road Grain Mandi", "district_state",
            "en", "assets/images/farmer_greenharvest.jpg",
            "Pioneering organic soil regeneration and community crop aggregation. [Demo Profile]",
            "Organic pulses, spices and cold-pressed oils. Open to partnerships for value-addition.",
            "A collective of 120 smallholder organic farmers in central Madhya Pradesh specializing in chemical-free heirloom wheat, cold-pressed mustard oil, organic chickpea, and natural turmeric. [Demo Profile]",
            json.dumps(["Packaging partners", "Bulk buyers", "Logistics support"]),
            json.dumps(["Organic Farming", "Crop Aggregation", "PGS Certification"]),
            "https://greenharvest.example.com", "+91 98765 55443",
            1
        ),
        (
            "harpreet-singh", "Harpreet Singh", "harpreet@udyamsetu.in", default_hash,
            "entrepreneur", "Doaba Bio-Organics & Cold-Pressed Oils", "Agriculture", "Hoshiarpur, Punjab",
            "Punjab", "Hoshiarpur", "Dasuya", "144205", "G.T. Road Agri Hub", "district_state",
            "en", "assets/images/farmer_portrait.jpg",
            "Zero-chemical sustainable multi-cropping and cold-pressed seed oils. [Demo Profile]",
            "Cold-pressed flaxseed, yellow mustard oil, organic jaggery, and chemical-free basmati.",
            "Fourth-generation farmer converting 18 acres into bio-diverse natural cultivation of oilseeds, pulses, and traditional sugarcane. Running an on-farm solar-powered oil extraction mill. [Demo Profile]",
            json.dumps(["Retail distributors", "Packaging partners", "Bulk organic buyers"]),
            json.dumps(["Organic Farming", "Cold-Press Extraction", "Soil Testing"]),
            "https://doabaoils.example.com", "+91 98765 33445",
            1
        ),
        (
            "deepak-kumhar", "Deepak Kumhar", "deepak@udyamsetu.in", default_hash,
            "entrepreneur", "MittiKala Terracotta & Studio Pottery", "Pottery & Crafts", "Kutch, Gujarat",
            "Gujarat", "Kutch", "Bhuj", "370020", "Crafts Village Workshop Lane", "district_state",
            "en", "assets/images/potter_artisan.jpg",
            "Breathing contemporary life into ancient clay crafting traditions. [Demo Profile]",
            "Lead-free earthenware cookware, terracotta water carafes, and traditional glazed tableware.",
            "Continuing ancestral Kutch pottery techniques with sustainable terracotta and natural slip glazes. We craft durable curd-setting handis, water dispensers, and decorative architectural terracotta tiles. [Demo Profile]",
            json.dumps(["Culinary brands", "Urban home stores", "Hospitality partners"]),
            json.dumps(["Terracotta Craft", "Clay Chemistry", "Kiln Firing"]),
            "https://mittikala.example.com", "+91 98765 22334",
            0
        ),
        (
            "lakshmi-narayan", "Lakshmi Narayan", "lakshmi@udyamsetu.in", default_hash,
            "entrepreneur", "Cauvery Eco-Weaves & Sustainable Packaging", "Natural Products", "Thanjavur, Tamil Nadu",
            "Tamil Nadu", "Thanjavur", "Kumbakonam", "612001", "Cauvery Riverbank Road", "district_state",
            "en", "assets/images/crafts_banner.jpg",
            "Transforming agricultural banana stem waste into biodegradable packaging. [Demo Profile]",
            "Biodegradable banana fiber mailers, gift sleeves, and natural korai grass storage baskets.",
            "We upcycle discarded banana pseudo-stems into sturdy, water-resistant packaging pouches, mailers, and woven baskets. Our enterprise provides supplementary income to 30 farmer families in the Cauvery delta. [Demo Profile]",
            json.dumps(["E-commerce brands", "Food manufacturers", "Logistics providers"]),
            json.dumps(["Natural Fibers", "Eco Packaging", "Rural Innovation"]),
            "https://cauveryecoweaves.example.com", "+91 98765 44556",
            1
        ),
        # Community Members (2 accounts for testing customer & partner workflows)
        (
            "vikram-aditya", "Vikram Aditya", "vikram@udyamsetu.in", default_hash,
            "community", "", "", "New Delhi, Delhi",
            "Delhi", "New Delhi", "Connaught Place", "110001", "Barakhamba Road Arcade", "district_state",
            "en", "assets/images/digital_rahul.jpg",
            "Curator supporting authentic rural artisanal and agricultural goods. [Demo Profile]",
            "Retail curation and sustainable retail advisory for urban organic stores.",
            "Passionate about linking conscious urban consumers with verified grassroots artisans and organic farmer producer companies across India. [Demo Profile]",
            json.dumps(["Organic foods", "Terracotta crafts", "Handlooms"]),
            json.dumps(["Retail Merchandising", "Product Curation", "Quality Assessment"]),
            "https://curatedindia.example.com", "+91 98765 66554",
            0
        ),
        (
            "pooja-deshmukh", "Pooja Deshmukh", "pooja@udyamsetu.in", default_hash,
            "community", "", "", "Pune, Maharashtra",
            "Maharashtra", "Pune", "Shivajinagar", "411038", "FC Road Garden Square", "district_state",
            "en", "assets/images/meera_patil.jpg",
            "Enthusiast for chemical-free farm produce and traditional recipes. [Demo Profile]",
            "Conscious consumer interested in small-batch spices, raw honey, and eco-packaging.",
            "Active community supporter exploring sustainable direct-from-farm ingredients and zero-waste packaging solutions for everyday household use. [Demo Profile]",
            json.dumps(["Cold-pressed oils", "Raw honey", "Biodegradable packaging"]),
            json.dumps(["Community Organizing", "Consumer Advocacy", "Recipe Testing"]),
            "https://sustainableliving.example.com", "+91 98765 77665",
            0
        )
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO users (
        user_id, name, email, password_hash, account_type, business_name, category, location,
        state, district, subdistrict_or_town, pincode, address_landmark, location_display_preference,
        preferred_language, avatar, quote, description, full_story, looking_for, skills, website, phone, verified
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users)

    # Products (2 to 3 realistic products per entrepreneur)
    products = [
        # Asha Devi
        ("asha-devi", "Handwoven Moonj Baskets (Set of 3)", "₹850", "assets/images/hero_entrepreneur.jpg"),
        ("asha-devi", "Terracotta Hand-Painted Planters", "₹450", "assets/images/potter_artisan.jpg"),
        ("asha-devi", "Natural Jute & Moonj Utility Tote", "₹620", "assets/images/village_journey.jpg"),
        # Ramesh Kumar
        ("ramesh-kumar", "Malnad Green Cardamom 8mm (250g)", "₹750", "assets/images/packaging_spices.jpg"),
        ("ramesh-kumar", "Whole Tellicherry Black Pepper (500g)", "₹380", "assets/images/packaging_spices.jpg"),
        ("ramesh-kumar", "High-Curcumin Lakadong Turmeric (250g)", "₹190", "assets/images/packaging_spices.jpg"),
        # Meera Patil
        ("meera-patil", "Kolhapuri Special Kanda Lasun Masala (500g)", "₹240", "assets/images/meera_patil.jpg"),
        ("meera-patil", "Roasted Poha Chivda Snack Jar (400g)", "₹160", "assets/images/packaging_spices.jpg"),
        ("meera-patil", "Ragi & Organic Jaggery Ladoos (Box of 12)", "₹290", "assets/images/packaging_spices.jpg"),
        # Rahul Sharma
        ("rahul-sharma", "Mobile Product Photography & Catalog Pack", "₹2,500", "assets/images/phone_photography.jpg"),
        ("rahul-sharma", "WhatsApp Business & UPI Store Setup", "₹1,800", "assets/images/digital_rahul.jpg"),
        ("rahul-sharma", "Bilingual Product Label & Packaging Design", "₹1,200", "assets/images/phone_photography.jpg"),
        # Suresh Yadav
        ("suresh-yadav", "Raw Unfiltered Litchi Honey (500g)", "₹340", "assets/images/suresh_yadav.jpg"),
        ("suresh-yadav", "Pure Mustard Blossom Honey (500g)", "₹280", "assets/images/packaging_spices.jpg"),
        ("suresh-yadav", "Artisanal Beeswax Food Wraps (Pack of 3)", "₹320", "assets/images/crafts_banner.jpg"),
        # Ananya Sharma
        ("ananya-sharma", "Handspun Khadi Cotton Stole (Indigo Dye)", "₹750", "assets/images/hero_entrepreneur.jpg"),
        ("ananya-sharma", "Handloom Dabu Print Table Runner", "₹580", "assets/images/village_journey.jpg"),
        ("ananya-sharma", "Vegetable Dye Block-Printed Dupatta", "₹920", "assets/images/crafts_banner.jpg"),
        # Green Harvest
        ("green-harvest", "Organic Desi Chana / Chickpea (1kg)", "₹130", "assets/images/farmer_greenharvest.jpg"),
        ("green-harvest", "Wood-Pressed Yellow Mustard Oil (1L)", "₹240", "assets/images/packaging_spices.jpg"),
        ("green-harvest", "Stone-Ground Sharbati Wheat Flour (5kg)", "₹320", "assets/images/farmer_greenharvest.jpg"),
        # Harpreet Singh
        ("harpreet-singh", "Cold-Pressed Flaxseed Alsi Oil (500ml)", "₹280", "assets/images/packaging_spices.jpg"),
        ("harpreet-singh", "Traditional Jaggery Gur Cubes (1kg)", "₹140", "assets/images/packaging_spices.jpg"),
        ("harpreet-singh", "Aromatic Heritage Dehraduni Basmati (2kg)", "₹360", "assets/images/farmer_portrait.jpg"),
        # Deepak Kumhar
        ("deepak-kumhar", "Natural Terracotta Water Dispenser (4L)", "₹650", "assets/images/potter_artisan.jpg"),
        ("deepak-kumhar", "Handcrafted Clay Curd Setting Handi", "₹280", "assets/images/potter_artisan.jpg"),
        ("deepak-kumhar", "Painted Kutch Clay Tea Kulhads (Set of 6)", "₹390", "assets/images/crafts_banner.jpg"),
        # Lakshmi Narayan
        ("lakshmi-narayan", "Biodegradable Banana Fiber Courier Mailers (50 pcs)", "₹600", "assets/images/crafts_banner.jpg"),
        ("lakshmi-narayan", "Handwoven Korai Grass Picnic Basket", "₹520", "assets/images/hero_entrepreneur.jpg"),
        ("lakshmi-narayan", "Upcycled Banana Fiber Gift Sleeves (Pack of 20)", "₹350", "assets/images/packaging_spices.jpg")
    ]
    cursor.executemany("""
    INSERT INTO products (user_id, name, price, image) VALUES (?, ?, ?, ?)
    """, products)

    # Feed Posts (15 distinct posts across 9 authors)
    posts = [
        (
            "meera-patil",
            "We are looking for a reliable collaborator who can provide biodegradable, moisture-resistant pouch packaging with custom printed labels for our roasted millet snacks. Any leads welcome! [Demo Post]",
            "opportunity", "Packaging", 7, 3
        ),
        (
            "ramesh-kumar",
            "How do you find customers outside your district? We produce organic turmeric and other spices. Most sales are currently local. How have fellow rural entrepreneurs expanded interstate? [Demo Post]",
            "question", "Market Access", 9, 4
        ),
        (
            "asha-devi",
            "Proud to announce our artisan collective just dispatched 300 handwoven eco-friendly moonj baskets for a heritage homestay chain! Big thanks to our fellow members who guided us on moisture-barrier packaging. [Demo Post]",
            "story", "Artisan Success", 21, 5
        ),
        (
            "rahul-sharma",
            "Offering pro-bono product photography review for any local entrepreneur looking to improve their smartphone photo quality for WhatsApp catalogs. Drop a comment below! [Demo Post]",
            "opportunity", "Digital Services", 12, 2
        ),
        (
            "suresh-yadav",
            "What is the most economical way to ship 500g glass jars of raw honey without high transit breakage? We are comparing corrugated fluting vs paper honeycomb wraps. [Demo Post]",
            "question", "Distribution", 8, 3
        ),
        (
            "green-harvest",
            "Completed our seasonal PGS-India group peer review across 35 smallholder farms in Hoshangabad. Soil carbon tests showed an encouraging 18% improvement over last year! [Demo Post]",
            "story", "Organic Farming", 16, 4
        ),
        (
            "harpreet-singh",
            "Installed a traditional wood-pestle cold-press unit (kacchi ghani) in Dasuya today. Running cold-pressed mustard and flaxseed oil without any heating maintains maximum natural antioxidants. [Demo Post]",
            "story", "Agri-Processing", 14, 2
        ),
        (
            "deepak-kumhar",
            "Looking to collaborate with tea and beverage brands who want custom lead-free terracotta kulhads or glazed tasting cups in batches of 200–500. [Demo Post]",
            "opportunity", "Pottery & Crafts", 11, 3
        ),
        (
            "lakshmi-narayan",
            "Instead of burning banana pseudo-stems after harvest, our group has processed 4 tons of agro-waste into strong, water-resistant fiber bags this month. Circular economy in action! [Demo Post]",
            "story", "Sustainability", 19, 4
        ),
        (
            "ananya-sharma",
            "Has anyone experimented with pomegranates and marigold petals from temple waste for fast natural yellow dyes on organic cotton? Would love to exchange dye recipes. [Demo Post]",
            "question", "Natural Dyes", 10, 3
        ),
        (
            "meera-patil",
            "Obtained our expanded FSSAI central registration today for interstate distribution! It took two months of documentation, but following standard SOPs made the audit smooth. [Demo Post]",
            "story", "Food Processing", 15, 2
        ),
        (
            "rahul-sharma",
            "Helped three women weavers in Amer set up QR code payment standees and automated WhatsApp order confirmations. Direct payments without middlemen give immediate confidence! [Demo Post]",
            "story", "Digital Tools", 13, 1
        ),
        (
            "green-harvest",
            "We have harvested 10 quintals of certified organic yellow mustard and chickpea. Open to joint value-addition partnerships with food brands needing bulk certified raw ingredients. [Demo Post]",
            "opportunity", "Joint Venture", 17, 3
        ),
        (
            "suresh-yadav",
            "The litchi bloom in Muzaffarpur orchards this year was abundant. Our bees gathered light floral nectar with a subtle fruity aroma. Testing shows 0% added sugar and perfect moisture. [Demo Post]",
            "story", "Beekeeping", 11, 2
        ),
        (
            "lakshmi-narayan",
            "We have standardized banana-fiber padded courier mailers that replace plastic bubble wrap. Samples available for small business owners shipping fragile crafts or bottled goods! [Demo Post]",
            "opportunity", "Eco-Packaging", 18, 5
        )
    ]
    cursor.executemany("""
    INSERT INTO posts (author_id, content, post_type, tag, likes, comments_count) VALUES (?, ?, ?, ?, ?, ?)
    """, posts)

    # Post Likes (Seeding real likes matching posts)
    post_likes_data = [
        # Post 1 (id=1)
        (1, "rahul-sharma"), (1, "lakshmi-narayan"), (1, "vikram-aditya"), (1, "asha-devi"),
        (1, "green-harvest"), (1, "harpreet-singh"), (1, "pooja-deshmukh"),
        # Post 2 (id=2)
        (2, "asha-devi"), (2, "rahul-sharma"), (2, "meera-patil"), (2, "vikram-aditya"),
        (2, "harpreet-singh"), (2, "deepak-kumhar"), (2, "lakshmi-narayan"), (2, "suresh-yadav"),
        (2, "pooja-deshmukh"),
        # Post 3 (id=3)
        (3, "ramesh-kumar"), (3, "rahul-sharma"), (3, "meera-patil"), (3, "green-harvest"),
        (3, "suresh-yadav"), (3, "ananya-sharma"), (3, "deepak-kumhar"), (3, "lakshmi-narayan"),
        (3, "vikram-aditya"), (3, "pooja-deshmukh"), (3, "harpreet-singh")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO post_likes (post_id, user_id) VALUES (?, ?)
    """, post_likes_data)

    # Collaborations (5 opportunities)
    collabs = [
        (
            "collab-1",
            "Eco-Friendly Pouch Packaging for Traditional Snacks",
            "Need biodegradable, moisture-resistant pouch packaging with custom printed labels.",
            "We currently manufacture over 500 kg of traditional dried snacks and roasted millet items monthly in Satara, Maharashtra. We are looking for a reliable supplier or collaborator who can provide biodegradable, moisture-resistant pouch packaging with custom printed labels that keep shelf life intact.",
            "Food Products", "Seeking Partners", "Packaging", "Maharashtra",
            "meera-patil", "assets/images/packaging_spices.jpg", "2 days ago"
        ),
        (
            "collab-2",
            "Digital Branding & Catalog Photography for Handicraft Artisans",
            "Looking for a digital studio partner to showcase our handwoven crafts online.",
            "Our women's artisan collective creates premium quality moonj and terracotta home decor in Varanasi. We seek a digital marketing and photography collaborator who can run focused online promotions and assist us with Amazon Karigar / ONDC cataloging.",
            "Handicrafts", "Seeking Partners", "Marketing", "Uttar Pradesh",
            "asha-devi", "assets/images/crafts_banner.jpg", "3 days ago"
        ),
        (
            "collab-3",
            "Organic Spice Blends & Joint Value Addition",
            "Looking to collaborate on a premium range of certified organic blended spice packs.",
            "Green Harvest has access to high-grade certified organic chili, coriander, and turmeric in central MP. We want to partner with spice growers or culinary brands to develop export-quality blended masalas with standardized recipes.",
            "Agriculture", "Seeking Partners", "Product Development", "Madhya Pradesh",
            "green-harvest", "assets/images/farmer_greenharvest.jpg", "5 days ago"
        ),
        (
            "collab-4",
            "Bulk Glass Jar Sourcing & Fragile Transit Logistics",
            "Seeking dependable food-grade glass jar suppliers and interstate courier rates.",
            "Looking to connect with packaging vendors who supply 250g and 500g hexagon glass jars at wholesale rates, plus logistics partners offering safe transport with low breakage across eastern India.",
            "Organic Products", "Seeking Partners", "Logistics", "Bihar",
            "suresh-yadav", "assets/images/suresh_yadav.jpg", "1 week ago"
        ),
        (
            "collab-5",
            "Sustainable Agro-Waste Packaging Supply for Artisans",
            "Supplying banana fiber protective sleeves and mailers to craft and food businesses.",
            "Cauvery Eco-Weaves produces standardized banana fiber protective mailers that can replace single-use plastic wraps. We are looking for craft clusters and food producers interested in bulk trials.",
            "Natural Products", "Seeking Partners", "Sustainability", "Tamil Nadu",
            "lakshmi-narayan", "assets/images/crafts_banner.jpg", "1 week ago"
        )
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO collaborations (collab_id, title, subtitle, full_description, category, collab_type, tag, location, author_id, thumb, time_ago)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, collabs)

    # Collaboration Requests (Mix of pending, accepted, rejected)
    collab_requests = [
        ("collab-1", "rahul-sharma", "meera-patil", "Hello Meera ji, I can help connect your snack brand with sustainable kraft-paper pouch makers in Jaipur.", "pending"),
        ("collab-2", "rahul-sharma", "asha-devi", "Namaste Asha ji! I would love to assist your artisan collective with smartphone photography training and Amazon Karigar catalog setup.", "accepted"),
        ("collab-3", "ramesh-kumar", "green-harvest", "Namaste, we produce Western Ghats black pepper and cardamom. We could combine our spices with your organic pulses for premium combo packs.", "accepted"),
        ("collab-4", "deepak-kumhar", "suresh-yadav", "Greetings! Have you considered glazed stoneware clay jars as an eco-alternative to glass for your honey? I can share a sample prototype.", "rejected")
    ]
    cursor.executemany("""
    INSERT INTO collaboration_requests (collab_id, sender_id, receiver_id, message, status)
    VALUES (?, ?, ?, ?, ?)
    """, collab_requests)

    # Collaborative Projects (for the 2 accepted requests)
    cursor.execute("""
    INSERT INTO collaborative_projects (title, description, category, partner1_id, partner2_id, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Handicrafts Digital Catalog & Karigar Showcase",
        "Joint initiative combining Asha Devi's moonj & terracotta crafts with Rahul Sharma's digital photography and cataloging.",
        "Handicrafts", "asha-devi", "rahul-sharma", "Active"
    ))

    cursor.execute("""
    INSERT INTO collaborative_projects (title, description, category, partner1_id, partner2_id, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Western Ghats & Central India Organic Spice Synergy",
        "Joint value-pack initiative combining Green Harvest certified organic turmeric with Ramesh Kumar's Malnad whole black pepper.",
        "Agriculture", "green-harvest", "ramesh-kumar", "Active"
    ))

    # Discussions (3 community threads)
    discussions = [
        (
            "disc-1", "ramesh-kumar",
            "How do you find customers outside your district?",
            "We produce organic turmeric and other spices. Currently most of our sales are local. I would like to know how other rural entrepreneurs have reached customers in different states. Any advice or experiences would be really helpful!",
            "Question", 6
        ),
        (
            "disc-2", "meera-patil",
            "Best biodegradable packaging materials for shipping food items in monsoon?",
            "With the monsoon approaching, standard kraft paper pouches sometimes absorb moisture during long courier transit. Has anyone found an eco-friendly barrier coating or lining that keeps dry snacks crispy without plastic?",
            "Advice", 8
        ),
        (
            "disc-3", "deepak-kumhar",
            "How to set fair prices when expanding from village haats to online stores?",
            "In our village weekly haat, we sell clay cookware at very low margins because customers are neighbors. When listing online or supplying urban shops, courier costs and breakages must be factored in. How do fellow makers calculate a fair pricing formula?",
            "Question", 11
        )
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO discussions (disc_id, author_id, title, body, tag, likes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, discussions)

    # Comments across the 3 discussions
    comments = [
        # Discussion 1
        (
            "disc-1", "asha-devi",
            "Namaste Ramesh ji. We faced the exact same barrier when expanding our handloom bags! What unlocked interstate buyers was participating in state government SARAS artisan melas in state capitals, plus registering with India Post Business Parcel service for reliable and cheap parcel transit.",
            "2 hours ago"
        ),
        (
            "disc-1", "rahul-sharma",
            "Setting up a WhatsApp Business catalog with direct UPI payment links is step one. Also, look into ONDC (Open Network for Digital Commerce) through seller apps like Mystore. It connects your turmeric directly to buyers in Delhi and Mumbai with zero commission overhead.",
            "1 hour ago"
        ),
        (
            "disc-1", "meera-patil",
            "Try sending sample sampler packages of your organic turmeric directly to organic grocery owners in Pune and Bengaluru. Once they taste genuine farm quality, they place recurring monthly bulk orders.",
            "35 mins ago"
        ),
        # Discussion 2
        (
            "disc-2", "lakshmi-narayan",
            "Meera ji, we use a cassava and cornstarch bio-film layer inside banana fiber paper. It holds up well against 85% relative humidity for over 45 days. Happy to send you a test swatch to Satara.",
            "3 hours ago"
        ),
        (
            "disc-2", "suresh-yadav",
            "We had a similar issue with honey label dampness in Muzaffarpur. Switching to soy-ink on water-resistant recycled stone paper solved it completely.",
            "1 hour ago"
        ),
        # Discussion 3
        (
            "disc-3", "asha-devi",
            "Deepak ji, we follow a simple formula: (Material cost + Fair daily artisan wage) × 1.35 for overheads & packaging, plus actual shipping. Urban buyers appreciate transparent fair-trade pricing.",
            "4 hours ago"
        ),
        (
            "disc-3", "vikram-aditya",
            "As an urban retail curator, I always advise makers not to underprice their craft! Urban customers will happily pay for authentic, lead-free handmade quality if the artisan story is clear.",
            "2 hours ago"
        ),
        (
            "disc-3", "rahul-sharma",
            "Bundle products into gift sets of 2 or 3 items. It increases the average order value and absorbs the fixed shipping cost much better.",
            "45 mins ago"
        )
    ]
    cursor.executemany("""
    INSERT INTO comments (disc_id, author_id, text, time_ago) VALUES (?, ?, ?, ?)
    """, comments)

    # Articles (Learn & Share)
    articles = [
        (
            "art-1", "Success Stories",
            "How we expanded our customer base through online marketplaces",
            "meera-patil", "June 10, 2024", "assets/images/packaging_spices.jpg",
            "A step-by-step account of taking a home kitchen enterprise from selling 20 jars a week locally to dispatching 400+ food packages a month across three states.",
            json.dumps([
                "Start with small test orders to understand shipping time and shelf stability.",
                "Collect direct customer feedback on WhatsApp to iterate packaging quickly.",
                "Form local partnerships with fellow artisans to share courier shipment costs."
            ])
        ),
        (
            "art-2", "How-To Guides",
            "Simple ways to take better product photos using your phone",
            "rahul-sharma", "June 8, 2024", "assets/images/phone_photography.jpg",
            "You don't need an expensive camera to showcase your crafts. Learn how to use morning window light, simple white background charts, and basic camera angles to make your products stand out.",
            json.dumps([
                "Always shoot in indirect morning daylight near a north-facing window.",
                "Use a clean white chart paper as an infinity curve background.",
                "Keep camera lens clean and shoot from eye level of the product."
            ])
        ),
        (
            "art-3", "Success Stories",
            "Our journey from a small village business to national markets",
            "asha-devi", "June 5, 2024", "assets/images/village_journey.jpg",
            "How an initiative starting with five neighborhood women grew into a self-reliant artisan collective recognized at national craft melas.",
            json.dumps([
                "Standardize quality controls across all artisan batches.",
                "Maintain transparent ledger books for member dividend sharing.",
                "Tell the artisan story behind every handcrafted product tag."
            ])
        ),
        (
            "art-4", "Business Tips",
            "Packaging essentials: protecting fragile craft goods in transit",
            "suresh-yadav", "May 25, 2024", "assets/images/hero_entrepreneur.jpg",
            "Practical techniques using corrugated fluting, shredded recycled paper, and honeycomb sleeves to minimize transit breakage.",
            json.dumps([
                "Double-box fragile glass and terracotta items.",
                "Use biodegradable shredded paper as shock absorber.",
                "Mark packages clearly with bilingual 'Handle with Care' labels."
            ])
        ),
        (
            "art-5", "Industry Insights",
            "Understanding organic certification for smallholder farmers",
            "green-harvest", "May 18, 2024", "assets/images/farmer_greenharvest.jpg",
            "A plain-language breakdown of PGS-India and Jaivik Bharat certifications, cluster group guarantees, and timeline expectations.",
            json.dumps([
                "Form a local PGS peer-review group with 5+ farmers.",
                "Document organic input preparation records religiously.",
                "Transition periods take 2-3 seasons before full certified status."
            ])
        )
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO articles (article_id, category, title, author_id, date_str, image, summary, lessons)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, articles)

    # Connections between demo users
    connections = [
        ("asha-devi", "ramesh-kumar", "connected"),
        ("asha-devi", "rahul-sharma", "connected"),
        ("meera-patil", "ramesh-kumar", "connected"),
        ("meera-patil", "lakshmi-narayan", "connected"),
        ("green-harvest", "ramesh-kumar", "connected"),
        ("ananya-sharma", "asha-devi", "connected"),
        ("deepak-kumhar", "asha-devi", "connected")
    ]
    cursor.executemany("""
    INSERT OR IGNORE INTO connections (user_id_1, user_id_2, status) VALUES (?, ?, ?)
    """, connections)

    conn.commit()
    print("ThriveHub SQLite Database initialized and seeded successfully.")

def print_database_counts():
    """Prints a detailed count of all database entities."""
    conn = get_db()
    cursor = conn.cursor()
    tables = [
        "users", "products", "posts", "post_likes", "collaborations",
        "collaboration_requests", "collaborative_projects", "conversations",
        "conversation_participants", "messages", "notifications",
        "discussions", "comments", "articles", "connections"
    ]
    print("\n--- Current ThriveHub Database Entity Counts ---")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"  {table:28}: {count}")
        except Exception as e:
            print(f"  {table:28}: Error ({e})")
    conn.close()

if __name__ == "__main__":
    if "--backup" in sys.argv:
        backup_file = backup_db()
        print(f"Database backed up to: {backup_file}")
    elif "--reset" in sys.argv:
        print(f"Resetting and reseeding development database at {get_db_path()}...")
        # Create timestamped backup first
        backup_file = backup_db()
        if backup_file:
            print(f"Created safety backup at: {backup_file}")
        init_db(reset=True)
        print_database_counts()
    else:
        # Default run: ensure schema exists and seed if empty
        init_db(reset=False)
        print_database_counts()
