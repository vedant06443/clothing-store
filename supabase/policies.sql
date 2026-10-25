-- ==============================================================================
-- Suyog Textile — Row Level Security (RLS) Policies
-- File: supabase/policies.sql
-- Run after schema.sql.
-- ==============================================================================

-- 1. ENABLE RLS ON ALL TABLES
alter table public.profiles enable row level security;
alter table public.addresses enable row level security;
alter table public.categories enable row level security;
alter table public.products enable row level security;
alter table public.coupons enable row level security;
alter table public.settings enable row level security;
alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.admin_audit_log enable row level security;

-- 2. CATEGORIES POLICIES
-- Public can view all categories. Only admins can modify.
drop policy if exists "Categories are viewable by everyone" on public.categories;
create policy "Categories are viewable by everyone"
  on public.categories for select
  using (true);

drop policy if exists "Admins have full access to categories" on public.categories;
create policy "Admins have full access to categories"
  on public.categories for all
  to authenticated
  using (public.is_admin())
  with check (public.is_admin());

-- 3. PRODUCTS POLICIES
-- Public can only view active products. Admins can view all and manage.
drop policy if exists "Active products are viewable by everyone" on public.products;
create policy "Active products are viewable by everyone"
  on public.products for select
  using (is_active = true or public.is_admin());

drop policy if exists "Admins have write access to products" on public.products;
create policy "Admins have write access to products"
  on public.products for insert
  to authenticated
  with check (public.is_admin());

drop policy if exists "Admins can update products" on public.products;
create policy "Admins can update products"
  on public.products for update
  to authenticated
  using (public.is_admin())
  with check (public.is_admin());

drop policy if exists "Admins can delete products" on public.products;
create policy "Admins can delete products"
  on public.products for delete
  to authenticated
  using (public.is_admin());

-- 4. SETTINGS POLICIES
-- Public can view only whitelisted storefront keys. Admins have full access.
drop policy if exists "Whitelisted settings are public" on public.settings;
create policy "Whitelisted settings are public"
  on public.settings for select
  using (
    key in (
      'free_shipping_threshold',
      'shipping_fee',
      'store_hours',
      'store_address',
      'store_phones',
      'whatsapp_number',
      'social_links'
    )
    or public.is_admin()
  );

drop policy if exists "Admins can manage settings" on public.settings;
create policy "Admins can manage settings"
  on public.settings for all
  to authenticated
  using (public.is_admin())
  with check (public.is_admin());

-- 5. COUPONS POLICIES
-- NO public select! Only admins can read/write coupons directly.
-- Public coupon validation is executed securely via validate_coupon() RPC.
drop policy if exists "Coupons are only accessible to admins" on public.coupons;
create policy "Coupons are only accessible to admins"
  on public.coupons for all
  to authenticated
  using (public.is_admin())
  with check (public.is_admin());

-- 6. PROFILES POLICIES
-- Users can view and edit their own profile. Admins can view all profiles.
drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
  on public.profiles for select
  to authenticated
  using (id = auth.uid() or public.is_admin());

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
  on public.profiles for update
  to authenticated
  using (id = auth.uid() or public.is_admin())
  with check (id = auth.uid() or public.is_admin());

-- 7. ADDRESSES POLICIES
-- Users have full CRUD over their own addresses.
drop policy if exists "Users can view own addresses" on public.addresses;
create policy "Users can view own addresses"
  on public.addresses for select
  to authenticated
  using (user_id = auth.uid() or public.is_admin());

drop policy if exists "Users can insert own addresses" on public.addresses;
create policy "Users can insert own addresses"
  on public.addresses for insert
  to authenticated
  with check (user_id = auth.uid());

drop policy if exists "Users can update own addresses" on public.addresses;
create policy "Users can update own addresses"
  on public.addresses for update
  to authenticated
  using (user_id = auth.uid() or public.is_admin())
  with check (user_id = auth.uid() or public.is_admin());

drop policy if exists "Users can delete own addresses" on public.addresses;
create policy "Users can delete own addresses"
  on public.addresses for delete
  to authenticated
  using (user_id = auth.uid() or public.is_admin());

-- 8. ORDERS POLICIES
-- Direct client insert is disallowed (must use place_order RPC).
-- Authenticated customers can view only their own orders. Admins can view all.
drop policy if exists "Users can view own orders" on public.orders;
create policy "Users can view own orders"
  on public.orders for select
  to authenticated
  using (user_id = auth.uid() or public.is_admin());

drop policy if exists "Admins can update orders" on public.orders;
create policy "Admins can update orders"
  on public.orders for update
  to authenticated
  using (public.is_admin())
  with check (public.is_admin());

-- Notice: No DELETE policy is created on orders. Orders cannot be deleted by anyone.

-- 9. ORDER ITEMS POLICIES
-- Direct client insert is disallowed.
-- Customers can view items belonging to their own orders. Admins can view all.
drop policy if exists "Users can view own order items" on public.order_items;
create policy "Users can view own order items"
  on public.order_items for select
  to authenticated
  using (
    exists (
      select 1 from public.orders o
      where o.id = order_items.order_id
        and (o.user_id = auth.uid() or public.is_admin())
    )
  );

-- Notice: No DELETE policy on order_items.

-- 10. ADMIN AUDIT LOG POLICIES
-- Only admins can read audit logs. Nobody can update or delete logs.
drop policy if exists "Only admins can view audit log" on public.admin_audit_log;
create policy "Only admins can view audit log"
  on public.admin_audit_log for select
  to authenticated
  using (public.is_admin());

-- ==============================================================================
-- STORAGE BUCKET: product-images
-- ==============================================================================
-- Create product-images bucket if storage schema exists
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'product-images',
  'product-images',
  true,
  2097152, -- 2 MB
  array['image/jpeg', 'image/png', 'image/webp']
)
on conflict (id) do update set
  public = true,
  file_size_limit = 2097152,
  allowed_mime_types = array['image/jpeg', 'image/png', 'image/webp'];

-- Storage RLS Policies
drop policy if exists "Public can view product images" on storage.objects;
create policy "Public can view product images"
  on storage.objects for select
  using (bucket_id = 'product-images');

drop policy if exists "Admins can upload product images" on storage.objects;
create policy "Admins can upload product images"
  on storage.objects for insert
  to authenticated
  with check (
    bucket_id = 'product-images' and
    public.is_admin()
  );

drop policy if exists "Admins can update product images" on storage.objects;
create policy "Admins can update product images"
  on storage.objects for update
  to authenticated
  using (
    bucket_id = 'product-images' and
    public.is_admin()
  );

drop policy if exists "Admins can delete product images" on storage.objects;
create policy "Admins can delete product images"
  on storage.objects for delete
  to authenticated
  using (
    bucket_id = 'product-images' and
    public.is_admin()
  );
