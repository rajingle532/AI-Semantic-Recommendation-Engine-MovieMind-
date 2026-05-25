"""
Offers & Price Guidance Service.
Provides legal static bank offers, price tier ranges, and BookMyShow deep links.
"""

# ─── City slug mapping for BookMyShow URLs ───────────────────────────────────
CITY_BMS_SLUGS = {
    "mumbai": "mumbai",
    "delhi": "delhi-ncr",
    "bangalore": "bangalore",
    "bengaluru": "bangalore",
    "pune": "pune",
    "hyderabad": "hyderabad",
    "chennai": "chennai",
    "kolkata": "kolkata",
    "ahmedabad": "ahmedabad",
    "jaipur": "jaipur",
    "lucknow": "lucknow",
    "surat": "surat",
    "nagpur": "nagpur",
    "indore": "indore",
    "bhopal": "bhopal",
    "patna": "patna",
    "chandigarh": "chandigarh",
    "kochi": "kochi",
    "goa": "goa",
}

# ─── Ticket Price Tiers (government/industry standard) ───────────────────────
PRICE_TIERS = {
    "metro": {
        "cities": ["mumbai", "delhi", "bangalore", "bengaluru", "hyderabad", "chennai", "kolkata"],
        "range": "₹200 – ₹600",
        "recliner": "₹800 – ₹1500",
        "imax": "₹600 – ₹1200",
    },
    "tier2": {
        "cities": ["pune", "ahmedabad", "jaipur", "lucknow", "nagpur", "surat", "indore", "bhopal", "chandigarh", "kochi", "goa"],
        "range": "₹150 – ₹400",
        "recliner": "₹500 – ₹900",
        "imax": "₹400 – ₹700",
    },
    "tier3": {
        "cities": [],  # everything else
        "range": "₹80 – ₹250",
        "recliner": "₹300 – ₹600",
        "imax": "N/A",
    }
}

# ─── Static known bank offers (update monthly) ───────────────────────────────
BANK_OFFERS = [
    {
        "bank": "ICICI Bank",
        "card_type": "Credit & Debit",
        "offer": "Buy 1 Get 1 Free",
        "day": "Tuesdays only",
        "platform": "BookMyShow",
        "max_discount": "Up to ₹250",
        "emoji": "🏦"
    },
    {
        "bank": "SBI Card",
        "card_type": "Credit Card",
        "offer": "₹75 off on 2 tickets",
        "day": "Weekdays (Mon–Thu)",
        "platform": "BookMyShow",
        "max_discount": "₹75 per transaction",
        "emoji": "💳"
    },
    {
        "bank": "HDFC Bank",
        "card_type": "Credit & Debit",
        "offer": "25% off up to ₹150",
        "day": "All days",
        "platform": "Paytm Movies",
        "max_discount": "₹150",
        "emoji": "🏦"
    },
    {
        "bank": "Axis Bank",
        "card_type": "Select Credit Cards",
        "offer": "₹100 cashback on 2 tickets",
        "day": "Weekends",
        "platform": "BookMyShow",
        "max_discount": "₹100",
        "emoji": "💳"
    },
    {
        "bank": "Amazon Pay ICICI",
        "card_type": "Credit Card",
        "offer": "5% cashback on all tickets",
        "day": "All days",
        "platform": "Amazon Movies",
        "max_discount": "Unlimited",
        "emoji": "📦"
    },
    {
        "bank": "Kotak Bank",
        "card_type": "Credit Card",
        "offer": "₹200 off on minimum 2 tickets",
        "day": "Fridays",
        "platform": "BookMyShow",
        "max_discount": "₹200",
        "emoji": "🏦"
    },
]

# ─── UPI / Wallet Offers ──────────────────────────────────────────────────────
WALLET_OFFERS = [
    {
        "platform": "PhonePe",
        "offer": "10% cashback on movie tickets",
        "max_discount": "₹50",
        "emoji": "📱"
    },
    {
        "platform": "Paytm",
        "offer": "₹75 off on 2+ tickets",
        "max_discount": "₹75",
        "emoji": "💰"
    },
]


def get_city_slug(city: str) -> str:
    """Convert city name to BookMyShow URL slug."""
    return CITY_BMS_SLUGS.get(city.lower().strip(), city.lower().replace(" ", "-"))


def get_price_tier(city: str) -> dict:
    """Get ticket price tier for a city."""
    city_lower = city.lower().strip()
    for tier_name, tier in PRICE_TIERS.items():
        if city_lower in tier.get("cities", []):
            return {"tier": tier_name, **tier}
    return {"tier": "tier3", **PRICE_TIERS["tier3"]}


def get_bms_deep_link(city: str, movie_name: str = None) -> str:
    """Generate BookMyShow deep link for a city and optional movie."""
    slug = get_city_slug(city)
    if movie_name:
        # Clean movie name for URL
        clean = movie_name.lower().replace(" ", "-").replace(":", "").replace("'", "")
        return f"https://in.bookmyshow.com/buytickets/{clean}/{slug}"
    return f"https://in.bookmyshow.com/explore/movies-{slug}"


def get_paytm_deep_link(city: str) -> str:
    slug = city.lower().strip()
    return f"https://paytm.com/movies/{slug}"


def format_offers_response(city: str, movie_name: str = None) -> str:
    """Generate a smart offers card for the chatbot."""
    tier_info = get_price_tier(city)
    bms_link = get_bms_deep_link(city, movie_name)
    paytm_link = get_paytm_deep_link(city)
    offers_link = "https://in.bookmyshow.com/offers"

    movie_str = f" for **{movie_name}**" if movie_name else ""
    resp = f"💎 **Smart Savings{movie_str} in {city.title()}:**\n\n"

    # Price range
    resp += f"🎟️ **Expected Ticket Prices:**\n"
    resp += f"• Regular: {tier_info['range']}\n"
    resp += f"• Recliner: {tier_info['recliner']}\n"
    if tier_info['imax'] != "N/A":
        resp += f"• IMAX/4DX: {tier_info['imax']}\n"
    resp += "\n"

    # Top 3 bank offers
    resp += f"💳 **Best Bank Offers Right Now:**\n"
    for offer in BANK_OFFERS[:3]:
        resp += f"{offer['emoji']} **{offer['bank']}:** {offer['offer']} ({offer['day']}) — {offer['max_discount']}\n"
    resp += "\n"

    # UPI offers
    resp += f"📱 **UPI Offers:**\n"
    for w in WALLET_OFFERS:
        resp += f"{w['emoji']} **{w['platform']}:** {w['offer']} (max {w['max_discount']})\n"
    resp += "\n"

    # Booking links
    resp += f"🔗 **Book Now:**\n"
    resp += f"• [BookMyShow — {city.title()}]({bms_link})\n"
    resp += f"• [Paytm Movies]({paytm_link})\n"
    resp += f"• [See All Current Offers]({offers_link})\n"

    return resp
