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

# ---------- ALAP ----------
st.set_page_config(page_title="🧭 MI-ajánlások – kérdőív", page_icon="📝", layout="centered")
DATA_PATH = Path("responses.csv")

def save_row(row: dict):
    """Append: egy sor mentése CSV-be; beágyazott dict/list JSON-ként."""
    flat = {}
    for k, v in row.items():
        if isinstance(v, (dict, list)):
            flat[k] = json.dumps(v, ensure_ascii=False)
        else:
            flat[k] = v
    df_new = pd.DataFrame([flat])
    if DATA_PATH.exists():
        df_old = pd.read_csv(DATA_PATH)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")

def progress_bar(current_page, total_pages):
    st.progress(current_page / total_pages)

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

# minden oldal betöltésekor logoljuk a belépést
st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()

# ---------- NAV FUNKCIÓ (felülírás) ----------




TOTAL_PAGES = 16  # 0..15

# ---------- ANYAGOK (ajánlatok + skálák) ----------
TEXT_OFFERS = {
    "Prága": """**Prága – Kulturális élmény**  
Egy 4 napos prágai utazást ajánlok Önnek, amely 3 éjszaka szállást tartalmaz egy belvárosi hotelben, reggelivel.  
Az út során idegenvezető kíséretében fedezheti fel a Károly hidat, az Óváros teret és a prágai vár történelmi utcáit.  
**Az ajánlat ára: 129 900 Ft/fő.**""",
    "Barcelona": """**Barcelona – Mediterrán élmény**  
Ajánlok Önnek egy 4 napos barcelonai városlátogatást, amely 3 éjszakás szállást biztosít egy tengerpart közeli, 4 csillagos hotelben, reggelivel.  
Az utazás során megcsodálhatja Gaudí ikonikus alkotásait, köztük a Sagrada Famíliát és a Güell parkot, valamint átélheti a mediterrán város vibráló hangulatát.  
**Az ajánlat ára: 159 900 Ft/fő.**""",
    "Róma": """**Róma – Történelmi élmény**  
Szívesen ajánlok Önnek egy 4 napos római kirándulást, amely 3 éjszakás szállást tartalmaz egy központi elhelyezkedésű hotelben, reggelivel.  
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

# ---------- STÍLUS ----------
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 18px; }
.q-card { padding:20px 22px; margin:14px 0 18px 0; border:1px solid #e6e6e6; border-radius:14px; background:#fafafa; }
.q-title { font-weight:600; font-size:18px; margin-bottom:10px; }
.q-help { color:#666; font-size:16px; margin:-6px 0 6px 0; }
.stButton>button { font-size:18px; padding:10px 22px; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

# ---------- NAV FUNKCIÓ (javított) ----------
def nav(prev=None, next=None, submit=False):
    c1, c2 = st.columns([1,1])
    with c1:
        if prev is not None and st.button("← Vissza", key=f"prev_{st.session_state.page}"):
            st.session_state.page = prev
            st.rerun()
    with c2:
        if submit:
            if st.button("Tovább →", key=f"submit_{st.session_state.page}"):
                return "submit"
        else:
            if next is not None and st.button("Tovább →", key=f"next_{st.session_state.page}"):
                st.session_state.page = next
                st.rerun()
    return None


# ========== OLDALAK ==========

page = st.session_state.page

page = st.session_state.page

# ========= OLDALAK =========
page = st.session_state.page

# ---- ide jön az óra ----
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Frissítés 1 másodpercenként
st_autorefresh(interval=1000, key="clock_refresh")

# Jelenlegi idő
now = datetime.now().strftime("%H:%M:%S")

# Jobb felső sarokba
col1, col2 = st.columns([9,1])
with col2:
    st.caption(f"🕒 {now}")
# -------------------------



from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# frissítés 1 másodpercenként
st_autorefresh(interval=1000, key="time_refresh")

# oldal belépés ideje logolva
if f"page_{page}_entered" not in st.session_state.timestamps:
    st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()



# oldal belépés ideje logolva
st.session_state.timestamps[f"page_{page}_entered"] = datetime.utcnow().isoformat()



# 0. Beleegyezés + instrukciók
if page == 0:
    st.title("🧭 MI-ajánlások – kérdőív")
    progress_bar(0, TOTAL_PAGES)
    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.markdown("**Beleegyezés**")
    consent = st.radio(
        "Hozzájárulok a névtelen válaszaim kutatási célú felhasználásához.",
        ["Igen", "Nem"], index=None, key="consent")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.markdown("**Instrukciók**")
    st.write("A következő oldalakon MI által javasolt utazási ajánlatokat lát. "
             "Kérjük, olvassa el / nézze meg, majd válaszoljon a kérdésekre.")
    st.write("⚠️ A döntése során **ne vegye figyelembe az árat** – ezt külön is ellenőrizzük.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Kezdés ➜"):
        if consent != "Igen":
            st.error("A kérdőív folytatásához szükség van a beleegyezésre.")
        else:
            st.session_state.page = 1
            st.rerun()

# ===== Ajánlat oldalak (1-3) =====
elif page == 1:
    progress_bar(page, TOTAL_PAGES)
    st.header("Ajánlat 1/3 – Prága")

    if st.session_state.group == "text":
        st.markdown(TEXT_OFFERS["Prága"])
    else:
        st.image(IMAGES["Prága"], caption=CAPTIONS["Prága"], use_container_width=True)

    nav(prev=0, next=2)



elif page == 2:
    progress_bar(page, TOTAL_PAGES)
    st.header("Ajánlat 2/3 – Barcelona")

    if st.session_state.group == "text":
        st.markdown(TEXT_OFFERS["Barcelona"])
    else:
        st.image(IMAGES["Barcelona"], caption=CAPTIONS["Barcelona"], use_container_width=True)

    nav(prev=1, next=3)


elif page == 3:
    progress_bar(page, TOTAL_PAGES)
    st.header("Ajánlat 3/3 – Róma")

    if st.session_state.group == "text":
        st.markdown(TEXT_OFFERS["Róma"])
    else:
        st.image(IMAGES["Róma"], caption=CAPTIONS["Róma"], use_container_width=True)

    nav(prev=2, next=4)


# ===== 4. oldal: Döntés =====
elif page == 4:
    progress_bar(page, TOTAL_PAGES)
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

    action = nav(prev=3, next=5, submit=True)
    if action == "submit":
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

# ===== 5. oldal: Befolyásoló tényezők =====
elif page == 5:
    progress_bar(page, TOTAL_PAGES)
    st.header("Mi befolyásolta a döntését?")
    st.caption("(1 = egyáltalán nem, 10 = nagyon erősen)")

    factors = {}
    for i, f in enumerate(DECISION_FACTORS):
        factors[f] = st.slider(
            f,
            min_value=1,
            max_value=10,
            value=5,
            step=1,
            key=f"factor_{i}"
        )

    # itt azonnal elmentjük a factors értékeit
    st.session_state.answers["factors"] = factors

    progress_bar(page, TOTAL_PAGES)
    st.header("3. Döntési élmény")
    st.write("Az alábbi kérdések arra vonatkoznak, hogyan élte meg a döntés meghozatalát. "
             "Kérjük, értékelje az állításokat 1–10-es skálán (rádiógombok).")

    experience_qs = [
        "Biztos voltam abban, hogy jó döntést hoztam.",
        "Megkönnyebbülést éreztem a választás után.",
        "Nyugodtnak éreztem magam a döntés közben.",
        "Úgy éreztem, hogy a döntés az én kezemben van."
    ]

    exp_ans = {}
    for i, q in enumerate(experience_qs):
        exp_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"exp_{i}")
    st.session_state.answers["experience"] = exp_ans

    # csak egyszer hívjuk meg a nav-ot
    nav(prev=4, next=6)

# 6. oldal – 4.1 Megerősítéskeresés
elif page == 6:
    progress_bar(page, TOTAL_PAGES)
    st.header("4.1 Megerősítéskeresés")
    st.write("Kérjük, értékelje az alábbi állításokat 1–10-es skálán (rádiógombok).")

    confirmation_qs = [
        "Vásárlás után kérem mások véleményét, hogy jól döntöttem-e.",
        "Fontos számomra, hogy a környezetem jóváhagyja a vásárlási döntéseimet.",
        "Bizonytalan helyzetben inkább megvárom, mit mondanak mások a termékről.",
        "Gyakran hasonlítom össze a választásomat az ismerőseim döntéseivel."
    ]

    confirmation_ans = {}
    for i, q in enumerate(confirmation_qs):
        confirmation_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"conf_{i}")
    st.session_state.answers["confirmation"] = confirmation_ans
    nav(prev=5, next=7)


# 7. MI-bizalom + reklámfelismerés (MIND 1–10)
elif page == 6:
    progress_bar(page, TOTAL_PAGES)
    st.header("MI-bizalom és reklámfelismerés")

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.subheader("MI-bizalom (1–10)")
    ai = {}
    for i, q in enumerate(AI_TRUST):
        ai[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"ai_{i}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.subheader("Reklámfelismerés (1–10)")
    pk = {}
    for i, q in enumerate(PERSUASION_KNOWLEDGE):
        pk[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"pk_{i}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.answers["ai_trust"] = ai
    st.session_state.answers["persuasion"] = pk
    nav(prev=6, next=8)

# 8. Manipuláció-ellenőrzés + figyelmi próba
elif page == 7:
    progress_bar(page, TOTAL_PAGES)
    st.header("Ellenőrző kérdések")

    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.subheader("Manipuláció-ellenőrzés (1–10)")
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
    nav(prev=7, next=9)
# 8. oldal – 4.3 Hogyan hatott Önre az MI-ajánlás?
elif page == 8:
    progress_bar(page, TOTAL_PAGES)
    st.header("4.3 Hogyan hatott Önre az MI-ajánlás a döntése során?")

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
    nav(prev=7, next=9)

# 9. oldal – 4.2 Felelősségérzet
elif page == 7:
    progress_bar(page, TOTAL_PAGES)
    st.header("4.2 Felelősségérzet")
    st.write("Kérjük, értékelje az alábbi állításokat 1–10-es skálán (rádiógombok).")

    responsibility_qs = [
        "Ha egy termék nem válik be, magamat hibáztatom a rossz döntésért.",
        "Vásárláskor gyakran inkább mások vagy egy rendszer javaslataira támaszkodom, nem a saját megérzésemre. (fordított tétel)",
        "Az elégedettségem vagy csalódásom a vásárlásaimnál az én döntésem következménye."
    ]

    responsibility_ans = {}
    for i, q in enumerate(responsibility_qs):
        responsibility_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"resp_{i}")
    st.session_state.answers["responsibility"] = responsibility_ans
    nav(prev=7, next=10)
# 9. oldal – 4.4 Alternatívák mérlegelése
elif page == 9:
    progress_bar(page, TOTAL_PAGES)
    st.header("4.4 Alternatívák mérlegelése")
    st.write("Kérjük, értékelje az alábbi állításokat 1–10-es skálán (rádiógombok).")

    maximization_qs = [
        "Vásárlás előtt több különböző terméket is össze szoktam hasonlítani.",
        "Fontos számomra, hogy minden lehetséges alternatívát megvizsgáljak.",
        "Sok időt töltök azzal, hogy más opciókat is mérlegeljek.",
        "Gyakran átnézek több weboldalt vagy boltot, mielőtt döntök.",
        "Általában nem elégszem meg az első javasolt lehetőséggel. (fordított tétel)"
    ]

    maximization_ans = {}
    for i, q in enumerate(maximization_qs):
        maximization_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"max_{i}")
    st.session_state.answers["maximization"] = maximization_ans
    nav(prev=8, next=10)
# 10. oldal – 4.5 Nyitott kérdés
elif page == 10:
    progress_bar(page, TOTAL_PAGES)
    st.header("4.5 Nyitott kérdés")
    st.write("Kérem, írja le röviden, mi volt az a legfontosabb szempont, ami alapján végül az adott ajánlatot választotta.")

    choice_reason = st.text_area("Válasza:", key="choice_reason")

    st.session_state.answers["choice_reason"] = choice_reason
    nav(prev=9, next=11)
# 11. oldal – 5. Vásárlási gyakoriság
elif page == 11:
    progress_bar(page, TOTAL_PAGES)
    st.header("5. Vásárlási gyakoriság")
    st.caption("(Kérem, jelölje, milyen gyakran vásárol az alábbi módokon.)")

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
    nav(prev=10, next=12)
# 12. oldal – AIAS-4 skála
elif page == 12:
    progress_bar(page, TOTAL_PAGES)
    st.header("6. AIAS-4 skála")
    st.write("(1 = Egyáltalán nem értek egyet … 10 = Teljes mértékben egyetértek)")

    aias_qs = [
        "Úgy gondolom, hogy a mesterséges intelligencia javítani fogja az életemet.",
        "Úgy gondolom, hogy a mesterséges intelligencia javítani fogja a munkámat.",
        "Úgy gondolom, hogy a jövőben használni fogok mesterséges intelligencia alapú technológiát.",
        "Úgy gondolom, hogy a mesterséges intelligencia összességében pozitív az emberiség számára."
    ]

    aias_ans = {}
    for i, q in enumerate(aias_qs):
        aias_ans[q] = st.radio(q, list(range(1,11)), horizontal=True, key=f"aias_{i}")
    st.session_state.answers["aias"] = aias_ans
    nav(prev=11, next=13)
# 13. oldal – Mesterséges intelligencia használata
elif page == 13:
    progress_bar(page, TOTAL_PAGES)
    st.header("7. Mesterséges intelligencia használata")

    ai_use = st.radio(
        "7.1. Használja Ön a mindennapokban mesterséges intelligencia alapú eszközöket (pl. ChatGPT, ajánlórendszerek, chatbotok)?",
        ["Igen", "Nem"],
        index=None,
        key="ai_use"
    )

    ai_freq = st.radio(
        "7.2. Milyen gyakran használ mesterséges intelligenciát?",
        ["Soha", "Ritkán", "Havonta", "Hetente", "Hetente többször"],
        index=None,
        key="ai_freq"
    )

    st.session_state.answers["ai_use"] = ai_use
    st.session_state.answers["ai_freq"] = ai_freq
    nav(prev=12, next=14)


# 14. oldal – Demográfiai kérdések
elif page == 14:
    progress_bar(page, TOTAL_PAGES)
    st.header("8. Demográfiai kérdések")

    demo = {}
    demo["Neme"] = st.radio(
        "8.1 Kérjük, jelölje a nemét:",
        ["Férfi", "Nő", "Egyéb / nem szeretném megadni"],
        index=None, key="demo_gender"
    )
    demo["Életkora"] = st.radio(
        "8.2 Kérjük, adja meg az életkorát:",
        ["18–24 év", "25–34 év", "35–44 év", "45–54 év", "55 év vagy idősebb"],
        index=None, key="demo_age"
    )
    demo["Legmagasabb iskolai végzettsége"] = st.radio(
        "8.3 Kérjük, adja meg a legmagasabb iskolai végzettségét:",
        ["Középiskola", "Felsőfokú tanulmányok folyamatban", "Egyetemi / főiskolai diploma", "Posztgraduális végzettség"],
        index=None, key="demo_edu"
    )
    demo["Foglalkozása / státusza"] = st.radio(
        "8.4 Kérjük, jelölje a foglalkozását / státuszát:",
        ["Tanuló / hallgató", "Dolgozó alkalmazottként", "Vállalkozó", "Munkanélküli", "Egyéb"],
        index=None, key="demo_job"
    )
    demo["Lakóhely típusa"] = st.radio(
        "8.5 Kérjük, jelölje a lakóhelyének típusát:",
        ["Főváros", "Megyeszékhely", "Egyéb város", "Község"],
        index=None, key="demo_residence"
    )

    st.session_state.answers["demographics"] = demo
    nav(prev=13, next=15)


# 15. Köszönő + mentés
elif page == 15:
    progress_bar(page, TOTAL_PAGES)
    st.success("Köszönjük a kitöltést! ✅")

    record = {
        "rid": st.session_state.rid,
        "entered_at": st.session_state.entered_at,
        "submitted_at": datetime.utcnow().isoformat(),
        "group": st.session_state.group,
        "answers": st.session_state.answers,
        "timestamps": st.session_state.timestamps,  # <= ITT a helye
    }
    save_row(record)
from datetime import datetime

def calc_durations(timestamps: dict):
    durations = {}
    for key, value in timestamps.items():
        if key.endswith("_entered"):
            page = key.replace("_entered", "")
            entered = datetime.fromisoformat(value)
            left_key = f"{page}_left"
            if left_key in timestamps:
                left = datetime.fromisoformat(timestamps[left_key])
                durations[page] = (left - entered).total_seconds()
            else:
                durations[page] = None  # még nem lépett ki erről az oldalról
    return durations



    if st.button("Újrakezdés"):
        st.session_state.clear()
        st.rerun()
# ---------- STÍLUS FELÜLÍRÁS ----------
st.markdown("""
<style>
.q-card {
    padding:0;
    margin:0;
    border:none;
    border-radius:0;
    background:transparent;
}
</style>
""", unsafe_allow_html=True)
# ---------- CLEAN MODE (extra erős) ----------

HIDE_UI = """
<style>
/* Menü, footer, header */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}

/* Deploy, Fork, GitHub, Share, Crown badge */
.stDeployButton, .stAppDeployButton, .stShareButton {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
[data-testid="stSidebarCollapseButton"] {display: none !important;}
[data-testid="stHeaderActionButtons"] {display: none !important;}
[data-testid="stActionButton"] {display: none !important;}
button[kind="header"] {display: none !important;}

/* Accessibility / villogó ikonok */
[class*="accessibility"] {display: none !important;}
[class*="stAppFloatingActionButton"] {display: none !important;}
[title="Accessibility"] {display: none !important;}
[title="Open settings"] {display: none !important;}

/* Plusz margó fix */
.block-container {padding-top: 1rem;}
</style>
"""
import streamlit as st
st.markdown(HIDE_UI, unsafe_allow_html=True)


