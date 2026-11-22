# Custom trip planner

## API

All paths below are under `/api/`.

| Method and path | Access | Purpose |
| --- | --- | --- |
| `GET /trip-planner/options/` | Public | Active destinations, accommodation, transport, activities, budgets, travel styles, and active seasonal rates. |
| `POST /trip-planner/inquiries/` | Public, throttled to 5 requests/hour per IP | Validate and save an enquiry. Returns a reference ID, estimate snapshot, and WhatsApp URL when configured. |
| `GET /trip-planner/inquiries/` | Django staff | Paginated enquiry list. Supports `search`, `status`, `departure_date`, `budget_band__slug`, `destination`, `limit`, and `offset` query parameters. |
| `GET /trip-planner/inquiries/{reference_id}/` | Django staff | Read the enquiry and customer details. |
| `PATCH /trip-planner/inquiries/{reference_id}/` | Django staff | Update enquiry status and internal notes. |
| `POST /trip-planner/inquiries/{reference_id}/quotation/` | Django staff | Create a quotation. |
| `PATCH /trip-planner/inquiries/{reference_id}/quotation/` | Django staff | Update an existing quotation. |

The public submission accepts customer/contact fields, dates, traveller counts, destination, activity, and additional-service slug lists, optional stay, transport, budget, and travel-style slugs, plus optional food and special requirements. Budget scope is `per_person` or `total`. The public response intentionally omits contact details. Customer enquiry reads and updates are restricted to staff.

## Data and pricing

`PlannerPlace`, `PlannerStayOption`, `PlannerTransportOption`, `PlannerActivity`, `PlannerAdditionalService`, `PlannerBudgetBand`, `PlannerTravelStyle`, and `PlannerSeasonRate` are editable in Django Admin. The initial catalog is added by migration `0011_seed_trip_planner_options`. Rate fields are left blank so the planner displays “Request a Personalized Quote” until the business configures real amounts.

The system stores `TripInquiry`, its destination/activity/additional-service selections, and an optional `TripQuotation`. Estimates use only configured catalog amounts and active seasonal rates. Estimates are indicative; quotations are entered by staff and totals are calculated from their component amounts.

## Render deployment

The existing Render build command runs `python manage.py migrate`, so migrations `0010` and `0011` apply during deployment without resetting existing tables or records. The existing `DATABASE_URL` should remain the Render PostgreSQL connection string.

`BUSINESS_WHATSAPP_NUMBER` is an optional Render environment variable containing the international-format number with digits only. If omitted, the backend uses the number already present in the frontend contact configuration. Catalog options and configured prices can be reviewed in Django Admin after deployment.
