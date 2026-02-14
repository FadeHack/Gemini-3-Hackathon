# KiranaGPT Backend API Contract v1.0

> 🧊 **FROZEN FOR HACKATHON** - These contracts will NOT change during development
>
> Last Updated: 2026-02-14
> Status: **STABLE** - Frontend can integrate immediately
> Breaking Changes: **PROHIBITED** - Any breaking changes require /api/v2

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Base Configuration](#base-configuration)
3. [REST API Endpoints](#rest-api-endpoints)
4. [WebSocket API](#websocket-api)
5. [TypeScript Types](#typescript-types)
6. [Error Handling](#error-handling)
7. [Demo Mode](#demo-mode)
8. [Integration Checklist](#integration-checklist)

---

## Quick Start

### For Next.js Frontend

```bash
# 1. Backend is running at:
http://localhost:8000

# 2. Test health endpoint:
curl http://localhost:8000/health

# 3. View interactive docs:
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc

# 4. Copy TypeScript types from section below

# 5. Start integrating! ✅
```

---

## Base Configuration

### Connection Details

```typescript
const API_CONFIG = {
  baseURL: 'http://localhost:8000',
  wsURL: 'ws://localhost:8000',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  }
};
```

### Common Headers

All requests use:
- `Content-Type: application/json`
- No authentication required (hackathon POC)

### Response Format

All successful responses return JSON with appropriate status code:
- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found (store doesn't exist)
- `500`: Internal Server Error

---

## REST API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Purpose:** Verify backend is running

**Request:** No parameters

**Response:**
```typescript
interface HealthResponse {
  status: "ok";
  version: string;
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### 2. Process Message (Main Endpoint)

**Endpoint:** `POST /api/message`

**Purpose:** Process text, image, or voice messages

**Request Body:**
```typescript
interface MessageRequest {
  store_id: string;
  message_type: "text" | "image" | "voice";
  content: string;  // Plain text OR base64 encoded (image/audio)
  language?: "hinglish" | "hindi" | "english" | "kannada" | "tamil";
  metadata?: {
    image_type?: "shelf" | "parchi";
    [key: string]: any;
  };
}
```

**Response:**
```typescript
interface MessageResponse {
  message_id: string;
  status: "processing" | "completed" | "error";
  websocket_channel: string;  // WS URL for real-time updates
  timestamp: string;  // ISO 8601 format
}
```

**Example - Text Message:**
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "sharma_general_store",
    "message_type": "text",
    "content": "Maggi ka stock kitna hai?",
    "language": "hinglish"
  }'
```

**Response:**
```json
{
  "message_id": "msg_20260214_143000",
  "status": "processing",
  "websocket_channel": "ws://localhost:8000/ws/sharma_general_store",
  "timestamp": "2026-02-14T14:30:00Z"
}
```

**Example - Shelf Photo:**
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "sharma_general_store",
    "message_type": "image",
    "content": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "metadata": {
      "image_type": "shelf"
    }
  }'
```

**Example - Kacchi Parchi:**
```json
{
  "store_id": "sharma_general_store",
  "message_type": "image",
  "content": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "metadata": {
    "image_type": "parchi"
  }
}
```

**Example - Voice Message:**
```json
{
  "store_id": "sharma_general_store",
  "message_type": "voice",
  "content": "data:audio/wav;base64,UklGRiQAAABXQVZF...",
  "language": "hinglish"
}
```

**Status Codes:**
- `200`: Message accepted for processing
- `400`: Invalid request (missing fields, invalid message_type, etc.)
- `404`: Store not found
- `500`: Server error

---

### 3. Get Store Profile

**Endpoint:** `GET /api/store/{store_id}/profile`

**Purpose:** Fetch store details

**Path Parameters:**
- `store_id` (string): Store identifier (e.g., "sharma_general_store")

**Response:**
```typescript
interface StoreProfile {
  store_id: string;
  store_name: string;
  owner_name: string;
  city: string;
  phone: string;
  upi_id: string;
  language_preference: string;
}
```

**Example:**
```bash
curl http://localhost:8000/api/store/sharma_general_store/profile
```

```json
{
  "store_id": "sharma_general_store",
  "store_name": "Sharma General Store",
  "owner_name": "Rajesh Sharma",
  "city": "Indore",
  "phone": "+91 98765 43210",
  "upi_id": "rajesh@paytm",
  "language_preference": "hinglish"
}
```

---

### 4. Get Store Inventory

**Endpoint:** `GET /api/store/{store_id}/inventory`

**Purpose:** Get current stock levels for all products

**Path Parameters:**
- `store_id` (string): Store identifier

**Response:**
```typescript
interface InventoryResponse {
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
  status_message: string;  // Hinglish message like "Stock theek hai 👍"
}
```

**Example:**
```bash
curl http://localhost:8000/api/store/sharma_general_store/inventory
```

```json
{
  "store_id": "sharma_general_store",
  "total_products": 20,
  "low_stock_count": 4,
  "critical_stock_count": 2,
  "products": [
    {
      "sku_id": "maggi_70g",
      "name": "Maggi 2-Minute Noodles 70g",
      "category": "instant_food",
      "current_stock": 3,
      "avg_daily_sales": 10,
      "days_of_stock": 0.3,
      "reorder_point": 20,
      "price": 12.0,
      "status": "critical",
      "status_message": "🔴 Critically low - only 0.3 days left!"
    }
  ],
  "last_updated": "2026-02-14T14:30:00Z"
}
```

---

### 5. Get P&L Summary

**Endpoint:** `GET /api/store/{store_id}/pnl`

**Purpose:** Get profit & loss summary

**Path Parameters:**
- `store_id` (string): Store identifier

**Query Parameters:**
- `days` (integer, optional): Number of days to summarize (default: 30)

**Response:**
```typescript
interface PnLSummary {
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

interface DailyPnL {
  date: string;  // YYYY-MM-DD
  revenue: number;
  transactions: number;
  cash: number;
  upi: number;
  credit: number;
}
```

**Example:**
```bash
curl http://localhost:8000/api/store/sharma_general_store/pnl?days=7
```

```json
{
  "store_id": "sharma_general_store",
  "period_days": 7,
  "summary": {
    "total_revenue": 45678.50,
    "total_transactions": 234,
    "avg_transaction_value": 195.20,
    "cash_sales": 28000.00,
    "upi_sales": 15678.50,
    "credit_sales": 2000.00,
    "outstanding_credit": 8900.00
  },
  "daily_breakdown": [],
  "timestamp": "2026-02-14T14:30:00Z"
}
```

---

### 6. Get Demand Forecast

**Endpoint:** `GET /api/store/{store_id}/forecast`

**Purpose:** Get demand forecast with festival/weather awareness

**Path Parameters:**
- `store_id` (string): Store identifier

**Query Parameters:**
- `days` (integer, optional): Forecast period in days (default: 7)

**Response:**
```typescript
interface ForecastResponse {
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
  stockout_day?: number;  // Day when stock runs out
  has_festival_impact: boolean;
}

interface Festival {
  name: string;
  starts: string;  // ISO date
  days_until: number;
  duration_days: number;
  impact: "high" | "medium" | "low";
}
```

**Example:**
```bash
curl http://localhost:8000/api/store/sharma_general_store/forecast?days=7
```

```json
{
  "store_id": "sharma_general_store",
  "forecast_days": 7,
  "forecasts": [
    {
      "product_id": "maggi_70g",
      "product_name": "Maggi 2-Minute Noodles 70g",
      "category": "instant_food",
      "current_stock": 3,
      "base_daily_sales": 10,
      "avg_forecast_demand": 12.5,
      "days_of_stock_forecast": 0.24,
      "recommended_order_qty": 82,
      "urgency": "critical",
      "stockout_day": 1,
      "has_festival_impact": true
    }
  ],
  "upcoming_festivals": [
    {
      "name": "Navratri",
      "starts": "2026-02-16T00:00:00",
      "days_until": 2,
      "duration_days": 9,
      "impact": "high"
    }
  ],
  "timestamp": "2026-02-14T14:30:00Z"
}
```

---

## WebSocket API

### Connection

**Endpoint:** `ws://localhost:8000/ws/{store_id}`

**Example (JavaScript):**
```typescript
const storeId = 'sharma_general_store';
const ws = new WebSocket(`ws://localhost:8000/ws/${storeId}`);

ws.onopen = () => {
  console.log('Connected to KiranaGPT');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleWebSocketEvent(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from KiranaGPT');
};
```

### Event Types (Server → Client)

All events follow this base structure:
```typescript
interface WebSocketEvent {
  event: string;  // Event type identifier
  data: Record<string, any>;  // Event-specific payload
  timestamp: string;  // ISO 8601 timestamp
}
```

#### 1. `connection_established`

Sent immediately after connection.

```typescript
interface ConnectionEstablishedEvent {
  event: "connection_established";
  data: {
    store_id: string;
    session_id: string;
    message: string;
  };
  timestamp: string;
}
```

**Example:**
```json
{
  "event": "connection_established",
  "data": {
    "store_id": "sharma_general_store",
    "session_id": "sess_xyz123",
    "message": "Connected successfully"
  },
  "timestamp": "2026-02-14T14:30:00Z"
}
```

#### 2. `reasoning_step`

AI thinking process visualization.

```typescript
interface ReasoningStepEvent {
  event: "reasoning_step";
  data: {
    step_number: number;
    step_type: string;  // "SHELF_ANALYSIS", "OCR_EXTRACTION", etc.
    description: string;
    icon: string;  // Emoji
    details: Record<string, any>;
  };
  timestamp: string;
}
```

**Example:**
```json
{
  "event": "reasoning_step",
  "data": {
    "step_number": 1,
    "step_type": "SHELF_ANALYSIS",
    "description": "Analyzing shelf layout and identifying products",
    "icon": "📸",
    "details": {
      "status": "in_progress",
      "confidence": 0.95
    }
  },
  "timestamp": "2026-02-14T14:30:01Z"
}
```

**Common `step_type` values:**
- `SHELF_ANALYSIS` - Shelf photo processing
- `OCR_EXTRACTION` - Handwriting recognition
- `VOICE_PROCESSING` - Audio transcription
- `INTENT_DETECTION` - Understanding user intent
- `INVENTORY_UPDATE` - Updating stock
- `DEMAND_FORECAST` - Calculating predictions
- `PRICE_COMPARISON` - Comparing distributor prices
- `ORDER_GENERATION` - Creating procurement order

#### 3. `chat_message`

AI response message.

```typescript
interface ChatMessageEvent {
  event: "chat_message";
  data: {
    message_id: string;
    sender: "ai" | "system";
    message_type: "text" | "markdown";
    content: string;  // Message text (may include markdown)
    language: string;
  };
  timestamp: string;
}
```

**Example:**
```json
{
  "event": "chat_message",
  "data": {
    "message_id": "msg_ai_20260214_143008",
    "sender": "ai",
    "message_type": "markdown",
    "content": "**📦 Shelf Analysis Complete!**\n\n8 products detected...",
    "language": "hinglish"
  },
  "timestamp": "2026-02-14T14:30:08Z"
}
```

#### 4. `inventory_update`

Stock level changed.

```typescript
interface InventoryUpdateEvent {
  event: "inventory_update";
  data: {
    product_id: string;
    product_name: string;
    old_stock: number;
    new_stock: number;
    change: number;  // Negative for sales, positive for delivery
    transaction_type: "sale" | "delivery" | "adjustment";
    reason: string;
  };
  timestamp: string;
}
```

**Example:**
```json
{
  "event": "inventory_update",
  "data": {
    "product_id": "maggi_70g",
    "product_name": "Maggi 2-Minute Noodles 70g",
    "old_stock": 10,
    "new_stock": 5,
    "change": -5,
    "transaction_type": "sale",
    "reason": "Parchi OCR - 5 packets sold"
  },
  "timestamp": "2026-02-14T14:30:10Z"
}
```

#### 5. `procurement_order`

Order generated.

```typescript
interface ProcurementOrderEvent {
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

interface OrderItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  distributor: string;
}

interface DistributorOrder {
  distributor_id: string;
  distributor_name: string;
  items: OrderItem[];
  subtotal: number;
  delivery_time: string;
}

interface UPILink {
  distributor_name: string;
  amount: number;
  upi_link: string;  // upi://pay?pa=...
}
```

#### 6. `udhaar_update`

Credit ledger updated.

```typescript
interface UdhaarUpdateEvent {
  event: "udhaar_update";
  data: {
    customer_name: string;
    old_balance: number;
    new_balance: number;
    change: number;
    transaction_details: string;
  };
  timestamp: string;
}
```

#### 7. `pnl_update`

Profit & loss updated.

```typescript
interface PNLUpdateEvent {
  event: "pnl_update";
  data: {
    today_revenue: number;
    today_transactions: number;
    cash: number;
    upi: number;
    credit: number;
  };
  timestamp: string;
}
```

#### 8. `error`

Error occurred during processing.

```typescript
interface ErrorEvent {
  event: "error";
  data: {
    error_type: string;
    error_code: string;
    message: string;  // Technical message
    user_message: string;  // User-friendly Hinglish message
    fallback_action?: "retry" | "skip" | "manual";
    retry_count?: number;
    max_retries?: number;
  };
  timestamp: string;
}
```

**Example:**
```json
{
  "event": "error",
  "data": {
    "error_type": "gemini_api_error",
    "error_code": "GEMINI_TIMEOUT",
    "message": "Gemini API request timed out after 30s",
    "user_message": "Rajesh bhai, thoda technical issue aa raha hai. Kripya dobara try karein.",
    "fallback_action": "retry",
    "retry_count": 1,
    "max_retries": 3
  },
  "timestamp": "2026-02-14T14:30:15Z"
}
```

### Event Handling Example

```typescript
function handleWebSocketEvent(event: WebSocketEvent) {
  switch (event.event) {
    case 'connection_established':
      console.log('Connected:', event.data.message);
      break;

    case 'reasoning_step':
      displayReasoningStep(event.data);
      break;

    case 'chat_message':
      displayChatMessage(event.data.content);
      break;

    case 'inventory_update':
      updateInventoryUI(event.data);
      break;

    case 'procurement_order':
      displayProcurementOrder(event.data);
      break;

    case 'error':
      showError(event.data.user_message);
      break;

    default:
      console.log('Unknown event:', event.event);
  }
}
```

---

## TypeScript Types

### Complete Type Definitions

Copy-paste ready for your Next.js project:

```typescript
// ============ API Request Types ============

export interface MessageRequest {
  store_id: string;
  message_type: "text" | "image" | "voice";
  content: string;
  language?: "hinglish" | "hindi" | "english" | "kannada" | "tamil";
  metadata?: {
    image_type?: "shelf" | "parchi";
    [key: string]: any;
  };
}

// ============ API Response Types ============

export interface MessageResponse {
  message_id: string;
  status: "processing" | "completed" | "error";
  websocket_channel: string;
  timestamp: string;
}

export interface HealthResponse {
  status: "ok";
  version: string;
}

export interface StoreProfile {
  store_id: string;
  store_name: string;
  owner_name: string;
  city: string;
  phone: string;
  upi_id: string;
  language_preference: string;
}

export interface InventoryResponse {
  store_id: string;
  total_products: number;
  low_stock_count: number;
  critical_stock_count: number;
  products: InventoryItem[];
  last_updated: string;
}

export interface InventoryItem {
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

export interface PnLSummary {
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

export interface DailyPnL {
  date: string;
  revenue: number;
  transactions: number;
  cash: number;
  upi: number;
  credit: number;
}

export interface ForecastResponse {
  store_id: string;
  forecast_days: number;
  forecasts: ProductForecast[];
  upcoming_festivals: Festival[];
  timestamp: string;
}

export interface ProductForecast {
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

export interface Festival {
  name: string;
  starts: string;
  days_until: number;
  duration_days: number;
  impact: "high" | "medium" | "low";
}

// ============ WebSocket Event Types ============

export interface WebSocketEvent {
  event: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface ConnectionEstablishedEvent extends WebSocketEvent {
  event: "connection_established";
  data: {
    store_id: string;
    session_id: string;
    message: string;
  };
}

export interface ReasoningStepEvent extends WebSocketEvent {
  event: "reasoning_step";
  data: {
    step_number: number;
    step_type: string;
    description: string;
    icon: string;
    details: Record<string, any>;
  };
}

export interface ChatMessageEvent extends WebSocketEvent {
  event: "chat_message";
  data: {
    message_id: string;
    sender: "ai" | "system";
    message_type: "text" | "markdown";
    content: string;
    language: string;
  };
}

export interface InventoryUpdateEvent extends WebSocketEvent {
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
}

export interface ProcurementOrderEvent extends WebSocketEvent {
  event: "procurement_order";
  data: {
    order_id: string;
    items: OrderItem[];
    total_cost: number;
    total_savings: number;
    distributor_split: DistributorOrder[];
    upi_links: UPILink[];
  };
}

export interface OrderItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  distributor: string;
}

export interface DistributorOrder {
  distributor_id: string;
  distributor_name: string;
  items: OrderItem[];
  subtotal: number;
  delivery_time: string;
}

export interface UPILink {
  distributor_name: string;
  amount: number;
  upi_link: string;
}

export interface UdhaarUpdateEvent extends WebSocketEvent {
  event: "udhaar_update";
  data: {
    customer_name: string;
    old_balance: number;
    new_balance: number;
    change: number;
    transaction_details: string;
  };
}

export interface PNLUpdateEvent extends WebSocketEvent {
  event: "pnl_update";
  data: {
    today_revenue: number;
    today_transactions: number;
    cash: number;
    upi: number;
    credit: number;
  };
}

export interface ErrorEvent extends WebSocketEvent {
  event: "error";
  data: {
    error_type: string;
    error_code: string;
    message: string;
    user_message: string;
    fallback_action?: "retry" | "skip" | "manual";
    retry_count?: number;
    max_retries?: number;
  };
}

// ============ Error Response ============

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

// ============ Utility Types ============

export type MessageType = "text" | "image" | "voice";
export type Language = "hinglish" | "hindi" | "english" | "kannada" | "tamil";
export type StockStatus = "healthy" | "low" | "critical";
export type Urgency = "critical" | "high" | "medium" | "low";
export type EventType =
  | "connection_established"
  | "reasoning_step"
  | "chat_message"
  | "inventory_update"
  | "procurement_order"
  | "udhaar_update"
  | "pnl_update"
  | "error";
```

---

## Error Handling

### Standard Error Format

All errors follow this structure:

```typescript
interface ErrorResponse {
  error: string;  // Error code/type
  message: string;  // Human-readable message
  details?: Record<string, any>;  // Optional additional info
  timestamp: string;  // ISO 8601
}
```

### HTTP Status Codes

| Code | Meaning | When It Happens |
|------|---------|-----------------|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Invalid input (missing fields, wrong types) |
| 404 | Not Found | Store doesn't exist |
| 500 | Server Error | Internal error (log it!) |
| 503 | Service Unavailable | Gemini API down (use demo mode) |

### Example Error Responses

**400 - Bad Request:**
```json
{
  "error": "validation_error",
  "message": "message_type must be one of: text, image, voice",
  "details": {
    "field": "message_type",
    "provided": "audio",
    "allowed": ["text", "image", "voice"]
  },
  "timestamp": "2026-02-14T14:30:00Z"
}
```

**404 - Not Found:**
```json
{
  "error": "store_not_found",
  "message": "Store not found: invalid_store_123",
  "timestamp": "2026-02-14T14:30:00Z"
}
```

**500 - Server Error:**
```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred",
  "details": {
    "error_id": "err_xyz123"
  },
  "timestamp": "2026-02-14T14:30:00Z"
}
```

### Error Handling Best Practices

```typescript
async function sendMessage(request: MessageRequest) {
  try {
    const response = await fetch('http://localhost:8000/api/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error: ErrorResponse = await response.json();

      switch (response.status) {
        case 400:
          // Validation error - show to user
          alert(error.message);
          break;
        case 404:
          // Store not found - redirect to setup
          window.location.href = '/setup';
          break;
        case 500:
          // Server error - retry or show generic message
          console.error('Server error:', error);
          alert('Something went wrong. Please try again.');
          break;
        case 503:
          // Service unavailable - use demo mode or show maintenance
          alert('Service temporarily unavailable. Try demo mode.');
          break;
      }

      throw new Error(error.message);
    }

    return await response.json() as MessageResponse;
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}
```

---

## Demo Mode

### Overview

Demo mode allows frontend development **without a Gemini API key** using cached responses.

### Enable Demo Mode

**In backend `.env` file:**
```env
DEMO_MODE=true
```

Then restart the backend:
```bash
uvicorn main:app --reload
```

### What You Get

✅ **All message types work**
- Text queries → Instant AI responses
- Shelf photos → Complete product detection + procurement order
- Parchi images → OCR extraction + inventory updates
- Voice messages → Transcription + stock updates

✅ **Realistic data**
- Matches production format exactly
- Includes all fields
- WebSocket events fire correctly

✅ **Fast & reliable**
- < 100ms response time
- No network issues
- Perfect for testing

### Demo Scenarios

#### 1. Shelf Photo Analysis

**Input:** Any image with `metadata.image_type = "shelf"`

**Output:**
- 8 products detected
- 2 critical stock alerts
- Festival context (Navratri in 2 days)
- Procurement order worth ₹44,996
- ₹5,124 savings highlighted

#### 2. Kacchi Parchi OCR

**Input:** Any image with `metadata.image_type = "parchi"`

**Output:**
- 4 transactions extracted
- 1 uncertain item (68% confidence)
- Payment breakdown: ₹266 cash, ₹105 UPI, ₹140 udhaar
- Udhaar ledger updated

#### 3. Voice Message

**Input:** Any audio with `message_type = "voice"`

**Output:**
- Hinglish transcription
- SALE intent detected (94% confidence)
- Stock updated
- Negative stock alert

### Testing Demo Mode

```bash
# Test shelf photo
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "sharma_general_store",
    "message_type": "image",
    "content": "data:image/jpeg;base64,fake_data_here",
    "metadata": {"image_type": "shelf"}
  }'

# Result: Instant response with full shelf analysis
```

### Demo Mode vs Production

| Feature | Demo Mode | Production |
|---------|-----------|------------|
| Speed | < 100ms | 2-5 seconds |
| API Key | Not needed | Required |
| Network | Works offline | Needs internet |
| Responses | Fixed/cached | Dynamic/real |
| WebSocket | Full support | Full support |
| Accuracy | Sample data | Real AI |

**Perfect for:**
- Frontend development
- Offline presentations
- Testing UI flows
- Hackathon demos

---

## Integration Checklist

### Phase 1: Setup ✅

- [ ] Backend running at `http://localhost:8000`
- [ ] Health check returns `200 OK`
- [ ] `/docs` endpoint accessible (Swagger UI)
- [ ] TypeScript types copied to project
- [ ] API client configured with base URL

### Phase 2: Message API ✅

- [ ] Can send text messages
- [ ] Can send image messages (base64 encoded)
- [ ] Can send voice messages (base64 encoded)
- [ ] Handle `metadata.image_type` for shelf vs parchi
- [ ] Parse `MessageResponse` correctly
- [ ] Extract `websocket_channel` URL

### Phase 3: WebSocket ✅

- [ ] Connect to WebSocket endpoint
- [ ] Handle `connection_established` event
- [ ] Display `reasoning_step` events (AI thinking)
- [ ] Show `chat_message` responses
- [ ] Update UI on `inventory_update`
- [ ] Display `procurement_order` details
- [ ] Handle `error` events gracefully
- [ ] Reconnect on disconnect

### Phase 4: Store Data ✅

- [ ] Fetch store profile
- [ ] Display inventory list
- [ ] Show stock status (healthy/low/critical)
- [ ] Format currency in lakhs (₹1,50,000)
- [ ] Display P&L summary
- [ ] Render demand forecast
- [ ] Show upcoming festivals

### Phase 5: Error Handling ✅

- [ ] Handle 400 validation errors
- [ ] Handle 404 store not found
- [ ] Handle 500 server errors
- [ ] Handle 503 service unavailable
- [ ] Show user-friendly messages
- [ ] Implement retry logic for 503
- [ ] Log errors for debugging

### Phase 6: Polish ✅

- [ ] Loading states during processing
- [ ] Typing indicators (from reasoning steps)
- [ ] Success/error toasts
- [ ] Offline mode detection
- [ ] Demo mode toggle
- [ ] Mobile-responsive UI

### Ready to Ship! 🚀

Once all checkboxes are checked, your integration is complete!

---

## Quick Reference

### All Endpoints

```
GET  /health
POST /api/message
GET  /api/store/{store_id}/profile
GET  /api/store/{store_id}/inventory
GET  /api/store/{store_id}/pnl?days=30
GET  /api/store/{store_id}/forecast?days=7
WS   /ws/{store_id}
```

### All WebSocket Events

```
connection_established → Connected successfully
reasoning_step        → AI thinking process
chat_message         → AI response
inventory_update     → Stock changed
procurement_order    → Order generated
udhaar_update        → Credit ledger updated
pnl_update          → P&L summary updated
error               → Error occurred
```

### Common Status Codes

```
200 → Success
400 → Bad Request (fix your input)
404 → Not Found (check store_id)
500 → Server Error (backend issue)
503 → Service Unavailable (try demo mode)
```

---

## Support

### Questions?

1. **Check Interactive Docs:** http://localhost:8000/docs
2. **View Alternative Docs:** http://localhost:8000/redoc
3. **Test in Demo Mode:** Set `DEMO_MODE=true`
4. **Check Backend Logs:** `tail -f kirana-backend/logs/*.log`

### Common Issues

**"Connection refused"**
→ Backend not running. Start with: `uvicorn main:app --reload`

**"Store not found"**
→ Check `store_id`. Use: `sharma_general_store` (demo store)

**"Gemini API timeout"**
→ Enable demo mode or check API key

**"WebSocket disconnected"**
→ Normal after idle. Reconnect automatically.

---

## Contract Version History

### v1.0 (2026-02-14) - CURRENT

- Initial frozen contract
- All 7 endpoints defined
- 8 WebSocket event types
- TypeScript types provided
- Demo mode documented

**Breaking Changes:** NONE allowed in v1.x

---

**🎉 You're all set! Start building your Next.js frontend with confidence!**

*This contract is frozen for the hackathon. Any questions or issues, check the interactive docs at /docs or enable demo mode.*
