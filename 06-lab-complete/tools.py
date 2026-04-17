# -*- coding: utf-8 -*-
"""
Travel Tools — Mock database cho TravelBuddy agent.

Chứa dữ liệu giả lập chuyến bay và khách sạn nội địa Việt Nam.
"""
from langchain_core.tools import tool

# ─────────────────────────────────────────────────────────
# Mock Flight Database
# ─────────────────────────────────────────────────────────
_FLIGHTS: dict[tuple[str, str], list[dict]] = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1_450_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "08:30", "arrival": "09:50", "price": 950_000,  "class": "economy"},
        {"airline": "Bamboo Airways",   "departure": "12:00", "arrival": "13:20", "price": 1_100_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "19:20", "price": 2_200_000, "class": "business"},
    ],
    ("Đà Nẵng", "Hà Nội"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:20", "price": 1_500_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "15:00", "arrival": "16:20", "price": 980_000,  "class": "economy"},
        {"airline": "Bamboo Airways",   "departure": "19:30", "arrival": "20:50", "price": 1_050_000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2_100_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "10:00", "arrival": "12:15", "price": 1_350_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "16:00", "arrival": "18:15", "price": 3_200_000, "class": "business"},
    ],
    ("Phú Quốc", "Hà Nội"): [
        {"airline": "Vietnam Airlines", "departure": "13:00", "arrival": "15:15", "price": 2_050_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "17:00", "arrival": "19:15", "price": 1_300_000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:05", "price": 1_800_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "07:30", "arrival": "09:35", "price": 950_000,  "class": "economy"},
        {"airline": "Bamboo Airways",   "departure": "09:00", "arrival": "11:05", "price": 1_100_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "20:00", "arrival": "22:05", "price": 2_800_000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Hà Nội"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:05", "price": 1_750_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "12:00", "arrival": "14:05", "price": 900_000,  "class": "economy"},
        {"airline": "Bamboo Airways",   "departure": "18:30", "arrival": "20:35", "price": 1_050_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:30", "arrival": "07:55", "price": 1_200_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "11:00", "arrival": "12:25", "price": 750_000,  "class": "economy"},
        {"airline": "Bamboo Airways",   "departure": "15:00", "arrival": "16:25", "price": 900_000,  "class": "economy"},
    ],
    ("Đà Nẵng", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "08:30", "arrival": "09:55", "price": 1_250_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "14:00", "arrival": "15:25", "price": 780_000,  "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "08:10", "price": 1_100_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "09:30", "arrival": "10:40", "price": 650_000,  "class": "economy"},
        {"airline": "Bamboo Airways",   "departure": "14:00", "arrival": "15:10", "price": 750_000,  "class": "economy"},
    ],
    ("Phú Quốc", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "12:00", "arrival": "13:10", "price": 1_050_000, "class": "economy"},
        {"airline": "VietJet Air",      "departure": "16:00", "arrival": "17:10", "price": 680_000,  "class": "economy"},
    ],
}

# ─────────────────────────────────────────────────────────
# Mock Hotel Database
# ─────────────────────────────────────────────────────────
_HOTELS: dict[str, list[dict]] = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury",     "stars": 5, "price_per_night": 1_800_000, "area": "Mỹ Khê",       "rating": 4.5},
        {"name": "Brilliant Hotel",         "stars": 4, "price_per_night": 1_200_000, "area": "Trung tâm",    "rating": 4.3},
        {"name": "Furama Resort",           "stars": 5, "price_per_night": 3_500_000, "area": "Bãi biển",     "rating": 4.7},
        {"name": "Khách sạn Bạch Đằng",    "stars": 3, "price_per_night": 650_000,  "area": "Trung tâm",    "rating": 4.0},
        {"name": "Sungroup Beach Resort",   "stars": 4, "price_per_night": 2_100_000, "area": "Non Nước",     "rating": 4.4},
        {"name": "Nhà nghỉ Sông Hàn",      "stars": 2, "price_per_night": 300_000,  "area": "Sơn Trà",      "rating": 3.8},
    ],
    "Phú Quốc": [
        {"name": "JW Marriott Phu Quoc",    "stars": 5, "price_per_night": 4_500_000, "area": "Bãi Kem",      "rating": 4.8},
        {"name": "Vinpearl Resort",         "stars": 5, "price_per_night": 3_200_000, "area": "Bãi Dài",      "rating": 4.6},
        {"name": "Mövenpick Resort",        "stars": 5, "price_per_night": 2_800_000, "area": "Phía Bắc",     "rating": 4.5},
        {"name": "La Veranda Resort",       "stars": 4, "price_per_night": 1_900_000, "area": "Dương Đông",   "rating": 4.4},
        {"name": "Seashells Hotel",         "stars": 4, "price_per_night": 1_400_000, "area": "Dương Đông",   "rating": 4.2},
        {"name": "Sunrise Beach Resort",    "stars": 4, "price_per_night": 1_100_000, "area": "Dương Tơ",     "rating": 4.1},
        {"name": "Nhà nghỉ Kiều Nga",       "stars": 2, "price_per_night": 380_000,  "area": "Dương Đông",   "rating": 3.9},
    ],
    "Hồ Chí Minh": [
        {"name": "Caravelle Saigon",        "stars": 5, "price_per_night": 3_800_000, "area": "Quận 1",       "rating": 4.7},
        {"name": "New World Saigon",        "stars": 5, "price_per_night": 3_200_000, "area": "Quận 1",       "rating": 4.6},
        {"name": "Liberty Central",         "stars": 4, "price_per_night": 1_500_000, "area": "Quận 1",       "rating": 4.3},
        {"name": "Majestic Hotel",          "stars": 4, "price_per_night": 2_100_000, "area": "Bến Nghé",     "rating": 4.4},
        {"name": "Khách sạn Kim Đô",        "stars": 3, "price_per_night": 800_000,  "area": "Quận 1",       "rating": 4.0},
        {"name": "Nhà nghỉ Bùi Viện",       "stars": 2, "price_per_night": 280_000,  "area": "Bùi Viện",     "rating": 3.7},
    ],
    "Hà Nội": [
        {"name": "Sofitel Legend Metropole","stars": 5, "price_per_night": 4_200_000, "area": "Hoàn Kiếm",    "rating": 4.9},
        {"name": "Lotte Hotel Hanoi",       "stars": 5, "price_per_night": 3_600_000, "area": "Ba Đình",      "rating": 4.7},
        {"name": "Melia Hanoi",             "stars": 5, "price_per_night": 2_900_000, "area": "Hai Bà Trưng", "rating": 4.5},
        {"name": "Silk Path Hotel",         "stars": 4, "price_per_night": 1_600_000, "area": "Hoàn Kiếm",    "rating": 4.3},
        {"name": "Golden Lotus Hotel",      "stars": 3, "price_per_night": 750_000,  "area": "Hoàn Kiếm",    "rating": 4.1},
        {"name": "Nhà nghỉ Phố Cổ",         "stars": 2, "price_per_night": 350_000,  "area": "Hoàn Kiếm",    "rating": 3.8},
    ],
}


# ─────────────────────────────────────────────────────────
# Tool Functions
# ─────────────────────────────────────────────────────────

@tool
def search_flights(origin: str, destination: str) -> str:
    """Tìm kiếm chuyến bay từ điểm đi đến điểm đến.

    Args:
        origin: Thành phố khởi hành (ví dụ: "Hà Nội", "Hồ Chí Minh")
        destination: Thành phố đến (ví dụ: "Đà Nẵng", "Phú Quốc")
    """
    key = (origin.strip(), destination.strip())
    flights = _FLIGHTS.get(key)
    if not flights:
        return f"Không tìm thấy chuyến bay từ {origin} đến {destination} trong hệ thống."

    lines = [f"✈️ Chuyến bay từ {origin} → {destination}:\n"]
    for i, f in enumerate(flights, 1):
        lines.append(
            f"{i}. {f['airline']} | {f['departure']} → {f['arrival']} | "
            f"Hạng {f['class']} | {f['price']:,}đ/vé".replace(",", ".")
        )
    return "\n".join(lines)


@tool
def search_hotels(city: str, max_price_per_night: int = 99_999_999) -> str:
    """Tìm kiếm khách sạn tại thành phố với giới hạn giá mỗi đêm.

    Args:
        city: Tên thành phố (ví dụ: "Đà Nẵng", "Phú Quốc", "Hồ Chí Minh", "Hà Nội")
        max_price_per_night: Giá tối đa mỗi đêm (VND), mặc định không giới hạn
    """
    hotels = _HOTELS.get(city.strip())
    if not hotels:
        return f"Không tìm thấy thông tin khách sạn tại {city} trong hệ thống."

    filtered = [h for h in hotels if h["price_per_night"] <= max_price_per_night]
    filtered.sort(key=lambda h: h["rating"], reverse=True)

    if not filtered:
        return (
            f"Không có khách sạn nào tại {city} trong ngân sách "
            f"{max_price_per_night:,}đ/đêm.".replace(",", ".")
        )

    lines = [f"🏨 Khách sạn tại {city} (ngân sách ≤ {max_price_per_night:,}đ/đêm):\n".replace(",", ".")]
    for i, h in enumerate(filtered, 1):
        lines.append(
            f"{i}. {'⭐' * h['stars']} {h['name']} | {h['area']} | "
            f"{h['price_per_night']:,}đ/đêm | Đánh giá: {h['rating']}/5".replace(",", ".")
        )
    return "\n".join(lines)


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """Tính toán và kiểm tra ngân sách chuyến đi.

    Args:
        total_budget: Tổng ngân sách (VND)
        expenses: Danh sách chi phí, định dạng "tên:số_tiền,tên:số_tiền"
                  Ví dụ: "vé máy bay:2900000,khách sạn 3 đêm:5400000,ăn uống:1500000"
    """
    items: list[tuple[str, int]] = []
    for part in expenses.split(","):
        part = part.strip()
        if ":" not in part:
            continue
        name, amt = part.rsplit(":", 1)
        try:
            items.append((name.strip(), int(amt.strip())))
        except ValueError:
            continue

    total_spent = sum(a for _, a in items)
    remaining = total_budget - total_spent

    lines = [f"💰 Tổng ngân sách: {total_budget:,}đ\n".replace(",", ".")]
    lines.append("Chi phí dự kiến:")
    for name, amt in items:
        lines.append(f"  • {name}: {amt:,}đ".replace(",", "."))
    lines.append(f"\nTổng chi: {total_spent:,}đ".replace(",", "."))

    if remaining >= 0:
        lines.append(f"✅ Còn lại: {remaining:,}đ".replace(",", "."))
    else:
        lines.append(f"⚠️ Vượt ngân sách: {abs(remaining):,}đ — cần điều chỉnh!".replace(",", "."))

    return "\n".join(lines)
