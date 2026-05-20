import io
import math
import random
import socket
from datetime import datetime, time, timedelta

import altair as alt
import pandas as pd
import streamlit as st

RATE_KZT_PER_HOUR = 500
FREE_MINUTES = 60
REFRESH_SECONDS = 1


st.set_page_config(
    page_title="VisionPark AI",
    page_icon="🚗",
    layout="wide",
)


st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #131a2a 0%, #0b0f18 55%, #070b12 100%);
        color: #e7ecff;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 1rem;
        color: #f6f8ff;
        letter-spacing: 0.4px;
    }

    .metric-card {
        background: linear-gradient(145deg, #1a2338, #121a2b);
        border: 1px solid rgba(124, 152, 255, 0.28);
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.28);
    }

    .metric-label {
        font-size: 0.95rem;
        color: #9fb0dd;
        margin-bottom: 8px;
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
        font-size: 1.2rem;
        font-weight: 700;
        color: #dfe7ff;
    }

    .hint {
        font-size: 0.9rem;
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
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='main-title'>VisionPark AI — Мониторинг парковки</div>", unsafe_allow_html=True)

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


def fee_kzt(entry_at: datetime, end_at: datetime) -> int:
    """Первый час бесплатно, каждый следующий час (или его часть) — 500 ₸."""
    minutes = max(0.0, (end_at - entry_at).total_seconds() / 60.0)
    if minutes <= FREE_MINUTES:
        return 0
    billable_minutes = minutes - FREE_MINUTES
    billable_hours = math.ceil(billable_minutes / 60.0)
    return int(billable_hours * RATE_KZT_PER_HOUR)


def hours_parked(entry_at: datetime, end_at: datetime) -> float:
    return round((end_at - entry_at).total_seconds() / 3600.0, 2)


def planned_stay_duration() -> timedelta:
    """Реалистичное время на парковке: от ~45 мин до ~4 ч."""
    return timedelta(
        hours=random.randint(0, 3),
        minutes=random.randint(45, 180),
    )


def assign_planned_exit(record: dict) -> dict:
    entry = record["entry_at"]
    record["planned_exit_at"] = entry + planned_stay_duration()
    return record


def normalize_car(record: dict) -> dict:
    if isinstance(record.get("entry_at"), datetime):
        if "paid_kzt" not in record:
            record["paid_kzt"] = None
        if "paid_at" not in record:
            record["paid_at"] = None
        if "planned_exit_at" not in record:
            assign_planned_exit(record)
        return record
    today = datetime.now().date()
    tstr = record.get("Время въезда", "12:00:00")
    try:
        h, m, s = (int(x) for x in tstr.split(":"))
        entry_at = datetime.combine(today, time(h, m, s))
    except (ValueError, IndexError):
        entry_at = datetime.now()
    record["entry_at"] = entry_at
    if record.get("Статус") == "Оплачено":
        record["paid_at"] = entry_at + timedelta(hours=random.randint(1, 3), minutes=random.randint(0, 50))
        record["paid_kzt"] = fee_kzt(entry_at, record["paid_at"])
    else:
        record["paid_at"] = None
        record["paid_kzt"] = None
    assign_planned_exit(record)
    return record


def log_traffic(event_type: str, at: datetime, plate: str, amount: int | None = None) -> None:
    row = {"type": event_type, "at": at, "госномер": plate}
    if amount is not None:
        row["сумма"] = amount
    st.session_state.traffic_log.append(row)


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

st.session_state.cars = [normalize_car(dict(c)) for c in st.session_state.cars]

if not st.session_state.traffic_log:
    for c in st.session_state.cars:
        log_traffic("въезд", c["entry_at"], c["Госномер"])

if "occupied" not in st.session_state:
    st.session_state.occupied = 428
if "free" not in st.session_state:
    st.session_state.free = 72


def make_plate() -> str:
    letter = "ABCEHKMOPTXY"
    return (
        f"{random.choice(letter)}{random.randint(100, 999)}"
        f"{random.choice(letter)}{random.choice(letter)}"
    )


def simulate_arrival() -> bool:
    if st.session_state.free <= 0:
        return False
    st.session_state.occupied += 1
    st.session_state.free -= 1
    brands = [
        "Toyota Camry",
        "Kia Sportage",
        "Hyundai Elantra",
        "Chevrolet Malibu",
        "BMW 5 Series",
        "Mercedes C-Class",
        "Lada Vesta",
        "Nissan Qashqai",
        "Volkswagen Passat",
    ]
    status = random.choice(["Оплачено", "Ожидание"])
    now = datetime.now()
    row = {
        "Госномер": make_plate(),
        "Марка": random.choice(brands),
        "entry_at": now,
        "Статус": status,
        "paid_at": None,
        "paid_kzt": None,
    }
    if status == "Оплачено":
        row["paid_at"] = now
        row["paid_kzt"] = fee_kzt(now, now)
    assign_planned_exit(row)
    st.session_state.cars.insert(0, row)
    log_traffic("въезд", now, row["Госномер"])
    return True


def cars_on_lot_display(cars: list[dict]) -> list[dict]:
    out = []
    for c in cars:
        pe = c.get("planned_exit_at")
        out.append(
            {
                "Госномер": c["Госномер"],
                "Марка": c["Марка"],
                "Время въезда": c["entry_at"].strftime("%H:%M:%S"),
                "Плановый выезд": pe.strftime("%H:%M:%S") if pe else "—",
                "Статус": c["Статус"],
            }
        )
    return out


def payments_display_rows(cars: list[dict], now: datetime) -> list[dict]:
    rows = []
    for c in cars:
        entry = c["entry_at"]
        if c["Статус"] == "Оплачено" and c.get("paid_at"):
            end = c["paid_at"]
            paid = int(c.get("paid_kzt") or fee_kzt(entry, end))
            hp = hours_parked(entry, end)
        elif c["Статус"] == "Оплачено":
            end = now
            paid = int(c.get("paid_kzt") or fee_kzt(entry, end))
            hp = hours_parked(entry, end)
        else:
            end = now
            paid = fee_kzt(entry, now)
            hp = hours_parked(entry, now)
        rows.append(
            {
                "Госномер": c["Госномер"],
                "Марка": c["Марка"],
                "Время въезда": entry.strftime("%H:%M:%S"),
                "Статус": c["Статус"],
                "Пробыло, ч": hp,
                "Сумма оплаты, ₸": paid if c["Статус"] == "Оплачено" else "—",
                "К оплате сейчас, ₸": "—" if c["Статус"] == "Оплачено" else paid,
            }
        )
    return rows


def apply_exit(car: dict, exit_at: datetime) -> None:
    if car["Статус"] == "Оплачено" and car.get("paid_kzt") is not None and car.get("paid_at"):
        amount = int(car["paid_kzt"])
    else:
        amount = fee_kzt(car["entry_at"], exit_at)
    st.session_state.exits.insert(
        0,
        {
            "Госномер": car["Госномер"],
            "Марка": car["Марка"],
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


def process_due_exits(now: datetime) -> None:
    """Выезд в запланированное время (от въезда + время стоянки)."""
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
            ],
            "Значение": [
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                int(exits_today_df()["Сумма, ₸"].sum()) if not exits_today_df().empty else 0,
                len(exits_today_df()),
                len(st.session_state.cars),
                st.session_state.occupied,
                st.session_state.free,
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
    st.markdown("<div class='table-title'>История доходов</div>", unsafe_allow_html=True)

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


@st.fragment(run_every=timedelta(seconds=REFRESH_SECONDS))
def live_dashboard() -> None:
    now = datetime.now()
    process_due_exits(now)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div class='metric-card'><div class='metric-label'>Всего мест</div>"
            f"<div class='metric-value'>{TOTAL_SLOTS}</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div class='metric-card'><div class='metric-label'>Занято</div>"
            f"<div class='metric-value'>{st.session_state.occupied}</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            "<div class='metric-card'><div class='metric-label'>Свободно</div>"
            f"<div class='metric-value'>{st.session_state.free}</div></div>",
            unsafe_allow_html=True,
        )

    query = st.text_input("Поиск авто по номеру", placeholder="Например: A123BC", key="search_plate")

    st.markdown("<div class='table-title'>Автомобили в реальном времени</div>", unsafe_allow_html=True)
    df = pd.DataFrame(cars_on_lot_display(st.session_state.cars))
    if query:
        filtered = df[df["Госномер"].str.contains(query.strip(), case=False, na=False)]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        if filtered.empty:
            st.warning("Авто с таким номером не найдено.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("<div class='table-title'>Оплаты заехавших авто</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hint'>Тариф: первый час бесплатно, далее 500 ₸ за каждый начатый час. "
        "Выезд — по плановому времени от въезда (реалистичная стоянка).</div>",
        unsafe_allow_html=True,
    )
    pay_rows = payments_display_rows(st.session_state.cars, now)
    st.dataframe(pd.DataFrame(pay_rows), use_container_width=True, hide_index=True)

    st.markdown("<div class='table-title'>Журнал выездов</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='hint'>Выезд в запланированное время (обновление каждые {REFRESH_SECONDS} с).</div>",
        unsafe_allow_html=True,
    )
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
        st.markdown("### Поделиться сайтом")
        st.markdown("**В одной Wi‑Fi / офисной сети**")
        st.code(lan_url, language=None)
        st.caption(
            "Отправьте эту ссылку коллегам. Запускайте через `run_shared.bat` "
            "или `py -3 -m streamlit run VisionPark_App.py`. "
            "При запросе Windows Firewall разрешите доступ для Python."
        )
        st.markdown("**Через интернет (бесплатно)**")
        st.markdown(
            "1. Загрузите папку проекта на [GitHub](https://github.com)\n"
            "2. Откройте [share.streamlit.io](https://share.streamlit.io)\n"
            "3. **New app** → репозиторий → файл `VisionPark_App.py` → **Deploy**\n"
            "4. Получите постоянную ссылку вида `https://ваш-проект.streamlit.app`"
        )
        st.markdown("**На этом компьютере**")
        st.code("http://localhost:8501", language=None)


if st.button("Имитировать заезд авто", use_container_width=True):
    if simulate_arrival():
        st.success("Новое авто добавлено в поток.")
    else:
        st.warning("Нет свободных мест — заезд невозможен.")

show_share_panel()
live_dashboard()
