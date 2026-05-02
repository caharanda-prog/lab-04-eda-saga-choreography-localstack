# Event-Driven Saga Choreography (Order Processing)

## 🧩 Business Flow Overview

This project simulates an order processing system using an event-driven saga choreography pattern.

The goal is to coordinate multiple independent services (Order, Inventory, Payment) without a central orchestrator, ensuring consistency through events and compensating actions.

---

## 🔄 End-to-End Flow

### 🟢 Happy Path (Order Completed)

1. **OrderCreated** → An order is created
2. **InventorySuccess** → Inventory is successfully reserved
3. **PaymentSuccess** → Payment is processed
4. **OrderCompleted** → Order is finalized

---

### 🔴 Inventory Failure

1. **OrderCreated**
2. **InventoryFailed**
3. **OrderCancelled**

---

### 🔴 Payment Failure (with Compensation)

1. **OrderCreated**
2. **InventorySuccess**
3. **PaymentFailed**
4. **InventoryReleaseRequested**
5. **InventoryReleased**
6. **OrderCancelled**

---

## 🧠 Key Idea

Each service reacts to events and emits new ones.

There is no central coordinator. Instead, the system relies on:

* Event propagation
* Local decisions per service
* Compensation actions for rollback scenarios

---

## 🧾 Example Saga Timeline

```
ORD-7718:
OrderCreated
InventorySuccess
PaymentFailed
InventoryReleaseRequested
InventoryReleased
OrderCancelled
```

---

## 📊 Completed Orders Log (Business Traceability)

In addition to real-time event processing, the system maintains a persistent log of **completed sagas**.

A saga is considered complete when it reaches a terminal state:

* **OrderCompleted**
* **OrderCancelled**

For each completed order, the system stores the full sequence of events that occurred during its lifecycle.

This provides:

* End-to-end traceability per order
* Visibility into successful and failed flows
* Insight into where and why a process failed
* A clear separation between in-progress and finalized orders

---

### 🧾 Example Record

```json
  "ORD-2526": {
    "orderId": "ORD-2526",
    "finalStatus": "OrderCancelled",
    "events": [
      "OrderCreated",
      "InventorySuccess",
      "PaymentFailed",
      "InventoryReleaseRequested",
      "OrderCancelled",
      "InventoryReleased"
    ],
    "completedAt": "2026-05-02T14:58:00.866462"
  }
```

---

This log acts as a lightweight projection of the system state, enabling easier debugging, analysis, and validation of the saga lifecycle.

