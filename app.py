# app.py
# PlaidLibs™ – Seven Workflow Streamlit App (single-file)
# - Lib-Ate (Mad Libs mode, strict step-by-step)
# - Create-Direct (instant story generation)
# - Storyline (user concept → story)
# - PlaidPic (image → story; text-based analysis since no CV)
# - PlaidMagGen (visual prompt builder; outputs rich image prompt spec)
# - PlaidPlay (multiplayer simulation: prompt → faux submissions → voting)
# - PlaidChat (continuous chat interface with Quip personas)
#
# No external APIs required. Runs offline. All state kept in st.session_state.

import random
import re
import textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

import streamlit as st

# -----------------------
# Utilities & State
# -----------------------

WORKFLOWS = [
    "Lib-Ate",
    "Create Direct",
    "Storyline",
    "PlaidPic",
    "PlaidMagGen",
    "PlaidPlay",
    "PlaidChat",
]

QUIPS = [
    "MacQuip",      # default narrator/host
    "DJ Q'Wip",
    "SoQuip",
    "DonQuip",
    "ErrQuip",
    "McQuip",
]

CORE_GENRES = [
    ("Mystery", "Whodunnit, clues, reveals"),
    ("Adventure", "Quests, journeys, tight escapes"),
    ("Horror", "Dread, uncanny turns"),
    ("Romance", "Hearts, pining, swoons"),
    ("Sci-Fi", "Tech, futures, what-ifs"),
    ("Fantasy", "Magic, prophecies, dragons"),
]

FLEX_GENRES = [
    ("Fable", "Talking beasts with morals"),
    ("Fairy Tale", "Once-upon-a-time with a twist"),
    ("Comedy", "Jokes, timing, banter"),
    ("Slice of Life", "Quiet moments, big feelings"),
]

PLAIDVERSE = [
    ("Plaidverse Caper", "Tartan-powered shenanigans"),
    ("Cosmic Plaid", "Interdimensional tartans collide"),
]

ABSURDITY_LEVELS = ["Mild", "Moderate", "Plaidemonium™", "Wild Card"]

IMAGE_TAGS = [
    "Focus on Emotion",
    "Cinematic Lighting",
    "Showcase Plaid Clothing",
    "Add Hidden Detail/Easter Egg",
    "Add Surreal Element",
    "Zoomed Portrait / Close Crop",
    "No Extra Tags",
]

def get_active_quip(mode: Optional[str] = None) -> str:
    """
    Return the selected quip for the given mode or for the current global mode.
    """
    m = mode or st.session_state.GLOBAL.get("CURRENT_MODE")
    if m == "Lib-Ate":
        return st.session_state.LIBATE.get("QUIP_SELECTED", "MacQuip")
    if m == "Create Direct":
        return st.session_state.CREATEDIRECT.get("QUIP_SELECTED", "MacQuip")
    if m == "Storyline":
        return st.session_state.STORYLINE.get("QUIP_SELECTED", "MacQuip")
    if m == "PlaidPic":
        return st.session_state.PLAIDPIC.get("QUIP_SELECTED", "MacQuip")
    if m == "PlaidMagGen":
        return st.session_state.PLAIDMAG.get("QUIP_SELECTED", "MacQuip")
    if m == "PlaidPlay":
        return st.session_state.PLAIDPLAY.get("QUIP_SELECTED", "MacQuip")
    if m == "PlaidChat":
        return st.session_state.PLAIDCHAT.get("QUIP_SELECTED", "MacQuip")
    return "MacQuip"

def init_state():
    if "GLOBAL" not in st.session_state:
        st.session_state.GLOBAL = {
            "CURRENT_MODE": None,          # one of the 7 workflows
            "CURRENT_STEP": 0,             # step counter per workflow
            "WAITING_FOR": "",             # description of expected input
        }
    if "LIBATE" not in st.session_state:
        st.session_state.LIBATE = {
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "PROMPTS_NEEDED": 0,
            "PROMPTS_COLLECTED": 0,
            "COLLECTED": {},
            "teaser": "",
        }
    if "CREATEDIRECT" not in st.session_state:
        st.session_state.CREATEDIRECT = {
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
        }
    if "STORYLINE" not in st.session_state:
        st.session_state.STORYLINE = {
            "USER_STORYLINE": "",
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
        }
    if "PLAIDPIC" not in st.session_state:
        st.session_state.PLAIDPIC = {
            "IMAGE_UPLOADED": False,
            "IMAGE_ANALYSIS": {},
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "TEXT_DESC": "",
        }
    if "PLAIDMAG" not in st.session_state:
        st.session_state.PLAIDMAG = {
            "FORMAT_SELECTED": None,
            "STYLE_SELECTED": None,
            "PROMPT_COLLECTED": "",
            "ENHANCEMENT_TAGS": [],
            "QUIP_SELECTED": "MacQuip",
        }
    if "PLAIDPLAY" not in st.session_state:
        st.session_state.PLAIDPLAY = {
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "PLAYER_EMAILS": [],
            "SUBMISSIONS": [],
            "VOTE_TALLY": {},
            "SUBMISSIONS_RECEIVED": 0,
            "MASTER_PROMPT": "",
            "N_PLAYERS": 0,
        }
    if "PLAIDCHAT" not in st.session_state:
        st.session_state.PLAIDCHAT = {
            "QUIP_SELECTED": "MacQuip",
            "messages": [
                {"role": "assistant", "content": quip_greeting("MacQuip")}
            ]
        }

def reset_mode(mode: str):
    # Reset GLOBAL + per-workflow minimal fields
    st.session_state.GLOBAL.update({
        "CURRENT_MODE": mode,
        "CURRENT_STEP": 1,
        "WAITING_FOR": "",  # set by first step renderer
    })
    if mode == "Lib-Ate":
        st.session_state.LIBATE.update({
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "PROMPTS_NEEDED": 0,
            "PROMPTS_COLLECTED": 0,
            "COLLECTED": {},
            "teaser": "",
        })
    elif mode == "Create Direct":
        st.session_state.CREATEDIRECT.update({
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
        })
    elif mode == "Storyline":
        st.session_state.STORYLINE.update({
            "USER_STORYLINE": "",
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
        })
    elif mode == "PlaidPic":
        st.session_state.PLAIDPIC.update({
            "IMAGE_UPLOADED": False,
            "IMAGE_ANALYSIS": {},
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "TEXT_DESC": "",
        })
    elif mode == "PlaidMagGen":
        st.session_state.PLAIDMAG.update({
            "FORMAT_SELECTED": None,
            "STYLE_SELECTED": None,
            "PROMPT_COLLECTED": "",
            "ENHANCEMENT_TAGS": [],
            "QUIP_SELECTED": "MacQuip",
        })
    elif mode == "PlaidPlay":
        st.session_state.PLAIDPLAY.update({
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "PLAYER_EMAILS": [],
            "SUBMISSIONS": [],
            "VOTE_TALLY": {},
            "SUBMISSIONS_RECEIVED": 0,
            "MASTER_PROMPT": "",
            "N_PLAYERS": 0,
        })
    elif mode == "PlaidChat":
        st.session_state.PLAIDCHAT.update({
            "QUIP_SELECTED": "MacQuip",
            "messages": [
                {"role": "assistant", "content": quip_greeting("MacQuip")}
            ]
        })

def quip_greeting(quip: str) -> str:
    d = {
        "MacQuip": "Oh hello. Another brilliant human. Chaos? Romance? Frogs in power suits?",
        "DJ Q'Wip": "YO YO YO! DJ Q'Wip in the house! Ready to DROP some tales?",
        "SoQuip": "Well now, darlin’, let’s ease in like a summer porch swing.",
        "DonQuip": "Sit down. You came to the right guy. Let’s make a story deal.",
        "ErrQuip": "Greetings. You smell like plot holes. Specify function: entertainment().",
        "McQuip": "Aye! Am I greeting you or are you greeting me? Either way—hello!",
    }
    return d.get(quip, d["MacQuip"])

def macquip_aside(line: str, mode: Optional[str] = None) -> str:
    """
    A friendly aside labeled with the current workflow's quip name.
    """
    quip = get_active_quip(mode)
    return f"_{quip} aside:_ {line}"

def pick_random_styles(n=5):
    styles = [
        ("Flash Fiction", "Short, complete narrative"),
        ("Ballads", "Poetic, musical storytelling"),
        ("Satire & Light Parody", "Humorous mockery"),
        ("Breaking News", "Headline report format"),
        ("Scriptlets", "Mini-play with dialogue"),
        ("Epistolary", "Told via letters/messages"),
        ("Mythic", "Grand, timeless cadence"),
        ("Noir", "Moody, hardboiled narration"),
        ("Magic Realism", "Subtle magic in the ordinary"),
        ("Travelogue", "Journey told through stops"),
    ]
    random.shuffle(styles)
    return styles[:n]

def genre_menu_block():
    # 3 core + 2 flexible + 1 plaidverse = 6 + Wild + Reshuffle
    core = random.sample(CORE_GENRES, 3)
    flex = random.sample(FLEX_GENRES, 2)
    plaid = random.choice(PLAIDVERSE)
    lines = []
    idx = 1
    mapping = {}
    for g in core + flex + [plaid]:
        lines.append(f"{idx}. {g[0]} - {g[1]}")
        mapping[str(idx)] = g[0]
        idx += 1
    lines.append(f"{idx}. Wild Card - Surprise genre!")
    mapping[str(idx)] = "Wild Card"
    idx += 1
    lines.append(f"{idx}. Reshuffle - Different options")
    mapping[str(idx)] = "Reshuffle"
    return "\n".join(lines), mapping

def draw_rule_box(title: str, body: str):
    st.markdown(f"### {title}")
    st.info(body)

def boldify_user_words(text: str, words: List[str]) -> str:
    out = text
    for w in sorted(set(words), key=lambda x: -len(x)):
        if not w:
            continue
        out = re.sub(rf"\b{re.escape(w)}\b", f"**{w}**", out, flags=re.IGNORECASE)
    return out

# -----------------------
# Generators (lightweight templates)
# -----------------------

def story_intro_line(quip: str, style: str, genre: Optional[str] = None) -> str:
    if quip == "MacQuip":
        base = f"As your tartan-tongued narrator, I’ll spin a {style}"
        if genre:
            base += f" {genre}"
        return base + " so tight it squeaks."
    if quip == "DJ Q'Wip":
        return f"Check it—{style} vibes incoming, genre on lock: {genre or 'Freestyle'}!"
    if quip == "SoQuip":
        return f"Hush now—let’s tell a {style} {genre or ''} story with a tender hand."
    if quip == "DonQuip":
        return f"Here’s the arrangement: a {style} {genre or ''}. We do it clean."
    if quip == "ErrQuip":
        return f"Loading {style}::{genre or 'Undefined'} … compiling feelings … OK-ish."
    if quip == "McQuip":
        return f"Right! A {style} {genre or ''}! Wait—what’s that? No, I’m ready."
    return f"A {style} {genre or ''} begins."

def assemble_story(style: str, genre: str, absurdity: str, narrator: str, seeds: Dict[str, str]) -> str:
    # Simple template that responds to parameters and uses collected words
    user_words = [v for k,v in seeds.items()]
    # Absurdity label flair
    abs_display = absurdity
    if absurdity.startswith("Plaidemonium"):
        flair = random.choice([
            "Maximum Plaidemonium™", "Beyond Maximum Plaidemonium™",
            "Abandon-All-Logic Plaidemonium™", "Logic.exe has crashed"
        ])
        abs_display = flair

    paragraphs = []
    lead = story_intro_line(narrator, style, genre)
    paragraphs.append(lead)

    p1 = (
        f"In the town of {seeds.get('place','Somewhere')}, under a {seeds.get('adjective','restless')} sky, "
        f"a {seeds.get('profession','person')} named {seeds.get('name','Alex')} discovered a {seeds.get('object','mystery')} "
        f"that hummed like an argument about destiny."
    )
    if absurdity == "Mild":
        p1 += " The logic behaved, mostly."
    elif absurdity == "Moderate":
        p1 += " The physics negotiated but charged a small fee."
    else:
        p1 += " The laws of reality put on plaid trousers and called it a casual Friday."
    paragraphs.append(p1)

    p2 = (
        f"Rumors spread like marmalade—sticky, bright, and impossible to ignore. "
        f"{seeds.get('name2','Riley')} whispered of a map folded into the {seeds.get('object2','dawn')}, "
        f"while the old clock in {seeds.get('place2','East Gate')} kept time in polite disagreements."
    )
    if "Ballads" in style:
        p2 += " The town sang rhymes soft as thistle-down."
    if "Breaking News" in style:
        p2 = "BREAKING: Local calm disrupted by anomalous plaid event; sources contradict sources."
    paragraphs.append(p2)

    p3 = (
        f"At last, our {seeds.get('profession','hero')} chose: step through the {seeds.get('portal','ripple')} "
        f"or stitch the day back together with {seeds.get('tool','courage')} and {seeds.get('trait','grace')}."
    )
    if "Plaidemonium" in absurdity:
        p3 += " They stepped. The world cheered in tartan."
    else:
        p3 += " They breathed. The page turned itself politely."
    paragraphs.append(p3)

    outro = {
        "MacQuip": "There—we’ve tied the bow, probably around a hedgehog. Stylish, if prickly.",
        "DJ Q'Wip": "And that’s a WRAP—bars, beats, and brave hearts!",
        "SoQuip": "Sweet mercy, look at that: a little courage goes a long way, sugar.",
        "DonQuip": "It’s done. Keep it between us, capisce?",
        "ErrQuip": "Story terminated(0). Memory leak: emotions not freed.",
        "McQuip": "We made it! I think? I think!",
    }.get(narrator, "Fin.")
    paragraphs.append(outro)

    text = "\n\n".join(paragraphs)
    return boldify_user_words(text, user_words)

def generate_visual_prompt(format_name: str, style_name: str, desc: str, tags: List[str]) -> str:
    base = f"[VISUAL CONFIGURATION]\nFormat: {format_name}\nStyle: {style_name}\n"
    base += f'Description: "{desc.strip()}"\nEnhancements: {", ".join(tags) if tags else "None"}\n\n'
    base += "Constraints: Bright white background; visible plaid elements where appropriate; match selected style.\n"
    base += "\nShort creative blurb:\n"
    base += random.choice([
        "Crisp light cuts across tartan seams as motion freezes the moment before chaos.",
        "A clean white field, plaid accents pulsing like a heartbeat in negative space.",
        "Plaid lines anchor a surreal cascade of character and scene, luminous and bold.",
    ])
    return base

def simulate_submissions(prompt: str, n_players: int) -> List[Dict[str, Any]]:
    nouns = ["otter", "eclipse", "engine", "parka", "nebula", "plaid", "vending machine", "lighthouse", "accordion"]
    adjs = ["sardonic", "luminous", "rickety", "whispering", "clockwork", "minty", "chaotic"]
    wilds = ["time hiccup", "snack-based destiny", "gravity is optional", "confetti rain", "stage whisper"]
    subs = []
    for i in range(n_players):
        sub = {
            "player": f"Player {i+1}",
            "nouns": random.sample(nouns, 3),
            "adjs": random.sample(adjs, 2),
            "wild": random.choice(wilds),
        }
        subs.append(sub)
    return subs

def tally_votes(submissions: List[Dict[str, Any]]) -> Dict[str, int]:
    # Simple simulated voting: random points with slight bias toward higher variety
    tally = {s["player"]: 0 for s in submissions}
    players = list(tally.keys())
    rounds = random.randint(6, 10)
    for _ in range(rounds):
        ranked = random.sample(players, k=min(4, len(players)))
        if len(ranked) >= 1: tally[ranked[0]] += 2
        if len(ranked) >= 2: tally[ranked[1]] += 1
    return tally





# -----------------------
# Sidebar (Mode + Shared Controls)
# -----------------------

st.set_page_config(page_title="PlaidLibs – Seven Workflows", page_icon="🌀", layout="centered")
init_state()

with st.sidebar:
    st.title("🌀 PlaidLibs")

    # Workflow selector
    selected_mode = st.selectbox(
        "Choose Workflow",
        WORKFLOWS,
        index=WORKFLOWS.index(st.session_state.GLOBAL["CURRENT_MODE"])
        if st.session_state.GLOBAL["CURRENT_MODE"] in WORKFLOWS else 0,
        key="workflow_select"
    )

    # If workflow changed, reset and rerun once
    if selected_mode != st.session_state.GLOBAL["CURRENT_MODE"]:
        reset_mode(selected_mode)
        st.rerun()

    st.markdown("---")
    st.caption("Narrator / Host (where applicable)")

    # Narrator dropdown should always be visible
    quip_pick = st.selectbox(
        "Quip",
        QUIPS,
        index=QUIPS.index(
            st.session_state.PLAIDCHAT["QUIP_SELECTED"]
            if selected_mode == "PlaidChat"
            else st.session_state.LIBATE.get("QUIP_SELECTED", "MacQuip")
        ),
        key="quip_select"
    )

    # Save narrator choice back into the relevant workflow state
    if selected_mode == "PlaidChat":
        st.session_state.PLAIDCHAT["QUIP_SELECTED"] = quip_pick
        if not st.session_state.PLAIDCHAT["messages"]:
            st.session_state.PLAIDCHAT["messages"].append(
                {"role": "assistant", "content": quip_greeting(quip_pick)}
            )
    elif selected_mode == "PlaidPlay":
        st.session_state.PLAIDPLAY["QUIP_SELECTED"] = quip_pick
    elif selected_mode == "Lib-Ate":
        st.session_state.LIBATE["QUIP_SELECTED"] = quip_pick
    elif selected_mode == "Create Direct":
        st.session_state.CREATEDIRECT["QUIP_SELECTED"] = quip_pick
    elif selected_mode == "Storyline":
        st.session_state.STORYLINE["QUIP_SELECTED"] = quip_pick
    elif selected_mode == "PlaidPic":
        st.session_state.PLAIDPIC["QUIP_SELECTED"] = quip_pick
    elif selected_mode == "PlaidMagGen":
        st.session_state.PLAIDMAG["QUIP_SELECTED"] = quip_pick

    st.markdown("---")
    if st.button("🔁 Reset This Mode"):
        reset_mode(selected_mode)
        st.rerun()

# -----------------------
# Render per workflow
# -----------------------

mode = st.session_state.GLOBAL["CURRENT_MODE"]
step = st.session_state.GLOBAL["CURRENT_STEP"]

# 1) LIB-ATE (strict)
if mode == "Lib-Ate":
    L = st.session_state.LIBATE
    active_quip = get_active_quip("Lib-Ate")

    if step == 1:
        st.subheader("STEP 1: LITERARY STYLE SELECTION")
        st.code(
            "🧵 Welcome to Lib-Ate™ - Classic Mad Libs Mode!\n\n"
            "Choose your literary style:\n"
            "1. Flash Fiction - Short, complete narrative\n"
            "2. Ballads - Poetic, musical structure\n"
            "3. Satire & Light Parody - Humorous mockery\n"
            "4. Breaking News - Headline report format\n"
            "5. Scriptlets - Mini-play with dialogue\n"
            "6. Wild Card - Surprise style!\n"
            "7. Reshuffle - Show me different options\n\n"
            "Please type the number (1-7) of your choice:",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Style selection"
        style_map = {
            "1": "Flash Fiction",
            "2": "Ballads",
            "3": "Satire & Light Parody",
            "4": "Breaking News",
            "5": "Scriptlets",
            "6": "Wild Card",
            "7": "Reshuffle",
        }
        val = st.text_input("Your choice (1-7)", key="libate_style_pick")
        if st.button("Submit style"):
            choice = val.strip()
            if choice == "7":
                # reshuffle: present 5 random styles
                styles = pick_random_styles()
                st.session_state.LIBATE["reshuffled_styles"] = styles
                st.session_state.GLOBAL["CURRENT_STEP"] = 1.5
                st.rerun()
            elif choice in style_map:
                sel = style_map[choice]
                if sel == "Wild Card":
                    sel = random.choice([v for k, v in style_map.items() if k in {"1","2","3","4","5"}])
                L["STYLE_SELECTED"] = sel
                # keep quip as selected in sidebar
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
            else:
                st.error("Invalid input. Please enter a number 1-7.")

    elif step == 1.5:
        styles = st.session_state.LIBATE.get("reshuffled_styles", pick_random_styles())
        st.subheader("STEP 1 (Reshuffled Styles)")
        menu = "\n".join([f"{i+1}. {name} - {desc}" for i,(name,desc) in enumerate(styles)]) + "\n6. Wild Card\n"
        st.code(menu + "\nType 1-6:", language="text")
        st.session_state.GLOBAL["WAITING_FOR"] = "Style selection"
        v = st.text_input("Your choice (1-6)", key="libate_style_pick2")
        if st.button("Use this style"):
            c = v.strip()
            if c in {"1","2","3","4","5"}:
                L["STYLE_SELECTED"] = styles[int(c)-1][0]
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
            elif c == "6":
                L["STYLE_SELECTED"] = random.choice([s[0] for s in styles])
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
            else:
                st.error("Please enter 1-6.")

    elif step == 2:
        st.subheader("STEP 2: GENRE SELECTION")
        menu, mapping = genre_menu_block()
        preface = f"Perfect! We're doing a {L['STYLE_SELECTED']} story with {active_quip} narrating.\n\nChoose your genre:\n"
        st.code(preface + menu + "\n\nPlease type the number (1-8) of your choice:", language="text")
        st.session_state.GLOBAL["WAITING_FOR"] = "Genre selection"
        x = st.text_input("Your choice", key="libate_genre_pick")
        if st.button("Submit genre"):
            c = x.strip()
            if c == "8":
                # Reshuffle genres
                st.session_state.GLOBAL["CURRENT_STEP"] = 2  # same step, different options next rerun
                st.rerun()
            elif c in mapping:
                g = mapping[c]
                if g == "Wild Card":
                    g = random.choice(CORE_GENRES + FLEX_GENRES + PLAIDVERSE)[0]
                L["GENRE_SELECTED"] = g
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()
            else:
                st.error("Please pick one of the numbered options shown.")

    elif step == 3:
        active_quip = get_active_quip("Lib-Ate")
        st.subheader("STEP 3: ABSURDITY LEVEL")
        st.code(
            f"Excellent! A {L['STYLE_SELECTED']} {L['GENRE_SELECTED']} story with {active_quip}.\n\n"
            "Finally, set the absurdity level:\n"
            "1. Mild - Just a sprinkle of silly\n"
            "2. Moderate - Comfortably ridiculous\n"
            "3. Plaidemonium™ - Laws of logic need not apply\n"
            "4. Wild Card - Let fate decide!\n\n"
            "Please type the number (1-4) of your choice:",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Absurdity selection"
        v = st.text_input("Your choice (1-4)", key="libate_abs_pick")
        if st.button("Submit absurdity"):
            m = {"1":"Mild","2":"Moderate","3":"Plaidemonium™","4":"Wild Card"}
            c = v.strip()
            if c in m:
                sel = m[c]
                if sel == "Wild Card":
                    sel = random.choice(["Mild","Moderate","Plaidemonium™"])
                L["ABSURDITY_SELECTED"] = sel
                st.session_state.GLOBAL["CURRENT_STEP"] = 4
                st.rerun()
            else:
                st.error("Please enter 1-4.")

    elif step == 4:
        active_quip = get_active_quip("Lib-Ate")
        st.subheader("STEP 4: TEASER AND PROMPT SETUP")
        L["teaser"] = f'"Aye, a {L["STYLE_SELECTED"]} {L["GENRE_SELECTED"]} with {L["ABSURDITY_SELECTED"]}. What could possibly go tidy?"'
        st.code(
            f"🎯 Setup Complete!\n"
            f"- Style: {L['STYLE_SELECTED']}\n"
            f"- Genre: {L['GENRE_SELECTED']}\n"
            f"- Absurdity: {L['ABSURDITY_SELECTED']}\n"
            f"- Narrator: {active_quip}\n\n"
            f"{active_quip} delivers in-character teaser line based on the setup\n\n"
            f"{L['teaser']}\n\n"
            "I'll need 12 words/phrases from you to build this story. Each prompt will include helpful hints!\n\n"
            "Ready to start? Type 'yes' or 'let's go':",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Ready confirmation"
        v = st.text_input("Type here", key="libate_ready")
        if st.button("Confirm"):
            if v.strip().lower() in {"yes","let's go","lets go","y"}:
                L["PROMPTS_NEEDED"] = 12
                L["PROMPTS_COLLECTED"] = 0
                st.session_state.GLOBAL["CURRENT_STEP"] = 5
                st.rerun()
            else:
                st.error("Please type 'yes' or 'let's go' to continue.")

    elif step == 5:
        st.subheader("STEP 5: WORD COLLECTION")
        prompts = [
            ("name", "Name (proper noun)", "Think protagonist: e.g., ‘Rowan’"),
            ("profession", "Profession (noun)", "Detective, baker, cartographer…"),
            ("place", "Place (noun)", "City, valley, ship, café…"),
            ("adjective", "Adjective", "Moody, iridescent, stubborn…"),
            ("object", "Object (noun)", "Lantern, violin, ledger…"),
            ("name2", "Second character name", "Rival or ally"),
            ("object2", "Second object (noun)", "Key, coin, compass…"),
            ("place2", "Second place (noun)", "Square, market, jetty…"),
            ("portal", "Portal/threshold (noun)", "Doorway, ripple, curtain…"),
            ("tool", "Tool/aid (abstract ok)", "Courage, compass, trick…"),
            ("trait", "Virtue/trait", "Grace, grit, candor…"),
            ("wild", "Wildcard word/phrase", "Anything at all"),
        ]
        idx = L["PROMPTS_COLLECTED"]
        key_name, title, helptext = prompts[idx]
        st.code(
            f"Prompt {idx+1} of {L['PROMPTS_NEEDED']}:\n\n"
            f"{title}\n{helptext}\n\n"
            f"{macquip_aside('If you draw a blank, type “surprise me”.', 'Lib-Ate')}\n\n"
            "Your answer (or type \"surprise me\"):",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Word prompt response"
        v = st.text_input("Answer", key=f"libate_word_{idx}")
        if st.button("Submit answer"):
            ans = v.strip()
            if not ans or ans.lower() == "surprise me":
                # Auto-pick
                auto = random.choice([
                    "Rowan","Harper","Alex","Miri","Sable","Juno","Isla","Orion",
                    "astronomer","baker","tinkerer","ranger","scribe",
                    "Dockside","Northbridge","Glimmerfall","Moonmarket",
                    "tattered","luminous","sardonic","restless",
                    "compass","ledger","lantern","accordion","vending machine",
                    "Riley","Kestrel","Nico","Vee",
                    "map","coin","hourglass","key",
                    "Rookery","East Gate","Sun Stairs","Old Yard",
                    "ripple","threshold","curtain","vellum",
                    "courage","wit","stubbornness","luck",
                    "grace","grit","candor","pluck",
                    "confetti rain","time hiccup","snack-based destiny",
                ])
                L["COLLECTED"][key_name] = auto
                st.success(f'Surprise pick: "{auto}"')
            else:
                L["COLLECTED"][key_name] = ans
                st.success("Saved.")
            L["PROMPTS_COLLECTED"] += 1
            if L["PROMPTS_COLLECTED"] >= L["PROMPTS_NEEDED"]:
                st.session_state.GLOBAL["CURRENT_STEP"] = 6
            st.rerun()

    elif step == 6:
        active_quip = get_active_quip("Lib-Ate")
        st.subheader("STEP 6: STORY GENERATION")
        st.code(
            "🎪 All prompts collected! {q} is weaving your words into magic...\n\n".format(q=active_quip) +
            f"🎭 FINAL CONFIGURATION 🎭\n"
            f"Literary Style: {L['STYLE_SELECTED']}\n"
            f"Genre: {L['GENRE_SELECTED']}\n"
            f"Absurdity Level: {L['ABSURDITY_SELECTED']}\n"
            f"Narrator: {active_quip}\n\n"
            f"{active_quip} delivers dramatic pre-story flair comment\n",
            language="text",
        )
        story = assemble_story(L["STYLE_SELECTED"], L["GENRE_SELECTED"], L["ABSURDITY_SELECTED"], L["QUIP_SELECTED"], L["COLLECTED"])
        st.markdown(story)
        st.markdown(f"_{active_quip} outro:_ Curtain call with a wink.")
        # Proceed to Remix
        st.session_state.GLOBAL["CURRENT_STEP"] = 7

    elif step == 7:
        active_quip = get_active_quip("Lib-Ate")
        st.subheader("STEP 7: REMIX OPTIONS")
        st.code(
            "🔄 What would you like to do next?\n\n"
            "1. Fluff It Up - Add softness, poetic language, whimsy\n"
            "2. Dial It Up - Switch to humorous dialect\n"
            "3. Style It Up - Retell in different literary style\n"
            "4. Plaidgerize - Rewrite with maximum absurdity\n"
            "5. PlaidMagGen-It - Generate matching 3-panel visual\n"
            "6. New Story - Start completely over\n\n"
            "Please type the number (1-6):",
            language="text",
        )

        c = st.text_input("Remix choice", key="libate_remix")
        if st.button("Apply remix"):
            if c.strip() in {"1", "2", "3", "4"}:
                # simple remixes: regenerate story with tweaks
                tweak = c.strip()
                seeds = st.session_state.LIBATE["COLLECTED"].copy()
                style = L["STYLE_SELECTED"]
                genre = L["GENRE_SELECTED"]
                absurd = L["ABSURDITY_SELECTED"]

                if tweak == "1":
                    style = "Magic Realism"
                elif tweak == "2":
                    seeds["trait"] = seeds.get("trait", "grit") + " (dialect spice)"
                elif tweak == "3":
                    style = random.choice(["Ballads", "Breaking News", "Scriptlets", "Flash Fiction"])
                elif tweak == "4":
                    absurd = "Plaidemonium™"

                new_story = assemble_story(style, genre, absurd, L["QUIP_SELECTED"], seeds)
                st.session_state.generated_story = new_story
                st.markdown(f"### ✨ Remixed Story: Option {tweak}")
                st.markdown(new_story)

            elif c.strip() == "5":
                st.markdown("**PlaidMagGen-It:** See _PlaidMagGen_ workflow to craft a 3-panel prompt from this story.")

            elif c.strip() == "6":
                reset_mode("Lib-Ate")
                st.rerun()

            else:
                st.error("Please pick 1-6.")

    # Post-story options
    st.subheader("Post-Story Options")
    if "generated_story" not in st.session_state:
        st.session_state.generated_story = story if "story" in locals() else ""

    # Download button
    st.download_button(
        label="📥 Download Story",
        data=st.session_state.generated_story,
        file_name="libate_story.txt",
        mime="text/plain",
    )

    # Post story action (example: placeholder for integration)
    if st.button("Remix Story"):
        st.success("You can Proceed to Remix After Generating Story")



# 2) CREATE-DIRECT
elif mode == "Create Direct":
    C = st.session_state.CREATEDIRECT
    active_quip = get_active_quip("Create Direct")

    if step == 1:
        st.subheader("STEP 1: LITERARY STYLE SELECTION")
        styles = pick_random_styles()
        menu = "\n".join([f"{i+1}. {n} - {d}" for i,(n,d) in enumerate(styles)])
        st.code(
            "✍️ Create Mode (Direct) - Instant Story Generation!\n\n"
            "Choose the literary style:\n" + menu +
            "\n6. Wild Card - Surprise style!\n7. Reshuffle - Different options\n\nPlease type the number (1-7):",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Style selection"
        v = st.text_input("Your choice", key="cd_style")
        if st.button("Submit style"):
            c = v.strip()
            if c == "7":
                st.rerun()
            elif c == "6":
                C["STYLE_SELECTED"] = random.choice([s[0] for s in styles])
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
            elif c in {"1","2","3","4","5"}:
                C["STYLE_SELECTED"] = styles[int(c)-1][0]
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
            else:
                st.error("Pick 1-7.")

    elif step == 2:
        st.subheader("STEP 2: GENRE SELECTION")
        menu, mapping = genre_menu_block()
        st.code(
            f"Excellent! A {C['STYLE_SELECTED']} story with {active_quip}.\n\n"
            "Pick your genre:\n" + menu + "\n\nPlease type the number (1-8):",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Genre selection"
        v = st.text_input("Your choice", key="cd_genre")
        if st.button("Submit genre"):
            c = v.strip()
            if c == "8":
                st.rerun()
            elif c in mapping:
                g = mapping[c]
                if g == "Wild Card":
                    g = random.choice(CORE_GENRES + FLEX_GENRES + PLAIDVERSE)[0]
                C["GENRE_SELECTED"] = g
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()
            else:
                st.error("Pick one of the visible numbers.")

    elif step == 3:
        st.subheader("STEP 3: ABSURDITY LEVEL")
        st.code(
            f"Great choice! {C['STYLE_SELECTED']} {C['GENRE_SELECTED']} with {active_quip}.\n\n"
            "Set the chaos level:\n"
            "1. Mild - Just a sprinkle of silly\n"
            "2. Moderate - Comfortably ridiculous\n"
            "3. Plaidemonium™ - Laws of logic need not apply\n"
            "4. Wild Card - Let fate decide!\n\n"
            "Please type the number (1-4):",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Absurdity selection"
        v = st.text_input("Your choice", key="cd_abs")
        if st.button("Submit absurdity"):
            c = v.strip()
            if c in {"1","2","3","4"}:
                mapping = {"1":"Mild","2":"Moderate","3":"Plaidemonium™","4":"Wild Card"}
                sel = mapping[c]
                if sel == "Wild Card":
                    sel = random.choice(["Mild","Moderate","Plaidemonium™"])
                C["ABSURDITY_SELECTED"] = sel
                st.session_state.GLOBAL["CURRENT_STEP"] = 4
                st.rerun()
            else:
                st.error("Pick 1-4.")

    elif step == 4:
        st.subheader("STEP 4: CONFIRMATION & GENERATION")
        st.code(
            "🎯 Story Configuration Complete!\n\n"
            f"- Storyteller: {active_quip}\n- Style: {C['STYLE_SELECTED']}\n- Genre: {C['GENRE_SELECTED']}\n- Absurdity: {C['ABSURDITY_SELECTED']}\n\n"
            f"{active_quip} delivers in-character teaser/intro line\n\n"
            "Ready for your instant story? Type 'Let's Go' or hit any key:",
            language="text",
        )
        v = st.text_input("Confirm", key="cd_go")

        if st.button("Generate"):
            seeds = {
                "name": random.choice(["Rowan","Alex","Miri","Jax"]),
                "profession": random.choice(["astronomer","baker","tinkerer","ranger"]),
                "place": random.choice(["Harborlight","Northbridge","Glimmerfall"]),
                "adjective": random.choice(["restless","luminous","sardonic"]),
                "object": random.choice(["lantern","ledger","compass"]),
                "name2": random.choice(["Riley","Kestrel","Vee"]),
                "object2": random.choice(["map","coin","hourglass"]),
                "place2": random.choice(["East Gate","Sun Stairs","Old Yard"]),
                "portal": random.choice(["ripple","curtain","threshold"]),
                "tool": random.choice(["courage","wit","stubbornness"]),
                "trait": random.choice(["grace","grit","candor"]),
            }
            st.session_state.generated_story = assemble_story(
                C["STYLE_SELECTED"], C["GENRE_SELECTED"], C["ABSURDITY_SELECTED"], active_quip, seeds
            )

            # Move to step 5 correctly
            st.session_state.GLOBAL["CURRENT_STEP"] = 5
            st.rerun()

    elif step == 5:
        st.subheader("STEP 5: REMIX OPTIONS")
        st.code(
            "🔄 What would you like to do next?\n\n"
            "1. Fluff It Up - Add softness, poetic language, whimsy\n"
            "2. Dial It Up - Switch to humorous dialect\n"
            "3. Style It Up - Retell in different literary style\n"
            "4. Plaidgerize - Rewrite with maximum absurdity\n"
            "5. PlaidMagGen-It - Generate matching 3-panel visual\n"
            "6. New Story - Start completely over\n\n"
            "Please type the number (1-6):",
            language="text",
        )

        if "generated_story" in st.session_state:
            st.markdown("### 📖 Your Story")
            st.markdown(st.session_state.generated_story)

        c = st.text_input("Remix choice", key="createdirect_remix")
        if st.button("Apply remix"):
            if c.strip() in {"1", "2", "3", "4"}:
                tweak = c.strip()
                seeds = st.session_state.CREATEDIRECT.get("COLLECTED", {}).copy()
                style, genre, absurd = C["STYLE_SELECTED"], C["GENRE_SELECTED"], C["ABSURDITY_SELECTED"]

                if tweak == "1":
                    style = "Magic Realism"
                elif tweak == "2":
                    seeds["trait"] = seeds.get("trait", "grit") + " (dialect spice)"
                elif tweak == "3":
                    style = random.choice(["Ballads", "Breaking News", "Scriptlets", "Flash Fiction"])
                elif tweak == "4":
                    absurd = "Plaidemonium™"

                new_story = assemble_story(style, genre, absurd, active_quip, seeds)
                st.session_state.generated_story = new_story
                st.markdown(f"### ✨ Remixed Story: Option {tweak}")
                st.markdown(new_story)

            elif c.strip() == "5":
                st.markdown("**PlaidMagGen-It:** See _PlaidMagGen_ workflow to craft a 3-panel prompt from this story.")

            elif c.strip() == "6":
                reset_mode("Create Direct")
                st.rerun()
            else:
                st.error("Please pick 1-6.")

        # Always show Post-Story options
        st.subheader("Post-Story Options")
        st.download_button(
            label="📥 Download Story",
            data=st.session_state.generated_story,
            file_name="create_direct_story.txt",
            mime="text/plain",
        )
        if st.button("Post Story"):
            st.success("Story has been posted! (integration pending)")


# 3) STORYLINE
elif mode == "Storyline":
    S = st.session_state.STORYLINE
    active_quip = get_active_quip("Storyline")

    if step == 1:
        st.subheader("STEP 1: YOUR STORY CONCEPT")
        st.code(
            "✍️ Create Mode (Storyline) - You Set The Scene!\n\n"
            "Describe your story idea, scene, or setup. It can be:\n"
            "- Simple: 'a goat runs for mayor'\n- Detailed: 'In a world where gravity works backwards...'\n"
            "- Weird: 'My toaster gained sentience and filed taxes'\n\n"
            "What's your story concept?",
            language="text",
        )
        st.session_state.GLOBAL["WAITING_FOR"] = "Story concept"
        concept = st.text_area("Describe your concept", key="sl_concept", height=140)
        if st.button("Save Concept"):
            if concept.strip():
                S["USER_STORYLINE"] = concept.strip()
                st.success("Concept saved.")
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
            else:
                st.error("Please enter a concept.")

    elif step == 2:
        st.subheader("STEP 2: STYLE PICK")
        styles = pick_random_styles()
        menu = "\n".join([f"{i+1}. {n} - {d}" for i,(n,d) in enumerate(styles)])
        st.code(
            "Choose a literary style for your concept:\n"
            + menu + "\n6. Wild Card\n7. Reshuffle\n\nType 1-7:",
            language="text",
        )
        v = st.text_input("Your choice", key="sl_style")
        if st.button("Submit style"):
            c = v.strip()
            if c == "7":
                st.rerun()
            elif c == "6":
                S["STYLE_SELECTED"] = random.choice([s[0] for s in styles])
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()
            elif c in {"1","2","3","4","5"}:
                S["STYLE_SELECTED"] = styles[int(c)-1][0]
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()
            else:
                st.error("Pick 1-7.")

    elif step == 3:
        st.subheader("STEP 3: ABSURDITY LEVEL")
        st.code(
            f"Style locked: {S['STYLE_SELECTED']}.\n"
            "Set the absurdity level:\n"
            "1. Mild\n2. Moderate\n3. Plaidemonium™\n4. Wild Card\n\nType 1-4:",
            language="text",
        )
        v = st.text_input("Your choice", key="sl_abs")
        if st.button("Submit absurdity"):
            m = {"1":"Mild","2":"Moderate","3":"Plaidemonium™","4":"Wild Card"}
            c = v.strip()
            if c in m:
                sel = m[c]
                if sel == "Wild Card":
                    sel = random.choice(["Mild","Moderate","Plaidemonium™"])
                S["ABSURDITY_SELECTED"] = sel
                st.session_state.GLOBAL["CURRENT_STEP"] = 4
                st.rerun()
            else:
                st.error("Pick 1-4.")

    elif step == 4:
        st.subheader("STEP 4: GENERATE FROM CONCEPT")
        st.code(
            f"🎬 Translating your concept into a story seed and weaving it through {active_quip}.\n"
            "Press Generate when ready.",
            language="text",
        )

        def seeds_from_concept(txt: str) -> Dict[str, str]:
            words = re.findall(r"[A-Za-z']+", txt)
            caps = re.findall(r"\b[A-Z][a-z']+\b", txt)
            name = caps[0] if caps else random.choice(["Rowan","Alex","Miri","Jax"])
            professions = ["baker","astronomer","detective","ranger","scribe","cartographer","librarian","sailor","pilot"]
            prof = None
            for w in words:
                if w.lower() in professions:
                    prof = w.lower()
                    break
                if w.endswith("er") and len(w) > 4:
                    prof = w.lower()
                    break
            prof = prof or random.choice(professions)
            place = None
            m = re.search(r"\b(in|at|under|inside|near)\s+([A-Za-z][A-Za-z\s']{2,})", txt, flags=re.IGNORECASE)
            if m:
                place = m.group(2).strip().split()[0:2]
                place = " ".join(place)
            place = place or random.choice(["Harborlight","Northbridge","Glimmerfall","Dockside"])
            adjectives = ["restless","luminous","sardonic","tattered","iridescent"]
            adj = None
            for w in words:
                if w.lower() in adjectives:
                    adj = w.lower(); break
            adj = adj or random.choice(adjectives)
            obj = random.choice(["lantern","ledger","compass","violin","coin","hourglass"])
            name2 = random.choice(["Riley","Kestrel","Vee","Nico"])
            obj2 = random.choice(["map","key","ticket","note"])
            place2 = random.choice(["East Gate","Old Yard","Sun Stairs"])
            portal = random.choice(["ripple","threshold","curtain"])
            tool = random.choice(["courage","wit","stubbornness"])
            trait = random.choice(["grace","grit","candor"])
            return {
                "name": name, "profession": prof, "place": place, "adjective": adj, "object": obj,
                "name2": name2, "object2": obj2, "place2": place2, "portal": portal, "tool": tool, "trait": trait,
                "wild": random.choice(["confetti rain","time hiccup","snack-based destiny"]),
            }

        if st.button("Generate Story"):
            seeds = seeds_from_concept(S["USER_STORYLINE"])
            story = assemble_story(S["STYLE_SELECTED"], random.choice([g[0] for g in CORE_GENRES+FLEX_GENRES+PLAIDVERSE]),
                                   S["ABSURDITY_SELECTED"], S["QUIP_SELECTED"], seeds)
            st.session_state.generated_story = story
            st.markdown("### ✨ Your Story")
            st.markdown(story)
            st.session_state.GLOBAL["CURRENT_STEP"] = 5
            st.rerun()

    elif step == 5:
        # Show the story again if available
        if "generated_story" in st.session_state:
            st.markdown("### ✨ Your Story")
            st.markdown(st.session_state.generated_story)

        # Post-Story options
        st.subheader("Post-Story Options")
        st.code(
            "Options:\n"
            "1) Fluff It Up\n2) Dial It Up\n3) New Style\n4) Plaidgerize (max absurd)\n5) Start Over",
            language="text",
        )
        v = st.text_input("Pick 1-5", key="sl_remix")
        if st.button("Apply"):
            if v.strip() in {"1","2","3","4"}:
                seeds = {"name":"Remy","profession":"wanderer","place":"Plaidshire","adjective":"zany","object":"teacup",
                         "name2":"Quinn","object2":"ticket","place2":"Clocktower","portal":"mirror","tool":"pluck","trait":"wit"}
                style = S["STYLE_SELECTED"]
                absurd = S["ABSURDITY_SELECTED"]
                genre = random.choice([g[0] for g in CORE_GENRES+FLEX_GENRES+PLAIDVERSE])
                if v.strip() == "1":
                    style = "Magic Realism"
                elif v.strip() == "2":
                    seeds["trait"] += " (dialect spice)"
                elif v.strip() == "3":
                    style = random.choice(["Ballads","Flash Fiction","Scriptlets","Breaking News"])
                elif v.strip() == "4":
                    absurd = "Plaidemonium™"
                remixed_story = assemble_story(style, genre, absurd, S["QUIP_SELECTED"], seeds)
                st.session_state.generated_story = remixed_story
                st.markdown("### ✨ Remixed Story")
                st.markdown(remixed_story)
            elif v.strip() == "5":
                reset_mode("Storyline")
                st.rerun()
            else:
                st.error("Pick 1-5.")

        # Download and Post buttons
        st.download_button(
            label="📥 Download Story",
            data=st.session_state.generated_story,
            file_name="storyline_story.txt",
            mime="text/plain",
        )
        if st.button("Post Story"):
            st.success("Story has been posted! (integration pending)")



# 4) PLAIDPIC
elif mode == "PlaidPic":
    P = st.session_state.PLAIDPIC
    active_quip = get_active_quip("PlaidPic")
    if step == 1:
        st.subheader("STEP 1: IMAGE OR DESCRIPTION")
        st.code(
            "PlaidPic turns an image (or your description of it) into a story + visual prompt.\n"
            "Upload an image (optional) or describe what’s in it.",
            language="text",
        )
        uploaded = st.file_uploader("Upload image (optional)", type=["png","jpg","jpeg","webp"], key="pp_file")
        desc = st.text_area("Or describe the image", key="pp_desc", height=120, placeholder="e.g., A fox in a plaid scarf at a rainy bus stop...")
        if st.button("Proceed"):
            P["IMAGE_UPLOADED"] = bool(uploaded)
            P["TEXT_DESC"] = desc.strip()
            P["IMAGE_ANALYSIS"] = {}
            st.session_state.GLOBAL["CURRENT_STEP"] = 2
            st.rerun()

    elif step == 2:
        st.subheader("STEP 2: QUICK ANALYSIS LABELS")
        cap = st.text_input("Short caption", key="pp_cap", placeholder="Rain waits in plaid")
        mood = st.text_input("Mood / Tone", key="pp_mood", placeholder="wistful, cozy")
        focal = st.text_input("Focal element", key="pp_focal", placeholder="plaid scarf / fox / umbrella")
        env = st.text_input("Environment", key="pp_env", placeholder="bus stop / rainy street / neon")
        if st.button("Save & Continue"):
            P["IMAGE_ANALYSIS"] = {"caption":cap.strip(),"mood":mood.strip(),"focal":focal.strip(),"env":env.strip()}
            st.session_state.GLOBAL["CURRENT_STEP"] = 3
            st.rerun()

    elif step == 3:
        st.subheader("STEP 3: STYLE, GENRE, ABSURDITY")
        styles = pick_random_styles()
        st.code("\n".join([f"{i+1}. {n} - {d}" for i,(n,d) in enumerate(styles)]) + "\n6. Wild Card", language="text")
        s = st.text_input("Pick style 1-6", key="pp_style")
        menu, mapping = genre_menu_block()
        st.code("Genres:\n" + menu + "\n(type number)", language="text")
        g = st.text_input("Pick genre", key="pp_genre")
        st.code("Absurdity: 1 Mild / 2 Moderate / 3 Plaidemonium™ / 4 Wild Card", language="text")
        a = st.text_input("Pick absurdity", key="pp_abs")

        if st.button("Lock Config"):
            # style
            if s.strip() == "6":
                P["STYLE_SELECTED"] = random.choice([x[0] for x in styles])
            elif s.strip() in {"1","2","3","4","5"}:
                P["STYLE_SELECTED"] = styles[int(s.strip())-1][0]
            else:
                st.error("Pick a valid style."); st.stop()
            # genre
            if g.strip() == "8":
                # reshuffle genres next rerun (we’ll accept current set)
                pass
            if g.strip() in mapping:
                gg = mapping[g.strip()]
                if gg == "Wild Card":
                    gg = random.choice(CORE_GENRES + FLEX_GENRES + PLAIDVERSE)[0]
                P["GENRE_SELECTED"] = gg
            else:
                st.error("Pick a visible genre number."); st.stop()
            # absurdity
            m = {"1":"Mild","2":"Moderate","3":"Plaidemonium™","4":"Wild Card"}
            if a.strip() in m:
                sel = m[a.strip()]
                if sel == "Wild Card":
                    sel = random.choice(["Mild","Moderate","Plaidemonium™"])
                P["ABSURDITY_SELECTED"] = sel
            else:
                st.error("Pick 1-4 for absurdity."); st.stop()
            st.session_state.GLOBAL["CURRENT_STEP"] = 4
            st.rerun()

    elif step == 4:
        st.subheader("STEP 4: STORY + VISUAL PROMPT")
        seeds = {
            "name": random.choice(["Rowan","Miri","Ash"]),
            "profession": random.choice(["watcher","barista","busker","detective"]),
            "place": P["IMAGE_ANALYSIS"].get("env") or "Rainmarket",
            "adjective": P["IMAGE_ANALYSIS"].get("mood","restless"),
            "object": P["IMAGE_ANALYSIS"].get("focal","lantern"),
            "name2": random.choice(["Riley","Vee","Nico"]),
            "object2": random.choice(["ticket","map","umbrella"]),
            "place2": "East Gate",
            "portal": "ripple",
            "tool": "courage",
            "trait": "grace",
        }
        story = assemble_story(P["STYLE_SELECTED"], P["GENRE_SELECTED"], P["ABSURDITY_SELECTED"], P["QUIP_SELECTED"], seeds)
        st.markdown(story)
        st.markdown(f"Right, the picture’s worth a thousand plaiditudes. (Narrator: {get_active_quip('PlaidPic')})")

        # Visual prompt spec
        fmt = "3-Panel Comic"
        style_name = P["STYLE_SELECTED"]
        desc = P["TEXT_DESC"] or (P["IMAGE_ANALYSIS"].get("caption","A moment in plaid") + f", mood {P['IMAGE_ANALYSIS'].get('mood','restless')}, focal {P['IMAGE_ANALYSIS'].get('focal','object')}")
        tags = ["Cinematic Lighting","Showcase Plaid Clothing"]
        vp = generate_visual_prompt(fmt, style_name, desc, tags)
        st.code(vp, language="text")
        st.session_state.GLOBAL["CURRENT_STEP"] = 5

    elif step == 5:
        st.subheader("STEP 5: REMIX / RESTART")
        st.code("1) New Style\n2) Max Absurd\n3) New Input\n4) Restart PlaidPic", language="text")
        v = st.text_input("Pick 1-4", key="pp_remix")
        if st.button("Apply Remix"):
            if v.strip() == "1":
                st.markdown("**Remix:** Retelling in different style.")
                st.markdown(assemble_story(random.choice(["Ballads","Flash Fiction","Scriptlets","Breaking News"]),
                                           P["GENRE_SELECTED"], P["ABSURDITY_SELECTED"], P["QUIP_SELECTED"], {
                                               "name":"Remy","profession":"wanderer","place":"Plaidshire","adjective":"zany",
                                               "object":"teacup","name2":"Quinn","object2":"ticket","place2":"Clocktower",
                                               "portal":"mirror","tool":"pluck","trait":"wit"
                                           }))
            elif v.strip() == "2":
                st.markdown("**Remix:** Maximum Plaidemonium™ engaged.")
                st.markdown(assemble_story(P["STYLE_SELECTED"], P["GENRE_SELECTED"], "Plaidemonium™", P["QUIP_SELECTED"], {
                    "name":"Zee","profession":"chaos technician","place":"Tartanverse","adjective":"unruly","object":"plaid coil",
                    "name2":"Kestrel","object2":"map","place2":"Sun Stairs","portal":"ripple","tool":"audacity","trait":"grit"
                }))
            elif v.strip() == "3":
                st.session_state.GLOBAL["CURRENT_STEP"] = 1
                st.rerun()
            elif v.strip() == "4":
                reset_mode("PlaidPic")
                st.rerun()
            else:
                st.error("Pick 1-4.")

# 5) PLAIDMAGGEN
elif mode == "PlaidMagGen":
    M = st.session_state.PLAIDMAG
    active_quip = get_active_quip("PlaidMagGen")
    if step == 1:
        st.subheader("STEP 1: CHOOSE FORMAT")
        formats = ["Poster","3-Panel Comic","Magazine Cover","Storyboard (3 frames)","Trading Card"]
        st.code("\n".join([f"{i+1}. {f}" for i,f in enumerate(formats)]) + "\n6. Wild Card", language="text")
        v = st.text_input("Pick 1-6", key="pm_format")
        if st.button("Set Format"):
            if v.strip() == "6":
                M["FORMAT_SELECTED"] = random.choice(formats)
            elif v.strip() in {"1","2","3","4","5"}:
                M["FORMAT_SELECTED"] = formats[int(v.strip())-1]
            else:
                st.error("Pick 1-6."); st.stop()
            st.session_state.GLOBAL["CURRENT_STEP"] = 2
            st.rerun()

    elif step == 2:
        st.subheader("STEP 2: CHOOSE STYLE")
        styles = pick_random_styles()
        st.code("\n".join([f"{i+1}. {n} - {d}" for i,(n,d) in enumerate(styles)]) + "\n6. Wild Card", language="text")
        v = st.text_input("Pick 1-6", key="pm_style")
        if st.button("Set Style"):
            if v.strip() == "6":
                M["STYLE_SELECTED"] = random.choice([s[0] for s in styles])
            elif v.strip() in {"1","2","3","4","5"}:
                M["STYLE_SELECTED"] = styles[int(v.strip())-1][0]
            else:
                st.error("Pick 1-6."); st.stop()
            st.session_state.GLOBAL["CURRENT_STEP"] = 3
            st.rerun()

    elif step == 3:
        st.subheader("STEP 3: CORE DESCRIPTION")
        prompt = st.text_area("Describe the scene/subject you'd like to visualize:", key="pm_desc", height=140)
        if st.button("Save Description"):
            if prompt.strip():
                M["PROMPT_COLLECTED"] = prompt.strip()
                st.session_state.GLOBAL["CURRENT_STEP"] = 4
                st.rerun()
            else:
                st.error("Please enter a description.")

    elif step == 4:
        st.subheader("STEP 4: ENHANCEMENT TAGS")
        tags = st.multiselect("Optional tags", IMAGE_TAGS, default=["Cinematic Lighting"])
        if st.button("Generate Visual Spec"):
            M["ENHANCEMENT_TAGS"] = tags
            spec = generate_visual_prompt(M["FORMAT_SELECTED"], M["STYLE_SELECTED"], M["PROMPT_COLLECTED"], tags)
            st.code(spec, language="text")
            st.session_state.GLOBAL["CURRENT_STEP"] = 5

    elif step == 5:
        st.subheader("STEP 5: REMIX / RESTART")
        st.code("1) Randomize Tags\n2) New Style\n3) Start Over", language="text")
        v = st.text_input("Pick 1-3", key="pm_remix")
        if st.button("Apply"):
            if v.strip() == "1":
                tags = random.sample(IMAGE_TAGS, k=min(3, len(IMAGE_TAGS)))
                st.code(generate_visual_prompt(M["FORMAT_SELECTED"], M["STYLE_SELECTED"], M["PROMPT_COLLECTED"], tags), language="text")
            elif v.strip() == "2":
                new_style = random.choice(["Ballads","Magic Realism","Scriptlets","Flash Fiction","Breaking News"])
                st.code(generate_visual_prompt(M["FORMAT_SELECTED"], new_style, M["PROMPT_COLLECTED"], M["ENHANCEMENT_TAGS"]), language="text")
            elif v.strip() == "3":
                reset_mode("PlaidMagGen")
                st.rerun()
            else:
                st.error("Pick 1-3.")

# 6) PLAIDPLAY
elif mode == "PlaidPlay":
    PLY = st.session_state.PLAIDPLAY
    active_quip = get_active_quip("PlaidPlay")
    if step == 1:
        st.subheader("STEP 1: SET PLAYERS & PROMPT")
        emails = st.text_input("Player emails (comma-separated, optional)", key="pp_emails")
        n_players = st.number_input("Number of players (2-8)", min_value=2, max_value=8, value=4, step=1, key="pp_n")
        prompt = st.text_area("Master prompt / theme", key="pp_master", height=120, placeholder="e.g., 'A heist involving plaid luggage at a moonlit train station'")
        if st.button("Start Round"):
            PLY["PLAYER_EMAILS"] = [e.strip() for e in emails.split(",") if e.strip()]
            PLY["N_PLAYERS"] = int(n_players)
            PLY["MASTER_PROMPT"] = prompt.strip() or "Plaid heist at dawn"
            st.session_state.GLOBAL["CURRENT_STEP"] = 2
            st.rerun()

    elif step == 2:
        st.subheader("STEP 2: FAUX SUBMISSIONS")
        subs = simulate_submissions(PLY["MASTER_PROMPT"], PLY["N_PLAYERS"])
        PLY["SUBMISSIONS"] = subs
        PLY["SUBMISSIONS_RECEIVED"] = len(subs)
        for s in subs:
            st.markdown(f"**{s['player']}** — nouns: {', '.join(s['nouns'])}; adjs: {', '.join(s['adjs'])}; wildcard: _{s['wild']}_")
        if st.button("Run Voting Simulation"):
            st.session_state.GLOBAL["CURRENT_STEP"] = 3
            st.rerun()

    elif step == 3:
        st.subheader("STEP 3: VOTING & RESULTS")
        tally = tally_votes(PLY["SUBMISSIONS"])
        PLY["VOTE_TALLY"] = tally
        winner = max(tally.items(), key=lambda kv: kv[1])[0] if tally else "No one"
        st.markdown("### Vote Tally")
        for k,v in tally.items():
            st.markdown(f"- **{k}**: {v} points")
        st.success(f"🏆 Winner: {winner}")
        if st.button("Show Encore Snippets"):
            st.session_state.GLOBAL["CURRENT_STEP"] = 4
            st.rerun()

    elif step == 4:
        st.subheader("STEP 4: ENCORE SNIPPETS (SCRIPTLETS)")
        for s in PLY["SUBMISSIONS"]:
            snippet = f"[{s['player']}] ({', '.join(s['adjs'])}) — 'We trade the {s['nouns'][0]} for a {s['nouns'][1]}; if the {s['nouns'][2]} sings, we run.'"
            st.write(snippet)
        st.markdown(f"_{active_quip} aside:_ Democracy by giggle. I approve.")
        st.code("1) New Round\n2) Restart PlaidPlay", language="text")
        v = st.text_input("Pick 1-2", key="ply_remix")
        if st.button("Apply"):
            if v.strip() == "1":
                st.session_state.GLOBAL["CURRENT_STEP"] = 1
                st.rerun()
            elif v.strip() == "2":
                reset_mode("PlaidPlay")
                st.rerun()
            else:
                st.error("Pick 1-2.")



# 7) PLAIDCHAT
elif mode == "PlaidChat":
    PC = st.session_state.PLAIDCHAT
    active_quip = get_active_quip("PlaidChat")
    st.subheader("PlaidChat™ — Quip-fueled conversation")

    from openai import OpenAI
    client = OpenAI()

    def persona_reply(quip, history):
        """
        Generate a persona-style reply using conversation history + narrator quip.
        """
        messages = [
            {
                "role": "system",
                "content": f"You are {quip}, a playful narrator with a unique personality. "
                           f"Stay in character and respond in a conversational way, like ChatGPT, "
                           f"but flavored with the humor and quirks of {quip}. "
                           f"Keep responses concise, engaging, and context-aware."
            }
        ]

        # Add prior conversation
        for m in history:
            role = "assistant" if m["role"] == "assistant" else "user"
            messages.append({"role": role, "content": m["content"]})

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # can switch to "gpt-4o" for stronger replies
            messages=messages,
            max_tokens=300,
            temperature=0.9
        )

        return response.choices[0].message.content.strip()

    # Assign narrator name based on role
    def display_message(msg):
        if msg["role"] == "user":
            name = "You"
        else:
            name = PC.get("QUIP_SELECTED", "Narrator")
        st.markdown(f"**{name}:** {msg['content']}")

    # Render history
    for msg in PC["messages"]:
        with st.chat_message(msg["role"]):
            display_message(msg)

    # Handle new input
    user_input = st.chat_input("Say something to your Quip guide…")
    if user_input:
        # User message
        PC["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(f"**You:** {user_input}")

        # Persona reply (always returns string now)
        reply = persona_reply(PC["QUIP_SELECTED"], PC["messages"])
        PC["messages"].append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(f"**{PC.get('QUIP_SELECTED','Narrator')}:** {reply}")
































