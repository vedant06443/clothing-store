# Suyog Textile — Supabase Backend & Admin Setup Guide

This guide provides step-by-step instructions to configure, initialize, and maintain the Supabase backend for **Suyog Textile** (`https://suyogtextile.in`).

---

## Architecture & Security Overview

- **Static Frontend**: Hosted on Render Static Sites (or Apache / cPanel).
- **Backend-as-a-Service**: Supabase (Postgres Database, GoTrue Auth, Storage, Edge Functions).
- **Zero Client Secrets**:
  - The `supabaseUrl` and `supabaseAnonKey` in `assets/js/config.js` are **public by design**.
  - **Security is enforced strictly in the database** using Row Level Security (RLS) policies, triggers, and `SECURITY DEFINER` functions.
  - The `service_role` key and database passwords must **NEVER** be committed to Git or embedded in frontend code.

---

## Step 1: Create Your Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and create a free account or sign in.
2. Click **New Project**:
   - **Name**: `suyog-textile`
   - **Database Password**: Generate and securely save a strong password (keep this in your password manager; do not put it in the codebase).
   - **Region**: Select `ap-south-1 (Mumbai)` for lowest latency for Indian shoppers.
3. Once the project finishes provisioning, go to **Project Settings** (gear icon) -> **API**:
   - Copy the **Project URL** (e.g. `https://xyzcompany.supabase.co`).
   - Copy the **`anon` `public` API key**.
4. Open [assets/js/config.js](file:///assets/js/config.js) in this repository and paste the values:
   ```javascript
   supabaseUrl: 'https://YOUR_PROJECT_REF.supabase.co',
   supabaseAnonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
   ```

---

## Step 2: Run Database Migrations in SQL Editor

In your Supabase dashboard, click **SQL Editor** (icon `>_` on the left sidebar). Run the following SQL scripts in **exact chronological order**:

### Execution Order:

1. **`supabase/schema.sql`**:
   - Creates custom ENUM types (`user_role`, `order_status`, `payment_method`, `payment_status`, `discount_type`).
   - Creates all 9 tables:
     - `profiles`: Linked to `auth.users`. Contains role (`customer`, `admin`).
     - `addresses`: Customer shipping and billing addresses.
     - `categories`: Product category hierarchy.
     - `products`: Product catalog with integer INR prices, stock, and attributes.
     - `coupons`: Promotional discount rules.
     - `settings`: Whitelisted store settings (shipping threshold, phone, email, etc.).
     - `orders`: Master order ledger.
     - `order_items`: Line items with price snapshots.
     - `admin_audit_log`: Immutable change log.
   - Sets up triggers:
     - `on_auth_user_created`: Auto-creates customer profile upon sign up.
     - `protect_profile_role`: Blocks non-admin users from escalating their role.
     - `restore_stock_on_cancel`: Restores product inventory when an order status is marked as `cancelled`.
     - `audit_products` & `audit_coupons`: Automatically records staff actions.
   - Installs Security Definer RPC functions:
     - `is_admin()`: Safe role verification.
     - `validate_coupon(p_code, p_order_inr)`: Validates coupon and computes discount.
     - `place_order(...)`: Atomically creates orders, verifies prices against live DB, validates coupons, and decrements stock.
     - `get_order_status(p_order_no, p_phone)`: Allows guests to track their order safely without exposing sensitive records.

2. **`supabase/policies.sql`**:
   - Enables Row Level Security (RLS) on all 9 tables.
   - Restricts sensitive customer orders, addresses, and profiles so users can only view and edit their own data.
   - Grants showroom administrators full management access based on `is_admin()`.
   - Protects the `coupons` table so coupon formulas cannot be scraped by anonymous visitors.
   - Configures storage policies for the `product-images` bucket.

3. **`supabase/seed.sql`**:
   - Inserts store categories (`Sarees`, `Kurtis`, `Lehengas`, `Salwar Suits`, `Gowns`, `Menswear`).
   - Seeds initial store configuration parameters (`free_shipping_threshold_inr`, showroom phone, address, timings).
   - Inserts standard promotional coupons (`WELCOME10`, `FESTIVE20`, `FLAT500`).
   - Inserts the complete initial catalog of 12 luxury products with exact Indian Rupee prices and initial inventory counts.

4. **`supabase/tests.sql`**:
   - Executes an automated test suite verifying:
     - Role elevation block for anonymous/customer users.
     - RLS boundaries (ensuring customers cannot view other customers' orders).
     - Accurate pricing and coupon calculation.
     - Free shipping threshold logic (test orders at ₹1,498, ₹1,499, and ₹1,500).
   - Inspect the query results: All test cases must return `PASS`.

---

## Step 3: Configure Authentication Settings

In the Supabase dashboard, navigate to **Authentication** -> **URL Configuration**:

1. **Site URL**:
   - Set to `https://suyogtextile.in` (or `http://localhost:3000` / `http://127.0.0.1:5500` during local testing).
2. **Redirect URLs**:
   Add the following paths:
   - `https://suyogtextile.in/login.html`
   - `https://suyogtextile.in/account.html`
   - `https://suyogtextile.in/admin/index.html`
3. **Email Auth Settings** (under **Authentication** -> **Providers** -> **Email**):
   - **Enable Email Provider**: ON
   - **Confirm email**:
     - For production: Keep ON. Supabase sends confirmation emails to verify customer addresses.
     - For instant testing: You may temporarily toggle OFF to sign in immediately without clicking an email link.

---

## Step 4: Create the Storage Bucket for Product Images

1. In the Supabase dashboard, click **Storage** (folder icon) -> **New Bucket**.
2. **Bucket Name**: `product-images` (must match exactly).
3. **Public bucket**: Toggle **ON** (so shoppers can view product photos on the site).
4. **File size limit**: `2MB` (`2097152 bytes`).
5. **Allowed MIME types**: `image/jpeg`, `image/png`, `image/webp`.
6. Click **Save Bucket**.
   *(Note: The access policies are already established by `supabase/policies.sql` — anyone can read photos, but only administrators can upload or delete them).*

---

## Step 5: Bootstrap Your First Administrator Account

Because `profiles.role` cannot be updated through the browser or public API (protected by database trigger `protect_profile_role`), the first showroom administrator must be bootstrapped via the Supabase SQL Editor:

1. Visit your live store or local site at `https://suyogtextile.in/login.html`.
2. Click **Create an Account** and register your showroom admin email (e.g., `admin@suyogtextile.in` or your personal email) with a strong password.
3. Open the **Supabase SQL Editor** and execute the elevation query:
   ```sql
   UPDATE public.profiles
   SET role = 'admin'
   WHERE id IN (
     SELECT id FROM auth.users WHERE email = 'admin@suyogtextile.in'
   );
   ```
4. Verify elevation:
   ```sql
   SELECT id, full_name, role FROM public.profiles WHERE role = 'admin';
   ```
5. You can now access the administrative portal at `https://suyogtextile.in/admin/` and sign in.

---

## Step 6: Deploying to Render & Apache / cPanel

### Render Deployment (Static Site):
1. Connect your GitHub repository to Render.
2. Select **Static Site**.
3. **Build Command**: Leave empty (no build step is needed).
4. **Publish Directory**: `./public` (or `public`).
5. **Environment Variables**: None required (all public config is in `assets/js/config.js`).
6. The `render.yaml` file in the repo root will automatically apply standard URL redirects.

### Apache / cPanel Deployment (Git Version Control):
1. In cPanel, go to **Domains** and verify the exact **Document Root** for `suyogtextile.in` (e.g. `/home/username/public_html/` or `/home/username/suyogtextile.in/`).
2. Open `.cpanel.yml` and set `export DEPLOYPATH=/home/YOUR_CPANEL_USER/YOUR_DOCUMENT_ROOT/`.
3. In cPanel -> **Git™ Version Control**, click **Update from Remote** followed by **Deploy HEAD Commit**.
4. Test self-verification: visit `https://suyogtextile.in/deploy-check.txt` in your browser. It will immediately print the deployed commit SHA and timestamp!
5. All live web files are automatically copied from `public/.` into your document root, while `supabase/`, docs, and backend test scripts stay protected outside the web server.

---

## Step 7: Database Backup & Maintenance

### Automated Backups
- Supabase automatically takes daily backups of your Postgres database.
- You can review and restore backups under **Project Settings** -> **Database** -> **Backups**.

### Manual Snapshot via CLI / pg_dump
To take an off-site backup at any time using your Supabase database connection string (found under **Project Settings** -> **Database**):
```bash
pg_dump "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" > backup_$(date +%Y%m%d).sql
```

---

## Step 8: Phase 5 (Online Payment via Razorpay) Roadmap

*Phase 5 is currently disabled in the storefront (`onlinePaymentEnabled: false`).*

When the store is ready to accept online payments (Cards, UPI, Netbanking):
1. Create a Razorpay merchant account and get your Key ID and Key Secret.
2. Add the Razorpay Key Secret into Supabase Vault / Secrets:
   ```bash
   supabase secrets set RAZORPAY_KEY_SECRET=your_secret_key
   ```
3. Deploy a Supabase Edge Function `create-razorpay-order`:
   - It receives `{ order_id, amount_inr }`.
   - Validates the order against Supabase Postgres.
   - Calls Razorpay API to generate a `razorpay_order_id`.
   - Returns `{ razorpay_order_id, key_id }` to the frontend.
4. Set `onlinePaymentEnabled: true` in `assets/js/config.js`.

---

## Business Parameters Verification Checklist (`TODO_CONFIRM`)

Review and confirm the following business parameters before launch:

| Parameter | Location | Current Configured Value | Description |
|---|---|---|---|
| `supabaseUrl` | `assets/js/config.js` | `TODO_CONFIRM` | Your live Supabase project URL |
| `supabaseAnonKey` | `assets/js/config.js` | `TODO_CONFIRM` | Your live Supabase anon public API key |
| `freeShippingThreshold` | `assets/js/config.js` & `settings` table | `1499` | Free shipping threshold in INR |
| `shippingFee` | `assets/js/config.js` & `settings` table | `99` | Flat standard shipping fee under threshold |
| `codFee` | `assets/js/config.js` & `settings` table | `0` | Cash on Delivery convenience charge |
| `phones` | `assets/js/config.js` | `0253 4515460`, `+91 86693 96037` | Showroom landline and mobile |
| `whatsappNumber` | `assets/js/config.js` | `918669396037` | WhatsApp business contact number |
| `address` | `assets/js/config.js` | `Lahoti Mala, 484, Jadhav Sankul road, Ashoknagar, Satpur Colony, Nashik 422007` | Showroom physical location |
| `adminEmail` | Supabase Auth & `admin/index.html` | To be created by owner | Primary showroom manager email |
