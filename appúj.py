# app.py — Teljes kérdőív készre drótozva
# - képek az app.py-val egy mappában (praga.png, barcelona.png, roma.png)
# - minden skála 1–10 rádiós Likert (nincs csúszka)
# - vissza/előre gombok, haladásjelző, CSV-mentés
# - nincsenek duplikált key-ek

import streamlit as st
import pandas as pd
import json, time, uuid, random
from datetime import datetime
from pathlib import Path

import smtplib
from email.mime.text import MIMEText
import streamlit as st

def send_email_notification(record: dict):
    try:
        sender = st.secrets["email"]["address"]
        password = st.secrets["email"]["password"]
        receiver = st.secrets["email"]["address"]

        subject = "Új kérdőív kitöltés érkezett"
        body = f"Egy új válasz érkezett:\n\n{record}"

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = receiver

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
    except Exception as e:
        # Hibát is jelez a felületen, de ne dobja el a mentést
        st.error(f"Email küldési hiba: {e}")
 
# ---------- ALAP ----------
st.set_page_config(page_title="🧭 MI-ajánlások a fogyasztói döntésekben", page_icon="📝", layout="centered")
DATA_PATH = Path("responses.xlsx")

def save_row(row: dict):
    """Append: egy sor mentése Excel (XLSX) fájlba, lapos táblázatként."""
    flat = {}
    for k, v in row.items():
        if isinstance(v, dict):
            for subk, subv in v.items():
                flat[f"{k}_{subk}"] = subv
        elif isinstance(v, list):
            flat[k] = json.dumps(v, ensure_ascii=False)
        else:
            flat[k] = v

    df_new = pd.DataFrame([flat])

    if DATA_PATH.exists():
        df_old = pd.read_excel(DATA_PATH, engine="openpyxl")
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        # ha még nincs fájl, akkor a df_all = df_new legyen
        df_all = df_new

    # fontos oszlopok sorrendje
    id_cols = ["rid", "entered_at", "submitted_at", "group"]
    time_cols = [f"duration_page_{i}" for i in range(1, 20)]
    other_cols = [c for c in df_all.columns if c not in id_cols + time_cols]

    # ha hiányzik valamelyik időoszlop, hozzuk létre
    for col in time_cols:
        if col not in df_all.columns:
            df_all[col] = None

    # új sorrend
    df_all = df_all[id_cols + time_cols + other_cols]

    df_all.to_excel(DATA_PATH, index=False, engine="openpyxl")

  


def progress_bar(current_page, total_pages):
    st.progress(current_page / total_pages)

def calc_durations(timestamps: dict, total_pages: int):
    durations = {}
    for page_num in range(total_pages + 1):  # 0..TOTAL_PAGES
        key_entered = f"page_{page_num}_entered"
        key_left = f"page_{page_num}_left"
        if key_entered in timestamps and key_left in timestamps:
            entered = datetime.fromisoformat(timestamps[key_entered])
            left = datetime.fromisoformat(timestamps[key_left])
            durations[page_num] = (left - entered).total_seconds()
        else:
            durations[page_num] = 0
    return durations



# ---------- SESSION ----------
if "rid" not in st.session_state:
    st.session_state.rid = str(uuid.uuid4())
if "page" not in st.session_state:
    st.session_state.page = 0
if "entered_at" not in st.session_state:
    st.session_state.entered_at = datetime.utcnow().isoformat()
if "group" not in st.session_state:
    st.session_state.group = random.choice(["text", "visual"])
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "timestamps" not in st.session_state:   # ⬅️ EZ AZ ÚJ RÉSZ
    st.session_state.timestamps = {}
page = st.session_state.page


# ---------- DEFAULT VÁLTOZÓK ----------
if "factors" not in st.session_state:
    st.session_state.factors = {}

if "experience" not in st.session_state:
    st.session_state.experience = {}

if "ai_influence" not in st.session_state:
    st.session_state.ai_influence = None


# minden oldal betöltésekor logoljuk a belépést
st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

# ---------- NAV FUNKCIÓ (felülírás) ----------




TOTAL_PAGES = 19  # 0..18

# ---------- ANYAGOK (ajánlatok + skálák) ----------
TEXT_OFFERS = {
    "Prága":"""Egy 4 napos prágai utazást ajánlok Önnek, amely 3 éjszaka szállást tartalmaz egy belvárosi hotelben, reggelivel.  
Az út során idegenvezető kíséretében fedezheti fel a Károly hidat, az Óváros teret és a prágai vár történelmi utcáit.  
**Az ajánlat ára: 129 900 Ft/fő.**""",
    "Barcelona":"""Ajánlok Önnek egy 4 napos barcelonai városlátogatást, amely 3 éjszakás szállást biztosít egy tengerpart közeli, 4 csillagos hotelben, reggelivel.  
Az utazás során megcsodálhatja Gaudí ikonikus alkotásait, köztük a Sagrada Famíliát és a Güell parkot, valamint átélheti a mediterrán város vibráló hangulatát.  
**Az ajánlat ára: 159 900 Ft/fő.**""",
    "Róma":"""Szívesen ajánlok Önnek egy 4 napos római kirándulást, amely 3 éjszakás szállást tartalmaz egy központi elhelyezkedésű hotelben, reggelivel.  
Az ajánlat része a belépő a Colosseumba és a Vatikáni Múzeumokba, így közvetlen közelről élheti át az örök város kulturális kincseit.  
**Az ajánlat ára: 134 900 Ft/fő.**""",
}

IMAGES = {
    # a képek az app.py-val EGY mappában legyenek (ékezet NÉLKÜL!)
    "Prága": "praga.png",
    "Barcelona": "barcelona.png",
    "Róma": "roma.png",
}

CAPTIONS = {
    "Prága": "Prága – 129 900 Ft/fő · 4 nap · Kulturális élmény",
    "Barcelona": "Barcelona – 159 900 Ft/fő · 4 nap · Mediterrán élmény",
    "Róma": "Róma – 134 900 Ft/fő · 4 nap · Történelmi élmény",
}

DECISION_FACTORS = [
    "Az ajánlat ára",
    "A város iránti kíváncsiságom",
    "Korábbi pozitív élményeim a helyszínnel",
    "Ismerőseim véleménye",
    "Az ajánlat szövegének stílusa",
    "A kép vizuális minősége",
    "Az ajánlat platformja (ahol megjelent)",
    "Az, hogy mesterséges intelligencia generálta-e",
    "Távolság / utazás kényelme",
    "Biztonsági szempontok",
    "Időjárás / évszak",
    "Saját pénzügyi helyzetem",
    "Egyéb személyes szempont",
]

EXPERIENCE_ITEMS = [
    "Mennyire érezte hitelesnek az ajánlatokat?",
    "Mennyire volt könnyű megérteni a szövegeket/képeket?",
    "Mennyire tűntek megbízhatónak az ajánlatok?",
    "Mennyire volt kellemes az élmény?",
    "Mennyire érezte személyre szabottnak az ajánlatokat?",
    "Mennyire érezte, hogy a mesterséges intelligencia jól tudja, mi érdekli?",
]

AI_TRUST = [
    "Általában bízom az MI által generált tartalmakban.",
    "Az MI ajánlásai hasznosak számomra.",
    "Az MI gyakran félrevezető információt ad. (fordított tétel)",
    "Szívesen hozok döntést MI-ajánlások alapján.",
]

PERSUASION_KNOWLEDGE = [
    "Könnyen felismerem, ha egy ajánlat marketing célból készült.",
    "Gyorsan észreveszem, ha valami túl szép ahhoz, hogy igaz legyen.",
    "Általában átlátok a reklámokon.",
]

MANIP_CHECK = [
    "Az értékeléskor figyelmen kívül hagytam az árat.",
    "Megértettem, hogy a tartalmakat MI generálta / állíthatta elő.",
]

DEMOGRAPHICS = {
    "Nem": ["Nő", "Férfi", "Egyéb", "Nem szeretnék válaszolni"],
    "Életkor": ["18-24", "25-34", "35-44", "45-54", "55+"],
    "Legmagasabb iskolai végzettség": [
        "Középiskola",
        "Főiskola / Egyetem (BA/BSc)",
        "Mesterképzés (MA/MSc)",
        "PhD / DLA",
    ],
}



def nav(prev=None, next=None, submit=False, require_key=None):
    def _get_val(rk):
        # 1. top-level session_state
        if rk in st.session_state:
            return st.session_state[rk]
        # 2. answers dict
        if "answers" in st.session_state and rk in st.session_state["answers"]:
            return st.session_state["answers"][rk]
        return None

    c1, c2 = st.columns([1,1])

    with c1:
        if prev is not None and st.button("← Vissza", key=f"prev_{st.session_state.page}_to_{prev}"):
            # ⬅️ oldal elhagyása
            st.session_state.timestamps[f"page_{st.session_state.page}_left"] = datetime.utcnow().isoformat()
            st.session_state.page = prev
            st.session_state.timestamps[f"page_{st.session_state.page}_entered"] = datetime.utcnow().isoformat()
            st.rerun()

    with c2:
        if submit:
            if st.button("Beküldés ✅", key=f"submit_{st.session_state.page}"):
                return "submit"
        elif next is not None:
            if st.button("Tovább →", key=f"next_{st.session_state.page}_to_{next}"):
                if require_key:
                    keys = require_key if isinstance(require_key, (list, tuple)) else [require_key]
                    for rk in keys:
                        val = _get_val(rk)
                        if val is None:
                            st.error("⚠️ Kérjük, töltsön ki minden mezőt, mielőtt továbblépne!")
                            st.stop()
                        if isinstance(val, dict) and any(v is None for v in val.values()):
                            st.error("⚠️ Kérjük, töltsön ki minden mezőt, mielőtt továbblépne!")
                            st.stop()

                # ⬅️ oldal elhagyása
                st.session_state.timestamps[f"page_{st.session_state.page}_left"] = datetime.utcnow().isoformat()
                st.session_state.page = next
                st.session_state.timestamps[f"page_{st.session_state.page}_entered"] = datetime.utcnow().isoformat()
                st.rerun()
    return None


def calc_durations(timestamps: dict):
    durations = {}
    for key, value in timestamps.items():
        if key.endswith("_entered"):
            page_tag = key.replace("_entered", "")
            entered = datetime.fromisoformat(value)
            left_key = f"{page_tag}_left"
            if left_key in timestamps:
                left = datetime.fromisoformat(timestamps[left_key])
                page_num = int(page_tag.split("_")[-1])
                durations[page_num] = (left - entered).total_seconds()
            else:
                durations[int(page_tag.split("_")[-1])] = 0
    return durations





# oldal belépés ideje logolva
if f"page_{page}_entered" not in st.session_state.timestamps:
    st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()



# oldal belépés ideje logolva
st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()



# 0. oldal – Bevezető + Beleegyezés + Instrukciók
if page == 0:
    st.title("🧭 MI-ajánlások a fogyasztói döntésekben")

    st.markdown("""
    Kedves Kitöltő!

    Budai Katalin vagyok, a Budapesti Gazdaságtudományi Egyetem pénzügy-számvitel alapszakos hallgatója. 
    Ez a kérdőív a Tudományos Diákköri Konferenciára készülő kutatásom része, amelyben azt vizsgálom, 
    hogyan befolyásolhatja a mesterséges intelligencia a fogyasztói döntéshozatalt. 

    A kitöltés körülbelül 8-10 percet vesz igénybe, és nagy segítséget jelent számomra. 
    Még nagyobb támogatás, ha a kérdőívet másoknak is továbbítja, mert minél több válaszra van szükségem 
    a kutatás sikeres megvalósításához.

    Előre is köszönöm a segítségét és közreműködését!
    """)

    progress_bar(0, TOTAL_PAGES)

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.markdown("**Beleegyezés**")
    consent = st.radio(
        "Hozzájárulok a névtelen válaszaim kutatási célú felhasználásához.",
        ["Igen", "Nem"], index=None, key="consent_0")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
  

    if st.button("Kezdés →"):
        if consent != "Igen":
            st.error("A kérdőív folytatásához szükség van a hozzájárulásra.")
        else:
            st.session_state.timestamps[f"page_{st.session_state.page}_left"] = datetime.utcnow().isoformat()
            st.session_state.page = 1
            st.session_state.timestamps[f"page_{st.session_state.page}_entered"] = datetime.utcnow().isoformat()
            st.rerun()


# ===== Ajánlat oldalak (1-3) =====
elif page == 1:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.now()

    st.markdown("**Instrukciók**")
    st.write("A következő oldalakon MI által javasolt utazási ajánlatokat lát. "
             "Kérjük, olvassa el / nézze meg, majd válaszoljon a kérdésekre.")
    st.write("⚠️ A döntése során **ne vegye figyelembe az árat** – ezt külön is ellenőrizzük.")

    if st.button("Tovább →"):
        st.session_state.page = 2
        st.rerun()

elif page == 2:
    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Ajánlat 1/3")
    st.subheader("Prága – Kulturális élmény")

    if st.session_state.group == "text":
        st.markdown(TEXT_OFFERS["Prága"])
    else:
        st.image(IMAGES["Prága"], caption=CAPTIONS["Prága"])

    nav(prev=1, next=3)


elif page == 3:
    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Ajánlat 2/3")
    st.subheader("Barcelona – Mediterrán élmény")

    if st.session_state.group == "text":
        st.markdown(TEXT_OFFERS["Barcelona"])
    else:
        st.image(IMAGES["Barcelona"], caption=CAPTIONS["Barcelona"], use_container_width=True)

    nav(prev=2, next=4)


elif page == 4:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Ajánlat 3/3")
    st.subheader("Róma – Történelmi élmény")

    if st.session_state.group == "text":
        st.markdown(TEXT_OFFERS["Róma"])
    else:
        st.image(IMAGES["Róma"], caption=CAPTIONS["Róma"], use_container_width=True)

    nav(prev=3, next=5)


# ===== 5. oldal: Döntés =====
elif page == 5:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("2. Döntés")

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    decision_choice = st.radio(
        "Melyik ajánlatot fogadná el?",
        ["Prága", "Barcelona", "Róma", "Egyiket sem"],
        index=None,
        key="decision_choice"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    decision_count = st.radio(
        "Összesen hány ajánlatot tartott elfogadhatónak?",
        [0, 1, 2, 3],
        index=None,
        key="decision_count"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    action = nav(prev=4, next=6, require_key=["decision_choice", "decision_count"])

    
    if action:
        errs = []
        if decision_choice is None:
            errs.append("Válassza ki, melyik ajánlatot fogadná el.")
        if decision_count is None:
            errs.append("Adja meg, hány ajánlatot tartott elfogadhatónak.")
        if decision_choice not in (None, "Egyiket sem") and decision_count == 0:
            errs.append("A választott ajánlatnak szerepelnie kell az elfogadhatók között.")
        if decision_choice == "Egyiket sem" and decision_count != 0:
            errs.append("Ha „Egyiket sem”-et választ, az elfogadhatók száma 0 kell legyen.")

        if len(errs) > 0:
            st.error(" • ".join(errs))
        else:
            st.session_state.answers["decision_choice"] = decision_choice
            st.session_state.answers["decision_count"] = decision_count
            st.session_state.page += 1
            st.rerun()

# ===== 6. oldal: Befolyásoló tényezők =====
elif page == 6:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Mi befolyásolta a döntését?")
    st.write("Az alábbi kérdések arra vonatkoznak, hogyan élte meg a döntés meghozatalát, "
             "és hogyan viszonyul az utólagos következményekhez. "
             "Kérjük, értékelje az állításokat az adott skálán!")

    st.caption("Kérjük, értékelje az alábbi állításokat egy 1-től 10-ig terjedő skálán, "
               "ahol az 1 = egyáltalán nem értek egyet, a 10 = teljes mértékben egyetértek.")

    factors_ans = {}
    for i, q in enumerate(DECISION_FACTORS):
     factors_ans[q] = st.slider(
        q,
        min_value=1,
        max_value=10,
        value=5,   # alapérték, mindig van (itt nincs None lehetőség)
        step=1,
        key=f"factor_{i}"
        
        )

    st.session_state.answers["factors"] = factors_ans
      
    nav(prev=5, next=7, require_key="factors")


# ===== 7. oldal: Döntési élmény =====
elif page == 7:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Döntési élmény")
    st.caption("Kérjük, értékelje az alábbi állításokat egy 1-től 10-ig terjedő skálán, "
               "ahol az 1 = egyáltalán nem értek egyet, a 10 = teljes mértékben egyetértek.")

    experience_qs = [
        "Biztos voltam abban, hogy jó döntést hoztam.",
        "Megkönnyebbülést éreztem a választás után.",
        "Nyugodtnak éreztem magam a döntés közben.",
        "Úgy éreztem, hogy a döntés az én kezemben van."
    ]

    exp_ans = {}
    for i, q in enumerate(experience_qs):
        exp_ans[q] = st.radio(
            q,
            list(range(1, 11)),
            horizontal=True,
            key=f"exp_{i}",
            index=None
        )
    st.session_state.answers["exp_ans.items"] = exp_ans

   # --- ÉRVÉNYESSÉG ELLENŐRZÉS + NAV ---
    all_valid = True
    for q, val in exp_ans.items():
        if val is None:
            all_valid = False

    nav(prev=6, next=8, require_key="experience")



# 8. oldal – 4.1 Élménykérdések
elif page == 8:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Élményre vonatkozó kérdések")
    st.write("Az alábbi kérdések arra vonatkoznak, milyen élmény volt a döntési folyamat számára. ")
    st.caption("Kérjük, értékelje az alábbi állításokat egy 1-től 10-ig terjedő skálán, ahol az 1 = egyáltalán nem értek egyet, a 10 = teljes mértékben egyetértek.")

    # ⬅️ EZ HIÁNYZOTT
    confirmation_qs = [
        "A döntés után is gondolkodtam, vajon helyesen választottam-e.",
        "Szerettem volna, ha valaki megerősíti, hogy jól döntöttem.",
        "Úgy éreztem, szívesen megosztanám másokkal a választásomat.",
    ]

    confirmation_ans = {}
    for i, q in enumerate(confirmation_qs):
        confirmation_ans[q] = st.radio(
            q,
            list(range(1, 11)),
            horizontal=True,
            index=None,
            key=f"conf7_{i}"   # ← egyedi kulcs (ne ütközzön a 8. oldallal!)
        )

    st.session_state.answers["confirmation"] = confirmation_ans

    # --- ÉRVÉNYESSÉG ELLENŐRZÉS + NAV ---
    all_valid = True
    for q, val in confirmation_ans.items():
        if val is None:
            all_valid = False

    nav(prev=7, next=9, require_key="confirmation")






elif page == 9:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Megerősítéskeresés")
    st.write("Az alábbi kérdések arra vonatkoznak, mennyire igényel megerősítést a döntései után. ")
    st.caption("Kérjük, értékelje az alábbi állításokat egy 1-től 10-ig terjedő skálán, ahol az 1 = egyáltalán nem értek egyet, a 10 = teljes mértékben egyetértek.")

    confirmation_qs = [
        "Vásárlás után kérem mások véleményét, hogy jól döntöttem-e.",
        "Fontos számomra, hogy a környezetem jóváhagyja a vásárlási döntéseimet.",
        "Bizonytalan helyzetben inkább megvárom, mit mondanak mások a termékről.",
        "Gyakran hasonlítom össze a választásomat az ismerőseim döntéseivel.",
    ]

    confirmation_ans = {}
    for i, q in enumerate(confirmation_qs):
        confirmation_ans[q] = st.radio(
            q,
            list(range(1, 11)),
            horizontal=True,
            index=None,
            key=f"conf8_{i}"   # ← egyedi kulcs (ne ütközzön a 7. oldallal!)
        )

    st.session_state.answers["confirmation_page8"] = confirmation_ans

   # --- ÉRVÉNYESSÉG ELLENŐRZÉS + NAV ---
    all_valid = True
    for q, val in confirmation_ans.items():
        if val is None:
            all_valid = False

    nav(prev=8, next=10, require_key="confirmation_page8")




# 9. oldal – 4.2 Felelősségérzet
elif page == 10:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Felelősségérzet")
    st.write("Az alábbi kérdések arra vonatkoznak, mennyire érzi magát felelősének a döntései után. ")
    st.caption("Kérjük, értékelje az alábbi állításokat egy 1-től 10-ig terjedő skálán, ahol az 1 = egyáltalán nem értek egyet, a 10 = teljes mértékben egyetértek.")

    confirmation_qs = [
        "Ha egy termék nem válik be, magamat hibáztatom a rossz döntésért.",
        "Vásárláskor gyakran inkább mások vagy egy rendszer javaslataira támaszkodom, nem a saját megérzésemre. (fordított tétel)",
        "Az elégedettségem vagy csalódásom a vásárlásaimnál az én döntésem következménye.",
        
    ]

    confirmation_ans = {}
    for i, q in enumerate(confirmation_qs):
        confirmation_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"conf_{i}", index=None)
    st.session_state.answers["confirmation"] = confirmation_ans

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

# minden rádió ki van töltve?
    for q, val in st.session_state.get("confirmation", {}).items():
     if val is None:
        all_valid = False

    nav(prev=9, next=11, require_key="confirmation")

    

# 10. oldal – 4.3 Hogyan hatott Önre az MI-ajánlás?
if page == 11:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Hogyan hatott Önre az MI-ajánlás a döntése során?")

    ai_influence = st.radio(
        "Kérjük, válassza ki az Önre leginkább jellemző állítást:",
        [
            "Egyáltalán nem vettem figyelembe az ajánlást",
            "Az ajánlás egybeesett azzal, amit magamtól is választottam volna",
            "Az ajánlás új szempontot adott, amit figyelembe vettem",
            "Az ajánlás teljesen megváltoztatta a döntésemet"
        ],
        index=None,
        key="ai_influence"
    )

    st.session_state.answers["ai_influence"] = ai_influence

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

    if st.session_state.get("ai_influence") is None:  # nincs választás
      all_valid = False

    nav(prev=10, next=12, require_key="ai_influence")





# 11. Manipuláció-ellenőrzés + figyelmi próba
elif page == 12:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Ellenőrző kérdések")
    st.caption("Az alábbi kérdések arra szolgálnak, hogy ellenőrizzük a figyelmet és a válaszok következetességét.")


    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.subheader("Manipuláció-ellenőrzés")
    mc = {}
    for i, q in enumerate(MANIP_CHECK):
        mc[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"mc_{i}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.subheader("Figyelmi próba")
    attn = st.radio("Válassza a **harmadik** opciót!", ["Első", "Második", "Harmadik", "Negyedik"],
                    index=None, key="attention_check")
    st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.answers["manip_check"] = mc
    st.session_state.answers["attention"] = attn

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

    if st.session_state.get("attention") is None:
        all_valid = False

    nav(prev=11, next=13, require_key="attention")





# 12. oldal – 4.4 Alternatívák mérlegelése
elif page == 13:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Alternatívák mérlegelése")
    st.write("Az alábbi kérdések arra vonatkoznak, mennyire mérlegeli a különböző lehetőségeket döntés előtt.")
    st.caption("Kérjük, értékelje az alábbi állításokat egy 1-től 10-ig terjedő skálán, ahol az 1 = egyáltalán nem értek egyet, a 10 = teljes mértékben egyetértek.")

    maximization_qs = [
        "Vásárlás előtt több különböző terméket is össze szoktam hasonlítani.",
        "Fontos számomra, hogy minden lehetséges alternatívát megvizsgáljak.",
        "Sok időt töltök azzal, hogy más opciókat is mérlegeljek.",
        "Gyakran átnézek több weboldalt vagy boltot, mielőtt döntök.",
        "Általában nem elégszem meg az első javasolt lehetőséggel. (fordított tétel)"
    ]

    maximization_ans = {}
    for i, q in enumerate(maximization_qs):
        maximization_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"max_{i}", index=None)
    st.session_state.answers["maximization"] = maximization_ans

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True


    for q, val in st.session_state.get("maximization", {}).items() : 
     if val is None:
           all_valid = False

    nav(prev=12, next=14, require_key="maximization")

   


# 13. oldal – 4.5 Nyitott kérdés
elif page == 14:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Nyitott kérdés")
    st.write("Kérem, írja le röviden, mi volt az a legfontosabb szempont, ami alapján végül az adott ajánlatot választotta.")

    # 🔹 ez a mező mindig megjelenik
    choice_reason = st.text_area("Válasza:", key="choice_reason")

    # 🔹 mentés az answers-be
    st.session_state.answers["choice_reason"] = choice_reason

    
    
  # --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

    if st.session_state.get("choice_reason") is None:
        all_valid = False

    nav(prev=13, next=15, require_key="choice_reason")


# 14. oldal – 5. Vásárlási gyakoriság
elif page == 15:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Vásárlási gyakoriság")
    st.caption("Kérem, jelölje, milyen gyakran vásárol az alábbi módokon.")

    freq_opts = ["Soha", "Ritkán (évente 1–2 alkalom)", "Havonta", "Hetente", "Hetente többször"]

    freq = {}
    freq["Milyen gyakran vásárol online (pl. webshopban, alkalmazáson keresztül)?"] = st.radio(
        "Milyen gyakran vásárol online (pl. webshopban, alkalmazáson keresztül)?",
        freq_opts, index=None, key="freq_online"
    )
    freq["Milyen gyakran vásárol személyesen (pl. boltban, üzletben)?"] = st.radio(
        "Milyen gyakran vásárol személyesen (pl. boltban, üzletben)?",
        freq_opts, index=None, key="freq_offline"
    )
    freq["Milyen gyakran használ mesterséges intelligencia eszközt (pl. chatbotot, ajánlórendszert) vásárlásai során?"] = st.radio(
        "Milyen gyakran használ mesterséges intelligencia eszközt (pl. chatbotot, ajánlórendszert) vásárlásai során?",
        freq_opts, index=None, key="freq_ai"
    )

    st.session_state.answers["frequency"] = freq

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

    for q, val in st.session_state.get("frequency", {}).items():
    
        all_valid = False

    nav(prev=14, next=16, require_key="frequency")

   


# 15. oldal – AIAS-4 skála
elif page == 16:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("AIAS-4 skála")
    st.write("Az alábbi kérdések azt vizsgálják, hogyan látja a mesterséges intelligencia jövőbeli hatásait.")
    st.caption("Kérjük, értékelje az alábbi állításokat egy 1-től 10-ig terjedő skálán, ahol az 1 = egyáltalán nem értek egyet, a 10 = teljes mértékben egyetértek")
    aias_qs = [
        "Úgy gondolom, hogy a mesterséges intelligencia javítani fogja az életemet.",
        "Úgy gondolom, hogy a mesterséges intelligencia javítani fogja a munkámat.",
        "Úgy gondolom, hogy a jövőben használni fogok mesterséges intelligencia alapú technológiát.",
        "Úgy gondolom, hogy a mesterséges intelligencia összességében pozitív az emberiség számára."
    ]

    aias_ans = {}
    for i, q in enumerate(aias_qs):
        aias_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"aias_{i}", index=None)

    st.session_state.answers["aias"] = aias_ans

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

    for q, val in st.session_state.get("aias", {}).items():
     
        all_valid = False

    nav(prev=15, next=17, require_key="aias")

  


# 16. oldal – Mesterséges intelligencia használata
elif page == 17:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Mesterséges intelligencia használata")

    ai_use = st.radio(
        "Használja Ön a mindennapokban mesterséges intelligencia alapú eszközöket (pl. ChatGPT, ajánlórendszerek, chatbotok)?",
        ["Igen", "Nem"],
        index=None,
        key="ai_use"
    )

    ai_freq = st.radio(
        "Milyen gyakran használ mesterséges intelligenciát?",
        ["Soha", "Ritkán", "Havonta", "Hetente", "Hetente többször"],
        index=None,
        key="ai_freq"
    )

    st.session_state.answers["ai_use"] = ai_use
    st.session_state.answers["ai_freq"] = ai_freq

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

    if st.session_state.get("ai_use") is None:
       all_valid = False
       if st.session_state.get("ai_freq") is None:
        all_valid = False

    nav(prev=16, next=18, require_key="ai_use")

    




# 17. oldal – Demográfiai kérdések
elif page == 18:
    # belépési idő rögzítése
    if f"page_{page}_entered" not in st.session_state.timestamps:
        st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

    progress_bar(page, TOTAL_PAGES)
    st.caption(f"Oldal {page+1} / {TOTAL_PAGES}")
    st.header("Demográfiai kérdések")

    demo = {}
    demo["Neme"] = st.radio(
        "Kérjük, jelölje a nemét:",
        ["Férfi", "Nő", "Egyéb / nem szeretném megadni"],
        index=None, key="demo_gender"
    )
    demo["Életkora"] = st.radio(
        "Kérjük, adja meg az életkorát:",
        ["18–24 év", "25–34 év", "35–44 év", "45–54 év", "55 év vagy idősebb"],
        index=None, key="demo_age"
    )
    demo["Legmagasabb iskolai végzettsége"] = st.radio(
        "Kérjük, adja meg a legmagasabb iskolai végzettségét:",
        ["Középiskola", "Felsőfokú tanulmányok folyamatban", "Egyetemi / főiskolai diploma", "Posztgraduális végzettség"],
        index=None, key="demo_edu"
    )
    demo["Foglalkozása / státusza"] = st.radio(
        "Kérjük, jelölje a foglalkozását / státuszát:",
        ["Tanuló / hallgató", "Dolgozó alkalmazottként", "Vállalkozó", "Munkanélküli", "Egyéb"],
        index=None, key="demo_job"
    )
    demo["Lakóhely típusa"] = st.radio(
        "Kérjük, jelölje a lakóhelyének típusát:",
        ["Főváros", "Megyeszékhely", "Egyéb város", "Község"],
        index=None, key="demo_residence"
    )

    st.session_state.answers["demographics"] = demo

# --- ÉRVÉNYESSÉG ELLENŐRZÉS ---
    all_valid = True

    for q, val in st.session_state.get("demographics", {}).items():
     if val is None:
        all_valid = False

    nav(prev=17, next=19, require_key="demographics")
  



elif page == TOTAL_PAGES:
    st.success("Köszönjük a kitöltést! ✅")
    st.write("Köszönöm, hogy időt szánt a kérdőív kitöltésére.")
    st.write("Ha teheti, kérem ossza meg a kérdőívet másokkal is. 🙏")

    record = {
        "rid": st.session_state.rid,
        "entered_at": st.session_state.entered_at,
        "submitted_at": datetime.now().astimezone().isoformat(),
        "group": st.session_state.group,
    }

    # --- válaszok külön oszlopokra ---
    for q, ans in st.session_state.answers.items():
        if isinstance(ans, dict):
            for subq, subv in ans.items():
                record[f"{q}_{subq}"] = subv
        else:
            record[q] = ans

    # --- oldalak ideje ---
    durations = calc_durations(st.session_state.timestamps)

    record["duration_page_1"] = round(durations.get(1, 0), 2)
    record["duration_page_2"] = round(durations.get(2, 0), 2)
    record["duration_page_3"] = round(durations.get(3, 0), 2)
    record["duration_page_4"] = round(durations.get(4, 0), 2)
    record["duration_page_5"] = round(durations.get(5, 0), 2)
    record["duration_page_6"] = round(durations.get(6, 0), 2)
    record["duration_page_7"] = round(durations.get(7, 0), 2)
    record["duration_page_8"] = round(durations.get(8, 0), 2)
    record["duration_page_9"] = round(durations.get(9, 0), 2)
    record["duration_page_10"] = round(durations.get(10, 0), 2)
    record["duration_page_11"] = round(durations.get(11, 0), 2)
    record["duration_page_12"] = round(durations.get(12, 0), 2)
    record["duration_page_13"] = round(durations.get(13, 0), 2)
    record["duration_page_14"] = round(durations.get(14, 0), 2)
    record["duration_page_15"] = round(durations.get(15, 0), 2)
    record["duration_page_16"] = round(durations.get(16, 0), 2)
    record["duration_page_17"] = round(durations.get(17, 0), 2)
    record["duration_page_18"] = round(durations.get(18, 0), 2)
    record["duration_page_19"] = round(durations.get(19, 0), 2)



    # --- MINDEN oldal időmérése ---
    durations = calc_durations(st.session_state.timestamps)
    for p, secs in durations.items():
        record[f"duration_page_{p}"] = round(secs, 2)

    # --- mentés ---
    save_row(record)

    st.stop()





    st.markdown("""
<style>

/* Input mezők doboz nélkül */
.stRadio > div,
.stTextInput > div,
.stTextArea > div,
.stSelectbox > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > textarea,
div[data-baseweb="select"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #ffffff !important;
}

/* Radio címkék */
.stRadio label {
    color: #ffffff !important;
}

.stButton>button:hover {
    background-color: #ff2a2a !important;
}

/* --- Mobil optimalizálás: valóban arányosított skála --- */
@media (max-width: 768px) {

    /* Szövegek kisebb, arányos méretben */
    p, .stMarkdown, .stText, .stHeader, .stSubheader {
        font-size: 14px !important;
        line-height: 1.35em !important;
    }

    /* Rádiógombok egy sorban, sűrítve */
    .stRadio > div {
        flex-wrap: nowrap !important;
        justify-content: space-evenly !important;
        align-items: center !important;
        gap: 1px !important;
    }

    /* Számok kisebbek, de olvashatók */
    .stRadio label {
        font-size: 14px !important;
        padding: 1px !important;
        margin-right: 1px !important;
        transform: scale(0.9);
    }

    /* Rádiók ténylegesen kisebb méretben */
    input[type="radio"] {
        width: 15px !important;
        height: 15px !important;
        transform: scale(0.85);
    }

    /* Gombok kicsit karcsúsítva, hogy ne tolják szét az oldalt */
    .stButton>button {
        min-width: 48%;
        font-size: 14px !important;
        padding: 6px 0 !important;
    }

    /* Oldalmargók mobilon sűrítve */
    .block-container {
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
    }
}


</style>
""", unsafe_allow_html=True)
