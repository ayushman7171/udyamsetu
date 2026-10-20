# ThriveHub

> **People · Opportunities · Growth**  
> A dedicated networking and collaboration platform designed for entrepreneurs, artisans, and grassroots producers, artisans, and grassroots producers.

---

## 🎨 Visual Reference & Design System

The platform includes 9 responsive screens:
1. **Home / Landing Page** (`index.html`) — Hero section, rural artisan imagery, and 4 core value proposition feature cards.
2. **Register & Login** (`register.html`) — Secure authentication form with business fields, password hashing, and clean mode toggle.
3. **Dashboard & Community Feed** (`dashboard.html`) — 3-column feed with sidebar navigation, interactive share box, categorized post feed (opportunities, questions, stories), like counters, and suggested entrepreneurs.
4. **Entrepreneurs Directory** (`directory.html`) — Live search and faceted filters (by Industry and Location) backed by SQLite queries.
5. **Entrepreneur Profile** (`profile.html`) — Panoramic artisan workshop banner, verified avatar, bio, products catalog with dynamic owner edit/add product modals, and tabs for About, Products, Collaboration Interests, and Social Links.
6. **Collaboration Opportunities** (`collaborations.html`) — Partnership cards with badges, "+ Create Collaboration" action, "My Requests" tab with Accept/Decline management, and "Joint Projects" listing.
7. **Create Collaboration** (`create-collaboration.html`) — Opportunity posting form saved into SQLite.
8. **Community Discussion** (`discussion.html`) — Dedicated thread view with active comment submission and peer replies.
9. **Learn & Share** (`learn.html`) — 3-column resource library with category filter pills and interactive article reader modals.
10. **Messages & Collaboration Chats** (`messages.html`) — Real-time database-backed 2-column chat with direct messaging, collaboration project chats, search, read receipts, and abuse protection.

---

## 🚀 Running the Application Locally

### 1. Requirements
- Python 3.8+
- Flask & Werkzeug (installed in standard Python environment)

### 2. Run the Server
```bash
python app.py
```
Open **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)** in your browser.

### 3. Reset & Re-Seed Database (Optional)
To reset the SQLite database (`udyamsetu.db`) with fresh seed accounts, collaborations, and sample messages:
```bash
python database.py
```

### 4. Run Automated Test Suite
To execute the comprehensive automated test suite covering all 23 authentication, authorization, profile, location, and messaging workflows:
```bash
python test_backend.py
```

---

## 📁 Project Structure

```
├── app.py                     # Main Flask application & REST API endpoints
├── auth.py                    # Password hashing, session helpers & @login_required decorator
├── database.py                # SQLite schema definition, connection helpers & seed data
├── locations.py               # Complete Indian States & Districts dataset and PIN validator
├── test_backend.py            # Automated test suite (23 tests covering all workflows)
├── verify_all.py              # End-to-end live server integration verification suite
├── udyamsetu.db               # SQLite database file
├── index.html                 # 1. Landing Page
├── register.html              # 2. Registration and Login (with business details & alert banners)
├── profile-setup.html         # 3. Entrepreneur Onboarding & Business Profile Setup
├── dashboard.html             # 4. Community Feed & Dashboard
├── directory.html             # 5. Entrepreneur Directory
├── profile.html               # 6. Dynamic Profile View & Editor
├── collaborations.html        # 7. Collaboration Opportunities & Request Management
├── create-collaboration.html  # 8. Create Collaboration Form
├── discussion.html            # 9. Community Discussion
├── learn.html                 # 10. Learn & Share Resource Library
├── messages.html              # 11. Real-Time Database-Backed Messaging
├── css/
│   └── style.css              # Design system, responsive layout, chat bubbles & modal styles
├── js/
│   ├── data.js                # Fallback reference data
│   └── main.js                # Auth session, dynamic nav, messaging polling & SQLite APIs
└── assets/
    └── images/                # High-fidelity rural entrepreneur & craft photography
```

---

## 🔌 Backend Architecture & REST API Endpoints

### 1. Database Schema (`udyamsetu.db`)
- **`users`**: Rural entrepreneur & community member accounts with password hashes, roles, locations, PIN codes, bios, and privacy settings.
- **`products`**: Product showcase items linked to entrepreneurs with pricing and images.
- **`posts`**: Community feed updates, opportunities, questions, and stories.
- **`post_likes`**: Tracks unique post likes per user.
- **`collaborations`**: Collaboration opportunities authored by entrepreneurs.
- **`collaboration_requests`**: Proposals sent between users with status tracking.
- **`collaborative_projects`**: Joint projects formed when collaboration requests are accepted.
- **`conversations`**: Direct and collaboration-linked conversations with unique pair keys.
- **`conversation_participants`**: Participant mapping with join time, role, and `last_read_at` read tracking.
- **`messages`**: Individual messages with body, sender ID, message type, and timestamps.
- **`user_blocks`**: User blocking records for abuse prevention.
- **`discussions` & `comments`**: Knowledge exchange threads and peer comments.
- **`articles`**: Guides and success stories with key lessons.
- **`connections`**: Tracks network connections between members.

### 2. Implemented REST API Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/me` | Current authenticated user's account info or unauthenticated status | No |
| `POST` | `/api/register` | Register new user with name, email, password, and account type | No |
| `POST` | `/api/login` | Authenticate existing user with email and password | No |
| `POST` | `/api/logout` | Clears user session | Yes |
| `GET` | `/api/profile` | Retrieve authenticated user's full profile with products and requests | Yes |
| `POST` / `PUT` | `/api/profile` | Update authenticated user's profile information | Yes |
| `POST` | `/api/profile/products` | Add a new product to authenticated user's catalog | Yes (Entrepreneur) |
| `DELETE` | `/api/profile/products/<id>` | Remove a product owned by authenticated user | Yes |
| `GET` | `/api/locations` | Retrieve complete Indian States & mapped districts dataset | No |
| `GET` | `/api/entrepreneurs` | List, search, and filter public entrepreneur profiles | No |
| `GET` | `/api/entrepreneurs/<id>` | Retrieve public profile, products, and collabs for an entrepreneur | No |
| `GET` | `/api/feed` | Retrieve community feed posts (filter by `type`) | No |
| `POST` | `/api/feed` | Create community post (authored by authenticated user) | Yes |
| `POST` | `/api/posts/<id>/like` | Toggle like counter for a post | Yes |
| `GET` | `/api/collaborations` | List collaboration opportunities | No |
| `POST` | `/api/collaborations` | Create new collaboration opportunity | Yes (Entrepreneur) |
| `POST` | `/api/collaborations/request` | Send collaboration proposal to an entrepreneur | Yes |
| `GET` | `/api/collaborations/requests` | List received and sent requests for authenticated user | Yes |
| `POST` | `/api/collaborations/requests/<id>/respond` | Accept or reject received collaboration request and spawn project chat | Yes |
| `GET` | `/api/collaborations/projects` | List active collaborative projects | No |
| `GET` | `/api/conversations` | List user's conversations with latest message, unread count & participants | Yes |
| `POST` | `/api/conversations` | Create or retrieve authorized direct or collaboration conversation | Yes |
| `GET` | `/api/conversations/<id>/messages` | Retrieve paginated chronological message history for conversation | Yes |
| `POST` | `/api/conversations/<id>/messages` | Send message (rate-limited, validated, sender-verified) | Yes |
| `POST` | `/api/conversations/<id>/read` | Mark all messages in conversation as read for current user | Yes |
| `GET` | `/api/conversations/unread-count` | Total unread message count across all conversations | Yes |
| `POST` | `/api/users/<id>/block` | Block a user, preventing further messaging | Yes |
| `POST` | `/api/users/<id>/unblock` | Unblock a previously blocked user | Yes |
| `GET` | `/api/users/<id>/block-status` | Check mutual blocking status with target user | Yes |
| `GET` | `/api/discussions/<id>` | Load discussion thread and peer comments | No |
| `POST` | `/api/discussions/<id>/comment` | Add reply to discussion | Yes |
| `GET` | `/api/articles` | Retrieve resource articles by category | No |
| `POST` | `/api/connect` | Toggle network connection with another entrepreneur | Yes |
| `GET` | `/api/connections` | List network connections for authenticated user | Yes |

---

## 🔒 Demo Seed Accounts

All seed accounts are initialized with password: `password123`
- `asha@udyamsetu.in` (Asha Devi — Handicrafts, UP)
- `ananya@udyamsetu.in` (Ananya Sharma — Agri-Tech & Handlooms, Rajasthan)
- `contact@greenharvest.in` (Green Harvest — Agriculture, MP)
- `rahul@udyamsetu.in` (Rahul Sharma — Digital Services, Rajasthan)
- `meera@udyamsetu.in` (Meera Patil — Homemade Food Products, Maharashtra)
- `suresh@udyamsetu.in` (Suresh Yadav — Organic Products, Bihar)
- `ramesh@udyamsetu.in` (Ramesh Kumar — Agriculture, Karnataka)

---

## 🌟 Advanced Features & Multi-Phase Enhancements

### 1. Account Types & Role-Based Access (Phase 1 & 2)
- **Account Types**:
  - `entrepreneur`: Can manage a business profile, showcase products, and post collaboration opportunities.
  - `community_member`: Can browse public profiles, read community posts, participate in discussions, and propose collaborations to entrepreneurs.
- **Onboarding Flow**:
  - Registration collects only core account details (`name`, `email`, `password`, `confirm_password`, `account_type`).
  - Entrepreneurs are seamlessly routed to `/profile-setup.html` to enter their business and location details.
  - Community members enter directly to `/dashboard.html` without business form fields.
- **Clean Profile Initialization**:
  - New accounts are initialized with empty strings/sensible placeholders. No fabricated bios, quotes, taglines, or products are generated.
  - Server-side role checks (`@role_required("entrepreneur")`) restrict product catalog creation and collaboration posting to verified entrepreneurs.

### 2. Comprehensive Indian Location Dataset & Privacy Controls (Phase 3)
- **Location Dataset** (`locations.py`):
  - Pre-populated coverage of all 28 Indian States & Union Territories with mapped districts.
  - API endpoints: `/api/locations`, `/api/locations/states`, `/api/locations/districts?state=<State>`.
- **Validation**:
  - Validates selected State and District on the backend.
  - Validates 6-digit Indian PIN codes using regex (`^[1-9][0-9]{5}$`).
- **Granular Location Privacy**:
  - Detailed address and PIN codes are stored privately and never exposed on public entrepreneur profile endpoints or directories.
  - Users select their `location_display_preference`:
    - `district_state` (e.g., "Satara, Maharashtra") [Recommended]
    - `state_only` (e.g., "Maharashtra")
    - `town_district` (e.g., "Wai, Satara")
- **Directory Search & Filtering**:
  - Search and filter entrepreneurs by State and District across `/directory.html`.

### 3. Security Hardening & Rate Limiting (Phase 4)
- **Password Security**: Minimum 8 characters with strength scoring and confirmation match validation.
- **Session Security**: Session cookies configured with `HttpOnly`, `SameSite=Lax`, and unique session cookie naming.
- **CSRF Protection**:
  - Server generates session-bound CSRF tokens via `/api/csrf-token` and validates double-submit tokens on all state-changing endpoints (`POST`, `PUT`, `DELETE`).
  - Frontend (`main.js`) automatically attaches `X-CSRF-Token` headers to requests.
- **Sliding-Window Rate Limiting**:
  - IP-based sliding window rate limiter protects sensitive endpoints (`/api/login`, `/api/register`, `/api/profile`, `/api/conversations`).
  - Exceeded thresholds return HTTP `429 Too Many Requests` with retry headers and informative error payloads.
  - *Note: Application-level rate limiting prevents brute-force credential stuffing and script spam; infrastructure-level volumetric DDoS mitigation should be configured via reverse proxy / CDN.*

### 4. Database-Backed Real-Time Messaging & Collaboration Chats (Phase 2)
- **Database Schema**:
  - `conversations`: Direct conversations with canonical `direct_key` (`direct:{min_uid}:{max_uid}`) and project-backed conversations with unique `project_id`.
  - `conversation_participants`: Tracks membership, roles, and `last_read_at` for individual read status.
  - `messages`: Chronological message records with sender ID, body, type (`text` vs `system`), and creation timestamps.
  - `user_blocks`: Persistent mutual blocking for abuse prevention.
- **Server-Side Authorization**:
  - Participant verification on every messaging endpoint (`GET` / `POST` / `read`).
  - Sender ID is strictly bound to the authenticated session (`session["user_id"]`), eliminating spoofing risks.
  - Non-participants receive `HTTP 403 Forbidden`.
  - Blocked users cannot message or initiate conversations (`HTTP 403 Forbidden`).
- **Message Validation & Rate Limiting**:
  - Enforces non-empty message bodies and 2,000 character maximum length.
  - Sliding-window rate limit (40 messages/minute, 20 new conversation starts/10 minutes).
- **Collaboration Lifecycle Integration**:
  - When a collaboration proposal is accepted, a joint project conversation is automatically generated for both authorized partners.
  - Idempotent: repeated accept actions reuse the existing project conversation without duplicate records.
- **Frontend Chat UI (`messages.html`)**:
  - Responsive 2-column layout matching the blue and cream theme (`#18639C` / `#FAF7F2`).
  - Filter tabs (`All`, `Direct`, `Projects`) and live search filter.
  - Message bubbles distinguishing outgoing (brand blue) vs incoming (white card) messages with timestamps and read checks.
  - Deep linking support (`?user=<user_id>`, `?project=<id>`, `?conversation=<conv_id>`).
  - Direct message button on entrepreneur profiles and "Project Chat" button on joint project cards.
  - Lightweight polling every 3.5s with message ID deduplication to prevent UI flickering.

---

## 🔔 In-App Notification System

ThriveHub includes a database-backed, transactional in-app notification engine:
- **Persistent Storage (`notifications` Table)**:
  - Fields: `id`, `recipient_id`, `actor_id`, `event_type`, `title`, `message`, `reference_type`, `reference_id`, `link_url`, `is_read`, `dedup_key`, `created_at`.
  - Foreign key constraints to `users(user_id)` with cascading deletion.
  - Performance indexes on `(recipient_id, is_read, created_at DESC)` and `(dedup_key)`.
- **Supported Notification Events**:
  - `new_message`: Triggered when an entrepreneur or community member receives a message in a direct or collaboration project chat.
  - `collab_request_received`: Triggered when an entrepreneur receives a partnership proposal from another member.
  - `collab_request_accepted`: Triggered when an entrepreneur accepts a partnership proposal, linking directly to the new project chat.
  - `collab_request_rejected`: Triggered when an entrepreneur declines a partnership proposal.
  - `new_comment`: Triggered when someone comments on a discussion authored by the user.
  - `new_connection`: Triggered when another member connects with the user.
- **Transactional Idempotency**:
  - Notifications are generated within the same database transaction as the triggering event whenever practical.
  - Unique `dedup_key` prevents duplicate notifications when operations (such as collaboration acceptance or message resends) are retried.
- **Strict Privacy & Server-Side Authorization**:
  - Endpoints strictly enforce that users can only view, read, or mutate their own notifications (`recipient_id == session["user_id"]`).
  - Cross-user mutation or access attempts are rejected with `HTTP 403 Forbidden`.
- **API Endpoints**:
  - `GET /api/notifications`: Paginated notifications stream (`limit`, `offset`, `unread`, `type`).
  - `GET /api/notifications/unread-count`: Lightweight polling endpoint returning `{"unread_count": N}`.
  - `POST /api/notifications/<id>/read`: Marks a single notification as read and returns the updated count.
  - `POST /api/notifications/read-all`: Marks all notifications as read for the authenticated user.
  - `DELETE /api/notifications/<id>`: Deletes a notification belonging to the authenticated user.
- **Frontend Components**:
  - **Header Notification Bell**: Dynamic unread counter badge (`#globalNotifBadge`), updating in real-time.
  - **Notification Dropdown**: Quick flyout from the bell icon with unread count pill, "Mark all read" button, filter tabs ("All", "Unread"), timestamp formatting ("Just now", "5m ago"), unread indicators, and instant click-to-navigate.
  - **Dedicated Notifications Page (`notifications.html`)**: Complete activity dashboard with filter pills ("All", "Unread", "Messages", "Partnerships"), "Load More" pagination, and responsive cards.
  - **Background Polling**: Periodic lightweight polling (every 20s) without server overload.

---

## 🌐 Multilingual Support & Localization Engine (i18n)

ThriveHub includes comprehensive multilingual support covering English and all **22 scheduled Indian languages**:
1. **Hindi (`hi`)** — हिन्दी (Complete / Human-reviewed)
2. **Bengali (`bn`)** — বাংলা (Complete / Human-reviewed)
3. **Marathi (`mr`)** — मराठी (Complete / Human-reviewed)
4. **Gujarati (`gu`)** — ગુજરાતી (Complete / Human-reviewed)
5. **Tamil (`ta`)** — தமிழ் (Complete / Human-reviewed)
6. **Telugu (`te`)** — తెలుగు (Complete / Human-reviewed)
7. **Kannada (`kn`)** — ಕನ್ನಡ (Complete / Human-reviewed)
8. **Punjabi (`pa`)** — ਪੰਜਾਬੀ (Complete / Human-reviewed)
9. **Urdu (`ur`)** — اردو (Complete / Human-reviewed, RTL Layout)
10. **English (`en`)** — English (Canonical reference & fallback language)
11. **Odia (`or`)** — ଓଡ଼ିଆ (Partial / Core UI translated)
12. **Malayalam (`ml`)** — മലയാളം (Partial / Core UI translated)
13. **Assamese (`as`)** — অসমীয়া (Partial / Core UI translated)
14. **Maithili (`mai`)** — मैथिली (Partial / Core UI translated)
15. **Sanskrit (`sa`)** — संस्कृतम् (Partial / Core UI translated)
16. **Nepali (`ne`)** — नेपाली (Partial / Core UI translated)
17. **Santali (`sat`)** — ᱥᱟᱱᱛᱟᱲᱤ (Staged awaiting review with English fallback)
18. **Kashmiri (`ks`)** — کٲشُر (Staged awaiting review, RTL Layout)
19. **Sindhi (`sd`)** — سنڌي (Staged awaiting review, RTL Layout)
20. **Konkani (`kok`)** — कोंकणी (Staged awaiting review with English fallback)
21. **Manipuri / Meitei (`mni`)** — ꯃꯤꯇꯩꯂꯣꯟ (Staged awaiting review with English fallback)
22. **Bodo (`br`)** — बड़ो (Staged awaiting review with English fallback)
23. **Dogri (`doi`)** — डोगरी (Staged awaiting review with English fallback)

### Key Architectural Features:
- **Organized Translation Dictionaries (`locales/<lang>.json`)**: Over 225 canonical keys categorized into `nav`, `landing`, `auth`, `dashboard`, `directory`, `profile`, `collab`, `msg`, `notif`, `disc`, `learn`, and `common`.
- **Safe English Fallback**: Any missing key or untranslated string seamlessly falls back to English without crashing or showing blank gaps.
- **Client-Side Engine (`js/i18n.js`)**: Real-time declarative translation using `data-i18n`, `data-i18n-placeholder`, `data-i18n-title`, and `data-i18n-aria` attributes across all 12 platform pages without page reloads or HTML duplication.
- **Language Selector**: Global dropdown in site navigation and registration flow showing native script names alongside English names, with RTL indicator badges.
- **Preference Persistence**: Saved in `localStorage` for guests and synced to `users.preferred_language` in SQLite for authenticated users.
- **Right-to-Left (RTL) Layout**: Dynamic `dir="rtl"` attribute and mirrored CSS stylesheets for Urdu (`ur`), Kashmiri (`ks`), and Sindhi (`sd`).
- **User-Generated Content (UGC) Integrity**: User-authored posts, messages, and business descriptions remain in their original authentic language. An optional `/api/translate` machine-translation preview toggle is provided with explicit disclaimer labeling.
- **Development Audit Endpoint (`GET /api/i18n/audit`)**: Inspects all locale dictionaries in real-time, reporting key count, coverage percentage, and missing keys.

---

## 🧪 Testing & Verification

Run the full automated backend test suite (33 tests covering authentication, roles, location validation, privacy leaks, CSRF, rate limits, messaging permissions, sender spoofing, collaboration chats, and the notification system):
```bash
python test_backend.py
```

Run the end-to-end integration and media verification script (36 passing checks):
```bash
python verify_all.py
```

Run the multilingual and i18n test suite (11 automated tests covering dictionary validity, fallback, RTL flags, preference persistence, and Unicode integrity):
```bash
python test_i18n.py
```

---

## 🗄️ Database Management & Demo Dataset

The ThriveHub development environment uses an SQLite database (`udyamsetu.db`) configured with foreign key enforcement and clean demo data.

### Resetting and Reseeding the Database
To perform a safe reset and reseed with clean demo data:
```bash
python database.py --reset
```
*Note: A timestamped safety backup (e.g. `udyamsetu_backup_YYYYMMDD_HHMMSS.db`) is automatically generated before any reset occurs.*

To create a manual backup at any time:
```bash
python database.py --backup
```

To initialize tables and seed only if empty (idempotent, safe for startup):
```bash
python database.py
```

### Seed Demo Accounts & Credentials
All demo accounts use the standard development password: `password123`

| Name | Role | Email | Category / Industry | Location | Verified Badge |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Asha Devi** | Entrepreneur | `asha@udyamsetu.in` | Handicrafts | Varanasi, Uttar Pradesh | Yes (1) |
| **Ramesh Kumar** | Entrepreneur | `ramesh@udyamsetu.in` | Agriculture | Chikkamagaluru, Karnataka | Yes (1) |
| **Meera Patil** | Entrepreneur | `meera@udyamsetu.in` | Food Products | Satara, Maharashtra | Yes (1) |
| **Rahul Sharma** | Entrepreneur | `rahul@udyamsetu.in` | Digital Services | Jodhpur, Rajasthan | Yes (1) |
| **Suresh Yadav** | Entrepreneur | `suresh@udyamsetu.in` | Organic Products | Muzaffarpur, Bihar | No (0) |
| **Ananya Sharma** | Entrepreneur | `ananya@udyamsetu.in` | Rural Textiles | Jaipur, Rajasthan | Yes (1) |
| **Green Harvest** | Entrepreneur | `contact@greenharvest.in` | Agriculture | Hoshangabad, Madhya Pradesh | Yes (1) |
| **Harpreet Singh** | Entrepreneur | `harpreet@udyamsetu.in` | Agriculture | Hoshiarpur, Punjab | Yes (1) |
| **Deepak Kumhar** | Entrepreneur | `deepak@udyamsetu.in` | Pottery & Crafts | Kutch, Gujarat | No (0) |
| **Lakshmi Narayan** | Entrepreneur | `lakshmi@udyamsetu.in` | Natural Products | Thanjavur, Tamil Nadu | Yes (1) |
| **Vikram Aditya** | Community Member | `vikram@udyamsetu.in` | Retail Curator | New Delhi, Delhi | No (0) |
| **Pooja Deshmukh** | Community Member | `pooja@udyamsetu.in` | Conscious Consumer | Pune, Maharashtra | No (0) |

---

## ⚡ Supabase & Vercel Deployment

ThriveHub is architected with a **dual adapter pattern**:
- **Local Development**: Runs with Flask (`python app.py`) and SQLite (`udyamsetu.db`).
- **Cloud / Production**: Deploys statically to **Vercel** backed by **Supabase Auth** and **Supabase PostgreSQL** via Row Level Security (RLS) and PostgREST.

### 1. Supabase Setup
- SQL migrations are versioned under [`supabase/migrations/`](supabase/migrations/) or combined in [`supabase/full_schema_and_rls.sql`](supabase/full_schema_and_rls.sql).
- In Supabase Dashboard -> **Authentication** -> **Providers** -> **Email**:
  - Enable Email Provider: **ON**
  - Allow new users to sign up: **ON**
  - Confirm email: **OFF** (for instant logins without SMTP limits)
- Run the migration/seeding script:
  ```bash
  python scripts/migrate_sqlite_to_supabase.py
  ```

### 2. Vercel Deployment
1. Push this repository to GitHub.
2. In [Vercel](https://vercel.com), import the repository as a static site.
3. Vercel automatically reads [`vercel.json`](vercel.json) to configure clean routes, headers, and asset caching.

