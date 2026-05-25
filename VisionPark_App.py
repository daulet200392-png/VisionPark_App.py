import io
import math
import random
import socket
from datetime import datetime, time, timedelta

import altair as alt
import pandas as pd
import streamlit as st

RATE_KZT_PER_HOUR = 500
RATE_SURGE_KZT = 1000
LOAD_SURGE_THRESHOLD = 80
FREE_MINUTES = 60
REFRESH_SECONDS = 2
VISUAL_SLOTS = 10
MEGA_CODE = "MEGA2024"
ELECTRIC_SHARE = 0.10
BLACKLIST_MARKER = "001"
VIOLATOR_SIM_CHANCE = 0.08

st.set_page_config(
    page_title="VisionPark AI",
    page_icon="🚗",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(ellipse at 20% 0%, #1a2744 0%, #0b0f18 45%, #060910 100%);
        color: #e7ecff;
    }

    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
        color: #f6f8ff;
        letter-spacing: 0.3px;
    }

    .main-title i {
        color: #6ea8ff;
        margin-right: 10px;
    }

    .subtitle {
        color: #8fa3d4;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }

    .metric-card {
        background: linear-gradient(145deg, #1a2338, #121a2b);
        border: 1px solid rgba(124, 152, 255, 0.28);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.28);
    }

    .metric-label {
        font-size: 0.9rem;
        color: #9fb0dd;
        margin-bottom: 8px;
    }

    .metric-label i {
        margin-right: 6px;
        color: #6ea8ff;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1;
    }

    .table-title {
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
        font-size: 1.15rem;
        font-weight: 700;
        color: #dfe7ff;
    }

    .table-title i {
        margin-right: 8px;
        color: #6ea8ff;
    }

    .hint {
        font-size: 0.88rem;
        color: #9fb0dd;
        margin-top: -0.35rem;
        margin-bottom: 0.5rem;
    }

    .peak-box {
        background: linear-gradient(145deg, #1e2a45, #141c30);
        border: 1px solid rgba(124, 152, 255, 0.35);
        border-radius: 12px;
        padding: 14px 18px;
        margin: 0.5rem 0 1rem 0;
        color: #dfe7ff;
    }

    .chart-panel {
        background: linear-gradient(145deg, #151d30, #101828);
        border: 1px solid rgba(124, 152, 255, 0.22);
        border-radius: 16px;
        padding: 16px 18px 8px 18px;
        margin-bottom: 1rem;
    }

    .chart-panel h3 {
        margin: 0 0 8px 0;
        font-size: 1rem;
        color: #c8d6ff;
        font-weight: 600;
    }

    .chart-panel h3 i {
        margin-right: 8px;
        color: #4ade80;
    }

    .parking-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
        margin: 0.5rem 0 1.2rem 0;
    }

    .slot {
        border-radius: 14px;
        padding: 18px 8px 12px 8px;
        text-align: center;
        font-weight: 700;
        font-size: 0.75rem;
        min-height: 88px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 2px solid transparent;
    }

    .slot i {
        font-size: 1.6rem;
    }

    .slot.free {
        background: linear-gradient(160deg, #14532d, #166534);
        border-color: #4ade80;
        color: #dcfce7;
        box-shadow: 0 8px 20px rgba(74, 222, 128, 0.2);
    }

    .slot.occupied {
        background: linear-gradient(160deg, #7f1d1d, #991b1b);
        border-color: #f87171;
        color: #fee2e2;
        box-shadow: 0 8px 20px rgba(248, 113, 113, 0.25);
    }

    .slot.electric {
        border-color: #38bdf8 !important;
    }

    .slot .plate-mini {
        font-size: 0.65rem;
        opacity: 0.9;
        font-weight: 600;
    }

    .voucher-box {
        background: linear-gradient(145deg, #1a2540, #121a2e);
        border: 1px solid rgba(250, 204, 21, 0.35);
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 1rem;
    }

    .badge-ev {
        display: inline-block;
        background: #0c4a6e;
        color: #7dd3fc;
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 0.75rem;
        margin-left: 6px;
    }

    .badge-mega {
        display: inline-block;
        background: #713f12;
        color: #fde047;
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 0.75rem;
        margin-left: 6px;
    }

    .tariff-surge {
        color: #ff4d4d;
        font-weight: 700;
        font-size: 1.05rem;
        padding: 10px 14px;
        border-radius: 10px;
        background: rgba(127, 29, 29, 0.35);
        border: 1px solid #f87171;
        margin: 0.5rem 0 1rem 0;
    }

    .search-hit {
        background: linear-gradient(145deg, #1e3a5f, #152a45);
        border: 1px solid #6ea8ff;
        border-radius: 14px;
        padding: 16px 20px;
        margin: 0.75rem 0 1rem 0;
        color: #e8f0ff;
    }

    .search-hit h4 {
        margin: 0 0 8px 0;
        color: #93c5fd;
    }

    .metrics-row {
        display: flex;
        gap: 12px;
        flex-wrap: nowrap;
        margin-bottom: 1rem;
        width: 100%;
    }

    .metrics-row .metric-card {
        flex: 1 1 0;
        min-width: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)
st.title("VisionPark AI")
st.caption("Умный мониторинг парковки ТРЦ")

TOTAL_SLOTS = 500
WEEKDAY_RU = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}


def get_load_percent() -> float:
    occupied = st.session_state.get("occupied", 0)
    return round(occupied / TOTAL_SLOTS * 100, 1)


def is_surge_pricing() -> bool:
    return get_load_percent() > LOAD_SURGE_THRESHOLD


def current_hourly_rate() -> int:
    return RATE_SURGE_KZT if is_surge_pricing() else RATE_KZT_PER_HOUR


def fee_kzt(entry_at: datetime, end_at: datetime, hourly_rate: int | None = None) -> int:
    rate = hourly_rate if hourly_rate is not None else current_hourly_rate()
    minutes = max(0.0, (end_at - entry_at).total_seconds() / 60.0)
    if minutes <= FREE_MINUTES:
        return 0
    billable_minutes = minutes - FREE_MINUTES
    billable_hours = math.ceil(billable_minutes / 60.0)
    return int(billable_hours * rate)


def is_blacklisted_plate(plate: str) -> bool:
    return BLACKLIST_MARKER in plate.upper()


def hourly_load_test_df() -> pd.DataFrame:
    if "hourly_load_test" not in st.session_state:
        random.seed(42)
        st.session_state.hourly_load_test = [
            {"Час": f"{h:02d}:00", "Загруженность, %": random.randint(35, 95)}
            for h in range(24)
        ]
    return pd.DataFrame(st.session_state.hourly_load_test)


def is_free_tariff(car: dict) -> bool:
    if car.get("mega_free"):
        return True
    if car.get("is_electric") or car.get("Тип") == "Электрокар":
        return True
    plate = car.get("Госномер", "")
    return plate in st.session_state.get("mega_free_plates", [])


def calculate_fee(car: dict, entry_at: datetime, end_at: datetime) -> int:
    if is_free_tariff(car):
        return 0
    return fee_kzt(entry_at, end_at)


def hours_parked(entry_at: datetime, end_at: datetime) -> float:
    return round((end_at - entry_at).total_seconds() / 3600.0, 2)


def roll_vehicle_type() -> tuple[str, bool]:
    is_ev = random.random() < ELECTRIC_SHARE
    return ("Электрокар", True) if is_ev else ("Обычный", False)


def planned_stay_duration() -> timedelta:
    return timedelta(hours=random.randint(0, 3), minutes=random.randint(45, 180))


def assign_planned_exit(record: dict) -> dict:
    record["planned_exit_at"] = record["entry_at"] + planned_stay_duration()
    return record


def normalize_car(record: dict) -> dict:
    if isinstance(record.get("entry_at"), datetime):
        for key, default in (("paid_kzt", None), ("paid_at", None), ("mega_free", False)):
            if key not in record:
                record[key] = default
        if "Тип" not in record:
            t, ev = roll_vehicle_type()
            record["Тип"] = t
            record["is_electric"] = ev
        if "planned_exit_at" not in record:
            assign_planned_exit(record)
        if "parking_slot" not in record:
            record["parking_slot"] = f"Сектор A, место {(len(st.session_state.cars) % VISUAL_SLOTS) + 1}"
        return record
    today = datetime.now().date()
    tstr = record.get("Время въезда", "12:00:00")
    try:
        h, m, s = (int(x) for x in tstr.split(":"))
        entry_at = datetime.combine(today, time(h, m, s))
    except (ValueError, IndexError):
        entry_at = datetime.now()
    record["entry_at"] = entry_at
    if "Тип" not in record:
        t, ev = roll_vehicle_type()
        record["Тип"] = t
        record["is_electric"] = ev
    record.setdefault("mega_free", False)
    if record.get("Статус") == "Оплачено":
        record["paid_at"] = entry_at + timedelta(hours=random.randint(1, 3), minutes=random.randint(0, 50))
        record["paid_kzt"] = calculate_fee(record, entry_at, record["paid_at"])
    else:
        record["paid_at"] = None
        record["paid_kzt"] = None
    assign_planned_exit(record)
    record["parking_slot"] = f"Сектор A, место {(len(st.session_state.cars) % VISUAL_SLOTS) + 1}"
    return record


def log_traffic(event_type: str, at: datetime, plate: str, amount: int | None = None) -> None:
    row = {"type": event_type, "at": at, "госномер": plate}
    if amount is not None:
        row["сумма"] = amount
    st.session_state.traffic_log.append(row)


def log_revenue(at: datetime, amount: int) -> None:
    st.session_state.revenue_log.append({"at": at, "сумма": amount})


def parse_exit_dt(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%d.%m %H:%M:%S")
    except ValueError:
        return None


def is_today(dt: datetime) -> bool:
    return dt.date() == datetime.now().date()


if "cars" not in st.session_state:
    st.session_state.cars = [
        {"Госномер": "A123BC", "Марка": "Toyota Camry", "Время въезда": "08:42:11", "Статус": "Оплачено"},
        {"Госномер": "B456DE", "Марка": "Kia Sportage", "Время въезда": "09:15:34", "Статус": "Ожидание"},
        {"Госномер": "C789FG", "Марка": "Hyundai Elantra", "Время въезда": "10:03:58", "Статус": "Оплачено"},
        {"Госномер": "D321HI", "Марка": "Lada Vesta", "Время въезда": "10:47:02", "Статус": "Ожидание"},
    ]

if "exits" not in st.session_state:
    st.session_state.exits = []
if "traffic_log" not in st.session_state:
    st.session_state.traffic_log = []
if "revenue_log" not in st.session_state:
    st.session_state.revenue_log = []
if "mega_free_plates" not in st.session_state:
    st.session_state.mega_free_plates = []

if "occupied" not in st.session_state:
    st.session_state.occupied = 428
if "free" not in st.session_state:
    st.session_state.free = 72

st.session_state.cars = [normalize_car(dict(c)) for c in st.session_state.cars]

if not st.session_state.traffic_log:
    for c in st.session_state.cars:
        log_traffic("въезд", c["entry_at"], c["Госномер"])

if not st.session_state.revenue_log:
    for ex in st.session_state.exits:
        dt = ex.get("exit_at") or parse_exit_dt(ex.get("Время выезда", ""))
        if dt:
            log_revenue(dt, int(ex.get("Сумма оплаты, ₸", 0)))


def make_plate(force_violator: bool = False) -> str:
    if force_violator or random.random() < VIOLATOR_SIM_CHANCE:
        return random.choice(["001", "A001BC", "K001MM", "001AA", "B001OP"])
    letter = "ABCEHKMOPTXY"
    return (
        f"{random.choice(letter)}{random.randint(100, 999)}"
        f"{random.choice(letter)}{random.choice(letter)}"
    )


def next_parking_slot() -> str:
    used = {c.get("parking_slot") for c in st.session_state.cars if c.get("parking_slot")}
    for n in range(1, VISUAL_SLOTS + 1):
        label = f"Сектор A, место {n}"
        if label not in used:
            return label
    return f"Сектор B, место {len(st.session_state.cars) + 1}"


def simulate_arrival() -> bool:
    if st.session_state.free <= 0:
        return False
    st.session_state.occupied += 1
    st.session_state.free -= 1
    brands = [
        "Toyota Camry",
        "Kia Sportage",
        "Hyundai Elantra",
        "Tesla Model 3",
        "BYD Atto 3",
        "BMW 5 Series",
        "Mercedes C-Class",
        "Lada Vesta",
        "Nissan Leaf",
        "Volkswagen ID.4",
    ]
    vtype, is_ev = roll_vehicle_type()
    status = random.choice(["Оплачено", "Ожидание"])
    now = datetime.now()
    plate = make_plate()
    row = {
        "Госномер": plate,
        "Марка": random.choice(brands),
        "parking_slot": next_parking_slot(),
        "entry_at": now,
        "Тип": vtype,
        "is_electric": is_ev,
        "Статус": status,
        "paid_at": None,
        "paid_kzt": None,
        "mega_free": False,
    }
    if status == "Оплачено":
        row["paid_at"] = now
        row["paid_kzt"] = calculate_fee(row, now, now)
    assign_planned_exit(row)
    st.session_state.cars.insert(0, row)
    log_traffic("въезд", now, row["Госномер"])
    if is_blacklisted_plate(plate):
        st.session_state.violator_alert = True
        st.session_state.violator_plate = plate
    return True


def normalize_mega_code(code: str) -> str:
    return code.strip().upper().replace(" ", "").replace("-", "")


def apply_mega_voucher(plate: str, code: str) -> tuple[bool, str]:
    normalized = normalize_mega_code(code)
    if normalized != MEGA_CODE:
        return False, f"Неверный код. Введите {MEGA_CODE} (без пробелов)."
    found = False
    for car in st.session_state.cars:
        if car["Госномер"] == plate:
            car["mega_free"] = True
            found = True
    if plate not in st.session_state.mega_free_plates:
        st.session_state.mega_free_plates.append(plate)
    if not found:
        return False, f"Машина {plate} не найдена на парковке."
    return True, f"Парковка для {plate} обнулена по чеку ТРЦ."


def on_mega_apply() -> None:
    plate = st.session_state.get("mega_car_select", "")
    code = st.session_state.get("mega_code_input", "")
    ok, msg = apply_mega_voucher(plate, code)
    st.session_state.mega_flash_ok = ok
    st.session_state.mega_flash_msg = msg


def on_simulate_arrival() -> None:
    st.session_state.violator_alert = False
    if simulate_arrival():
        st.session_state.arrival_flash_ok = True
        msg = "Новое авто добавлено в поток."
        if st.session_state.get("violator_alert"):
            msg = f"🚨 ОБНАРУЖЕН НАРУШИТЕЛЬ! Номер: {st.session_state.get('violator_plate', '001')}"
        st.session_state.arrival_flash_msg = msg
    else:
        st.session_state.arrival_flash_ok = False
        st.session_state.arrival_flash_msg = "Нет свободных мест — заезд невозможен."


def visual_occupied_count() -> int:
    return min(VISUAL_SLOTS, max(0, round(st.session_state.occupied / TOTAL_SLOTS * VISUAL_SLOTS)))


def render_parking_grid() -> None:
    st.subheader("Схема парковки (10 мест)")
    occ = visual_occupied_count()
    cars = st.session_state.cars
    row1 = st.columns(5)
    row2 = st.columns(5)
    for i in range(VISUAL_SLOTS):
        col = row1[i] if i < 5 else row2[i - 5]
        with col:
            if i < occ:
                car = cars[i] if i < len(cars) else None
                plate = car["Госномер"] if car else f"Место {i + 1}"
                is_ev = car and (car.get("is_electric") or car.get("Тип") == "Электрокар")
                prefix = "⚡" if is_ev else "🚗"
                st.markdown(
                    f"**{prefix} {plate}**\n\n🔴 Занято",
                    help="Электрокар" if is_ev else "Обычный автомобиль",
                )
            else:
                st.markdown("**🅿️ Свободно**\n\n🟢 Место свободно")
    st.caption(
        f"Визуализация: {occ} занято / {VISUAL_SLOTS - occ} свободно "
        f"(масштаб от {st.session_state.occupied} из {TOTAL_SLOTS} мест)."
    )


def revenue_last_24h_df() -> pd.DataFrame:
    now = datetime.now()
    labels = []
    values = []
    for h in range(24):
        bucket = (now - timedelta(hours=23 - h)).replace(minute=0, second=0, microsecond=0)
        labels.append(bucket.strftime("%H:%M"))
        total = 0
        for item in st.session_state.revenue_log:
            at = item.get("at")
            if not isinstance(at, datetime) or at < now - timedelta(hours=24):
                continue
            item_bucket = at.replace(minute=0, second=0, microsecond=0)
            if item_bucket == bucket:
                total += int(item.get("сумма", 0))
        values.append(total)
    return pd.DataFrame({"Выручка, ₸": values}, index=labels)


def show_revenue_24h_chart() -> None:
    st.subheader("Выручка за последние 24 часа")
    chart_df = revenue_last_24h_df().reset_index().rename(columns={"index": "Время"})
    st.line_chart(chart_df, x="Время", y="Выручка, ₸", use_container_width=True)


def cars_on_lot_display(cars: list[dict]) -> list[dict]:
    out = []
    for c in cars:
        pe = c.get("planned_exit_at")
        tariff = "Бесплатно"
        if c.get("mega_free") or c["Госномер"] in st.session_state.mega_free_plates:
            tariff = "Чек ТРЦ"
        elif c.get("is_electric") or c.get("Тип") == "Электрокар":
            tariff = "Электрокар"
        else:
            tariff = "Стандарт"
        out.append(
            {
                "Госномер": c["Госномер"],
                "Марка": c["Марка"],
                "Тип": c.get("Тип", "Обычный"),
                "Тариф": tariff,
                "Время въезда": c["entry_at"].strftime("%H:%M:%S"),
                "Плановый выезд": pe.strftime("%H:%M:%S") if pe else "—",
                "Место": c.get("parking_slot", "—"),
                "Статус": c["Статус"],
            }
        )
    return out


def render_metrics_row() -> None:
    load_pct = get_load_percent()
    cards = [
        ("fa-solid fa-layer-group", "Всего мест", str(TOTAL_SLOTS)),
        ("fa-solid fa-car", "Занято", str(st.session_state.occupied)),
        ("fa-solid fa-circle-check", "Свободно", str(st.session_state.free)),
        ("fa-solid fa-gauge-high", "Загрузка", f"{load_pct}%"),
    ]
    html = '<div class="metrics-row">'
    for icon, label, value in cards:
        html += (
            f'<div class="metric-card">'
            f'<div class="metric-label"><i class="{icon}"></i>{label}</div>'
            f'<div class="metric-value">{value}</div></div>'
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def show_dynamic_tariff() -> None:
    load_pct = get_load_percent()
    if is_surge_pricing():
        st.markdown(
            '<p class="tariff-surge">⚠️ Внимание: Включен повышенный тариф (1000 ₸/ч) — '
            f"загрузка парковки {load_pct}%</p>",
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"Стандартный тариф 500 ₸/ч · загрузка {load_pct}%")


def show_flow_analytics() -> None:
    st.subheader("Аналитика потока")
    st.caption("Тестовые данные загруженности парковки по часам")
    load_df = hourly_load_test_df()
    st.bar_chart(load_df, x="Час", y="Загруженность, %", use_container_width=True)


def show_car_search(query: str) -> None:
    st.subheader("Поиск авто")
    q = query.strip()
    if not q:
        st.caption("Введите госномер, чтобы найти машину на парковке.")
        return
    matches = [
        c
        for c in st.session_state.cars
        if q.upper() in c["Госномер"].upper() or c["Госномер"].upper() == q.upper()
    ]
    if not matches:
        st.warning(f"Автомобиль «{q}» не найден на парковке.")
        return
    for car in matches:
        slot = car.get("parking_slot", "—")
        ev = car.get("is_electric") or car.get("Тип") == "Электрокар"
        icon = "⚡" if ev else "🚗"
        st.markdown(
            f"""
            <div class="search-hit">
                <h4>{icon} Автомобиль найден</h4>
                <b>Госномер:</b> {car["Госномер"]}<br>
                <b>Марка:</b> {car["Марка"]}<br>
                <b>Место парковки:</b> {slot}<br>
                <b>Въезд:</b> {car["entry_at"].strftime("%H:%M:%S")}<br>
                <b>Статус:</b> {car["Статус"]} · <b>Тип:</b> {car.get("Тип", "Обычный")}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if is_blacklisted_plate(car["Госномер"]):
            st.error("🚨 ОБНАРУЖЕН НАРУШИТЕЛЬ! Номер в чёрном списке.")


def payments_display_rows(cars: list[dict], now: datetime) -> list[dict]:
    rows = []
    for c in cars:
        entry = c["entry_at"]
        free = is_free_tariff(c)
        if c["Статус"] == "Оплачено" and c.get("paid_at"):
            end = c["paid_at"]
            paid = 0 if free else int(c.get("paid_kzt") or calculate_fee(c, entry, end))
            hp = hours_parked(entry, end)
        else:
            end = now
            paid = 0 if free else calculate_fee(c, entry, now)
            hp = hours_parked(entry, end)
        rows.append(
            {
                "Госномер": c["Госномер"],
                "Марка": c["Марка"],
                "Тип": c.get("Тип", "Обычный"),
                "Время въезда": entry.strftime("%H:%M:%S"),
                "Статус": c["Статус"],
                "Пробыло, ч": hp,
                "Сумма оплаты, ₸": paid if c["Статус"] == "Оплачено" else "—",
                "К оплате сейчас, ₸": "—" if c["Статус"] == "Оплачено" else paid,
            }
        )
    return rows


def apply_exit(car: dict, exit_at: datetime) -> None:
    amount = calculate_fee(car, car["entry_at"], exit_at)
    if car["Статус"] == "Оплачено" and car.get("paid_kzt") is not None and car.get("paid_at"):
        amount = 0 if is_free_tariff(car) else int(car["paid_kzt"])
    st.session_state.exits.insert(
        0,
        {
            "Госномер": car["Госномер"],
            "Марка": car["Марка"],
            "Тип": car.get("Тип", "Обычный"),
            "Время въезда": car["entry_at"].strftime("%d.%m %H:%M:%S"),
            "Время выезда": exit_at.strftime("%d.%m %H:%M:%S"),
            "exit_at": exit_at,
            "Сумма оплаты, ₸": amount,
            "Статус при выезде": car["Статус"],
        },
    )
    st.session_state.occupied = max(0, st.session_state.occupied - 1)
    st.session_state.free = min(TOTAL_SLOTS, st.session_state.free + 1)
    log_traffic("выезд", exit_at, car["Госномер"], amount)
    log_revenue(exit_at, amount)


def process_due_exits(now: datetime) -> None:
    cars = st.session_state.cars
    due: list[tuple[int, dict, datetime]] = []
    for i, car in enumerate(cars):
        planned = car.get("planned_exit_at")
        if planned and now >= planned:
            due.append((i, car, planned))
    for i, car, exit_at in sorted(due, key=lambda x: x[0], reverse=True):
        cars.pop(i)
        apply_exit(car, exit_at)


def exits_today_df() -> pd.DataFrame:
    rows = []
    for ex in st.session_state.exits:
        dt = ex.get("exit_at") or parse_exit_dt(ex.get("Время выезда", ""))
        if dt and is_today(dt):
            rows.append(
                {
                    "Время": dt,
                    "Час": dt.strftime("%H:00"),
                    "Госномер": ex["Госномер"],
                    "Сумма, ₸": ex["Сумма оплаты, ₸"],
                }
            )
    return pd.DataFrame(rows)


def revenue_today_chart_df() -> pd.DataFrame:
    df = exits_today_df()
    if df.empty:
        hours = pd.date_range(
            start=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
            periods=24,
            freq="h",
        )
        return pd.DataFrame({"Час": [h.strftime("%H:00") for h in hours], "Доход, ₸": [0] * 24})
    hourly = df.groupby("Час", as_index=False)["Сумма, ₸"].sum()
    hourly = hourly.sort_values("Час")
    hourly["Накопительно, ₸"] = hourly["Сумма, ₸"].cumsum()
    return hourly


def traffic_flow_chart_df() -> pd.DataFrame:
    today = datetime.now().date()
    events = [
        e
        for e in st.session_state.traffic_log
        if isinstance(e.get("at"), datetime) and e["at"].date() == today
    ]
    if not events:
        return pd.DataFrame(
            {
                "Час": [f"{h:02d}:00" for h in range(24)],
                "Заезды": [0] * 24,
                "Выезды": [0] * 24,
            }
        )
    df = pd.DataFrame(events)
    df["Час"] = df["at"].dt.strftime("%H:00")
    entries = df[df["type"] == "въезд"].groupby("Час").size()
    exits = df[df["type"] == "выезд"].groupby("Час").size()
    hours = [f"{h:02d}:00" for h in range(24)]
    result = pd.DataFrame({"Час": hours})
    result["Заезды"] = result["Час"].map(entries).fillna(0).astype(int)
    result["Выезды"] = result["Час"].map(exits).fillna(0).astype(int)
    return result


def peak_traffic_insights() -> tuple[str, str]:
    log = st.session_state.traffic_log
    if not log:
        return (
            "Недостаточно данных для анализа потока.",
            "Заезды и выезды появятся по мере работы парковки.",
        )
    df = pd.DataFrame(
        [{"type": e["type"], "at": e["at"]} for e in log if isinstance(e.get("at"), datetime)]
    )
    if df.empty:
        return ("Нет событий.", "—")

    df["weekday"] = df["at"].dt.weekday.map(WEEKDAY_RU)
    df["hour"] = df["at"].dt.hour
    df["date"] = df["at"].dt.date

    all_events = df.groupby(["weekday", "hour"]).size().reset_index(name="count")
    peak_row = all_events.loc[all_events["count"].idxmax()]
    global_peak = (
        f"**Плотный поток (все дни):** {peak_row['weekday']}, "
        f"{peak_row['hour']:02d}:00–{(peak_row['hour'] + 1) % 24:02d}:00 "
        f"({int(peak_row['count'])} событий заезда/выезда)."
    )

    today = datetime.now().date()
    today_df = df[df["date"] == today]
    if today_df.empty:
        today_peak = "**Сегодня:** пока нет зафиксированного пика — ждём события."
    else:
        t_peak = today_df.groupby("hour").size().reset_index(name="count")
        tr = t_peak.loc[t_peak["count"].idxmax()]
        entries_t = int((today_df["type"] == "въезд").sum())
        exits_t = int((today_df["type"] == "выезд").sum())
        today_peak = (
            f"**Сегодня ({today.strftime('%d.%m.%Y')}):** пик активности "
            f"{int(tr['hour']):02d}:00–{(int(tr['hour']) + 1) % 24:02d}:00 "
            f"({int(tr['count'])} событий). Заездов: {entries_t}, выездов: {exits_t}."
        )

    return global_peak, today_peak


def build_excel_report() -> bytes:
    buffer = io.BytesIO()
    exits_df = pd.DataFrame(st.session_state.exits)
    if "exit_at" in exits_df.columns:
        exits_df = exits_df.drop(columns=["exit_at"])
    cars_df = pd.DataFrame(cars_on_lot_display(st.session_state.cars))
    traffic_df = pd.DataFrame(st.session_state.traffic_log)
    if not traffic_df.empty and "at" in traffic_df.columns:
        traffic_df["at"] = pd.to_datetime(traffic_df["at"]).dt.strftime("%d.%m.%Y %H:%M:%S")
    revenue_df = revenue_today_chart_df()
    flow_df = traffic_flow_chart_df()
    summary = pd.DataFrame(
        {
            "Показатель": [
                "Дата отчёта",
                "Доход за сегодня, ₸",
                "Количество выездов сегодня",
                "Машин на парковке",
                "Занято мест",
                "Свободно мест",
                "Электрокаров на парковке",
            ],
            "Значение": [
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                int(exits_today_df()["Сумма, ₸"].sum()) if not exits_today_df().empty else 0,
                len(exits_today_df()),
                len(st.session_state.cars),
                st.session_state.occupied,
                st.session_state.free,
                sum(1 for c in st.session_state.cars if c.get("is_electric")),
            ],
        }
    )
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Сводка", index=False)
        revenue_df.to_excel(writer, sheet_name="Доход по часам", index=False)
        flow_df.to_excel(writer, sheet_name="Поток заездов", index=False)
        exits_df.to_excel(writer, sheet_name="Выезды", index=False)
        cars_df.to_excel(writer, sheet_name="На парковке", index=False)
        traffic_df.to_excel(writer, sheet_name="Журнал событий", index=False)
    buffer.seek(0)
    return buffer.getvalue()


def show_revenue_history() -> None:
    st.subheader("История доходов")

    today_income = int(exits_today_df()["Сумма, ₸"].sum()) if not exits_today_df().empty else 0
    st.metric("Доход за сегодня", f"{today_income:,} ₸".replace(",", " "))

    revenue_df = revenue_today_chart_df()
    if today_income > 0 and "Накопительно, ₸" in revenue_df.columns:
        chart_rev = (
            alt.Chart(revenue_df)
            .mark_line(point=True, color="#6ea8ff")
            .encode(
                x=alt.X("Час:N", title="Час"),
                y=alt.Y("Накопительно, ₸:Q", title="Накопительный доход, ₸"),
                tooltip=["Час", "Сумма, ₸", "Накопительно, ₸"],
            )
            .properties(height=280, title="Накопительный доход за сегодня")
        )
        st.altair_chart(chart_rev, use_container_width=True)

        chart_hourly = (
            alt.Chart(revenue_df)
            .mark_bar(color="#4ade80")
            .encode(
                x=alt.X("Час:N", title="Час"),
                y=alt.Y("Сумма, ₸:Q", title="Доход за час, ₸"),
                tooltip=["Час", "Сумма, ₸"],
            )
            .properties(height=220, title="Доход по часам")
        )
        st.altair_chart(chart_hourly, use_container_width=True)
    else:
        st.info("Доход за сегодня появится после первых выездов с оплатой.")

    flow_df = traffic_flow_chart_df()
    flow_long = flow_df.melt(id_vars=["Час"], value_vars=["Заезды", "Выезды"], var_name="Событие", value_name="Кол-во")
    chart_flow = (
        alt.Chart(flow_long)
        .mark_line(point=True)
        .encode(
            x=alt.X("Час:N", title="Час"),
            y=alt.Y("Кол-во:Q", title="Количество"),
            color=alt.Color("Событие:N", title=""),
            tooltip=["Час", "Событие", "Кол-во"],
        )
        .properties(height=300, title="Заезды и выезды по часам (сегодня)")
    )
    st.altair_chart(chart_flow, use_container_width=True)

    global_peak, today_peak = peak_traffic_insights()
    st.markdown(
        f"<div class='peak-box'>{global_peak}<br><br>{today_peak}</div>",
        unsafe_allow_html=True,
    )

    try:
        excel_bytes = build_excel_report()
        st.download_button(
            label="Выгрузить отчет в Excel",
            data=excel_bytes,
            file_name=f"VisionPark_отчет_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except ImportError:
        st.error("Для Excel установите: pip install openpyxl")


def show_mega_voucher_form() -> None:
    st.subheader("Валидация чека ТРЦ")
    cars = st.session_state.cars
    if not cars:
        st.caption("Нет машин на парковке для применения чека.")
        return
    plates = [c["Госномер"] for c in cars]
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.selectbox("Машина", plates, key="mega_car_select")
    with c2:
        st.text_input("Код чека", placeholder="MEGA2024", key="mega_code_input")
    with c3:
        st.write("")
        st.write("")
        st.button("Применить", use_container_width=True, key="mega_apply", on_click=on_mega_apply)
    if st.session_state.get("mega_flash_msg"):
        if st.session_state.get("mega_flash_ok"):
            st.success(st.session_state.mega_flash_msg)
        else:
            st.error(st.session_state.mega_flash_msg)
    st.caption("Код MEGA2024 обнуляет парковку для выбранной машины.")


@st.fragment(run_every=timedelta(seconds=REFRESH_SECONDS))
def live_dashboard(query: str = "") -> None:
    now = datetime.now()
    process_due_exits(now)

    if st.session_state.get("violator_alert"):
        st.error(
            f"🚨 ОБНАРУЖЕН НАРУШИТЕЛЬ! Номер: {st.session_state.get('violator_plate', BLACKLIST_MARKER)}"
        )

    show_revenue_24h_chart()
    show_flow_analytics()
    show_dynamic_tariff()
    render_metrics_row()
    render_parking_grid()

    st.subheader("Автомобили в реальном времени")
    df = pd.DataFrame(cars_on_lot_display(st.session_state.cars))
    if query.strip():
        filtered = df[df["Госномер"].str.contains(query.strip(), case=False, na=False)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        if filtered.empty:
            st.warning("Авто с таким номером не найдено в таблице.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    ev_count = sum(1 for c in st.session_state.cars if c.get("is_electric"))
    st.caption(f"Электрокаров на парковке: {ev_count} (~10% заездов — бесплатный тариф)")

    st.subheader("Оплаты заехавших авто")
    rate_note = f"{current_hourly_rate()} ₸/ч" if is_surge_pricing() else "500 ₸/ч"
    st.caption(
        f"1-й час бесплатно, далее {rate_note}. Электрокар — 0 ₸. MEGA2024 — обнуление. "
        f"Чёрный список: номер с «{BLACKLIST_MARKER}»."
    )
    pay_rows = payments_display_rows(st.session_state.cars, now)
    st.dataframe(pd.DataFrame(pay_rows), use_container_width=True, hide_index=True)

    st.subheader("Журнал выездов")
    st.caption(f"Выезд по плановому времени (обновление каждые {REFRESH_SECONDS} с).")
    ex = st.session_state.exits
    display_exits = [{k: v for k, v in row.items() if k != "exit_at"} for row in ex]
    if display_exits:
        st.dataframe(pd.DataFrame(display_exits), use_container_width=True, hide_index=True)
    else:
        st.caption("Пока нет выездов — авто выедет по истечении времени стоянки после въезда.")

    show_revenue_history()


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def show_share_panel() -> None:
    local_ip = get_local_ip()
    port = 8501
    lan_url = f"http://{local_ip}:{port}"
    with st.sidebar:
        st.markdown("### Поделиться")
        st.markdown("**В одной Wi‑Fi / офисной сети**")
        st.code(lan_url, language=None)
        st.caption(
            "Запуск: `run_shared.bat` или `py -3 -m streamlit run VisionPark_App.py`. "
            "Разрешите доступ в Firewall."
        )
        st.markdown("**Через интернет**")
        st.markdown(
            "1. GitHub → 2. [share.streamlit.io](https://share.streamlit.io) → "
            "3. `VisionPark_App.py` → **Deploy**"
        )
        st.code("http://localhost:8501", language=None)
        st.markdown("---")
        st.markdown("**Легенда:** 🚗 занято · 🅿️ свободно · ⚡ электрокар")
        st.markdown(f"**Чёрный список:** номер содержит `{BLACKLIST_MARKER}`")


show_share_panel()

col_btn, _ = st.columns([1, 3])
with col_btn:
    st.button(
        "Имитировать заезд авто",
        use_container_width=True,
        type="primary",
        key="btn_arrival",
        on_click=on_simulate_arrival,
    )

if st.session_state.get("arrival_flash_msg"):
    if st.session_state.get("arrival_flash_ok"):
        if st.session_state.get("violator_alert"):
            st.error(st.session_state.arrival_flash_msg)
        else:
            st.success(st.session_state.arrival_flash_msg)
    else:
        st.warning(st.session_state.arrival_flash_msg)

show_mega_voucher_form()

query = st.text_input(
    "Поиск авто по номеру",
    placeholder="Например: A123BC или 001",
    key="search_plate",
)
show_car_search(query)

live_dashboard(query)
