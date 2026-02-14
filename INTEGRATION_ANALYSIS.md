# KiranaGPT Backend-Frontend Integration Analysis

**Date:** February 14, 2026
**Status:** Pre-Integration
**Backend:** FastAPI (Python) - `kirana-backend/`
**Frontend:** Next.js 15 (TypeScript) - `kirana-frontend/`

---

## Table of Contents

1. [REST API Comparison](#rest-api-comparison)
2. [WebSocket Events Comparison](#websocket-events-comparison)
3. [Payload Structure Analysis](#payload-structure-analysis)
4. [Discrepancies & Issues](#discrepancies--issues)
5. [Required Fixes](#required-fixes)
6. [Integration Checklist](#integration-checklist)

---

## REST API Comparison

### ✅ Matching Endpoints

| Endpoint | Backend | Frontend | Status |
|----------|---------|----------|--------|
| `GET /health` | ✅ | ✅ | ✅ Match |
| `POST /api/message` | ✅ | ✅ | ✅ Match |
| `GET /api/store/{store_id}/profile` | ✅ | ✅ | ✅ Match |
| `GET /api/store/{store_id}/inventory` | ✅ | ✅ | ✅ Match |
| `GET /api/store/{store_id}/pnl` | ✅ | ✅ | ✅ Match |

### ⚠️ Mismatched Endpoints

| Endpoint | Backend | Frontend | Issue |
|----------|---------|----------|-------|
| `GET /api/store/{store_id}/forecast` | ✅ Query param: `?days=7` | ✅ Path param: `/{days}` | **PATH vs QUERY param mismatch** |

**Backend:** `GET /api/store/{store_id}/forecast?days=7`
**Frontend expects:** `GET /api/store/{store_id}/forecast/{days}`

### ❌ Missing Endpoints

| Endpoint | Backend | Frontend | Issue |
|----------|---------|----------|-------|
| `GET /api/store/{store_id}/udhaar` | ❌ **MISSING** | ✅ Expected | **Backend needs to implement** |

---

## WebSocket Events Comparison

### Connection URL

✅ **MATCH**
- Backend: `ws://localhost:8000/ws/{store_id}`
- Frontend: `ws://localhost:8000/ws/{store_id}`

### Backend → Frontend Events

| Event Name | Backend | Frontend | Status |
|------------|---------|----------|--------|
| `connection_established` | ✅ | ✅ | ✅ Match |
| `reasoning_step` | ✅ | ✅ | ✅ Match |
| `chat_message` | ✅ | ✅ | ✅ Match |
| `inventory_update` | ✅ | ✅ | ✅ Match |
| `procurement_order` | ✅ | ✅ | ✅ Match |
| `udhaar_update` | ✅ | ✅ | ✅ Match |
| `pnl_update` | ✅ | ✅ | ✅ Match |
| `error` | ✅ | ✅ | ✅ Match |

### Frontend → Backend Events

| Event Name | Backend | Frontend | Status |
|------------|---------|----------|--------|
| `user_message` | ❓ Not documented | ✅ Implemented | **Backend may not handle** |

**Note:** Frontend SRS mentions `user_message` event as an alternative to REST `POST /api/message`. Backend contract doesn't document this.

---

## Payload Structure Analysis

### 1. POST /api/message

#### Request Payload

**Backend expects:**
```typescript
{
  store_id: string;
  message_type: "text" | "image" | "voice";
  content: string;  // Plain text OR base64 encoded
  language?: "hinglish" | "hindi" | "english" | "kannada" | "tamil";
  metadata?: {
    image_type?: "shelf" | "parchi";
    [key: string]: any;
  };
}
```

**Frontend sends:**
```typescript
{
  store_id: string;
  message_type: "text" | "image" | "voice";
  content: string;
  language?: "hinglish" | "hindi" | "english" | "kannada" | "tamil";
  metadata?: {
    image_type?: "shelf" | "parchi";
    [key: string]: any;
  };
}
```

✅ **MATCH** - Structures are identical

#### Response Payload

**Backend returns:**
```typescript
{
  message_id: string;
  status: "processing" | "completed" | "error";
  websocket_channel: string;
  timestamp: string;  // ISO 8601
}
```

**Frontend expects:**
```typescript
{
  message_id: string;
  status: "processing" | "completed" | "error";
  websocket_channel: string;
  timestamp?: string;  // Optional in frontend types
}
```

⚠️ **MINOR MISMATCH** - Frontend has `timestamp` as optional, backend always returns it

---

### 2. GET /api/store/{store_id}/profile

#### Response Payload

**Backend returns:**
```typescript
{
  store_id: string;
  store_name: string;
  owner_name: string;
  city: string;
  phone: string;
  upi_id: string;
  language_preference: string;
}
```

**Frontend expects:**
```typescript
{
  store_id: string;
  name: string;           // ⚠️ Different field name
  owner_name: string;
  language: string;        // ⚠️ Different field name
  city: string;
  state: string;           // ⚠️ Missing in backend
  products: [...];         // ⚠️ Missing in backend
  inventory_summary: {...}; // ⚠️ Missing in backend
}
```

❌ **MAJOR MISMATCH** - Significant structural differences

**Issues:**
1. Backend uses `store_name`, frontend expects `name`
2. Backend uses `language_preference`, frontend expects `language`
3. Frontend expects `state` field (missing in backend)
4. Frontend expects `products` array (missing in backend)
5. Frontend expects `inventory_summary` object (missing in backend)
6. Backend has `phone` and `upi_id` (frontend doesn't use)

---

### 3. GET /api/store/{store_id}/inventory

#### Response Payload

**Backend returns:**
```typescript
{
  store_id: string;
  total_products: number;
  low_stock_count: number;
  critical_stock_count: number;
  products: InventoryItem[];
  last_updated: string;
}

interface InventoryItem {
  sku_id: string;
  name: string;
  category: string;
  current_stock: number;
  avg_daily_sales: number;
  days_of_stock: number;
  reorder_point: number;
  price: number;
  status: "healthy" | "low" | "critical";
  status_message: string;
}
```

**Frontend expects:**
```typescript
{
  inventory: {
    [product_id: string]: {
      current_stock: number;
      today_sold: number;      // ⚠️ Missing in backend
      today_received: number;   // ⚠️ Missing in backend
      avg_daily_velocity: number;
      days_of_stock: number;
      status: "healthy" | "low" | "critical";
    }
  };
  last_updated: string;
}
```

❌ **MAJOR STRUCTURAL MISMATCH**

**Issues:**
1. Backend returns `products` array, frontend expects `inventory` object keyed by product_id
2. Backend missing `today_sold` and `today_received` fields
3. Field name difference: `avg_daily_sales` vs `avg_daily_velocity`
4. Frontend doesn't expect summary fields (`total_products`, `low_stock_count`, etc.)

---

### 4. GET /api/store/{store_id}/pnl

#### Response Payload

**Backend returns:**
```typescript
{
  store_id: string;
  period_days: number;
  summary: {
    total_revenue: number;
    total_transactions: number;
    avg_transaction_value: number;
    cash_sales: number;
    upi_sales: number;
    credit_sales: number;
    outstanding_credit: number;
  };
  daily_breakdown: DailyPnL[];
  timestamp: string;
}
```

**Frontend expects:**
```typescript
{
  date: string;
  total_revenue: number;
  total_cogs: number;          // ⚠️ Missing in backend
  gross_profit: number;         // ⚠️ Missing in backend
  margin_pct: number;           // ⚠️ Missing in backend
  cash_collected: number;       // Different field name
  upi_collected: number;        // Different field name
  credit_given: number;         // Different field name
  total_transactions: number;
  items_sold: number;           // ⚠️ Missing in backend
}
```

❌ **MAJOR MISMATCH**

**Issues:**
1. Backend returns nested `summary` object, frontend expects flat structure
2. Backend missing: `total_cogs`, `gross_profit`, `margin_pct`, `items_sold`
3. Field name differences: `cash_sales` vs `cash_collected`, etc.
4. Backend returns `period_days` and `daily_breakdown` (frontend doesn't use)
5. Backend returns `outstanding_credit` (frontend expects this in separate `/udhaar` endpoint)

---

### 5. GET /api/store/{store_id}/forecast

#### Response Payload

**Backend returns:**
```typescript
{
  store_id: string;
  forecast_days: number;
  forecasts: ProductForecast[];
  upcoming_festivals: Festival[];
  timestamp: string;
}

interface ProductForecast {
  product_id: string;
  product_name: string;
  category: string;
  current_stock: number;
  base_daily_sales: number;
  avg_forecast_demand: number;
  days_of_stock_forecast: number;
  recommended_order_qty: number;
  urgency: "critical" | "high" | "medium" | "low";
  stockout_day?: number;
  has_festival_impact: boolean;
}
```

**Frontend expects:**
```typescript
{
  forecast_days: number;
  products: [
    {
      product_id: string;
      daily_demand: [
        {
          date: string;
          demand: number;
          stock: number;
          festival?: string;
        }
      ];
      reorder_point: number;
      recommended_order: number;
    }
  ];
}
```

❌ **STRUCTURAL MISMATCH**

**Issues:**
1. Backend returns aggregate forecast per product, frontend expects daily breakdown
2. Backend `avg_forecast_demand` is a single number, frontend needs array of daily values
3. Field name: `recommended_order_qty` vs `recommended_order`
4. Frontend expects day-by-day stock projection with festival annotations

---

### 6. GET /api/store/{store_id}/udhaar (MISSING IN BACKEND)

**Frontend expects:**
```typescript
{
  total_outstanding: number;
  customers: [
    {
      name: string;
      amount: number;
      last_transaction: string;
      transactions_count: number;
    }
  ];
}
```

**Backend:** ❌ **NOT IMPLEMENTED**

---

## WebSocket Event Payloads

### reasoning_step Event

**Backend sends:**
```typescript
{
  event: "reasoning_step";
  data: {
    step_number: number;
    step_type: string;
    description: string;
    icon: string;
    details: Record<string, any>;
  };
  timestamp: string;
}
```

**Frontend expects:**
```typescript
{
  event: "reasoning_step";
  data: {
    step_number: number;
    step_type: string;
    icon: string;
    title: string;         // ⚠️ Missing in backend
    description: string;
    details: any;
    timestamp: string;     // ⚠️ Nested in data, not at root
  };
}
```

⚠️ **MINOR MISMATCH**
- Backend missing `title` field
- Timestamp location differs (root vs nested)

---

### inventory_update Event

**Backend sends:**
```typescript
{
  event: "inventory_update";
  data: {
    product_id: string;
    product_name: string;
    old_stock: number;
    new_stock: number;
    change: number;
    transaction_type: "sale" | "delivery" | "adjustment";
    reason: string;
  };
  timestamp: string;
}
```

**Frontend expects:**
```typescript
{
  event: "inventory_update";
  data: {
    product_id: string;
    product_name: string;
    old_stock: number;
    new_stock: number;
    change: number;
    change_type: "sold" | "received";  // ⚠️ Different enum values
    days_of_stock: number;              // ⚠️ Missing in backend
    status: string;                     // ⚠️ Missing in backend
    alerts: [...];                      // ⚠️ Missing in backend
    timestamp: string;
  };
}
```

⚠️ **MISMATCH**
- Field name: `transaction_type` vs `change_type`
- Enum values differ: `"sale" | "delivery" | "adjustment"` vs `"sold" | "received"`
- Backend missing: `days_of_stock`, `status`, `alerts`

---

### chat_message Event

**Backend sends:**
```typescript
{
  event: "chat_message";
  data: {
    message_id: string;
    sender: "ai" | "system";
    message_type: "text" | "markdown";
    content: string;
    language: string;
  };
  timestamp: string;
}
```

**Frontend expects:**
```typescript
{
  event: "chat_message";
  data: {
    message_id: string;
    sender: "ai" | "system";
    message_type: "text" | "image" | "order_card";  // ⚠️ Different types
    content: string;
    formatted_content: string;                       // ⚠️ Missing in backend
    timestamp: string;
    metadata?: {...};                                 // ⚠️ Missing in backend
  };
}
```

⚠️ **MISMATCH**
- Backend has `"text" | "markdown"`, frontend expects `"text" | "image" | "order_card"`
- Frontend expects `formatted_content` and `metadata` fields

---

### procurement_order Event

**Backend sends:**
```typescript
{
  event: "procurement_order";
  data: {
    order_id: string;
    items: OrderItem[];
    total_cost: number;
    total_savings: number;
    distributor_split: DistributorOrder[];
    upi_links: UPILink[];
  };
  timestamp: string;
}
```

**Frontend expects:**
```typescript
{
  event: "procurement_order";
  data: {
    order_id: string;
    items: [...];
    total_cost: number;
    savings_vs_default: number;     // ⚠️ Field name difference
    distributor_split: [...];
    upi_deeplink: string;            // ⚠️ Single link vs array
    valid_until: string;             // ⚠️ Missing in backend
  };
}
```

⚠️ **MISMATCH**
- Field name: `total_savings` vs `savings_vs_default`
- Backend has `upi_links` array, frontend expects single `upi_deeplink` string
- Frontend expects `valid_until` timestamp

---

## Discrepancies & Issues

### Critical Issues (Must Fix)

1. **❌ Missing Endpoint:** `GET /api/store/{store_id}/udhaar` not implemented in backend
2. **❌ Forecast Endpoint:** Path param vs query param mismatch
3. **❌ Store Profile Structure:** Major field name and structure differences
4. **❌ Inventory Response:** Array vs object keyed structure mismatch
5. **❌ P&L Response:** Nested vs flat structure, missing COGS/profit calculations
6. **❌ Forecast Data:** Aggregate vs daily breakdown mismatch

### Medium Issues (Should Fix)

7. **⚠️ Inventory Fields:** Missing `today_sold` and `today_received` in backend
8. **⚠️ WebSocket Timestamp:** Inconsistent placement (root vs data object)
9. **⚠️ Message Type Enums:** Different enum values for `inventory_update` change types
10. **⚠️ Chat Message Types:** Backend uses `"markdown"`, frontend expects `"order_card"`

### Minor Issues (Nice to Fix)

11. **ℹ️ Reasoning Step:** Missing `title` field in backend
12. **ℹ️ Procurement Order:** Field naming inconsistencies
13. **ℹ️ Optional Fields:** Some optional fields in frontend that are always sent by backend

---

## Required Fixes

### Backend Fixes (Priority Order)

#### 🔴 CRITICAL - Must Fix Before Integration

**1. Implement GET /api/store/{store_id}/udhaar**
- **File:** Create `kirana-backend/routes/store.py` endpoint
- **Action:** Add new route handler
```python
@router.get("/api/store/{store_id}/udhaar")
async def get_udhaar(store_id: str):
    return {
        "total_outstanding": 8740,
        "customers": [
            {
                "name": "Sharma ji",
                "amount": 2340,
                "last_transaction": "2026-02-14",
                "transactions_count": 5
            }
        ]
    }
```

**2. Fix Forecast Endpoint Path**
- **File:** `kirana-backend/routes/store.py`
- **Current:** `GET /api/store/{store_id}/forecast?days=7`
- **Change to:** `GET /api/store/{store_id}/forecast` (keep query param)
- **Action:** Frontend should use query param, not path param
- **Decision:** Backend approach is RESTful, frontend needs adjustment

**3. Fix Store Profile Response Structure**
- **File:** `kirana-backend/routes/store.py`
- **Action:** Add missing fields and rename for frontend compatibility
```python
{
    "store_id": "...",
    "name": "...",              # Add (or rename store_name)
    "store_name": "...",        # Keep for backward compatibility
    "owner_name": "...",
    "city": "...",
    "state": "...",             # Add state field
    "phone": "...",
    "upi_id": "...",
    "language": "...",          # Add (or rename language_preference)
    "language_preference": "...", # Keep for backward compatibility
    "products": [...],          # Add products array from inventory
    "inventory_summary": {...}  # Add summary object
}
```

**4. Fix Inventory Response Structure**
- **File:** `kirana-backend/routes/store.py`
- **Current:** Returns `{ products: [...] }`
- **Change to:** Return keyed object
```python
{
    "inventory": {
        "maggi_70g": {
            "current_stock": 45,
            "today_sold": 8,        # Add field
            "today_received": 48,    # Add field
            "avg_daily_velocity": 8.2,
            "days_of_stock": 5.5,
            "status": "healthy"
        }
    },
    "last_updated": "2026-02-14T14:30:00"
}
```

**5. Fix P&L Response Structure**
- **File:** `kirana-backend/routes/store.py`
- **Action:** Flatten structure and add missing calculations
```python
{
    "date": "2026-02-14",
    "total_revenue": 4820,
    "total_cogs": 3200,         # Add calculation
    "gross_profit": 1620,        # Add calculation
    "margin_pct": 33.6,          # Add calculation
    "cash_collected": 3680,      # Rename from cash_sales
    "upi_collected": 980,        # Rename from upi_sales
    "credit_given": 160,         # Rename from credit_sales
    "total_transactions": 23,
    "items_sold": 47             # Add field
}
```

**6. Fix Forecast Response to Include Daily Breakdown**
- **File:** `kirana-backend/routes/store.py`
- **Action:** Add daily demand array per product
```python
{
    "forecast_days": 7,
    "products": [
        {
            "product_id": "maggi_70g",
            "product_name": "Maggi 2-Minute Noodles 70g",
            "daily_demand": [
                {"date": "2026-02-15", "demand": 8, "stock": 45},
                {"date": "2026-02-16", "demand": 24, "stock": 21, "festival": "Navratri"}
            ],
            "reorder_point": 16,
            "recommended_order": 25  # Rename from recommended_order_qty
        }
    ],
    "upcoming_festivals": [...]
}
```

#### 🟡 MEDIUM - Should Fix for Better UX

**7. Add Fields to inventory_update WebSocket Event**
- **File:** `kirana-backend/services/websocket_service.py`
- **Action:** Add `days_of_stock`, `status`, `alerts` fields
```python
{
    "event": "inventory_update",
    "data": {
        "product_id": "maggi_70g",
        "product_name": "...",
        "old_stock": 10,
        "new_stock": 5,
        "change": -5,
        "transaction_type": "sale",
        "reason": "...",
        "days_of_stock": 4.6,      # Add
        "status": "warning",        # Add
        "alerts": [...]             # Add
    }
}
```

**8. Standardize WebSocket Timestamp Placement**
- **File:** `kirana-backend/services/websocket_service.py`
- **Action:** Move timestamp to data object for consistency
```python
{
    "event": "reasoning_step",
    "data": {
        ...
        "timestamp": "2026-02-14T14:30:00Z"  # Move here from root
    }
}
```

**9. Add title Field to reasoning_step Event**
- **File:** `kirana-backend/services/websocket_service.py`
```python
{
    "event": "reasoning_step",
    "data": {
        "step_number": 1,
        "step_type": "SHELF_ANALYSIS",
        "title": "Shelf Analysis",  # Add this field
        "description": "...",
        "icon": "🔍",
        "details": {...}
    }
}
```

#### 🟢 MINOR - Nice to Have

**10. Align Procurement Order Field Names**
- **File:** `kirana-backend/services/websocket_service.py`
```python
{
    "savings_vs_default": 340,  # Rename from total_savings
    "upi_deeplink": "upi://...", # Provide single primary link
    "valid_until": "2026-02-14T23:59:59Z"  # Add expiry
}
```

---

### Frontend Fixes (Priority Order)

#### 🔴 CRITICAL - Must Fix Before Integration

**1. Fix Forecast API Call**
- **File:** `kirana-frontend/lib/api.ts`
- **Current:** `GET /api/store/{store_id}/forecast/{days}`
- **Fix to:** `GET /api/store/{store_id}/forecast?days={days}`
```typescript
export async function getForecast(storeId: string, days: number = 7) {
    return apiRequest<ForecastResponse>(
        `/api/store/${storeId}/forecast?days=${days}` // Use query param
    );
}
```

**2. Update Store Profile Type to Match Backend**
- **File:** `kirana-frontend/types/api.ts`
- **Action:** Use backend field names or add mapping
```typescript
export interface StoreProfile {
    store_id: string;
    store_name: string;      // Backend field name
    owner_name: string;
    city: string;
    phone: string;
    upi_id: string;
    language_preference: string; // Backend field name
}
```

**3. Update Inventory Response Type**
- **File:** `kirana-frontend/types/api.ts`
- **Action:** Match backend array structure
```typescript
export interface InventoryResponse {
    store_id: string;
    total_products: number;
    low_stock_count: number;
    critical_stock_count: number;
    products: InventoryItem[];  // Array, not object
    last_updated: string;
}
```

**4. Update P&L Response Type**
- **File:** `kirana-frontend/types/api.ts`
- **Action:** Match backend nested structure
```typescript
export interface PnLSummary {
    store_id: string;
    period_days: number;
    summary: {
        total_revenue: number;
        total_transactions: number;
        avg_transaction_value: number;
        cash_sales: number;     // Backend field name
        upi_sales: number;      // Backend field name
        credit_sales: number;   // Backend field name
        outstanding_credit: number;
    };
    daily_breakdown: DailyPnL[];
    timestamp: string;
}
```

**5. Update Forecast Response Type**
- **File:** `kirana-frontend/types/api.ts`
- **Action:** Match backend aggregate structure
```typescript
export interface ProductForecast {
    product_id: string;
    product_name: string;
    category: string;
    current_stock: number;
    base_daily_sales: number;
    avg_forecast_demand: number;  // Single number, not array
    days_of_stock_forecast: number;
    recommended_order_qty: number; // Backend field name
    urgency: "critical" | "high" | "medium" | "low";
    stockout_day?: number;
    has_festival_impact: boolean;
}
```

#### 🟡 MEDIUM - Should Fix

**6. Update WebSocket Event Handlers**
- **File:** `kirana-frontend/lib/websocket.ts`
- **Action:** Handle timestamp at root level (backend sends it there)
```typescript
// Backend sends timestamp at root, not in data
const event = JSON.parse(message.data);
const timestamp = event.timestamp; // Not event.data.timestamp
```

**7. Handle Backend inventory_update Field Names**
- **File:** `kirana-frontend/lib/websocket.ts` or `store/index.ts`
- **Action:** Map `transaction_type` to `change_type`
```typescript
case 'inventory_update':
    const changeType = event.data.transaction_type === 'sale' ? 'sold' : 'received';
    // Use changeType in frontend
```

**8. Handle Backend chat_message Types**
- **File:** `kirana-frontend/lib/websocket.ts`
- **Action:** Map `"markdown"` to appropriate frontend type
```typescript
case 'chat_message':
    const messageType = event.data.message_type === 'markdown'
        ? 'text'  // Or handle markdown rendering
        : event.data.message_type;
```

#### 🟢 MINOR - Nice to Have

**9. Add Udhaar API Call**
- **File:** `kirana-frontend/lib/api.ts`
- **Action:** Ensure udhaar endpoint is called correctly
```typescript
export async function getUdhaar(storeId: string) {
    return apiRequest<UdhaarResponse>(`/api/store/${storeId}/udhaar`);
}
```

---

## Integration Checklist

### Pre-Integration Setup

- [ ] **Backend:** Update `.env` with `DEMO_MODE=false` for real API
- [ ] **Frontend:** Update `.env.local` with `NEXT_PUBLIC_USE_MOCK_API=false`
- [ ] **Backend:** Start server: `cd kirana-backend && uvicorn main:app --reload`
- [ ] **Frontend:** Start dev server: `cd kirana-frontend && npm run dev`
- [ ] **Network:** Verify both running on localhost (backend :8000, frontend :3000)

### Backend Changes Required

#### Endpoints
- [ ] **Implement** `GET /api/store/{store_id}/udhaar` endpoint
- [ ] **Update** `GET /api/store/{store_id}/profile` response structure
- [ ] **Update** `GET /api/store/{store_id}/inventory` response structure
- [ ] **Update** `GET /api/store/{store_id}/pnl` response structure
- [ ] **Update** `GET /api/store/{store_id}/forecast` response structure
- [ ] **Test** all endpoints return updated structures

#### WebSocket Events
- [ ] **Add** `title` field to `reasoning_step` event
- [ ] **Add** `days_of_stock`, `status`, `alerts` to `inventory_update` event
- [ ] **Add** `valid_until` to `procurement_order` event
- [ ] **Rename** `total_savings` to `savings_vs_default` in `procurement_order`
- [ ] **Standardize** timestamp placement (move to data object)
- [ ] **Test** all WebSocket events with new structure

### Frontend Changes Required

#### API Layer
- [ ] **Fix** forecast endpoint to use query param: `?days=7`
- [ ] **Update** `types/api.ts` to match backend response structures
- [ ] **Update** API service layer in `lib/api.ts`
- [ ] **Test** all API calls with real backend

#### WebSocket Layer
- [ ] **Update** WebSocket event handlers in `lib/websocket.ts`
- [ ] **Handle** timestamp at root level (not nested)
- [ ] **Map** backend field names to frontend expectations
- [ ] **Test** WebSocket connection and all event types

#### State Management
- [ ] **Update** Zustand store to handle backend data structures
- [ ] **Add** mapping functions for incompatible structures
- [ ] **Test** state updates with real WebSocket events

### Integration Testing

#### REST API Tests
- [ ] **Test** `POST /api/message` with text, image, voice
- [ ] **Test** `GET /api/store/{store_id}/profile`
- [ ] **Test** `GET /api/store/{store_id}/inventory`
- [ ] **Test** `GET /api/store/{store_id}/udhaar`
- [ ] **Test** `GET /api/store/{store_id}/pnl`
- [ ] **Test** `GET /api/store/{store_id}/forecast?days=7`
- [ ] **Verify** error responses (400, 404, 500)

#### WebSocket Tests
- [ ] **Test** WebSocket connection establishment
- [ ] **Test** `connection_established` event
- [ ] **Test** `reasoning_step` event rendering
- [ ] **Test** `inventory_update` event and UI updates
- [ ] **Test** `chat_message` event rendering
- [ ] **Test** `procurement_order` event and card display
- [ ] **Test** `udhaar_update` event
- [ ] **Test** `pnl_update` event
- [ ] **Test** `error` event handling
- [ ] **Test** WebSocket auto-reconnect

#### End-to-End Flows
- [ ] **Test** Shelf photo → reasoning steps → procurement order
- [ ] **Test** Kacchi parchi → OCR → inventory update
- [ ] **Test** Voice message → transcription → inventory update
- [ ] **Test** All three panels update in real-time
- [ ] **Test** Demo mode toggle switches between mock and real

### Post-Integration

- [ ] **Document** any remaining discrepancies
- [ ] **Update** API_CONTRACT.md if backend changes
- [ ] **Update** frontend-srs.md if frontend changes
- [ ] **Create** integration test suite
- [ ] **Deploy** to staging for testing

---

## Recommendations

### Short-term (Before Demo)

1. **Backend Priority:**
   - Implement `/udhaar` endpoint
   - Fix response structures for profile, inventory, P&L, forecast
   - Add missing fields to WebSocket events

2. **Frontend Priority:**
   - Fix forecast API call (query param)
   - Update all type definitions to match backend
   - Add data mapping layer for incompatible structures

3. **Testing:**
   - Create integration test script to verify all endpoints
   - Test complete demo flow end-to-end

### Long-term (Post-Hackathon)

1. **API Versioning:**
   - Consider creating `/api/v2` if breaking changes needed
   - Maintain backward compatibility with v1

2. **Type Safety:**
   - Generate TypeScript types from Python Pydantic models
   - Use tools like `pydantic-to-typescript`

3. **Documentation:**
   - Auto-generate API docs from OpenAPI/Swagger
   - Keep frontend-backend contracts in sync

4. **Testing:**
   - Add contract testing (Pact or similar)
   - Add E2E tests for critical flows

---

## Summary

### Critical Issues: 6
1. Missing `/udhaar` endpoint
2. Forecast path vs query param mismatch
3. Store profile structure mismatch
4. Inventory response structure mismatch
5. P&L response structure mismatch
6. Forecast data structure mismatch

### Medium Issues: 4
7. Missing inventory fields
8. WebSocket timestamp placement
9. Inventory update enum mismatch
10. Chat message type enum mismatch

### Minor Issues: 3
11. Missing reasoning step title
12. Procurement order field names
13. Optional field inconsistencies

**Total Issues:** 13

**Estimated Fix Time:**
- Backend: 6-8 hours
- Frontend: 4-6 hours
- Testing: 2-3 hours
- **Total: 12-17 hours**

---

## ✅ FIXES COMPLETED

### Backend Fixes (COMPLETED)

All critical backend fixes have been implemented:

1. **✅ GET /api/store/{store_id}/udhaar** - New endpoint added in [routes/store.py](kirana-backend/routes/store.py#L333-L406)
2. **✅ GET /api/store/{store_id}/profile** - Enhanced with frontend-compatible fields ([routes/store.py](kirana-backend/routes/store.py#L64-L84))
3. **✅ GET /api/store/{store_id}/inventory** - Returns both keyed object and array structures ([routes/store.py](kirana-backend/routes/store.py#L152-L184))
4. **✅ GET /api/store/{store_id}/pnl** - Flattened structure with calculated COGS, profit, margin ([routes/store.py](kirana-backend/routes/store.py#L289-L318))
5. **✅ GET /api/store/{store_id}/forecast** - Added daily_demand array per product ([routes/store.py](kirana-backend/routes/store.py#L499-L544))
6. **✅ WebSocket Events** - All events updated in [services/websocket_service.py](kirana-backend/services/websocket_service.py):
   - `reasoning_step`: Added `title` field and icon mapping ([websocket_service.py:126-183](kirana-backend/services/websocket_service.py#L126-L183))
   - `inventory_update`: Added `days_of_stock`, `status`, `alerts`, `change_type` fields ([websocket_service.py:231-314](kirana-backend/services/websocket_service.py#L231-L314))
   - `procurement_order`: Added `savings_vs_default`, `upi_deeplink`, `valid_until` fields ([websocket_service.py:316-352](kirana-backend/services/websocket_service.py#L316-L352))
   - `chat_message`: Added `formatted_content` and `metadata` fields ([websocket_service.py:184-229](kirana-backend/services/websocket_service.py#L184-L229))
   - **✅ `udhaar_update`**: NEW - Added sender method ([websocket_service.py:354-398](kirana-backend/services/websocket_service.py#L354-L398))
   - **✅ `pnl_update`**: NEW - Added sender method ([websocket_service.py:400-438](kirana-backend/services/websocket_service.py#L400-L438))
   - All events: Timestamp now in both root and data for compatibility

### Frontend Fixes (COMPLETED)

All frontend fixes have been implemented:

1. **✅ Forecast API call** - Fixed to use query parameter `?days=7` ([lib/apiConfig.ts](kirana-frontend/lib/apiConfig.ts#L21))
2. **✅ TypeScript types** - Already compatible with backend structures
3. **✅ WebSocket handlers** - Already properly structured to handle backend events

## 🧪 TESTING REQUIRED

### Integration Test Checklist

#### REST API Tests
- [ ] **POST /api/message** - Send text, image, voice messages
- [ ] **GET /api/store/{store_id}/profile** - Verify enhanced fields
- [ ] **GET /api/store/{store_id}/inventory** - Verify keyed object structure
- [ ] **GET /api/store/{store_id}/udhaar** - NEW endpoint verification
- [ ] **GET /api/store/{store_id}/pnl** - Verify flat structure with calculations
- [ ] **GET /api/store/{store_id}/forecast?days=7** - Verify daily_demand arrays

#### WebSocket Tests
- [ ] Connect to `ws://localhost:8000/ws/sharma_general_store`
- [ ] Receive `connection_established` event
- [ ] Send message and receive `reasoning_step` events with titles
- [ ] Receive `inventory_update` with days_of_stock, status, alerts
- [ ] Receive `procurement_order` with valid_until
- [ ] Receive `chat_message` events
- [ ] Verify timestamp in both root and data

#### End-to-End Flows
- [ ] Shelf photo → shelf analysis → procurement order
- [ ] Kacchi parchi → OCR → inventory updates
- [ ] Voice message → transcription → stock updates
- [ ] Real-time UI updates across all three panels

### How to Test

1. **Start Backend:**
   ```bash
   cd kirana-backend
   uvicorn main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd kirana-frontend
   npm run dev
   ```

3. **Test in Browser:**
   - Navigate to `http://localhost:3000`
   - Open browser DevTools Console
   - Send test messages and verify responses

4. **Switch to Real API:**
   - Update `.env.local`: `NEXT_PUBLIC_USE_MOCK_API=false`
   - Restart frontend dev server
   - Verify all API calls hit real backend

## 📋 KNOWN COMPATIBILITY NOTES

### Backward Compatibility Maintained

The backend now returns **both** old and new structures where possible:

- **Profile**: Returns both `store_name` and `name`
- **Inventory**: Returns both `products` array and `inventory` object
- **P&L**: Returns both nested `summary` and flat fields
- **Forecast**: Returns both `forecasts` and simplified `products`
- **WebSocket Events**: Timestamp in both root and data object

This ensures existing code continues to work while new code can use the improved structures.

### Migration Notes

If you want to use only the new structures in the future:
1. Update all frontend code to use new field names
2. Remove backward-compatible fields from backend responses
3. Bump API version to `/api/v2`

---

**Next Steps:**
1. ✅ Backend fixes implemented
2. ✅ Frontend fixes implemented
3. 🔄 **NOW: Run integration tests**
4. 🔄 **Test demo flows end-to-end**
5. 🔄 **Deploy to staging environment**

**Last Updated:** February 14, 2026 (Fixes Completed)
**Status:** ✅ Ready for Integration Testing
