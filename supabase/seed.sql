-- ==============================================================================
-- Suyog Textile — Supabase Database Seed Data
-- File: supabase/seed.sql
-- Run after schema.sql and policies.sql.
-- ==============================================================================

-- 1. SEED CATEGORIES
insert into public.categories (slug, name, sort)
values
  ('sarees', 'Sarees', 1),
  ('lehengas', 'Bridal & Party Lehengas', 2),
  ('salwar-suits', 'Salwar Suits & Anarkalis', 3),
  ('kurtis', 'Readymade Kurtis', 4),
  ('dresses', 'Indo-Western & Gowns', 5),
  ('mens-wear', 'Mens Ethnic & Kurta Sets', 6)
on conflict (slug) do update set
  name = excluded.name,
  sort = excluded.sort;

-- 2. SEED SETTINGS
insert into public.settings (key, value, description)
values
  ('free_shipping_threshold', '{"free_shipping_threshold": 1499}'::jsonb, 'Subtotal in INR above which shipping is free'),
  ('shipping_fee', '{"shipping_fee": 0}'::jsonb, 'TODO_CONFIRM: Shipping fee in INR for orders below free shipping threshold (seeded as 0)'),
  ('store_hours', '{"store_hours": "10:00 AM – 8:30 PM, all days"}'::jsonb, 'Showroom operating hours'),
  ('store_address', '{"store_address": "Lahoti Mala, 484, Jadhav Sankul road, Ashoknagar, Satpur Colony, Nashik, Maharashtra 422007"}'::jsonb, 'Physical showroom address in Nashik'),
  ('store_phones', '{"store_phones": ["0253 4515460", "+91 86693 96037"]}'::jsonb, 'Contact landline and mobile numbers'),
  ('whatsapp_number', '{"whatsapp_number": "918669396037"}'::jsonb, 'Official WhatsApp ordering number')
on conflict (key) do update set
  value = excluded.value,
  description = excluded.description;

-- 3. SEED COUPONS
insert into public.coupons (code, type, value, min_order_inr, category_slugs, starts_at, is_active)
values
  (
    'WELCOME10',
    'percent',
    10,
    999,
    array['sarees', 'kurtis'],
    now() - interval '1 day',
    true
  ),
  (
    'FESTIVE20',
    'percent',
    20,
    2999,
    array['lehengas', 'salwar-suits', 'dresses'],
    now() - interval '1 day',
    true
  ),
  (
    'FLAT500',
    'flat',
    500,
    3999,
    array['sarees'],
    now() - interval '1 day',
    true
  )
on conflict (code) do update set
  type = excluded.type,
  value = excluded.value,
  min_order_inr = excluded.min_order_inr,
  category_slugs = excluded.category_slugs,
  is_active = excluded.is_active;

-- 4. SEED PRODUCTS
-- Migrated directly from verified catalog in assets/data/products.js
-- Using category lookups to assign correct category_id foreign keys.
do $$
declare
  cat_sarees uuid;
  cat_lehengas uuid;
  cat_suits uuid;
  cat_kurtis uuid;
  cat_mens uuid;
begin
  select id into cat_sarees from public.categories where slug = 'sarees';
  select id into cat_lehengas from public.categories where slug = 'lehengas';
  select id into cat_suits from public.categories where slug = 'salwar-suits';
  select id into cat_kurtis from public.categories where slug = 'kurtis';
  select id into cat_mens from public.categories where slug = 'mens-wear';

  -- Product 1
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    1,
    'crimson-red-royal-banarasi-katan-silk-saree',
    'Crimson Red Royal Banarasi Katan Silk Saree',
    cat_sarees,
    'Exquisite handwoven Banarasi Katan silk saree woven with real gold-toned zari kadwa technique. Includes matching unstitched blouse piece. Features opulent floral jaal work.',
    8999,
    12999,
    array['Free Size (5.5m + 0.8m Blouse)'],
    15,
    array[
      'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80',
      'https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=800&q=80',
      'https://images.unsplash.com/photo-1609357605129-26f69add5d6e?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 2
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    2,
    'peacock-blue-handloom-kanjivaram-silk-saree',
    'Peacock Blue Handloom Kanjivaram Silk Saree',
    cat_sarees,
    'Authentic Kanchipuram silk saree in majestic peacock blue with contrasting crimson red korvai temple border and rich brocade pallu.',
    9999,
    15999,
    array['Free Size'],
    8,
    array[
      'https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=800&q=80',
      'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 3
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    3,
    'pastel-pink-organza-floral-hand-embroidered-saree',
    'Pastel Pink Organza Floral Hand-Embroidered Saree',
    cat_sarees,
    'Delicate sheer organza saree with pastel floral resham embroidery, scalloped gota patti borders, and lightweight breezy drape perfect for daytime soirees.',
    2799,
    4499,
    array['Free Size'],
    20,
    array[
      'https://images.unsplash.com/photo-1609357605129-26f69add5d6e?w=800&q=80',
      'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 4
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    4,
    'emerald-green-chanderi-silk-zari-work-saree',
    'Emerald Green Chanderi Silk Zari Work Saree',
    cat_sarees,
    'Traditional Chanderi woven saree featuring subtle gold zari bootis across the body with rich contrast border and pallu.',
    3499,
    5999,
    array['Free Size'],
    12,
    array[
      'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80',
      'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 5
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    5,
    'royal-velvet-bridal-lehenga-choli-set',
    'Royal Velvet Bridal Lehenga Choli Set',
    cat_lehengas,
    'Showstopper bridal masterpiece in deep micro-velvet adorned with dabka, nakshi, and zardozi handcraft. Set includes lehenga skirt, choli, and double net dupattas.',
    14999,
    24999,
    array['Semi-Stitched (Fits XS to XXL)'],
    5,
    array[
      'https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=800&q=80',
      'https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 6
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    6,
    'handcrafted-georgette-mirror-work-designer-lehenga',
    'Handcrafted Georgette Mirror Work Designer Lehenga',
    cat_lehengas,
    'Contemporary festive flared lehenga with genuine foil mirror work, thread highlights, and ruffled dupatta edge.',
    6499,
    10999,
    array['S', 'M', 'L', 'XL'],
    9,
    array[
      'https://images.unsplash.com/photo-1566737236500-c8ac43014a67?w=800&q=80',
      'https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 7
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    7,
    'wine-pure-chanderi-silk-embroidered-anarkali-suit',
    'Wine Pure Chanderi Silk Embroidered Anarkali Suit',
    cat_suits,
    'Regal floor-length Anarkali silhouette tailored in lustrous Chanderi silk with delicate thread embroidery on yoke and matching printed silk dupatta.',
    4299,
    6999,
    array['M', 'L', 'XL', 'XXL'],
    14,
    array[
      'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80',
      'https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 8
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    8,
    'powder-blue-georgette-sharara-suit-set',
    'Powder Blue Georgette Sharara Suit Set',
    cat_suits,
    'Trendy 3-piece georgette sharara suit featuring peplum style kurti with Lucknowi chikankari touch, wide flare sharara, and chiffon dupatta.',
    3299,
    5499,
    array['S', 'M', 'L', 'XL'],
    11,
    array[
      'https://images.unsplash.com/photo-1609357605129-26f69add5d6e?w=800&q=80',
      'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 9
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    9,
    'mustard-yellow-cotton-silk-straight-daily-kurti',
    'Mustard Yellow Cotton Silk Straight Daily Kurti',
    cat_kurtis,
    'Comfort-fit breathable cotton silk daily kurti with contrast potli button detailing and 3/4th sleeves. Ideal for office and festive puja.',
    1299,
    1999,
    array['S', 'M', 'L', 'XL', 'XXL'],
    25,
    array[
      'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80',
      'https://images.unsplash.com/photo-1609357605129-26f69add5d6e?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 10
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    10,
    'ivory-chikankari-georgette-long-festive-kurti',
    'Ivory Chikankari Georgette Long Festive Kurti',
    cat_kurtis,
    'Authentic hand-embroidered Lucknowi chikankari kurti on soft viscose georgette with subtle mukaish embellishments. Includes soft inner slip.',
    1899,
    2999,
    array['M', 'L', 'XL'],
    18,
    array[
      'https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=800&q=80',
      'https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 11
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    11,
    'royal-navy-raw-silk-sherwani-set-with-stole',
    'Royal Navy Raw Silk Sherwani Set with Stole',
    cat_mens,
    'Groom and wedding wear raw silk sherwani featuring intricate thread work on mandarin collar and cuffs, paired with churidar and contrast zari stole.',
    8999,
    14999,
    array['38', '40', '42', '44'],
    6,
    array[
      'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80',
      'https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

  -- Product 12
  insert into public.products (id, slug, name, category_id, description, price_inr, mrp_inr, sizes, stock, image_paths, is_active)
  values (
    12,
    'maroon-embroidered-silk-kurta-churidar-set',
    'Maroon Embroidered Silk Kurta Churidar Set',
    cat_mens,
    'Festive silk blend kurta pyjama set in rich maroon with antique gold hand embroidery along placket. Perfect for diwali, puja, and sangeet celebrations.',
    2499,
    3999,
    array['38', '40', '42', '44'],
    16,
    array[
      'https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80',
      'https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=800&q=80'
    ],
    true
  ) on conflict (slug) do update set
    name = excluded.name,
    category_id = excluded.category_id,
    description = excluded.description,
    price_inr = excluded.price_inr,
    mrp_inr = excluded.mrp_inr,
    sizes = excluded.sizes,
    stock = excluded.stock,
    image_paths = excluded.image_paths,
    is_active = excluded.is_active;

end $$;

-- Reset sequence for products id
select setval('public.products_id_seq', (select max(id) from public.products));

-- ==============================================================================
-- ADMIN BOOTSTRAP INSTRUCTIONS (SETUP.md)
-- DO NOT create admin users via seed data or website forms!
-- To make your user an admin:
-- 1. Sign up normally with your email on https://suyogtextile.in/login.html
-- 2. Open Supabase Dashboard -> SQL Editor
-- 3. Run the following query with your registered email:
--    update public.profiles
--    set role = 'admin'
--    where id = (select id from auth.users where email = 'YOUR_EMAIL_HERE');
-- ==============================================================================
