"""
Suyog Collection - Database Seeder
Seeds realistic categories, products, images, variants, coupons, and test users.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, create_tables
from app.models import User, Category, Product, ProductImage, ProductVariant, Coupon, Review
from app.utils.security import hash_password
from app.utils.helpers import generate_slug
from datetime import datetime, timezone, timedelta


def seed_database():
    print("Creating tables if not exists...")
    create_tables()

    db = SessionLocal()
    try:
        # ─── 1. Users ───
        print("Seeding Users...")
        admin = db.query(User).filter(User.email == "admin@vastravibe.com").first()
        if not admin:
            admin = User(
                email="admin@vastravibe.com",
                hashed_password=hash_password("admin123"),
                full_name="Suyog Collection Administrator",
                phone="+919876543210",
                is_active=True,
                is_admin=True
            )
            db.add(admin)

        customer = db.query(User).filter(User.email == "customer@example.com").first()
        if not customer:
            customer = User(
                email="customer@example.com",
                hashed_password=hash_password("customer123"),
                full_name="Priya Sharma",
                phone="+919812345678",
                is_active=True,
                is_admin=False
            )
            db.add(customer)

        db.commit()

        # ─── 2. Categories ───
        print("Seeding Categories...")
        categories_data = [
            {"name": "Sarees", "slug": "sarees", "description": "Authentic handwoven and designer sarees from master weavers across India.", "sort_order": 1, "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500&q=80"},
            {"name": "Kurtis", "slug": "kurtis", "description": "Everyday grace to festive opulence in pure cotton, silk, and chikankari kurtis.", "sort_order": 2, "image_url": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=500&q=80"},
            {"name": "Lehengas", "slug": "lehengas", "description": "Bridal, festive, and bridesmaid lehengas with intricate zardozi and gota patti work.", "sort_order": 3, "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500&q=80"},
            {"name": "Salwar Suits", "slug": "salwar-suits", "description": "Anarkali, sharara, and straight salwar kameez suits ready to wear.", "sort_order": 4, "image_url": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=500&q=80"},
            {"name": "Dresses", "slug": "dresses", "description": "Contemporary Indo-Western fusion dresses, maxis, and gowns.", "sort_order": 5, "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=500&q=80"},
            {"name": "Gents Wear", "slug": "mens-wear", "description": "Royal kurtas, Nehru jackets, sherwanis, and Indo-Western attire for men.", "sort_order": 6, "image_url": "https://images.unsplash.com/photo-1621609764095-b32bbe35cf36?w=500&q=80"},
        ]

        cat_map = {}
        for cdata in categories_data:
            cat = db.query(Category).filter(Category.slug == cdata["slug"]).first()
            if not cat:
                cat = Category(**cdata)
                db.add(cat)
                db.flush()
            else:
                cat.name = cdata["name"]
                cat.description = cdata["description"]
                cat.image_url = cdata["image_url"]
            cat_map[cdata["slug"]] = cat

        db.commit()

        # ─── 3. Products ───
        print("Seeding Products...")
        products_data = [
            # ── Sarees ──
            {
                "category_slug": "sarees",
                "name": "Crimson Red Royal Banarasi Katan Silk Saree",
                "brand": "VastraVibe Heritage",
                "price": 8999.0,
                "discount_price": 4499.0,
                "stock": 18,
                "sku": "VV-SAR-BAN-001",
                "fabric": "Katan Silk",
                "occasion": "Wedding",
                "description": "Exquisite crimson red Banarasi Katan silk saree woven with real gold-plated zari kadwa technique. Includes matching unstitched blouse piece. Features opulent floral jaal work.",
                "care_instructions": "Dry clean only. Store in a muslin cloth bag.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": False,
                "rating": 4.9,
                "review_count": 28,
                "primary_image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80",
                    "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=800&q=80"
                ],
                "variants": [
                    {"color": "Crimson Red", "size": "Free Size", "stock": 10},
                    {"color": "Maroon", "size": "Free Size", "stock": 8}
                ]
            },
            {
                "category_slug": "sarees",
                "name": "Peacock Blue Handloom Kanjivaram Pure Silk Saree",
                "brand": "VastraVibe Royal",
                "price": 14999.0,
                "discount_price": 8999.0,
                "stock": 12,
                "sku": "VV-SAR-KAN-002",
                "fabric": "Pure Mulberry Silk",
                "occasion": "Wedding",
                "description": "Authentic Kanchipuram silk saree in deep peacock blue with contrasting crimson red korvai temple border and rich brocade pallu.",
                "care_instructions": "Dry clean only. Avoid spraying perfumes directly on zari.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 5.0,
                "review_count": 19,
                "primary_image": "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=800&q=80"
                ],
                "variants": [
                    {"color": "Peacock Blue", "size": "Free Size", "stock": 12}
                ]
            },
            {
                "category_slug": "sarees",
                "name": "Pastel Pink Organza Floral Hand-Embroidered Saree",
                "brand": "VastraVibe Contemporary",
                "price": 5499.0,
                "discount_price": 2799.0,
                "stock": 25,
                "sku": "VV-SAR-ORG-003",
                "fabric": "Pure Organza",
                "occasion": "Party",
                "description": "Breezy pastel pink lightweight organza saree embellished with delicate scalloped cutwork border and hand-painted floral motifs.",
                "care_instructions": "Gentle hand wash or dry clean. Iron at lowest temperature with cloth barrier.",
                "is_featured": True,
                "is_bestseller": False,
                "is_new_arrival": True,
                "rating": 4.7,
                "review_count": 14,
                "primary_image": "https://images.unsplash.com/photo-1609357605129-26f69add5d6e?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1609357605129-26f69add5d6e?w=800&q=80"
                ],
                "variants": [
                    {"color": "Pink", "size": "Free Size", "stock": 15},
                    {"color": "Peach", "size": "Free Size", "stock": 10}
                ]
            },
            {
                "category_slug": "sarees",
                "name": "Emerald Green Chanderi Cotton Silk Zari Saree",
                "brand": "VastraVibe Weaves",
                "price": 3999.0,
                "discount_price": 1999.0,
                "stock": 30,
                "sku": "VV-SAR-CHA-004",
                "fabric": "Chanderi Silk Cotton",
                "occasion": "Festive",
                "description": "Lustrous emerald green Chanderi saree adorned with subtle gold coin buttas and lightweight tissue zari pallu. Ideal for festivals and pujas.",
                "care_instructions": "Dry clean recommended for first 2 washes.",
                "is_featured": False,
                "is_bestseller": True,
                "is_new_arrival": False,
                "rating": 4.6,
                "review_count": 32,
                "primary_image": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80"
                ],
                "variants": [
                    {"color": "Emerald Green", "size": "Free Size", "stock": 20},
                    {"color": "Teal", "size": "Free Size", "stock": 10}
                ]
            },
            {
                "category_slug": "sarees",
                "name": "Mustard Yellow Bandhani Georgette Gota Patti Saree",
                "brand": "VastraVibe Heritage",
                "price": 4999.0,
                "discount_price": 2499.0,
                "stock": 15,
                "sku": "VV-SAR-BAN-005",
                "fabric": "Georgette",
                "occasion": "Festive",
                "description": "Traditional Rajasthani tie-and-dye Bandhani saree highlighted with elaborate handcrafted Gota Patti lace border.",
                "care_instructions": "Dry clean only.",
                "is_featured": True,
                "is_bestseller": False,
                "is_new_arrival": True,
                "rating": 4.8,
                "review_count": 11,
                "primary_image": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800&q=80"
                ],
                "variants": [
                    {"color": "Yellow", "size": "Free Size", "stock": 15}
                ]
            },
            # ── Kurtis ──
            {
                "category_slug": "kurtis",
                "name": "Ivory Chikankari Pure Cotton Anarkali Kurti",
                "brand": "VastraVibe Lucknowi",
                "price": 2999.0,
                "discount_price": 1499.0,
                "stock": 40,
                "sku": "VV-KUR-CHK-001",
                "fabric": "100% Pure Cotton",
                "occasion": "Casual",
                "description": "Graceful white Lucknowi Chikankari Anarkali kurti handcrafted with shadow work and mukaish sequins. Breathable and supremely comfortable.",
                "care_instructions": "Hand wash gently in cold water with mild detergent.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 4.8,
                "review_count": 45,
                "primary_image": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?w=800&q=80"
                ],
                "variants": [
                    {"color": "White", "size": "S", "stock": 10},
                    {"color": "White", "size": "M", "stock": 15},
                    {"color": "White", "size": "L", "stock": 10},
                    {"color": "White", "size": "XL", "stock": 5}
                ]
            },
            {
                "category_slug": "kurtis",
                "name": "Ruby Maroon Silk Blend Flared Festive Kurti",
                "brand": "VastraVibe Festive",
                "price": 3499.0,
                "discount_price": 1899.0,
                "stock": 20,
                "sku": "VV-KUR-SLK-002",
                "fabric": "Art Silk Blend",
                "occasion": "Festive",
                "description": "Rich jewel-toned flared kurti with zari embroidery neckline and tassel detailing. Pair with cigarette pants or palazzo.",
                "care_instructions": "Dry clean only.",
                "is_featured": False,
                "is_bestseller": True,
                "is_new_arrival": False,
                "rating": 4.5,
                "review_count": 22,
                "primary_image": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&q=80"
                ],
                "variants": [
                    {"color": "Maroon", "size": "M", "stock": 8},
                    {"color": "Maroon", "size": "L", "stock": 7},
                    {"color": "Maroon", "size": "XL", "stock": 5}
                ]
            },
            # ── Lehengas ──
            {
                "category_slug": "lehengas",
                "name": "Maharani Velvet Bridal Lehenga in Deep Wine",
                "brand": "VastraVibe Couture",
                "price": 24999.0,
                "discount_price": 15999.0,
                "stock": 6,
                "sku": "VV-LEH-BRI-001",
                "fabric": "Micro Velvet",
                "occasion": "Wedding",
                "description": "Magnificent bridal semi-stitched lehenga choli set in deep wine micro-velvet, embellished with intricate zardozi, dori, and pearl work. Includes double dupatta.",
                "care_instructions": "Strictly dry clean only. Store in original garment bag.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 5.0,
                "review_count": 8,
                "primary_image": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&q=80"
                ],
                "variants": [
                    {"color": "Maroon", "size": "Semi-Stitched", "stock": 6}
                ]
            },
            {
                "category_slug": "lehengas",
                "name": "Sky Blue Foil Mirror Work Georgette Lehenga",
                "brand": "VastraVibe Contemporary",
                "price": 8999.0,
                "discount_price": 4999.0,
                "stock": 14,
                "sku": "VV-LEH-MIR-002",
                "fabric": "Georgette",
                "occasion": "Party",
                "description": "Shimmering sky blue sangeet & cocktail lehenga featuring intricate foil mirror work and a sweetheart neckline blouse with ruffled dupatta.",
                "care_instructions": "Dry clean only.",
                "is_featured": True,
                "is_bestseller": False,
                "is_new_arrival": True,
                "rating": 4.9,
                "review_count": 16,
                "primary_image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800&q=80"
                ],
                "variants": [
                    {"color": "Blue", "size": "Free Size", "stock": 14}
                ]
            },
            # ── Salwar Suits ──
            {
                "category_slug": "salwar-suits",
                "name": "Blush Pink Embroidered Georgette Sharara Suit Set",
                "brand": "VastraVibe Festive",
                "price": 5999.0,
                "discount_price": 3299.0,
                "stock": 22,
                "sku": "VV-SUT-SHA-001",
                "fabric": "Georgette",
                "occasion": "Festive",
                "description": "Stunning 3-piece Sharara suit with short peplum kurti, flared sharara bottoms, and heavily embroidered net dupatta.",
                "care_instructions": "Dry clean recommended.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 4.7,
                "review_count": 29,
                "primary_image": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800&q=80"
                ],
                "variants": [
                    {"color": "Pink", "size": "M", "stock": 8},
                    {"color": "Pink", "size": "L", "stock": 8},
                    {"color": "Pink", "size": "XL", "stock": 6}
                ]
            },
            # ── Men's / Gents Wear ──
            {
                "category_slug": "mens-wear",
                "name": "Navy Blue Raw Silk Kurta Pajama with Nehru Jacket",
                "brand": "VastraVibe Men",
                "price": 6999.0,
                "discount_price": 3999.0,
                "stock": 16,
                "sku": "VV-MEN-KUR-001",
                "fabric": "Raw Silk",
                "occasion": "Wedding",
                "description": "Regal 3-piece set comprising a solid navy blue kurta, matching churidar pajama, and a brocade woven Nehru jacket with metal buttons.",
                "care_instructions": "Dry clean only.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 4.8,
                "review_count": 18,
                "primary_image": "https://images.unsplash.com/photo-1621609764095-b32bbe35cf36?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1621609764095-b32bbe35cf36?w=800&q=80"
                ],
                "variants": [
                    {"color": "Navy", "size": "38", "stock": 4},
                    {"color": "Navy", "size": "40", "stock": 6},
                    {"color": "Navy", "size": "42", "stock": 6}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Royal Ivory & Gold Zari Embroidered Wedding Sherwani Set",
                "brand": "Suyog Heritage Men",
                "price": 14999.0,
                "discount_price": 8999.0,
                "stock": 12,
                "sku": "VV-GENT-SHER-002",
                "fabric": "Silk Brocade",
                "occasion": "Wedding",
                "description": "Opulent wedding sherwani crafted in pure ivory raw silk adorned with hand-embroidered golden zardozi motifs. Set includes sherwani, matching churidar, embellished stole, and royal safa.",
                "care_instructions": "Specialist dry clean only. Store in garment cover.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 4.95,
                "review_count": 32,
                "primary_image": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800&q=80"
                ],
                "variants": [
                    {"color": "Ivory", "size": "38", "stock": 3},
                    {"color": "Ivory", "size": "40", "stock": 4},
                    {"color": "Ivory", "size": "42", "stock": 3},
                    {"color": "Ivory", "size": "44", "stock": 2}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Deep Maroon Velvet Bandhgala Jodhpuri Suit",
                "brand": "Suyog Couture Men",
                "price": 11999.0,
                "discount_price": 6999.0,
                "stock": 15,
                "sku": "VV-GENT-BANDH-003",
                "fabric": "Velvet",
                "occasion": "Party",
                "description": "Regal Italian micro-velvet Bandhgala jacket with custom antique brass crest buttons and coordinated slim-fit formal trousers. Designed for grand receptions and sangeet celebrations.",
                "care_instructions": "Dry clean only.",
                "is_featured": True,
                "is_bestseller": False,
                "is_new_arrival": True,
                "rating": 4.88,
                "review_count": 21,
                "primary_image": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=800&q=80"
                ],
                "variants": [
                    {"color": "Maroon", "size": "38", "stock": 3},
                    {"color": "Maroon", "size": "40", "stock": 5},
                    {"color": "Maroon", "size": "42", "stock": 4},
                    {"color": "Maroon", "size": "44", "stock": 3}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Pure Lucknowi Chikankari Cotton Kurta Pajama - Pista Green",
                "brand": "Suyog Handlooms",
                "price": 3999.0,
                "discount_price": 2299.0,
                "stock": 25,
                "sku": "VV-GENT-CHIK-004",
                "fabric": "Cotton",
                "occasion": "Festive",
                "description": "Handcrafted Lucknowi Chikankari kurta in breezy pure cambric cotton with intricate bakhiya and shadow embroidery, paired with a matching white cotton pyjama.",
                "care_instructions": "Gentle hand wash in cold water or mild machine wash.",
                "is_featured": False,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 4.85,
                "review_count": 44,
                "primary_image": "https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1617137984095-74e4e5e3613f?w=800&q=80"
                ],
                "variants": [
                    {"color": "Pista Green", "size": "38", "stock": 6},
                    {"color": "Pista Green", "size": "40", "stock": 8},
                    {"color": "Pista Green", "size": "42", "stock": 7},
                    {"color": "Pista Green", "size": "44", "stock": 4}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Mustard Yellow Haldi Special Chanderi Silk Kurta Set",
                "brand": "VastraVibe Festive",
                "price": 4499.0,
                "discount_price": 2599.0,
                "stock": 20,
                "sku": "VV-GENT-KUR-005",
                "fabric": "Silk",
                "occasion": "Festive",
                "description": "Bright festive mustard yellow chanderi silk kurta with intricate thread work around the mandarin collar and placket, complete with a comfortable cotton silk churidar.",
                "care_instructions": "Dry clean recommended.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": False,
                "rating": 4.9,
                "review_count": 29,
                "primary_image": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&q=80"
                ],
                "variants": [
                    {"color": "Mustard Yellow", "size": "38", "stock": 5},
                    {"color": "Mustard Yellow", "size": "40", "stock": 6},
                    {"color": "Mustard Yellow", "size": "42", "stock": 5},
                    {"color": "Mustard Yellow", "size": "44", "stock": 4}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Designer Emerald Green Indo-Western Asymmetric Kurta Set",
                "brand": "Suyog Couture Men",
                "price": 8499.0,
                "discount_price": 4999.0,
                "stock": 14,
                "sku": "VV-GENT-INDO-006",
                "fabric": "Art Silk",
                "occasion": "Festive",
                "description": "Contemporary draped asymmetric kurta in royal emerald green featuring gold zari shoulder brooch accents and pleated dhoti pants.",
                "care_instructions": "Dry clean only.",
                "is_featured": True,
                "is_bestseller": False,
                "is_new_arrival": True,
                "rating": 4.87,
                "review_count": 15,
                "primary_image": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=800&q=80"
                ],
                "variants": [
                    {"color": "Emerald Green", "size": "38", "stock": 3},
                    {"color": "Emerald Green", "size": "40", "stock": 4},
                    {"color": "Emerald Green", "size": "42", "stock": 4},
                    {"color": "Emerald Green", "size": "44", "stock": 3}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Jet Black Art Silk Kurta with Handcrafted Mirror Work Jacket",
                "brand": "VastraVibe Men",
                "price": 7999.0,
                "discount_price": 4499.0,
                "stock": 22,
                "sku": "VV-GENT-MIR-007",
                "fabric": "Art Silk",
                "occasion": "Party",
                "description": "Dramatic monochromatic black kurta and trouser combination layered with a stunning real glass mirror-work sleeveless bundi vest.",
                "care_instructions": "Dry clean only to protect delicate mirror embroidery.",
                "is_featured": True,
                "is_bestseller": True,
                "is_new_arrival": True,
                "rating": 4.92,
                "review_count": 37,
                "primary_image": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=800&q=80"
                ],
                "variants": [
                    {"color": "Black", "size": "38", "stock": 5},
                    {"color": "Black", "size": "40", "stock": 7},
                    {"color": "Black", "size": "42", "stock": 6},
                    {"color": "Black", "size": "44", "stock": 4}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Woven Banarasi Brocade Nehru Modi Jacket - Gold & Wine",
                "brand": "Suyog Heritage Men",
                "price": 3499.0,
                "discount_price": 1899.0,
                "stock": 30,
                "sku": "VV-GENT-NEH-008",
                "fabric": "Brocade",
                "occasion": "Festive",
                "description": "Traditional Banarasi brocade woven Nehru jacket with mandarin collar and welt pockets. Versatile layer for kurtas, shirts, and festive celebrations.",
                "care_instructions": "Dry clean only.",
                "is_featured": False,
                "is_bestseller": True,
                "is_new_arrival": False,
                "rating": 4.8,
                "review_count": 52,
                "primary_image": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=800&q=80"
                ],
                "variants": [
                    {"color": "Gold", "size": "38", "stock": 8},
                    {"color": "Gold", "size": "40", "stock": 10},
                    {"color": "Gold", "size": "42", "stock": 8},
                    {"color": "Gold", "size": "44", "stock": 4}
                ]
            },
            {
                "category_slug": "mens-wear",
                "name": "Sky Blue Pure Linen Mandarin Collar Casual Kurta",
                "brand": "Suyog Men",
                "price": 2999.0,
                "discount_price": 1699.0,
                "stock": 24,
                "sku": "VV-GENT-LIN-009",
                "fabric": "Linen",
                "occasion": "Casual",
                "description": "Breathable 100% pure organic linen kurta with roll-up sleeves and wooden button accents. Ideal for summer festivities, puja rituals, and relaxed gatherings.",
                "care_instructions": "Machine wash cold with like colors.",
                "is_featured": False,
                "is_bestseller": False,
                "is_new_arrival": True,
                "rating": 4.76,
                "review_count": 26,
                "primary_image": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&q=80",
                "images": [
                    "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=800&q=80"
                ],
                "variants": [
                    {"color": "Sky Blue", "size": "38", "stock": 6},
                    {"color": "Sky Blue", "size": "40", "stock": 8},
                    {"color": "Sky Blue", "size": "42", "stock": 6},
                    {"color": "Sky Blue", "size": "44", "stock": 4}
                ]
            }
        ]

        for pdata in products_data:
            existing = db.query(Product).filter(Product.sku == pdata["sku"]).first()
            if existing:
                continue

            category = cat_map.get(pdata["category_slug"])
            if not category:
                continue

            slug = generate_slug(pdata["name"])
            price = pdata["price"]
            discount_price = pdata.get("discount_price")
            discount_percent = int(((price - discount_price) / price) * 100) if discount_price else 0
            colors_list = list({v.get("color") for v in pdata.get("variants", []) if v.get("color")})
            sizes_list = list({v.get("size") for v in pdata.get("variants", []) if v.get("size")})

            product = Product(
                category_id=category.id,
                name=pdata["name"],
                slug=slug,
                brand=pdata["brand"],
                sku=pdata["sku"],
                price=price,
                discount_price=discount_price,
                discount_percent=discount_percent,
                stock=pdata["stock"],
                fabric=pdata.get("fabric"),
                occasion=pdata.get("occasion"),
                colors=",".join(colors_list) if colors_list else None,
                sizes=",".join(sizes_list) if sizes_list else None,
                description=pdata["description"],
                care_instructions=pdata.get("care_instructions"),
                is_featured=pdata.get("is_featured", False),
                is_bestseller=pdata.get("is_bestseller", False),
                is_new_arrival=pdata.get("is_new_arrival", False),
                rating=pdata.get("rating", 5.0),
                review_count=pdata.get("review_count", 0)
            )
            db.add(product)
            db.flush()

            # Add images
            for idx, img_url in enumerate(pdata.get("images", [])):
                img = ProductImage(
                    product_id=product.id,
                    image_url=img_url,
                    sort_order=idx,
                    is_primary=(idx == 0)
                )
                db.add(img)

            # Add variants
            for vdata in pdata.get("variants", []):
                variant = ProductVariant(
                    product_id=product.id,
                    color=vdata.get("color"),
                    size=vdata.get("size"),
                    stock=vdata.get("stock", 5)
                )
                db.add(variant)

            # Add sample review
            review = Review(
                product_id=product.id,
                user_id=customer.id if customer else None,
                rating=5,
                title="Breathtaking quality & vibrant colors!",
                body="I ordered this for a family function and received countless compliments. The fabric drape and finish are truly top tier. Highly recommended!",
                is_approved=True,
                is_verified=True
            )
            db.add(review)

        db.commit()

        # ─── 4. Coupons ───
        print("Seeding Coupons...")
        coupons = [
            {
                "code": "WELCOME10",
                "discount_type": "percent",
                "discount_value": 10.0,
                "minimum_order": 999.0,
                "maximum_discount": 500.0,
                "valid_from": datetime.now(timezone.utc) - timedelta(days=10),
                "valid_until": datetime.now(timezone.utc) + timedelta(days=365),
                "usage_limit": 1000,
                "is_active": True
            },
            {
                "code": "FESTIVE20",
                "discount_type": "percent",
                "discount_value": 20.0,
                "minimum_order": 2999.0,
                "maximum_discount": 1000.0,
                "valid_from": datetime.now(timezone.utc) - timedelta(days=5),
                "valid_until": datetime.now(timezone.utc) + timedelta(days=90),
                "usage_limit": 500,
                "is_active": True
            },
            {
                "code": "SAVE70",
                "discount_type": "percent",
                "discount_value": 15.0,
                "minimum_order": 1999.0,
                "maximum_discount": 750.0,
                "valid_from": datetime.now(timezone.utc) - timedelta(days=1),
                "valid_until": datetime.now(timezone.utc) + timedelta(days=30),
                "usage_limit": 200,
                "is_active": True
            },
            {
                "code": "FLAT500",
                "discount_type": "fixed",
                "discount_value": 500.0,
                "minimum_order": 3499.0,
                "valid_from": datetime.now(timezone.utc) - timedelta(days=1),
                "valid_until": datetime.now(timezone.utc) + timedelta(days=60),
                "usage_limit": 300,
                "is_active": True
            }
        ]

        for cp in coupons:
            if not db.query(Coupon).filter(Coupon.code == cp["code"]).first():
                coupon = Coupon(**cp)
                db.add(coupon)

        db.commit()
        print("[SUCCESS] Database successfully seeded with Suyog Collection collection data!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
