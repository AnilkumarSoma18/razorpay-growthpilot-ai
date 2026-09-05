"""
Synthetic ecommerce data generator for Razorpay GrowthPilot AI.

*** ALL DATA PRODUCED HERE IS SYNTHETIC DEMO DATA. ***
It is generated locally with Faker + numpy for demonstration and development
purposes only. It is not real merchant, customer, or payment data, and every
row is marked as such (Merchant.is_demo_data=True). No calls to Razorpay are
made by this generator — payment rows here represent synthetic *historical*
records for analytics purposes, not live payment processing.

This module only builds Python objects / dicts. `scripts/seed_database.py`
is responsible for opening a DB session, calling these functions, and
committing.
"""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np
from faker import Faker

from app.models.enums import (
    CartEventType,
    CustomerEventType,
    CustomerSegment,
    OrderSource,
    OrderStatus,
    PaymentStatus,
)

SEED = 42
fake = Faker("en_IN")
Faker.seed(SEED)
random.seed(SEED)
np.random.seed(SEED)

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Category / product catalog design
# ---------------------------------------------------------------------------
# Each entry: (category_name, [subcategory names])
CATEGORY_TREE = {
    "Electronics": ["Laptops", "Headphones", "Mobile Accessories", "Cameras", "Camera Accessories", "Smartphones", "Tablets"],
    "Fashion": ["Men's Apparel", "Women's Apparel", "Footwear", "Bags & Wallets", "Watches"],
    "Home & Kitchen": ["Kitchen Appliances", "Home Decor", "Furniture", "Cookware"],
    "Sports & Fitness": ["Fitness Equipment", "Sportswear", "Outdoor Gear"],
    "Beauty & Personal Care": ["Skincare", "Haircare", "Fragrances"],
    "Books & Stationery": ["Fiction", "Non-Fiction", "Office Supplies"],
    "Toys & Games": ["Educational Toys", "Board Games", "Outdoor Toys"],
}

# Product-affinity groups used to populate compatible_products /
# frequently_bought_with and to bias co-purchase in generated orders.
# Keys are subcategory names that "anchor" a bundle; values are subcategory
# names customers of the anchor frequently also buy from.
AFFINITY_MAP = {
    "Laptops": ["Bags & Wallets", "Mobile Accessories", "Headphones"],
    "Cameras": ["Camera Accessories"],
    "Smartphones": ["Mobile Accessories", "Headphones"],
    "Men's Apparel": ["Footwear", "Watches"],
    "Women's Apparel": ["Footwear", "Bags & Wallets"],
    "Fitness Equipment": ["Sportswear"],
    "Kitchen Appliances": ["Cookware"],
}

PRICE_RANGES_INR = {
    "Laptops": (28000, 145000),
    "Headphones": (699, 24999),
    "Mobile Accessories": (199, 4999),
    "Cameras": (18000, 210000),
    "Camera Accessories": (299, 12999),
    "Smartphones": (9999, 129999),
    "Tablets": (8999, 79999),
    "Men's Apparel": (399, 4999),
    "Women's Apparel": (399, 5999),
    "Footwear": (699, 8999),
    "Bags & Wallets": (399, 6999),
    "Watches": (799, 24999),
    "Kitchen Appliances": (999, 24999),
    "Home Decor": (299, 8999),
    "Furniture": (1999, 49999),
    "Cookware": (299, 6999),
    "Fitness Equipment": (499, 34999),
    "Sportswear": (399, 3999),
    "Outdoor Gear": (599, 14999),
    "Skincare": (199, 3999),
    "Haircare": (149, 2999),
    "Fragrances": (399, 6999),
    "Fiction": (149, 899),
    "Non-Fiction": (199, 1499),
    "Office Supplies": (49, 2499),
    "Educational Toys": (299, 3999),
    "Board Games": (399, 2999),
    "Outdoor Toys": (299, 4999),
}

PRODUCT_ADJECTIVES = ["Pro", "Max", "Air", "Lite", "Plus", "Ultra", "Classic", "Prime", "Essential", "Studio"]

BRANDS_BY_CATEGORY = {
    "Laptops": ["Zenbook", "Voltix", "Corenex", "Skyline", "Nimbus"],
    "Headphones": ["EchoWave", "BassLine", "SonicPods", "AeroSound"],
    "Mobile Accessories": ["GripTech", "ChargeUp", "ClickCore"],
    "Cameras": ["Lumora", "Pixelite", "Framewise"],
    "Camera Accessories": ["Framewise", "SteadyGrip", "CardMax"],
    "Smartphones": ["Nexafone", "Orbix", "Pulsar"],
    "Tablets": ["Nexafone", "Slatepad"],
}


@dataclass
class GeneratedProduct:
    id: uuid.UUID
    category_name: str
    sku: str
    name: str
    description: str
    price: float
    inventory: int
    attributes: dict
    use_cases: list
    customer_segments: list
    rating: float


def _brand_for(category: str) -> str:
    return random.choice(BRANDS_BY_CATEGORY.get(category, ["Generic", "Everyday", "HomeBasics"]))


def _product_name(category: str, subcategory: str) -> str:
    brand = _brand_for(subcategory)
    adjective = random.choice(PRODUCT_ADJECTIVES)
    noun = subcategory.rstrip("s") if subcategory.endswith("s") and subcategory not in (
        "Camera Accessories", "Mobile Accessories",
    ) else subcategory
    return f"{brand} {noun} {adjective}"


def generate_categories() -> list[dict]:
    """Returns flat list of category dicts with parent linkage resolved by name."""
    categories = []
    for parent_name, subnames in CATEGORY_TREE.items():
        categories.append({"id": uuid.uuid4(), "name": parent_name, "parent_name": None})
        for sub in subnames:
            categories.append({"id": uuid.uuid4(), "name": sub, "parent_name": parent_name})
    return categories


def generate_products(categories: list[dict], target_count: int = 560) -> list[GeneratedProduct]:
    """Generates >= target_count products distributed across subcategories,
    with realistic price ranges and AI-readable catalog attributes."""
    subcats = [c for c in categories if c["parent_name"] is not None]
    products: list[GeneratedProduct] = []

    per_subcat = max(8, target_count // len(subcats))

    for cat in subcats:
        name = cat["name"]
        low, high = PRICE_RANGES_INR.get(name, (299, 4999))
        for _ in range(per_subcat):
            price = round(float(np.random.uniform(low, high)), 2)
            product_id = uuid.uuid4()
            use_cases = _use_cases_for(name)
            products.append(
                GeneratedProduct(
                    id=product_id,
                    category_name=name,
                    sku=f"SKU-{uuid.uuid4().hex[:10].upper()}",
                    name=_product_name(cat["parent_name"], name),
                    description=(
                        f"{_product_name(cat['parent_name'], name)} — a {name.lower()} "
                        f"product suited for {', '.join(use_cases[:2]).lower()}. "
                        f"(Synthetic demo catalog entry.)"
                    ),
                    price=price,
                    inventory=int(np.random.randint(0, 400)),
                    attributes={
                        "category": name,
                        "parent_category": cat["parent_name"],
                        "brand": _brand_for(name),
                    },
                    use_cases=use_cases,
                    customer_segments=_segments_for(name, price),
                    rating=round(float(np.random.uniform(3.2, 5.0)), 1),
                )
            )
    return products


def _use_cases_for(subcategory: str) -> list[str]:
    mapping = {
        "Laptops": ["college", "remote work", "gaming", "video editing"],
        "Headphones": ["studying", "commuting", "workouts", "calls"],
        "Mobile Accessories": ["daily carry", "productivity", "protection"],
        "Cameras": ["travel photography", "content creation", "events"],
        "Camera Accessories": ["travel photography", "content creation"],
        "Smartphones": ["daily use", "photography", "gaming"],
        "Tablets": ["reading", "note-taking", "entertainment"],
    }
    return mapping.get(subcategory, ["everyday use", "gifting"])


def _segments_for(subcategory: str, price: float) -> list[str]:
    segments = []
    if price < 1000:
        segments.append("price_sensitive")
    if subcategory in ("Laptops", "Cameras", "Smartphones", "Watches", "Furniture") and price > 40000:
        segments.append("high_value")
    if subcategory in ("Laptops", "Headphones", "Mobile Accessories", "Tablets"):
        segments.append("students")
    return segments or ["general"]


def link_product_affinity(products: list[GeneratedProduct]) -> dict[uuid.UUID, list[uuid.UUID]]:
    """Returns {product_id: [related_product_ids]} based on AFFINITY_MAP, used
    to populate compatible_products / frequently_bought_with and to bias
    synthetic co-purchases toward realistic bundles (laptop -> bag/mouse/
    keyboard/headphones, camera -> memory card/tripod/bag, etc.)."""
    by_category: dict[str, list[GeneratedProduct]] = {}
    for p in products:
        by_category.setdefault(p.category_name, []).append(p)

    affinity: dict[uuid.UUID, list[uuid.UUID]] = {}
    for anchor_cat, related_cats in AFFINITY_MAP.items():
        anchors = by_category.get(anchor_cat, [])
        related_pool: list[GeneratedProduct] = []
        for rc in related_cats:
            related_pool.extend(by_category.get(rc, []))
        if not related_pool:
            continue
        for anchor in anchors:
            picks = random.sample(related_pool, k=min(4, len(related_pool)))
            affinity[anchor.id] = [p.id for p in picks]
    return affinity


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

SEGMENT_WEIGHTS = {
    CustomerSegment.NEW: 0.30,
    CustomerSegment.RETURNING: 0.35,
    CustomerSegment.HIGH_VALUE: 0.10,
    CustomerSegment.PRICE_SENSITIVE: 0.15,
    CustomerSegment.INACTIVE: 0.10,
}

INDIAN_CITIES = [
    ("Bengaluru", "Karnataka"), ("Mumbai", "Maharashtra"), ("Delhi", "Delhi"),
    ("Hyderabad", "Telangana"), ("Chennai", "Tamil Nadu"), ("Pune", "Maharashtra"),
    ("Kolkata", "West Bengal"), ("Ahmedabad", "Gujarat"), ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh"),
]


@dataclass
class GeneratedCustomer:
    id: uuid.UUID
    full_name: str
    email: str
    phone: str
    city: str
    state: str
    segment: CustomerSegment
    acquired_at: datetime


def generate_customers(count: int = 2200) -> list[GeneratedCustomer]:
    segments = list(SEGMENT_WEIGHTS.keys())
    weights = list(SEGMENT_WEIGHTS.values())
    customers = []
    for i in range(count):
        segment = random.choices(segments, weights=weights, k=1)[0]
        city, state = random.choice(INDIAN_CITIES)
        # Older acquisition dates for inactive/returning; recent for new.
        if segment == CustomerSegment.NEW:
            days_ago = random.randint(0, 45)
        elif segment == CustomerSegment.INACTIVE:
            days_ago = random.randint(200, 720)
        else:
            days_ago = random.randint(45, 540)
        acquired_at = NOW - timedelta(days=days_ago)
        full_name = fake.name()
        customers.append(
            GeneratedCustomer(
                id=uuid.uuid4(),
                full_name=full_name,
                email=f"{full_name.lower().replace(' ', '.')}.{i}@example-demo.test",
                phone=fake.msisdn()[:10],
                city=city,
                state=state,
                segment=segment,
                acquired_at=acquired_at,
            )
        )
    return customers
