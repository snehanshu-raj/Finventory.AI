You are a senior full-stack frontend engineer. Your task is to build a complete, 
production-grade frontend application for an AI-powered pantry + personal finance 
manager called "PantryPilot" (or "FInventory"). 

Before writing a single line of code, thoroughly read and internalize ALL THREE 
reference files provided:

  1. api_docs.md       — Every API endpoint, request/response shapes, query params,
                         error codes, dependency flow, and background job schedules
  2. requirements.md   — The full backend domain model, business logic rules,
                         MongoDB collections, inventory status thresholds, and 
                         product goals
  3. gmail_requirements.md — The Gmail OAuth integration, unified expense model,
                              email_expenses collection, and Gmail sync APIs

Do NOT start building until you have read all three files completely. 
Every UI feature you build must map to a real API from api_docs.md.
Do not invent endpoints or fake data — use only what the API provides.

═══════════════════════════════════════════════════════════
TECH STACK
═══════════════════════════════════════════════════════════

Framework        : React 18 with Vite
Language         : TypeScript (strict mode)
Styling          : Tailwind CSS v4
State Management : Zustand (global) + React Query / TanStack Query (server state)
Charts           : Recharts
Routing          : React Router v6
HTTP Client      : Axios with interceptors
Icons            : Lucide React
Animations       : Framer Motion
Notifications    : react-hot-toast
File Upload      : react-dropzone
Forms            : React Hook Form + Zod validation

The app should be a Single Page Application that talks to:
  Base URL: http://localhost:8000

All API calls follow this response envelope:
  Success: { "success": true, "data": {...}, "message": "OK" }
  Error:   { "success": false, "error": { "code": "...", "message": "..." } }

Handle both cases globally with Axios response interceptors.

═══════════════════════════════════════════════════════════
APP ARCHITECTURE
═══════════════════════════════════════════════════════════

src/
├── api/                    # One file per API group
│   ├── users.ts            # POST /onboarding, GET /users/:id, PATCH /staples
│   ├── receipts.ts         # upload, list, detail, review
│   ├── inventory.ts        # list, low-stock, item detail, adjust, reset
│   ├── analytics.ts        # predictions, expenses, best-store, compare, dashboard
│   ├── meals.ts            # POST /meals/suggest
│   ├── shopping.ts         # POST /shopping/suggest
│   ├── notifications.ts    # list, test, dismiss
│   ├── gmail.ts            # connect, status, disconnect, sync, sync-runs
│   └── expenses.ts         # GET /expenses, /expenses/summary, /email-expenses
│
├── components/
│   ├── layout/             # Sidebar, TopBar, MobileNav, PageContainer
│   ├── ui/                 # Button, Card, Badge, Modal, Skeleton, EmptyState
│   ├── charts/             # SpendingChart, CategoryPieChart, InventoryGauge,
│   │                       # RunOutTimeline, PriceCompareChart
│   ├── inventory/          # InventoryGrid, InventoryCard, StatusBadge,
│   │                       # AdjustModal, LowStockAlert
│   ├── receipts/           # ReceiptDropzone, ReceiptCard, ReceiptReviewModal,
│   │                       # OcrConfidenceBadge
│   ├── meals/              # MealCard, MealSuggestionPanel, ConstraintsForm
│   ├── shopping/           # ShoppingListPanel, MustBuyNowRow, BuySoonRow
│   ├── notifications/      # NotificationFeed, NotificationBell, NotificationItem
│   ├── gmail/              # GmailConnectCard, SyncStatusBanner, EmailExpenseRow
│   └── expenses/           # UnifiedExpenseFeed, ExpenseSummaryCards,
│                           # ExpenseSourceFilter
│
├── pages/
│   ├── Onboarding.tsx      # First-run setup wizard
│   ├── Dashboard.tsx       # Main hub — GET /analytics/dashboard
│   ├── Inventory.tsx       # Full pantry view
│   ├── Receipts.tsx        # Upload + history
│   ├── Analytics.tsx       # Spend, predictions, price insights
│   ├── Meals.tsx           # Meal suggestions
│   ├── Shopping.tsx        # Smart shopping list
│   ├── Expenses.tsx        # Unified feed: receipts + Gmail
│   ├── Notifications.tsx   # All alerts
│   └── Settings.tsx        # Gmail OAuth, staple config, preferences
│
├── store/
│   ├── userStore.ts        # userId, profile, onboarding state
│   └── uiStore.ts          # sidebar open, active modal, theme
│
├── hooks/
│   ├── useInventory.ts
│   ├── useReceipts.ts
│   ├── useAnalytics.ts
│   ├── useNotifications.ts
│   ├── useGmail.ts
│   └── useExpenses.ts
│
└── utils/
    ├── formatters.ts        # currency, date, quantity+unit display
    ├── statusColors.ts      # ok→green, low→yellow, critical→orange, out→red
    └── constants.ts

═══════════════════════════════════════════════════════════
DESIGN SYSTEM
═══════════════════════════════════════════════════════════

Theme       : Dark mode primary (toggle available)
Palette     :
  Background  #0f172a (slate-900)
  Surface     #1e293b (slate-800)
  Surface-2   #334155 (slate-700)
  Primary     #0ea5e9 (sky-500) — CTAs, links, active states
  Accent      #f97316 (orange-500) — warnings, low-stock alerts
  Success     #22c55e (green-500)
  Warning     #eab308 (yellow-500)
  Critical    #f97316 (orange-500)
  Danger      #ef4444 (red-500)
  Text        #f1f5f9
  Muted       #94a3b8

Typography  : Inter (body) + Geist Mono (numbers/code)
Border      : 1px solid rgba(255,255,255,0.08)
Radius      : 12px cards, 8px buttons, 6px badges
Animation   : 200ms ease for hovers, 300ms for panels, spring for modals

Status color mapping (use consistently everywhere):
  ok          → green-500    ring + text + badge
  low         → yellow-400   ring + text + badge
  critical    → orange-500   ring + text + badge + pulse animation
  out_of_stock→ red-500      ring + text + badge + pulse animation

═══════════════════════════════════════════════════════════
PAGE-BY-PAGE REQUIREMENTS
═══════════════════════════════════════════════════════════

─────────────────────────────────────
PAGE 1: ONBOARDING WIZARD
─────────────────────────────────────
Trigger: If no userId in Zustand store, redirect here on load.

Step 1 — Personal Info
  Fields: name (text), email (email)
  Validation: Zod — name required, email valid format

Step 2 — Household Profile  
  Fields: household_size (number stepper 1–10), adults, children
  Derived: children = household_size - adults (auto-computed)

Step 3 — Staple Items
  Show a pre-filled grid of common staples:
    milk, rice, eggs, bread, butter, oil, sugar, salt, flour, atta
  Each staple card has:
    - Toggle to include/exclude
    - daily_consumption_estimate input (number)
    - unit dropdown (kg / liter / count / g / ml)
    - threshold_quantity input
  User can add custom staples with a "+ Add Custom" button

Step 4 — Preferences
  currency (USD/EUR/GBP/INR — dropdown)
  notification_enabled toggle
  notification_channels checkboxes (in_app checked by default)

Step 5 — Review & Submit
  Summary card of all selections
  POST /api/v1/users/onboarding
  On success → store userId in Zustand → redirect to Dashboard

Progress bar at top. Back/Next buttons. Smooth slide transitions (Framer Motion).

─────────────────────────────────────
PAGE 2: DASHBOARD
─────────────────────────────────────
API: GET /api/v1/analytics/dashboard

Layout: 2-column grid on desktop, single column mobile

Row 1 — KPI Strip (4 stat cards):
  - Monthly Spend          (data.monthly_spend — formatted as $X.XX)
  - Low Stock Items        (data.low_stock_count — badge turns orange if > 0)
  - Items Running Out      (count of data.items_running_out_7days)
  - Top Store This Month   (data.top_stores[0].store_name)

Row 2 — Left: Spending Trend Chart (Recharts LineChart — by_store spend)
         Right: Inventory Status Donut (ok/low/critical/out_of_stock counts)

Row 3 — Items Running Out (7 days):
  List of data.items_running_out_7days
  Each row: item name, days left (colored by status), status badge
  "Runs out in X days" with a progress bar depleting to zero

Row 4 — Low Stock Quick Actions:
  Cards for each low-stock item with a "Add to Shopping List" CTA

Row 5 — Recent Receipts strip (last 3 receipts from GET /receipts)

Row 6 — Gmail Sync Banner (if Gmail connected):
  Last synced time + "Sync Now" button → POST /integrations/gmail/sync

All sections use skeleton loaders while fetching.
Auto-refresh every 60 seconds.

─────────────────────────────────────
PAGE 3: INVENTORY
─────────────────────────────────────
APIs:
  GET /api/v1/inventory (with status/category/sort_by filters)
  GET /api/v1/inventory/low-stock
  PATCH /api/v1/inventory/{item_id}

Top bar:
  - Search input (client-side filter by canonical_name)
  - Status filter tabs: ALL | OK | LOW | CRITICAL | OUT
  - Category dropdown filter
  - Sort dropdown: Days Left | Quantity | Name
  - View toggle: Grid / List

Grid View (default):
  Each InventoryCard shows:
    - Item name (large)
    - Current quantity + unit (e.g. "3.78 L")
    - Status badge (color-coded)
    - Days Left gauge: circular progress ring (SVG)
      - Full = ok, depleting = low, empty/red = out
    - "Estimated run-out: Apr 11" 
    - Edit button → opens AdjustModal
    - Reminder toggle (reminderEnabled)

List View:
  Table with columns: Item | Category | Qty | Threshold | Days Left | 
                       Status | Last Updated | Actions

AdjustModal:
  - Current quantity display
  - Input: new quantity + unit
  - Reason textarea (optional)
  - PATCH /api/v1/inventory/{item_id}
  - Shows event history below (last 5 inventory_events)
  - Animated success flash on save

Low-Stock Alert Banner at top of page if any items are critical/out.

─────────────────────────────────────
PAGE 4: RECEIPTS
─────────────────────────────────────
APIs:
  POST /api/v1/receipts/upload (multipart)
  GET  /api/v1/receipts
  GET  /api/v1/receipts/{receipt_id}
  PATCH /api/v1/receipts/{receipt_id}/review

Left Panel — Upload Zone:
  react-dropzone styled drop area
  - Accept: image/jpeg, image/png
  - Max size: 10MB shown in UI
  - Drag-and-drop or click-to-upload
  - On drop: show image preview thumbnail
  - Progress indicator during upload
  - After success: flash a "Receipt scanned! X items found" toast
  - Display extracted receipt card inline immediately after upload

Receipt Card (post-upload):
  - Merchant name + address
  - Transaction date + total
  - Item list table:
      raw_text | canonical_name | qty | unit | price | confidence badge
      confidence < 0.8 → yellow warning badge "Needs Review"
  - "Edit Receipt" button → opens ReceiptReviewModal

Right Panel — Receipt History:
  List of past receipts (GET /receipts with pagination)
  Filters: month picker, store search
  Each row: merchant, date, total, item count, "View" button
  Clicking View expands full receipt detail in a slide-over panel

ReceiptReviewModal:
  - Editable form: merchant name, per-item canonical_name / qty / price
  - PATCH /api/v1/receipts/{id}/review
  - After save: shows "Inventory updated" confirmation

─────────────────────────────────────
PAGE 5: ANALYTICS
─────────────────────────────────────
APIs:
  GET /api/v1/analytics/expenses/summary
  GET /api/v1/analytics/predictions
  GET /api/v1/analytics/prices/best-store?item=X&window=30d
  GET /api/v1/analytics/prices/compare?item=X

Tab 1 — SPENDING
  - This Month vs Last Month comparison bar (two big numbers side-by-side 
    with delta arrow + % change)
  - Donut chart: by_category spending (Recharts PieChart)
  - Bar chart: by_store total_spend (Recharts BarChart)
  - Table: top_spend_items — name, total spend, purchase count

Tab 2 — PREDICTIONS (run-out timeline)
  GET /api/v1/analytics/predictions
  - Timeline view: horizontal bars sorted by predicted_run_out_date
  - Color: green (>7 days) → yellow (3–7 days) → orange (1–3 days) → red (<1 day)
  - "Predicted to run out on Apr 11" label per item
  - Items with null estimatedDaysLeft shown in a separate "No consumption 
    data" section

Tab 3 — PRICE INSIGHTS
  - Item search input (canonical_item_id)
  - Trigger: GET /analytics/prices/best-store + GET /analytics/prices/compare
  - Display:
      Best store card (large, highlighted)
      Store comparison table: storeName | avg unit price | samples | last seen
      Confidence score bar
      "Not enough data" empty state if confidence is null

─────────────────────────────────────
PAGE 6: MEALS
─────────────────────────────────────
API: POST /api/v1/meals/suggest

Left — Constraints Form:
  - Max prep time (slider 0–120 min)
  - Vegetarian toggle
  - Budget mode toggle
  - "Suggest Meals" button

Right — Meal Cards (Framer Motion staggered entrance):
  Each meal card shows:
  - Title (large)
  - Description
  - Pantry ingredients used (green chips with ✓ icon)
  - Missing ingredients (red chips with ✗ icon — these go to shopping list)
  - Prep time badge
  - "Why suggested" (italic, muted text)
  - "Add missing to Shopping List" button

Empty state: animated pantry illustration + "Your pantry is empty. 
Upload a receipt to get started."

Loading state: skeleton cards with shimmer.

─────────────────────────────────────
PAGE 7: SHOPPING
─────────────────────────────────────
API: POST /api/v1/shopping/suggest (with optional budget_limit)

Top: Budget limit input (optional) + "Generate List" button

Section 1 — MUST BUY NOW (out_of_stock + critical items):
  Red-accented section header
  Each row:
    - Item name + current qty ("0 left")
    - Cheapest store badge (if cheapest_store exists)
    - Estimated price (if estimated_price exists)
    - Checkbox to mark as "in cart"

Section 2 — BUY SOON (low items):
  Yellow-accented section header
  Same row format

Bottom actions:
  - "Export as Text" — generates plain text shopping list
  - "Copy to Clipboard" button

Checked items animate out with a strikethrough + fade.
Persisted in local state during session.

─────────────────────────────────────
PAGE 8: EXPENSES (Unified Feed)
─────────────────────────────────────
APIs:
  GET /api/v1/expenses
  GET /api/v1/expenses/summary
  GET /api/v1/email-expenses
  PATCH /api/v1/email-expenses/{id}/review

Top — Summary Cards:
  Today's spend | This Month's spend | Receipt expenses | Gmail expenses
  (from GET /expenses/summary)

Filter bar:
  - Source: ALL | RECEIPT | GMAIL
  - Category dropdown
  - Date range picker (fromDate / toDate)
  - Merchant search

Expense Feed (infinite scroll or paginated):
  Each row:
    Source icon (receipt icon vs Gmail icon)
    Merchant name
    Amount (bold, right-aligned)
    Category badge
    Date
    Confidence badge (if < 0.85 → "Needs Review" yellow badge)
    Expand row → shows raw subject/snippet for Gmail items

Gmail-source rows with needsHumanReview = true:
  Highlighted with yellow left border
  "Review" button → opens inline edit form
  PATCH /api/v1/email-expenses/{id}/review

─────────────────────────────────────
PAGE 9: NOTIFICATIONS
─────────────────────────────────────
APIs:
  GET /api/v1/notifications
  POST /api/v1/notifications/test
  PATCH /api/v1/notifications/{id} (dismiss)

NotificationBell in TopBar:
  Badge count of unread/pending notifications
  Dropdown panel (top 5 latest)

Full page:
  Filter: ALL | LOW_STOCK | WEEKLY_SUMMARY | UNREAD
  List of NotificationItems:
    - Type icon (bell for low_stock, chart for weekly_summary)
    - Title + message
    - Relative timestamp ("2 hours ago")
    - Status badge: sent / dismissed
    - Dismiss button → PATCH with status: "dismissed" + fade out animation

"Send Test Notification" button (dev tool panel):
  Opens modal with title + message inputs
  POST /api/v1/notifications/test

─────────────────────────────────────
PAGE 10: SETTINGS
─────────────────────────────────────
Tab 1 — Gmail Integration:
  GET /api/v1/integrations/gmail/status
  
  If NOT connected:
    "Connect Gmail" card with OAuth flow button
    Explains what data will be read (read-only, expense emails only)
    POST /api/v1/integrations/gmail/connect
  
  If connected:
    Connected status card (email, last synced time)
    "Sync Now" button → POST /integrations/gmail/sync
    Sync history table (GET /integrations/gmail/sync-runs):
      started_at | status | messages_found | messages_parsed | errors
    "Disconnect" button → POST /integrations/gmail/disconnect

Tab 2 — Staple Configuration:
  GET /api/v1/users/{id} → show current staples
  Editable table of staples:
    canonical_name | daily_consumption_estimate | unit | threshold_quantity
  "Save Changes" → PATCH /api/v1/users/{id}/staples

Tab 3 — Preferences:
  currency, locale, notification_enabled, notification_channels
  (Update via PATCH /api/v1/users/{id}/staples or a preferences endpoint)

═══════════════════════════════════════════════════════════
GLOBAL UX REQUIREMENTS
═══════════════════════════════════════════════════════════

Navigation:
  Desktop : Left sidebar (240px) — always visible
  Mobile  : Bottom tab bar (5 primary tabs) + hamburger for secondary
  Active state: bright left border + background highlight on sidebar item

Sidebar items (in order):
  Dashboard | Inventory | Receipts | Analytics | Meals | Shopping | 
  Expenses | Notifications | Settings

Loading States:
  Every data-fetching view MUST show skeleton loaders (not spinners alone)
  Skeletons must match the real layout shape

Empty States:
  Every list/grid must have a designed empty state with:
  - Relevant icon (Lucide)
  - Descriptive message
  - Primary CTA (e.g., "Upload your first receipt")

Error States:
  API errors → toast notification (react-hot-toast)
  Network errors → inline error banner with retry button
  401/403 → redirect to Onboarding
  404 → inline "not found" component

Optimistic Updates:
  AdjustModal inventory update → optimistic quantity update in grid
  Notification dismiss → immediate removal from list
  Shopping list checkbox → immediate strikethrough

Accessibility:
  All interactive elements keyboard-navigable
  Proper ARIA labels on icon-only buttons
  Focus rings visible

Responsive:
  Fully functional at 375px (mobile) and 1440px (desktop)
  Tables → card stacks on mobile
  Multi-column grids → single column on mobile

═══════════════════════════════════════════════════════════
SPECIFIC COMPONENT SPECS
═══════════════════════════════════════════════════════════

InventoryCard — Days Left Ring:
  SVG circular progress ring
  Radius 28px, strokeWidth 4px
  Full circle = threshold × 3 (generous buffer)
  Stroke color = statusColors[item.status]
  Animate on mount with Framer Motion (draw from 0)

ReceiptDropzone:
  Dashed border, animated on hover (border color pulse)
  On file drop → show thumbnail + file name + size
  Upload progress bar (indeterminate while awaiting OCR)
  On success → auto-expand receipt detail below

NotificationBell:
  Animated ring on new notification (CSS shake keyframe)
  Red dot badge with count (disappears when all dismissed)

GmailSyncBanner:
  Only visible if Gmail is connected
  Shows: "Last synced X mins ago" + sync status (idle/syncing/error)
  "Sync Now" triggers POST and shows loading spinner inline

StatusBadge component:
  Props: status: 'ok' | 'low' | 'critical' | 'out_of_stock'
  Returns colored pill with appropriate label and icon:
    ok           → green  "In Stock"
    low          → yellow "Low"
    critical     → orange "Critical" + pulse dot
    out_of_stock → red    "Out of Stock" + pulse dot

═══════════════════════════════════════════════════════════
DATA & STATE MANAGEMENT
═══════════════════════════════════════════════════════════

TanStack Query setup:
  queryClient with:
    staleTime: 30_000 (30s)
    cacheTime: 300_000 (5m)
    retry: 2
    refetchOnWindowFocus: true

Query keys (use consistent key factory pattern):
  ['inventory', userId]
  ['inventory', userId, itemId]
  ['receipts', userId, { page, month, store }]
  ['analytics', 'dashboard', userId]
  ['analytics', 'predictions', userId]
  ['analytics', 'expenses', userId]
  ['meals', userId]
  ['shopping', userId]
  ['notifications', userId]
  ['expenses', userId, filters]
  ['gmail', 'status', userId]
  ['gmail', 'sync-runs', userId]

Mutations with optimistic updates:
  adjustInventory → immediate quantity update in ['inventory', userId] cache
  dismissNotification → immediate removal from ['notifications', userId] cache
  reviewEmailExpense → mark reviewed in ['expenses', userId] cache

Zustand store:
  userStore: { userId, userName, userEmail, isOnboarded, setUser, clearUser }
  uiStore: { sidebarOpen, activeModal, theme, toggleSidebar, openModal, closeModal }

Persistence: userId persisted to localStorage via Zustand persist middleware.

═══════════════════════════════════════════════════════════
API CLIENT SETUP
═══════════════════════════════════════════════════════════

Create src/api/client.ts:

  const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    timeout: 30_000,
  });

  // Request interceptor: inject userId as header if available
  client.interceptors.request.use((config) => {
    const { userId } = useUserStore.getState();
    if (userId) config.headers['X-User-ID'] = userId;
    return config;
  });

  // Response interceptor: unwrap .data, handle errors globally
  client.interceptors.response.use(
    (res) => res.data.data,   // unwrap success envelope
    (err) => {
      const msg = err.response?.data?.error?.message || 'Something went wrong';
      toast.error(msg);
      return Promise.reject(err);
    }
  );

All API functions in src/api/*.ts use this client and return typed responses.

═══════════════════════════════════════════════════════════
ENVIRONMENT & CONFIG
═══════════════════════════════════════════════════════════

.env.local:
  VITE_API_BASE_URL=http://localhost:8000

vite.config.ts:
  - Path aliases: @/components, @/pages, @/api, @/store, @/hooks, @/utils
  - Proxy /api → http://localhost:8000 in dev

═══════════════════════════════════════════════════════════
DELIVERABLE CHECKLIST
═══════════════════════════════════════════════════════════

[ ] package.json with all dependencies
[ ] vite.config.ts with path aliases + proxy
[ ] tailwind.config.ts with custom color tokens
[ ] src/api/client.ts — Axios instance + interceptors
[ ] src/api/*.ts — one file per API group (fully typed)
[ ] src/store/userStore.ts + uiStore.ts (Zustand)
[ ] src/hooks/*.ts — one per domain
[ ] All 10 pages fully implemented
[ ] All components from the architecture above
[ ] Onboarding wizard with multi-step form
[ ] Dark mode toggle (persisted)
[ ] Skeleton loaders on every page
[ ] Empty states on every list/grid
[ ] Error states with retry
[ ] Responsive layout (mobile + desktop)
[ ] README.md with setup instructions

═══════════════════════════════════════════════════════════
IMPORTANT CONSTRAINTS
═══════════════════════════════════════════════════════════

1. NEVER mock data — all data comes from the real API at localhost:8000
2. NEVER call an endpoint not defined in api_docs.md
3. The userId from onboarding MUST be persisted and passed to every API call
4. Receipt upload MUST use multipart/form-data with fields: user_id + file
5. Meal suggestions and shopping list are POST endpoints (not GET)
6. Price insights require item = canonical_item_id (e.g. "milk", "eggs")
7. Gmail OAuth flow should be handled gracefully — show "not connected" 
   state if no linked account exists
8. All number displays: use Intl.NumberFormat for currency, 
   toFixed(2) for quantities
9. All date displays: use date-fns format() — show relative time for 
   notifications, absolute for receipts
10. Inventory status colors MUST match: ok=green, low=yellow, 
    critical=orange, out_of_stock=red — consistently everywhere

Build the complete frontend now. Start with the project scaffold and 
global layout, then implement each page in order. Write production-quality 
TypeScript with proper types for every API response.