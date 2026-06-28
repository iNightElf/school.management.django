# Parent Portal

A Progressive Web App (PWA) for parents to track their children's attendance, fees, and results, with push notifications.

---

## Architecture

```
parents/                  ← Django app
  models.py               ← ParentStudentLink, PushSubscription, NotificationLog, Announcement
  views.py                ← API endpoints
  services.py             ← notify() + notify_parents_of_student() + notify_all_parents()
  admin.py                ← Admin inlines + model admins
  urls.py                 ← Route definitions
  permissions.py          ← IsParentOfStudent

client/src/pages/parents/ ← React pages
  ParentLayout.tsx        ← Dedicated layout + bottom nav
  ParentDashboard.tsx     ← Student cards + recent announcements
  ParentAttendance.tsx    ← Monthly calendar
  ParentFees.tsx          ← Due/paid/balance
  ParentResults.tsx       ← Subject marks per term
  ParentAnnouncements.tsx ← Full announcement list

client/public/sw.js       ← Extended for push + offline caching
client/src/lib/usePushSubscription.ts  ← Auto-subscribe hook
```

---

## Backend Models

### `ParentStudentLink`
| Field | Type | Notes |
|-------|------|-------|
| `parent` | FK → User | `limit_choices_to={'role': 'parent'}` |
| `student` | FK → Student | |
| `created_at` | DateTime | auto |

Unique constraint on `(parent, student)`.

### `PushSubscription`
| Field | Type |
|-------|------|
| `user` | FK → User |
| `endpoint` | URL (max 500) |
| `p256dh_key` | Char(256) |
| `auth_key` | Char(64) |
| `user_agent` | Char(500) |
| `created_at` | DateTime |

### `NotificationLog`
| Field | Type |
|-------|------|
| `user` | FK → User |
| `event_type` | Char(30): `attendance_marked`, `fee_received`, `result_published`, `announcement` |
| `title` | Char(255) |
| `body` | Text |
| `payload` | JSON |
| `sent_at` | DateTime |
| `error` | Text (nullable) |

### `Announcement`
| Field | Type |
|-------|------|
| `author` | FK → User (nullable, SET_NULL) |
| `title` | Char(255) |
| `body` | Text |
| `created_at` | DateTime |

Ordered by `-created_at`.

---

## API Endpoints

| Endpoint | Method | Auth | Returns |
|----------|--------|------|---------|
| `/api/parents/my-students/` | GET | Parent | Linked students (id, studentId, name, roll, klass, session) |
| `/api/parents/attendance/{id}/` | GET | Parent | Monthly calendar with per-day status |
| `/api/parents/fees/{id}/` | GET | Parent | totalDue, totalPaid, balance, schedules[] |
| `/api/parents/results/{id}/` | GET | Parent | Subject marks by term |
| `/api/parents/announcements/` | GET | Any auth'd | Latest 20 announcements |
| `/api/parents/announcements/` | POST | Admin | Create + push to all parents |
| `/api/parents/push/subscribe/` | POST | Any auth'd | Store push subscription |
| `/api/parents/push/subscribe/` | DELETE | Any auth'd | Remove subscription |
| `/api/parents/push/vapid-key/` | GET | Public | VAPID public key |

### Query Parameters

**Attendance:** `?year=2026&month=6` (defaults to current month)
**Results:** `?session=2025-2026&term=1`

---

## Push Notifications

### Triggers

| Event | Source | Title |
|-------|--------|-------|
| Student marked absent | `attendance/views.py:batch` | "{name} was marked absent" |
| Result published | `results/views.py:perform_create` | "{name} — {term} results published" |
| Fee payment received | `finance/services/transaction_service.py` | "Payment received for {name}" |
| Admin creates announcement | `AnnouncementAdmin:save_model` | Announcement title |

### Delivery

1. `notify_parents_of_student()` — finds all parent users linked to a student, sends push, logs to `NotificationLog`
2. `notify_all_parents()` — sends to every user with `role='parent'`
3. `notify()` — iterates `PushSubscription` records for a user, sends via `pywebpush` (Web Push API with VAPID)
4. Expired subscriptions (HTTP 410) are auto-deleted
5. Every attempt is logged in `NotificationLog` with success/error

### Service Worker

- **`push` event:** Parse payload → `showNotification(title, body, icon, data.url)`
- **`notificationclick` event:** Close notification → focus existing tab or open new window at the deep-link URL
- **API caching:** `/api/parents/*` requests use stale-while-revalidate in `parent-cache-v1`

---

## Frontend Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/parent` | ParentDashboard | Student cards + recent announcements |
| `/parent/attendance` | ParentAttendance | Student selector |
| `/parent/attendance/:studentId` | ParentAttendance | Monthly calendar |
| `/parent/fees` | ParentFees | Student selector |
| `/parent/fees/:studentId` | ParentFees | Due/paid/balance |
| `/parent/results` | ParentResults | Student selector |
| `/parent/results/:studentId` | ParentResults | Subject marks |
| `/parent/announcements` | ParentAnnouncements | Full list |

All routes gated by `user.role === 'parent'`. Staff users are redirected away from `/parent/*`. Parent users are redirected away from staff routes.

### ParentLayout

- Header: Logo + "Parent Portal" + username + logout
- Bottom nav (mobile): Home | Attendance | Fees | Results | Updates
- Calls `usePushSubscription()` on mount to auto-subscribe to push

---

## Admin Workflow

1. **Create parent account:** Django Admin → Users → Add user → role = `Parent`
2. **Link students:** Edit parent user → "Parent-student links" inline → add students
3. **Post announcements:** Django Admin → Announcements → Add → title + body → Save
   - Saves auto-sets author and triggers push to all parents

---

## VAPID Keys

Generated once, added to `.env`:

```
VAPID_PUBLIC_KEY=<base64url-encoded-public-key>
VAPID_PRIVATE_KEY=<base64url-encoded-private-key>
VAPID_CLAIM_EMAIL=admin@alrawa.edu
```

Generate with:
```python
python -c "
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from base64 import urlsafe_b64encode
k = ec.generate_private_key(ec.SECP256R1())
pub = k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
priv = k.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
def b64url(b): return urlsafe_b64encode(b).rstrip(b'=').decode()
print('VAPID_PRIVATE_KEY=' + b64url(priv))
print('VAPID_PUBLIC_KEY=' + b64url(pub))
"
```

---

## Dependencies

- **Backend:** `pywebpush==2.3.0` (Web Push with VAPID)
- **Frontend:** none beyond existing (lucide-react icons, zustand store, API client)

---

## Build Order (as implemented)

| Phase | What | Files |
|-------|------|-------|
| 1 | `parent` role + `ParentStudentLink` + admin linking UI | `parents/models.py`, `parents/admin.py`, `accounts/models.py` |
| 2 | Read-only API endpoints | `parents/views.py`, `parents/urls.py`, `parents/permissions.py`, `parents/serializers.py` |
| 3 | Parent UI pages | `ParentLayout.tsx`, `ParentDashboard.tsx`, `ParentAttendance.tsx`, `ParentFees.tsx`, `ParentResults.tsx` |
| 4 | PWA push infrastructure | `PushSubscription` model, `sw.js` push handler, `usePushSubscription.ts` hook |
| 5 | Notification triggers + logging | `NotificationLog` model, `parents/services.py`, notify calls in attendance/result/finance views |
| 6 | Offline API caching | `parent-cache-v1` in `sw.js` (stale-while-revalidate) |
| 7 | Announcements | `Announcement` model + admin + API + frontend page |
