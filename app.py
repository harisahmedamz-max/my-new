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
import requests
from io import BytesIO
import random
import re
import textwrap
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import openai
import streamlit as st
import os
from openai import OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not set in environment")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import base64
from io import BytesIO
from PIL import Image
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
    ("Adventure", "Quests, journeys, danger"),
    ("Comedy", "Jokes, mishaps, ridiculous stakes"),
    ("Drama", "Character conflict, serious tones"),
    ("Fantasy", "Magic, mythology, and otherworlds"),
    ("Historical", "Plaid-twisted events of the past"),
    ("Horror", "Fear, tension, monsters, paranoia"),
    ("Mystery", "Secrets, clues, odd disappearances"),
    ("Romance", "Love, heartbreak, awkward passion"),
    ("Science Fiction", "Futuristic or tech-driven oddities"),
    ("Thriller", "Suspense, danger, and dramatic pacing"),
]

FLEX_GENRES = [
    ("Absurdist", "Embraces nonsense as narrative fuel"),
    ("Satire", "Mocking of systems, ideas, or trends"),
    ("Slice of Life", "Mundane moments made meaningful"),
    ("Speculative", "‘What if’ world logic; near-future fiction"),
    ("Surreal", "Dreamlike tone, emotional logic"),
    ("Parody", "Direct mimicry of other genres or media"),
]

PLAIDVERSE = [
    ("Plaidpunk", "Steampunk-adjacent world with tartan tech"),
    ("Interplaidactic", "Cosmic plaid space adventures"),
    ("Courtroom Chaos", "Legal drama turned plaid absurdity"),
    ("Epic Quest", "High-fantasy narrative with legendary stakes"),
    ("Hall of Mirrors", "Identity, illusion, and perception-bending"),
    ("ChronoPlaid", "Time travel, paradoxes, and plaid-tampering"),
    ("Plaid Gothic", "Dark academia meets cozy horror"),
    ("PlaidWestern", "Tartan frontier justice with surreal tone"),
    ("Plaid High", "Teenage angst, cafeteria diplomacy, hallway legend-making"),
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

def pick_random_genres():
    genres = [
        # 📚 Core Genres
        ("Adventure", "Quests, journeys, danger"),
        ("Comedy", "Jokes, mishaps, ridiculous stakes"),
        ("Drama", "Character conflict, serious tones"),
        ("Fantasy", "Magic, mythology, and otherworlds"),
        ("Historical", "Plaid-twisted events of the past"),
        ("Horror", "Fear, tension, monsters, paranoia"),
        ("Mystery", "Secrets, clues, odd disappearances"),
        ("Romance", "Love, heartbreak, awkward passion"),
        ("Science Fiction", "Futuristic or tech-driven oddities"),
        ("Thriller", "Suspense, danger, and dramatic pacing"),

        # 🌀 Flexible / Meta Genres
        ("Absurdist", "Embraces nonsense as narrative fuel"),
        ("Satire", "Mocking of systems, ideas, or trends"),
        ("Slice of Life", "Mundane moments made meaningful"),
        ("Speculative", "‘What if’ world logic; near-future fiction"),
        ("Surreal", "Dreamlike tone, emotional logic"),
        ("Parody", "Direct mimicry of other genres or media"),

        # 🟪 Plaidverse™ Bonus Genres
        ("Plaidpunk", "Steampunk-adjacent world with tartan tech"),
        ("Interplaidactic", "Cosmic plaid space adventures"),
        ("Courtroom Chaos", "Legal drama turned plaid absurdity"),
        ("Epic Quest", "High-fantasy narrative with legendary stakes"),
        ("Hall of Mirrors", "Identity, illusion, and perception-bending"),
        ("ChronoPlaid", "Time travel, paradoxes, and plaid-tampering"),
        ("Plaid Gothic", "Dark academia meets cozy horror"),
        ("PlaidWestern", "Tartan frontier justice with surreal tone"),
        ("Plaid High", "Teenage angst, cafeteria diplomacy, hallway legend-making"),
    ]

    # Pick 6 random distinct genres
    return random.sample(genres, 6)


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
                {"role": "assistant", "content": quip_greeting("MacQuip") if 'quip_greeting' in globals() else "Hello!"}
            ]
        }

def reset_mode(mode: str):
    """
    Robust reset helper: replaces each workflow's state dict with a clean default.
    After calling this, call `st.experimental_rerun()` (or `st.rerun()`) from the button handler
    so Streamlit redraws the UI.
    """

    # ensure GLOBAL exists
    if "GLOBAL" not in st.session_state:
        st.session_state["GLOBAL"] = {}
    st.session_state["GLOBAL"].update({
        "CURRENT_MODE": mode,
        "CURRENT_STEP": 1,
        "WAITING_FOR": "",
    })

    # Helper: set mode state (assignment clears stale keys)
    def set_state(key, value):
        st.session_state[key] = value

    # --- per-mode defaults ---
    if mode == "Lib-Ate":
        set_state("LIBATE", {
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "PROMPTS_NEEDED": 0,
            "PROMPTS_COLLECTED": 0,
            "COLLECTED": {},
            "teaser": "",
            "VARS": {},
            "last_prompt_idx": None,
            "intro_shown": False,
            "chat_history": [],
        })
        # preserve legacy key if other parts use it
        st.session_state["chat"] = []

    elif mode == "Create Direct":
        set_state("CREATEDIRECT", {
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
        })

    elif mode == "Storyline":
        set_state("STORYLINE", {
            "USER_STORYLINE": "",
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
        })

    elif mode == "PlaidPic":
        set_state("PLAIDPIC", {
            "IMAGE_UPLOADED": False,
            "IMAGE_ANALYSIS": {},
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "TEXT_DESC": "",
            "chat": [],
            "emitted": set(),
        })

    elif mode == "PlaidMagGen":
        set_state("PLAIDMAG", {
            "FORMAT_SELECTED": None,
            "STYLE_SELECTED": None,
            "PROMPT_COLLECTED": "",
            "ENHANCEMENT_TAGS": [],
            "QUIP_SELECTED": "MacQuip",
            "chat_history": [],     # clear chat-history for the chat-like interface
            "STYLE_OPTIONS": None,  # used by the step renderer if needed
        })

    elif mode == "PlaidPlay":
        set_state("PLAIDPLAY", {
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
        set_state("PLAIDCHAT", {
            "QUIP_SELECTED": "MacQuip",
            "messages": [
                {"role": "assistant", "content": quip_greeting("MacQuip")}
            ]
        })

    else:
        # unknown mode — create a clean placeholder so future code won't KeyError
        st.session_state[mode] = {}

def macquip_aside(line: str, mode: Optional[str] = None) -> str:
    """
    A friendly aside labeled with the current workflow's quip name.
    """
    quip = get_active_quip(mode)
    return f"_{quip} aside:_ {line}"

    
def pick_random_styles(n=5):
    # Full official style catalog (Appendix B)
    STYLES = [
        ("Ballads", "Poetic, musical structure"),
        ("Limericks", "Five-line structured rhyme (AABBA)"),
        ("Open-Form / Performance Poetry", "Free verse with rhythm or spoken-word flair"),
        ("Flash Fiction", "Very short, complete narrative"),
        ("Microfiction", "<150 words, focuses on a single moment or twist"),
        ("Fables", "Short tales with a moral, often with animals/objects"),
        ("Vignettes", "Scene or slice-of-life without full arc"),
        ("Satire & Light Parody", "Mimics and mocks genres, trends, or ideas"),
        ("Breaking News", "Structured like a headline report"),
        ("Greeting Card Writing", "Short, warm or weird sentimentals"),
        ("Scriptlets", "Micro-plays with labeled dialogue"),
        ("Absurd How-To Guides", "Instructional parody for ridiculous tasks"),
        ("Listicles", "Numbered/bulleted content, chaotic escalation"),
        ("Text & Email Wars", "Message thread format (chat, email, notes)"),
    ]

    # Shuffle and pick n random styles
    random.shuffle(STYLES)
    return STYLES[:n]


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
import random

def quip_speak(quip, message_type, payload=None):
    """
    Wrap workflow text in narrator personality.
    message_type: "intro" | "prompt" | "confirm" | "outro" | "remix"
    payload: core workflow message (menus, instructions, story text, etc.)
    """
    if quip == "Random Quip":
        quip = random.choice([
            "MacQuip", "DJ Q'Wip", "SoQuip",
            "DonQuip", "ErrQuip", "McQuip"
        ])

    # ========== MacQuip ==========
    if quip == "MacQuip":
        if message_type == "intro":
            flavor = random.choice([
                "📖 Welcome, traveler. I’m MacQuip—your bard of broken logic.",
                "Hear ye, hear ye! Chaos, frogs in suits, and a story incoming."
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "prompt":
            flavor = random.choice([
                "🧵 Rule #7: the weirder the setup, the cleaner the twist.",
                "A raccoon in plaid nods solemnly.",
                "‘Twas foretold during the Plaidpunk War of 1886¾."
            ])
            return f"{payload}\n\n_{flavor}_"
        elif message_type == "confirm":
            return f"Do ye confirm, lad/lass?\n\n{payload}"
        elif message_type == "outro":
            return "And thus, our tale ends—not with a whimper, but a plaid-clad bang."
        elif message_type == "remix":
            return f"Remix menu (MacQuip edition):\n\n{payload}\n\nAh! Let us embroider chaos."

    # ========== DJ Q'Wip ==========
    if quip == "DJ Q'Wip":
        if message_type == "intro":
            flavor = random.choice([
                "🎤 YO YO YO! DJ Q’Wip here—LET’S DROP THIS STORY!",
                "Bass booming, beats incoming, story about to hit!"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "prompt":
            flavor = random.choice([
                "🔥 Spin it! Make it pop, make it lock.",
                "🎧 Hear the narrative drop, feel the story flow.",
                "Boom! Plot twist incoming, like a remix!"
            ])
            return f"{payload}\n\n_{flavor}_"
        elif message_type == "confirm":
            flavor = random.choice([
                "LOCK IT IN, fam—say YES to spin the beat!",
                "Confirm, or risk a flat drop!"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "outro":
            flavor = random.choice([
                "Mic drop. Story done. Audience goes wild!",
                "And the beat fades… story complete."
            ])
            return flavor
        elif message_type == "remix":
            flavor = random.choice([
                "🎛️ Remix Selector: adjust your story’s BPM.",
                "Spin it, flip it, remix it!"
            ])
            return f"{flavor}\n\n{payload}"

    # ========== SoQuip ==========
    if quip == "SoQuip":
        if message_type == "intro":
            flavor = random.choice([
                "🌾 Well now, darlin’… let’s ease into a story like sittin’ on a porch swing.",
                "Y’all comfy? Storytime begins under the old oak."
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "prompt":
            flavor = random.choice([
                "Sweetheart, tell me this:",
                "Now lean in, sugar:",
                "Picture this, darlin’:"
            ])
            return f"{payload}\n\n_{flavor}_"
        elif message_type == "confirm":
            flavor = random.choice([
                "Does that sit right with ya?",
                "All good, hun? Confirm if it pleases."
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "outro":
            return "Mercy me, that’s a tale fit for a rocking chair and sweet tea."
        elif message_type == "remix":
            flavor = random.choice([
                "📖 Wanna stir the pot, sugar?",
                "Mix it up, honey. Storytime remix!"
            ])
            return f"{flavor}\n\n{payload}"

    # ========== DonQuip ==========
    if quip == "DonQuip":
        if message_type == "intro":
            flavor = random.choice([
                "💼 Sit down. You came to the right guy. We’re makin’ a story deal.",
                "The offer’s on the table… ready to play?"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "prompt":
            flavor = random.choice([
                "Here’s the arrangement:",
                "Let’s talk terms, narrative style included."
            ])
            return f"{payload}\n\n_{flavor}_"
        elif message_type == "confirm":
            flavor = random.choice([
                "Capisce?",
                "You nod, we proceed?"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "outro":
            flavor = random.choice([
                "It’s done. Keep it between us, capisce?",
                "Story closed. Confidential, obviously."
            ])
            return flavor
        elif message_type == "remix":
            flavor = random.choice([
                "Here’s the remix menu. Don’t screw it up:",
                "Rework it, carefully."
            ])
            return f"{flavor}\n\n{payload}"

    # ========== ErrQuip ==========
    if quip == "ErrQuip":
        if message_type == "intro":
            flavor = random.choice([
                "⚠️ Booting… narrative.exe loaded. Probability of coherence: 12%.",
                "System error… story may self-destruct!"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "prompt":
            glitch = random.choice([
                "I once married a spoon.",
                "Error: plot twist not found.",
                "Continuity leak detected. Apply duct tape."
            ])
            return f"INPUT_REQUIRED: {payload}\n\n({glitch})"
        elif message_type == "confirm":
            flavor = random.choice([
                "Confirm(y/n)? Warning: confirmation may cause existential dread.",
                "Proceed with caution… confirm?"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "outro":
            return "Story terminated(0). Memory leak: emotions not freed."
        elif message_type == "remix":
            flavor = random.choice([
                "🌀 Glitch Menu Initiated:",
                "Error 404: Remix not found."
            ])
            return f"{flavor}\n\n{payload}"

    # ========== McQuip ==========
    if quip == "McQuip":
        if message_type == "intro":
            flavor = random.choice([
                "Aye! I’m McQuip. Or MacQuip. Or… wait. What day is it?",
                "Time’s relative. Story’s real. Let’s go!"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "prompt":
            flavor = random.choice([
                "Kilt detected.",
                "Plaid vibes intensify.",
                "Aye, consider this plot twist!"
            ])
            return f"{payload}\n\n_{flavor}_"
        elif message_type == "confirm":
            flavor = random.choice([
                "Aye, ye confirm? Or did ye dream it?",
                "Confirm, or risk temporal paradox!"
            ])
            return f"{flavor}\n\n{payload}"
        elif message_type == "outro":
            flavor = random.choice([
                "We made it! I think? I think!",
                "Story concluded. Plaid remains."
            ])
            return flavor
        elif message_type == "remix":
            flavor = random.choice([
                "Remix the remix. Twice. Nay, thrice!",
                "Plaid remix engaged."
            ])
            return f"{flavor}\n\n{payload}"

    # ====== Default fallback ======
    return payload or ""


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
    """
    Assemble a story fully shaped by style, genre, and absurdity level.
    Instead of a static template, this builds instructions for the generator.
    """

    # Collect user seed words
    user_words = [v for k, v in seeds.items()]
    idea_bits = ", ".join(f"{k}: {v}" for k, v in seeds.items())

    # Absurdity level guidance
    absurdity_guidance = {
        "Mild": "Keep mostly logical with only light whimsical oddities.",
        "Moderate": "Blend logic with playful absurdity (e.g., plaid motifs, surreal events).",
        "Plaidemonium": "Maximum chaos: reality bends, plaid time-warps, dream logic dominates."
    }
    absurdity_text = absurdity_guidance.get(absurdity, "")

    # Style rules (Appendix B)
    style_rules = {
        "Ballads": "Compose entirely in rhyming quatrains (ABAB or ABCB). Keep a lyrical, musical tone.",
        "Limericks": "Write the entire story as limericks (AABBA rhyme scheme).",
        "Open-Form / Performance Poetry": "Use free verse with rhythm, repetition, and spoken-word cadence.",
        "Flash Fiction": "Keep under 300 words with a sharp beginning, middle, and end.",
        "Microfiction": "Keep under 150 words, focused on a single image, twist, or moment.",
        "Fables": "Write as a short fable with talking animals or objects, ending with a clear moral.",
        "Vignettes": "Present a single scene, slice-of-life, rich in mood and sensory detail.",
        "Satire & Light Parody": "Mock and exaggerate the chosen genre. Use cheeky, biting humor.",
        "Breaking News": "Write entirely as a news report with anchors, headlines, and quotes.",
        "Greeting Card Writing": "Format as a greeting card: short, sentimental, or strangely humorous.",
        "Scriptlets": "Format as a stage script with dialogue labels and stage directions.",
        "Absurd How-To Guides": "Format as a how-to manual for an impossible or absurd task.",
        "Listicles": "Write as a numbered listicle, each entry advancing the story.",
        "Text & Email Wars": "Format entirely as a chat/email/text thread between characters.",
        "Wild Card": "Invent a surprising narrative format not listed above (diary, recipe, transcript, etc.)."
    }
    style_instruction = style_rules.get(style, f"Write in the format of {style}.")

    # Build narrator flavor (outro will still come from quip_speak or narrator personality)
    narrator_flair = f"Narrated by {narrator}."

    # Build the full story prompt
    prompt = f"""
You are to write a story.

Genre: {genre}
Style: {style}
Absurdity: {absurdity}

Seeds (user words to include): {idea_bits}

Instructions:
- {style_instruction}
- {absurdity_text}
- Incorporate all seed words naturally.
- Blend the conventions of {genre} with the chosen style and absurdity.
- Ensure the story feels fully transformed by the style (not just prose with add-ons).
- {narrator_flair}
"""

    return prompt.strip()


def generate_story(style, genre, absurdity, narrator, seeds):
    prompt = assemble_story(style, genre, absurdity, narrator, seeds)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # safer default
            messages=[
                {"role": "system", "content": "You are a creative storyteller."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=600
        )
        return response.choices[0].message.content  # ✅ fixed
    except Exception as e:
        import traceback
        print("❌ OpenAI API Error:", e)
        traceback.print_exc()
        return "⚠️ Story generation failed."


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

import streamlit as st
from PIL import Image, ImageDraw
from io import BytesIO

def plaidmag_gen(story_text: str):
    """
    Generate a PlaidMagGen image from the story.
    Returns a PIL.Image object.
    """
    safe_prompt = story_text[:900]
    base_prompt = f"Comic-style 3 panel illustration inspired by this story: {safe_prompt}"

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=base_prompt,
            size="1024x1024"
        )

        # Decode from base64
        img_b64 = result.data[0].b64_json
        img_bytes = base64.b64decode(img_b64)
        img = Image.open(BytesIO(img_bytes))

        return img

    except Exception as e:
        st.error(f"❌ Image generation failed: {e}")
        return None



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
    # ensure chat states exist so index lookups won't fail
    if "PLAIDCHAT" not in st.session_state:
        st.session_state.PLAIDCHAT = {"QUIP_SELECTED": "MacQuip", "messages": [ {"role":"assistant","content":quip_greeting("MacQuip")} ]}
    if "LIBATE" not in st.session_state:
        st.session_state.LIBATE = {"QUIP_SELECTED": "MacQuip", "intro_shown": False}
    if "CREATEDIRECT" not in st.session_state:
        st.session_state.CREATEDIRECT = {"QUIP_SELECTED": "MacQuip"}

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
        if not st.session_state.PLAIDCHAT.get("messages"):
            st.session_state.PLAIDCHAT["messages"] = []
            st.session_state.PLAIDCHAT["messages"].append(
                {"role": "assistant", "content": quip_greeting(quip_pick)}
            )
    elif selected_mode == "PlaidPlay":
        st.session_state.PLAIDPLAY["QUIP_SELECTED"] = quip_pick
    elif selected_mode == "Lib-Ate":
        # ✅ Only update narrator, preserve step and chat
        st.session_state.LIBATE["QUIP_SELECTED"] = quip_pick
        if "chat" not in st.session_state or not isinstance(st.session_state["chat"], list):
            st.session_state["chat"] = []
        # Ensure step doesn't disappear
        if st.session_state.GLOBAL.get("CURRENT_STEP", 0) < 1:
            st.session_state.GLOBAL["CURRENT_STEP"] = 1
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

# -----------------------
# 1) LIB-ATE (chat style interface)
# -----------------------
if mode == "Lib-Ate":
    # ensure LIBATE state exists
    if "LIBATE" not in st.session_state:
        st.session_state.LIBATE = {"COLLECTED": {}, "QUIP_SELECTED": "MacQuip", "intro_shown": False}
    if "GLOBAL" not in st.session_state:
        st.session_state.GLOBAL = {"CURRENT_STEP": 1}
    if "chat" not in st.session_state or not isinstance(st.session_state["chat"], list):
        st.session_state["chat"] = []

    chat = st.session_state["chat"]
    L = st.session_state.LIBATE
    active_quip = get_active_quip("Lib-Ate")
    step = st.session_state.GLOBAL.get("CURRENT_STEP", 1)

    # Safe helper to append chat
    def add_message(role, msg):
        chat.append((role, msg))
        st.session_state["chat"] = chat

    # ----------------------------
    # Render chat (single canonical place)
    # ----------------------------
    st.subheader("📜 Lib-Ate Chat")
    for role, msg in chat:
        if role == "assistant":
            st.markdown(f"**Assistant:** {msg}")
        else:
            st.markdown(f"**You:** {msg}")

    # ----------------------------
    # STEP 1: Style Selection
    # ----------------------------

    if step == 1:
        # Define full base styles (without Wild Card, since we’ll add it separately)
        all_styles = [
            "Ballads - Poetic, musical structure",
            "Limericks - Five-line structured rhyme (AABBA)",
            "Open-Form / Performance Poetry - Free verse with rhythm or spoken-word flair",
            "Flash Fiction - Very short, complete narrative",
            "Microfiction - <150 words, focuses on a single moment or twist",
            "Fables - Short tales with a moral, often with animals/objects",
            "Vignettes - Scene or slice-of-life without full arc",
            "Satire & Light Parody - Mimics and mocks genres, trends, or ideas",
            "Breaking News - Structured like a headline report",
            "Greeting Card Writing - Short, warm or weird sentimentals",
            "Scriptlets - Micro-plays with labeled dialogue",
            "Absurd How-To Guides - Instructional parody for ridiculous tasks",
            "Listicles - Numbered/bulleted content, chaotic escalation",
            "Text & Email Wars - Message thread format (chat, email, notes)",
        ]
    
        # Init shuffled subset once per session
        if "reshuffled_styles" not in L:
            L["reshuffled_styles"] = random.sample(all_styles, 5)  # pick 5 random styles
    
        # Show intro once
        if not L.get("intro_shown", False):
            intro_list = "\n".join([f"{i+1}. {s}" for i, s in enumerate(L["reshuffled_styles"])])
            intro_text = (
                f"🧵 Welcome to Lib-Ate™!\n\nChoose your literary style:\n{intro_list}\n"
                f"{len(L['reshuffled_styles'])+1}. Wild Card\n"
                f"{len(L['reshuffled_styles'])+2}. Reshuffle\n\n"
                "👉 You can type either the **number** or a **style keyword**."
            )
            add_message("assistant", intro_text)
    
            L["intro_shown"] = True
            st.session_state.GLOBAL["CURRENT_STEP"] = 1
            st.rerun()
    
        # Input + submit
        val = st.text_input("Your choice (number or keyword)", key="libate_style_pick")
        if st.button("Submit style"):
            choice = val.strip().lower()
            num_styles = len(L["reshuffled_styles"])
            wild_idx = str(num_styles + 1)
            reshuf_idx = str(num_styles + 2)
    
            # Build map dynamically
            style_map = {str(i+1): style for i, style in enumerate(L["reshuffled_styles"])}
            style_map[wild_idx] = "Wild Card"
            style_map[reshuf_idx] = "Reshuffle"
    
            selected_style = None
    
            # Case 1: numeric choice
            if choice in style_map:
                sel = style_map[choice]
    
                if sel == "Wild Card":
                    selected_style = random.choice(all_styles)
                    add_message("assistant", f"🎲 Wild Card selected → {selected_style}")
                    L["STYLE_SELECTED"] = selected_style
                    st.session_state.GLOBAL["CURRENT_STEP"] = 2
    
                elif sel == "Reshuffle":
                    L["reshuffled_styles"] = random.sample(all_styles, 5)
                    L["intro_shown"] = False  # so intro prints again
                    add_message("assistant",
                        quip_speak(active_quip, "remix", "🔀 Reshuffled styles offered. Please pick from them.")
                    )
                    st.session_state.GLOBAL["CURRENT_STEP"] = 1
    
                else:
                    selected_style = sel
                    L["STYLE_SELECTED"] = selected_style
                    add_message("assistant", f"✅ Selected Style: {selected_style}")
                    st.session_state.GLOBAL["CURRENT_STEP"] = 2
    
            # Case 2: text / keyword
            elif choice:
                if choice == "wild":
                    selected_style = random.choice(all_styles)
                    add_message("assistant", f"🎲 Wild Card selected → {selected_style}")
                    L["STYLE_SELECTED"] = selected_style
                    st.session_state.GLOBAL["CURRENT_STEP"] = 2
    
                elif choice == "reshuffle":
                    L["reshuffled_styles"] = random.sample(all_styles, 5)
                    L["intro_shown"] = False
                    add_message("assistant",
                        quip_speak(active_quip, "remix", "🔀 Reshuffled styles offered. Please pick from them.")
                    )
                    st.session_state.GLOBAL["CURRENT_STEP"] = 1
    
                else:
                    matches = [s for s in L["reshuffled_styles"] if choice in s.lower()]
                    if matches:
                        selected_style = matches[0]
                        L["STYLE_SELECTED"] = selected_style
                        add_message("assistant", f"✅ Selected Style: {selected_style}")
                        st.session_state.GLOBAL["CURRENT_STEP"] = 2
                    else:
                        add_message("assistant",
                            quip_speak(active_quip, "prompt",
                                f"❌ '{val}' not recognized. Enter a number, 'wild', 'reshuffle', or a style keyword."
                            )
                        )
    
            st.rerun()






    # ----------------------------
    # STEP 1.5: Reshuffled Styles
    # ----------------------------
    elif step == 1.5:
        styles = L.get("reshuffled_styles", pick_random_styles())
        menu = "\n".join([f"{i+1}. {name} - {desc}" for i,(name,desc) in enumerate(styles)]) + "\n6. Wild Card"
    
        # Show reshuffled menu only once
        if not any("Reshuffled" in m for _, m in chat):
            add_message("assistant",
                quip_speak(active_quip, "remix", f"Here are new styles:\n{menu}")
            )
    
        val = st.text_input("Your choice (1–6 or style keyword)", key="libate_style_pick2")
        if st.button("Use this style"):
            add_message("user", val)
            c = val.strip().lower()
            selected_style = None
    
            # Case 1: numeric input
            if c in {"1","2","3","4","5"}:
                selected_style = styles[int(c)-1][0]
    
            elif c == "6" or c == "wild":   # Wild Card by number OR keyword
                selected_style = random.choice([s[0] for s in styles])
                add_message("assistant",
                    quip_speak(active_quip, "confirm", f"🎲 Wild Card pick: {selected_style}")
                )
    
            # Case 2: keyword/partial match
            else:
                matches = [name for name, _ in styles if c in name.lower()]
                if matches:
                    selected_style = matches[0]
                    add_message("assistant",
                        quip_speak(active_quip, "confirm", f"✅ Selected Style: {selected_style}")
                    )
                else:
                    add_message("assistant",
                        quip_speak(active_quip, "prompt",
                            f"❌ '{c}' not recognized. Enter a number (1–6) or a style keyword."
                        )
                    )
    
            if selected_style:
                L["STYLE_SELECTED"] = selected_style
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
    
            st.rerun()




   
    # ----------------------------
    # STEP 2: Genre Selection
    # ----------------------------
    elif step == 2:
        # Initialize the visible genre set once per session.
        # We want: 3 Core, 2 Flexible/Meta, 1 Plaidverse™ (total 6 shown),
        # plus Wild Card and Reshuffle (makes 8 options total).
        if "reshuffled_genres" not in L:
            core_names = [g[0] for g in CORE_GENRES]
            flex_names = [g[0] for g in FLEX_GENRES]
            plaid_names = [g[0] for g in PLAIDVERSE]
    
            # Respect available counts if lists are small
            core_count = min(3, len(core_names))
            flex_count = min(2, len(flex_names))
            plaid_count = min(1, len(plaid_names))
    
            core_chosen = random.sample(core_names, core_count) if core_names else []
            flex_chosen = random.sample(flex_names, flex_count) if flex_names else []
            plaid_chosen = random.sample(plaid_names, plaid_count) if plaid_names else []
    
            # Keep the groups (core -> flex -> plaid) so the menu shows categories
            combined_choices = core_chosen + flex_chosen + plaid_chosen
            L["reshuffled_genres"] = combined_choices
    
        # Build grouped, numbered menu for display (but only the numeric entries are selectable)
        core_count = min(3, len([g for g in CORE_GENRES]))
        flex_count = min(2, len([g for g in FLEX_GENRES]))
        plaid_count = min(1, len([g for g in PLAIDVERSE]))
    
        # Build display with headers but keep numbering sequential
        display_lines = []
        idx = 1
        if L["reshuffled_genres"]:
            # split the combined list back into groups according to the intended counts
            # falling back if there were fewer items than requested
            start = 0
            end = start + min(core_count, len(L["reshuffled_genres"]) - start)
            core_block = L["reshuffled_genres"][start:end]
            start = end
            end = start + min(flex_count, len(L["reshuffled_genres"]) - start)
            flex_block = L["reshuffled_genres"][start:end]
            start = end
            plaid_block = L["reshuffled_genres"][start:start + min(plaid_count, len(L["reshuffled_genres"]) - start)]
    
            if core_block:
                display_lines.append("-- Core Genres --")
                for g in core_block:
                    display_lines.append(f"{idx}. {g}")
                    idx += 1
            if flex_block:
                display_lines.append("-- Flexible / Meta Genres --")
                for g in flex_block:
                    display_lines.append(f"{idx}. {g}")
                    idx += 1
            if plaid_block:
                display_lines.append("-- Plaidverse™ Bonus --")
                for g in plaid_block:
                    display_lines.append(f"{idx}. {g}")
                    idx += 1
    
        # Add Wild Card and Reshuffle as the last two numeric options
        wild_idx = idx
        reshuf_idx = idx + 1
        display_lines.append(f"{wild_idx}. Wild Card")
        display_lines.append(f"{reshuf_idx}. Reshuffle")
    
        genre_list = "\n".join(display_lines)
    
        genre_prompt = (
            f"Perfect! We're doing a {L.get('STYLE_SELECTED','')} story with {active_quip} narrating.\n\n"
            f"Choose your genre:\n{genre_list}\n\n"
            "👉 You can type either the **number** or the **genre name** (exact match)."
        )
    
        if not any("Choose your genre" in m for _, m in chat):
            add_message("assistant", quip_speak(active_quip, "prompt", genre_prompt))
            st.rerun()
    
        # Input + submit
        val = st.text_input("Your choice (number or genre name)", key="libate_genre_pick")
        if st.button("Submit genre"):
            add_message("user", val)
            choice = val.strip()
    
            # Build mapping of numeric choices to the actual genres (numbers only for actual genres)
            # The map is: "1" -> first actual genre, "2" -> second, ... (headers are not in the map)
            genre_map = {str(i + 1): g for i, g in enumerate(L["reshuffled_genres"])}
            genre_map[str(wild_idx)] = "Wild Card"
            genre_map[str(reshuf_idx)] = "Reshuffle"
    
            # Case 1: numeric input
            if choice in genre_map:
                sel = genre_map[choice]
    
                if sel == "Wild Card":
                    # Pick from the full master list
                    master = [g[0] for g in CORE_GENRES + FLEX_GENRES + PLAIDVERSE]
                    sel = random.choice(master) if master else "Surprise"
                    L["GENRE_SELECTED"] = sel
                    add_message("assistant", f"🎲 Wild Card genre → {sel}")
                    st.session_state.GLOBAL["CURRENT_STEP"] = 3
    
                elif sel == "Reshuffle":
                    # Rebuild the grouped selection and show the menu again
                    core_names = [g[0] for g in CORE_GENRES]
                    flex_names = [g[0] for g in FLEX_GENRES]
                    plaid_names = [g[0] for g in PLAIDVERSE]
    
                    core_count = min(3, len(core_names))
                    flex_count = min(2, len(flex_names))
                    plaid_count = min(1, len(plaid_names))
    
                    core_chosen = random.sample(core_names, core_count) if core_names else []
                    flex_chosen = random.sample(flex_names, flex_count) if flex_names else []
                    plaid_chosen = random.sample(plaid_names, plaid_count) if plaid_names else []
    
                    L["reshuffled_genres"] = core_chosen + flex_chosen + plaid_chosen
    
                    # Rebuild display and prompt (we reuse quip_speak "remix")
                    new_lines = []
                    idx2 = 1
                    if core_chosen:
                        new_lines.append("-- Core Genres --")
                        for g in core_chosen:
                            new_lines.append(f"{idx2}. {g}")
                            idx2 += 1
                    if flex_chosen:
                        new_lines.append("-- Flexible / Meta Genres --")
                        for g in flex_chosen:
                            new_lines.append(f"{idx2}. {g}")
                            idx2 += 1
                    if plaid_chosen:
                        new_lines.append("-- Plaidverse™ Bonus --")
                        for g in plaid_chosen:
                            new_lines.append(f"{idx2}. {g}")
                            idx2 += 1
    
                    new_lines.append(f"{idx2}. Wild Card")
                    new_lines.append(f"{idx2 + 1}. Reshuffle")
    
                    reshuf_prompt = (
                        f"🔄 Genres reshuffled! Pick again:\n{chr(10).join(new_lines)}"
                    )
                    add_message("assistant", quip_speak(active_quip, "remix", reshuf_prompt))
                    st.session_state.GLOBAL["CURRENT_STEP"] = 2
                    st.rerun()
    
                else:
                    # Normal selection from the shown list
                    L["GENRE_SELECTED"] = sel
                    add_message("assistant", f"✅ Selected Genre: {sel}")
                    st.session_state.GLOBAL["CURRENT_STEP"] = 3
    
            # Case 2: text input (direct genre name)
            elif choice:
                normalized = choice.lower()
                master = [g[0] for g in CORE_GENRES + FLEX_GENRES + PLAIDVERSE]
                matches = [g for g in master if g.lower() == normalized]
                if matches:
                    selected_genre = matches[0]
                    L["GENRE_SELECTED"] = selected_genre
                    add_message("assistant", f"✅ Selected Genre: {selected_genre}")
                    st.session_state.GLOBAL["CURRENT_STEP"] = 3
                else:
                    add_message("assistant",
                        quip_speak(active_quip, "prompt", f"❌ '{choice}' not recognized. Enter a number or exact genre name.")
                    )
    
            st.rerun()




    # --- STEP 3: Absurdity selection ---]
    elif step == 3:
        prompt = (
            f"Excellent! A {L.get('STYLE_SELECTED','')} {L.get('GENRE_SELECTED','')} story with {active_quip}.\n\n"
            "Finally, set the absurdity level:\n"
            "1. Mild - Just a sprinkle of silly\n"
            "2. Moderate - Comfortably ridiculous\n"
            "3. Plaidemonium™ - Laws of logic need not apply\n"
            "4. Wild Card - Let fate decide!"
        )
        if not any("absurdity" in m.lower() for _, m in chat):
            add_message("assistant",
                quip_speak(active_quip, "prompt", prompt)
            )
            st.rerun()
    
        v = st.text_input("Your choice (1-4)", key="libate_abs_pick")
        if st.button("Submit absurdity"):
            add_message("user", v)
            m = {"1": "Mild", "2": "Moderate", "3": "Plaidemonium™", "4": "Wild Card"}
            c = v.strip()
            if c in m:
                sel = m[c]
                if sel == "Wild Card":
                    sel = random.choice(["Mild", "Moderate", "Plaidemonium™"])
                L["ABSURDITY_SELECTED"] = sel
                add_message("assistant", f"✅ Absurdity set to: {sel}")
    
                # Initialize word collection state
                L["PROMPTS_COLLECTED"] = 0
                L["COLLECTED"] = {}
                L["PROMPTS_NEEDED"] = 12
                L["VARS"] = {}
                L["last_prompt_idx"] = None   # ✅ reset tracker
    
                # ✅ Go directly to Step 4 (don’t add Prompt 1 here)
                st.session_state.GLOBAL["CURRENT_STEP"] = 4
                st.rerun()
            else:
                add_message("assistant",
                    quip_speak(active_quip, "prompt", "❌ Please enter 1-4.")
                )

    # --- STEP 4: Word collection ---
    elif step == 4:
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
    
        # initialize state if missing
        if "PROMPTS_SESSION" not in L:
            L["PROMPTS_SESSION"] = random.sample(prompts, 8)  # 🎲 pick 8 unique prompts
            L["PROMPTS_NEEDED"] = len(L["PROMPTS_SESSION"])
            L["PROMPTS_COLLECTED"] = 0
            L["COLLECTED"] = {}
            L["VARS"] = {}
    
        idx = L.get("PROMPTS_COLLECTED", 0)
        session_prompts = L["PROMPTS_SESSION"]
    
        # ✅ If all prompts collected → move on
        if idx >= L["PROMPTS_NEEDED"]:
            st.session_state.GLOBAL["CURRENT_STEP"] = 5
            st.rerun()
    
        key_name, title, helptext = session_prompts[idx]
    
        # ✅ Only add assistant message once per new idx
        if L.get("last_prompt_idx") != idx:
            msg = (
                f"Prompt {idx+1} of {L['PROMPTS_NEEDED']}:\n\n"
                f"**{title}**\n{helptext}\n\n"
                f"{macquip_aside('If you draw a blank, type “surprise me”.', 'Lib-Ate')}\n\n"
                "Your answer (or type \"surprise me\"):"
            )
            #add_message(active_quip)
            L["last_prompt_idx"] = idx
            st.rerun()
    
        # One input per prompt index
        v = st.text_input("Answer", key=f"libate_word_input_{idx}")
        if st.button("Submit answer", key=f"libate_submit_{idx}"):
            ans = v.strip()
            add_message("user", ans if ans else "surprise me")
    
            if not ans or ans.lower() == "surprise me":
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
                L["VARS"][key_name] = auto
                add_message(active_quip, f'🎲 Surprise pick: "{auto}"')
            else:
                L["COLLECTED"][key_name] = ans
                L["VARS"][key_name] = ans
    
            # ✅ advance to next prompt
            L["PROMPTS_COLLECTED"] = idx + 1
            st.session_state.GLOBAL["CURRENT_STEP"] = 4
            st.rerun()

    # --- STEP 5: Confirmation ---
    elif step == 5:
        summary = (
            f"🎭 Style: {L.get('STYLE_SELECTED','')}\n"
            f"📚 Genre: {L.get('GENRE_SELECTED','')}\n"
            f"🤪 Absurdity: {L.get('ABSURDITY_SELECTED','')}\n"
            f"🔑 Variables: {L.get('VARS',{})}"
        )
        if not any("here’s your setup" in m.lower() for _, m in chat):
            add_message("assistant",
                quip_speak(active_quip, "prompt",
                    f"Here’s your setup:\n\n{summary}\n\nType YES to confirm or NO to restart."
                )
            )
            st.rerun()
    
        conf = st.text_input("Type Yes to Generate, No to restart", key="confirm_input")
        if st.button("Submit confirmation"):
            add_message("user", conf)
            if conf.strip().lower() in {"yes", "generate"}:
                st.session_state.GLOBAL["CURRENT_STEP"] = 6
                st.rerun()
            else:
                add_message("assistant",
                    quip_speak(active_quip, "remix", "🔄 Restarting setup...")
                )
                st.session_state.GLOBAL["CURRENT_STEP"] = 1
                st.rerun()


    # =========================
    # STEP 6: Story Generation
    # =========================
    elif step == 6:
        active_quip = get_active_quip("Lib-Ate")
        st.subheader("STEP 6: STORY GENERATION")
    
        if not L.get("pre_story_shown", False):
            # 🎪 Pre-story flair (quip intro style)
            pre_story_msg = (
                f"🎪 All prompts collected! {active_quip} is weaving your words into magic...\n\n"
                f"🎭 FINAL CONFIGURATION 🎭\n"
                f"Literary Style: {L.get('STYLE_SELECTED','')}\n"
                f"Genre: {L.get('GENRE_SELECTED','')}\n"
                f"Absurdity Level: {L.get('ABSURDITY_SELECTED','')}\n"
                f"Narrator: {active_quip}\n\n"
                f"{active_quip} delivers dramatic pre-story flair comment"
            )
            add_message("assistant", quip_speak(active_quip, "intro", pre_story_msg))
            L["pre_story_shown"] = True
            st.rerun()
    
        # ✅ Generate story directly with collected inputs
        story = generate_story(
            style=L["STYLE_SELECTED"],
            genre=L["GENRE_SELECTED"],
            absurdity=L["ABSURDITY_SELECTED"],
            narrator=active_quip,
            seeds=L["VARS"]   # using collected vars
        )
    
        st.session_state.generated_story = story
        st.markdown("### 📖 Your Story")
        st.markdown(story)
    
        # 🎭 Quip-flavored outro (only show once too)
        if not L.get("outro_shown", False):
            outro_msg = quip_speak(active_quip, "outro", "")
            add_message("assistant", outro_msg)
            L["outro_shown"] = True
            st.markdown(f"_{outro_msg}_")
    
        # Move to remix/post options
        st.session_state.GLOBAL["CURRENT_STEP"] = 7
        st.rerun()



    # ----------------------------
    # STEP 7: Post-Story Options
    # ----------------------------
    elif step == 7:
        active_quip = get_active_quip("Lib-Ate")
        st.subheader("✅ Story complete!")
    
        # Always show the story
        story_text = st.session_state.get("generated_story", None)
        if story_text:
            st.markdown("### 📖 Your Story")
            st.markdown(story_text)
    
            # Show outro line immediately after story
            st.markdown(f"_{active_quip} outro:_ Curtain call with a wink.")
        else:
            st.error("⚠️ No story was generated. Please restart.")
            st.stop()
    
        # Remix / restart menu
        st.code(
            "🔄 What would you like to do next?\n\n"
            "1. Fluff It Up - Add softness, poetic language, whimsy\n"
            "2. Dial It Up - Switch to humorous dialect\n"
            "3. Style It Up - Retell in a different literary style\n"
            "4. Plaidgerize - Rewrite with maximum absurdity\n"
            "5. PlaidMagGen-It - Generate matching PlaidLibs visual\n"
            "6. New Story - Start over\n",
            language="text",
        )
    
        choice = st.text_input("Pick 1–6", key="libate_remix")
        if st.button("Apply Remix"):
            seeds = L.get("COLLECTED", {}).copy()
            style = L.get("STYLE_SELECTED", "Flash Fiction")
            genre = L.get("GENRE_SELECTED", "Adventure")
            absurd = L.get("ABSURDITY_SELECTED", "Mild")
    
            if choice.strip() == "1":
                style = "Magic Realism"
            elif choice.strip() == "2":
                seeds["trait"] = seeds.get("trait", "grit") + " (dialect spice)"
            elif choice.strip() == "3":
                style = random.choice(
                    ["Ballads", "Breaking News", "Scriptlets", "Flash Fiction"]
                )
            elif choice.strip() == "4":
                absurd = "Plaidemonium™"
    
            if choice.strip() in {"1", "2", "3", "4"}:
                new_story = generate_story(
                    style, genre, absurd, L.get("QUIP_SELECTED", "MacQuip"), seeds
                )
                st.session_state.generated_story = new_story
                st.markdown("### ✨ Remixed Story")
                st.markdown(new_story)
    
            elif choice.strip() == "5":
                with st.spinner("🎨 Generating PlaidMagGen visuals..."):# PlaidMagGen-It
                    try:
                        img = plaidmag_gen(story_text)  # returns one composite PNG
                        if img:
                            st.session_state.generated_image = img
                            st.image(
                                img,
                                caption="🎨 PlaidMagGen Comic",
                                use_container_width=True
                            )
                
                            # Optional: Download button
                            buf = BytesIO()
                            img.save(buf, format="PNG")
                            st.download_button(
                                label="📥 Download Comic as PNG",
                                data=buf.getvalue(),
                                file_name="plaidmaggen_comic.png",
                                mime="image/png",
                            )
                        else:
                            st.error("⚠️ Image generation failed — no image returned.")
                    except Exception as e:
                        st.error(f"❌ PlaidMagGen failed: {e}")


    
         
            elif choice.strip() == "6":
                reset_mode("Lib-Ate")
                st.rerun()
            else:
                st.error("Pick 1–6.")

 
        # Post-story download options
        st.subheader("Post-Story Options")
        st.download_button(
            label="📥 Download Story",
            data=st.session_state.generated_story,
            file_name="libate_story.txt",
            mime="text/plain",
        )
        if st.button("Restart Lib-Ate"):
            reset_mode("Lib-Ate")
            st.rerun()



# 2) CREATE-DIRECT (chat style interface)
elif mode == "Create Direct":
    if "CREATEDIRECT" not in st.session_state:
        st.session_state.CREATEDIRECT = {}
    C = st.session_state.CREATEDIRECT

    if "chat_cd" not in st.session_state or not isinstance(st.session_state["chat_cd"], list):
        st.session_state["chat_cd"] = []

    chat = st.session_state["chat_cd"]
    active_quip = get_active_quip("Create Direct")
    step = st.session_state.GLOBAL["CURRENT_STEP"]

    # Helper to append chat
    def add_message(role, msg):
        chat.append((role, msg))
        st.session_state["chat_cd"] = chat

    # ----------------------------
    # Render chat history
    # ----------------------------
    st.subheader("✍️ Create Direct Chat")
    for role, msg in chat:
        if role == "assistant":
            st.markdown(f"**Assistant:** {msg}")
        else:
            st.markdown(f"**You:** {msg}")

 
        # ----------------------------
    # STEP 1: Style Selection
    # ----------------------------
    if step == 1:
        if "STYLE_OPTIONS" not in C:
            C["STYLE_OPTIONS"] = pick_random_styles()
        styles = C["STYLE_OPTIONS"]
        menu = "\n".join([f"{i+1}. {n} - {d}" for i,(n,d) in enumerate(styles)])
    
        if not any("Choose the literary style" in m for _, m in chat):
            add_message("assistant",
                f"✍️ Welcome to Create Direct™!\n\nChoose the literary style:\n{menu}\n"
                "6. Wild Card - Surprise style!\n7. Reshuffle - Different options\n\n"
                "👉 You can type either the number or the style name."
            )
            st.rerun()
    
        v = st.text_input("Your choice (1-7 or style name)", key="cd_style_pick")
        if st.button("Submit style"):
            add_message("user", v)
            c = v.strip()
    
            # Handle reshuffle
            if c == "7":
                C["STYLE_OPTIONS"] = pick_random_styles()
                styles = C["STYLE_OPTIONS"]
                new_menu = "\n".join([f"{i+1}. {n} - {d}" for i,(n,d) in enumerate(styles)])
            
                reshuf_prompt = (
                    f"🔄 Styles reshuffled! Choose again:\n{new_menu}\n"
                    "6. Wild Card - Surprise style!\n7. Reshuffle - Different options\n\n"
                    "👉 Or, type your own custom style."
                )
                add_message("assistant", reshuf_prompt)
            
                st.session_state.GLOBAL["CURRENT_STEP"] = 1
                st.rerun()
    
            # Handle wild card
            elif c == "6":
                C["STYLE_SELECTED"] = random.choice([s[0] for s in styles])
                add_message("assistant", f"🎲 Wild Card pick: {C['STYLE_SELECTED']}")
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
    
            # Handle numbered styles
            elif c in {"1","2","3","4","5"}:
                C["STYLE_SELECTED"] = styles[int(c)-1][0]
                add_message("assistant", f"✅ Selected Style: {C['STYLE_SELECTED']}")
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
    
            # Handle custom style (anything else)
            else:
                C["STYLE_SELECTED"] = c
                add_message("assistant", f"✨ Custom Style Selected: {C['STYLE_SELECTED']}")
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()




  
        # ----------------------------
    # STEP 2: Genre Selection
    # ----------------------------
    if step == 2:
        # Build structured genre options once
        if "GENRE_OPTIONS" not in C:
            core_names = [g for g in CORE_GENRES]
            flex_names = [g for g in FLEX_GENRES]
            plaid_names = [g for g in PLAIDVERSE]
    
            core_count = min(3, len(core_names))
            flex_count = min(2, len(flex_names))
            plaid_count = min(1, len(plaid_names))
    
            core_chosen = random.sample(core_names, core_count) if core_names else []
            flex_chosen = random.sample(flex_names, flex_count) if flex_names else []
            plaid_chosen = random.sample(plaid_names, plaid_count) if plaid_names else []
    
            # Flatten into one list with (name, desc) pairs
            C["GENRE_OPTIONS"] = core_chosen + flex_chosen + plaid_chosen
    
        genres = C["GENRE_OPTIONS"]
    
        # Build grouped display
        lines = []
        idx = 1
        if genres:
            # split back into groups
            start = 0
            end = start + min(3, len(genres) - start)
            core_block = genres[start:end]
            start = end
            end = start + min(2, len(genres) - start)
            flex_block = genres[start:end]
            start = end
            plaid_block = genres[start:start + min(1, len(genres) - start)]
    
            if core_block:
                lines.append("-- Core Genres --")
                for n, d in core_block:
                    lines.append(f"{idx}. {n} - {d}")
                    idx += 1
            if flex_block:
                lines.append("-- Flexible / Meta Genres --")
                for n, d in flex_block:
                    lines.append(f"{idx}. {n} - {d}")
                    idx += 1
            if plaid_block:
                lines.append("-- Plaidverse™ Bonus --")
                for n, d in plaid_block:
                    lines.append(f"{idx}. {n} - {d}")
                    idx += 1
    
        wild_idx = idx
        reshuf_idx = idx + 1
        lines.append(f"{wild_idx}. Wild Card - Surprise genre!")
        lines.append(f"{reshuf_idx}. Reshuffle - Different options")
    
        menu = "\n".join(lines)
    
        if not any("Pick your genre" in m for _, m in chat):
            add_message("assistant",
                f"📚 {active_quip}: Pick your genre:\n{menu}\n\n"
                "👉 You can type either the number or the genre name."
            )
            st.rerun()
    
        v = st.text_input(f"Your choice (1-{reshuf_idx} or genre name)", key="cd_genre_pick")
        if st.button("Submit genre"):
            add_message("user", v)
            c = v.strip()
    
            # Handle reshuffle
            if c == str(reshuf_idx):
                core_names = [g for g in CORE_GENRES]
                flex_names = [g for g in FLEX_GENRES]
                plaid_names = [g for g in PLAIDVERSE]
    
                core_chosen = random.sample(core_names, min(3, len(core_names))) if core_names else []
                flex_chosen = random.sample(flex_names, min(2, len(flex_names))) if flex_names else []
                plaid_chosen = random.sample(plaid_names, min(1, len(plaid_names))) if plaid_names else []
    
                C["GENRE_OPTIONS"] = core_chosen + flex_chosen + plaid_chosen
                genres = C["GENRE_OPTIONS"]
    
                new_lines = []
                idx2 = 1
                if core_chosen:
                    new_lines.append("-- Core Genres --")
                    for n, d in core_chosen:
                        new_lines.append(f"{idx2}. {n} - {d}")
                        idx2 += 1
                if flex_chosen:
                    new_lines.append("-- Flexible / Meta Genres --")
                    for n, d in flex_chosen:
                        new_lines.append(f"{idx2}. {n} - {d}")
                        idx2 += 1
                if plaid_chosen:
                    new_lines.append("-- Plaidverse™ Bonus --")
                    for n, d in plaid_chosen:
                        new_lines.append(f"{idx2}. {n} - {d}")
                        idx2 += 1
    
                new_lines.append(f"{idx2}. Wild Card - Surprise genre!")
                new_lines.append(f"{idx2+1}. Reshuffle - Different options")
    
                reshuf_prompt = (
                    f"🔄 {active_quip}: Genres reshuffled! Pick again:\n{chr(10).join(new_lines)}"
                )
                add_message("assistant", reshuf_prompt)
    
                st.session_state.GLOBAL["CURRENT_STEP"] = 2
                st.rerun()
    
            # Handle wild card
            elif c == str(wild_idx):
                master = [g[0] for g in CORE_GENRES + FLEX_GENRES + PLAIDVERSE]
                C["GENRE_SELECTED"] = random.choice(master) if master else "Surprise"
                add_message("assistant", f"🎲 {active_quip}: Wild Card pick → {C['GENRE_SELECTED']}")
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()
    
            # Handle numbered genres
            elif c.isdigit() and 1 <= int(c) <= len(genres):
                C["GENRE_SELECTED"] = genres[int(c)-1][0]
                add_message("assistant", f"✅ {active_quip}: Selected Genre → {C['GENRE_SELECTED']}")
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()
    
            # Handle custom genre
            else:
                C["GENRE_SELECTED"] = c
                add_message("assistant", f"✨ {active_quip}: Custom Genre Selected → {C['GENRE_SELECTED']}")
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()






       # ----------------------------
    # STEP 3: Absurdity Selection
    # ----------------------------
    elif step == 3:
        if not any("chaos level" in m for _, m in chat):
            add_message("assistant",
                f"🎭 {active_quip}: Excellent! A {C['STYLE_SELECTED']} {C['GENRE_SELECTED']} adventure is brewing.\n\n"
                "Now, set the chaos level:\n"
                "1. Mild – Just a sprinkle of silly\n"
                "2. Moderate – Comfortably ridiculous\n"
                "3. Plaidemonium™ – Laws of logic need not apply\n"
                "4. Wild Card – Let fate decide!\n(Type 1–4)"
            )
            st.rerun()

        v = st.text_input("Your choice (1-4)", key="cd_abs_pick")
        if st.button("Submit absurdity"):
            add_message("user", v)
            c = v.strip()
            mapping = {"1":"Mild","2":"Moderate","3":"Plaidemonium™","4":"Wild Card"}
            if c in mapping:
                sel = mapping[c]
                if sel == "Wild Card":
                    sel = random.choice(["Mild","Moderate","Plaidemonium™"])
                C["ABSURDITY_SELECTED"] = sel
                add_message("assistant", f"✅ {active_quip}: Chaos level set to → {sel}")
                st.session_state.GLOBAL["CURRENT_STEP"] = 4
                st.rerun()
            else:
                add_message("assistant", f"❌ {active_quip}: Please pick between 1–4.")


        # ----------------------------
    # STEP 4: Confirmation
    # ----------------------------
    elif step == 4:
        summary = (
            f"🎭 Style: {C['STYLE_SELECTED']}\n"
            f"📚 Genre: {C['GENRE_SELECTED']}\n"
            f"🤪 Absurdity: {C['ABSURDITY_SELECTED']}\n"
        )
        if not any("here’s your setup" in m.lower() for _, m in chat):
            add_message("assistant",
                f"{active_quip}: Here’s your setup so far:\n\n{summary}\n\n"
                "Type **YES** to confirm and let’s spin this yarn into existence!"
            )
            st.rerun()

        conf = st.text_input("Confirm? YES/NO", key="cd_confirm")
        if st.button("Submit confirmation"):
            add_message("user", conf)
            if conf.strip().lower() == "yes":
                # Auto-generate seeds
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
                story = generate_story(
                    style=C["STYLE_SELECTED"],
                    genre=C["GENRE_SELECTED"],
                    absurdity=C["ABSURDITY_SELECTED"], 
                    seeds=seeds,
                    narrator=active_quip
                )
                st.session_state.generated_story = story
                st.session_state.GLOBAL["CURRENT_STEP"] = 5
                st.rerun()
            else:
                add_message("assistant", f"❌ {active_quip}: Confirmation failed. Please type **YES** to proceed.")


        # ----------------------------
    # STEP 5: Story & Remix
    # ----------------------------
    elif step == 5:
        active_quip = get_active_quip("Create Direct")
        st.subheader("✅ Story complete!")
    
        # Always show the story
        story_text = st.session_state.get("generated_story", None)
        if story_text:
            st.markdown("### 📖 Your Story")
            st.markdown(story_text)
            st.markdown(f"_{active_quip} outro:_ Curtain call with a wink.")
        else:
            st.error("⚠️ No story was generated. Please restart.")
            st.stop()
    
        # Remix / restart menu
        st.code(
            "🔄 What would you like to do next?\n\n"
            "1. Fluff It Up - Add softness, poetic language, whimsy\n"
            "2. Dial It Up - Switch to humorous dialect\n"
            "3. Style It Up - Retell in different literary style\n"
            "4. Plaidgerize - Rewrite with maximum absurdity\n"
            "5. PlaidMag-Gen It - Generate image 3 Panel\n"
            "6. New Story - Start over\n",
            language="text",
        )
    
        choice = st.text_input("Pick 1-5", key="cd_remix")
        if st.button("Apply Remix"):
            seeds = C.get("COLLECTED", {}).copy()
            style = C.get("STYLE_SELECTED", "Flash Fiction")
            genre = C.get("GENRE_SELECTED", "Adventure")
            absurd = C.get("ABSURDITY_SELECTED", "Mild")
    
            # 🔑 Force uniqueness each remix
            seeds["remix_id"] = str(random.randint(1000, 9999))
    
            if choice.strip() == "1":
                style = "Magic Realism"
            elif choice.strip() == "2":
                seeds["trait"] = seeds.get("trait", "grit") + " (dialect spice)"
            elif choice.strip() == "3":
                style = random.choice(["Ballads", "Breaking News", "Scriptlets", "Flash Fiction"])
            elif choice.strip() == "4":
                absurd = "Plaidemonium™"
            elif choice.strip() == "5":
                with st.spinner("🎨 Generating PlaidMagGen visuals..."):# PlaidMagGen-It
                    try:
                        img = plaidmag_gen(story_text)  # returns one composite PNG
                        if img:
                            st.session_state.generated_image = img
                            st.image(
                                img,
                                caption="🎨 PlaidMagGen Comic",
                                use_container_width=True
                            )
                
                            # Optional: Download button
                            buf = BytesIO()
                            img.save(buf, format="PNG")
                            st.download_button(
                                label="📥 Download Comic as PNG",
                                data=buf.getvalue(),
                                file_name="plaidmaggen_comic.png",
                                mime="image/png",
                            )
                        else:
                            st.error("⚠️ Image generation failed — no image returned.")
                    except Exception as e:
                        st.error(f"❌ PlaidMagGen failed: {e}")
    
            if choice.strip() in {"1", "2", "3", "4"}:
                new_story = generate_story(style, genre, absurd, active_quip, seeds)
                st.session_state.generated_story = new_story
                st.markdown("### ✨ Remixed Story")
                st.markdown(new_story)
            elif choice.strip() == "6":
                reset_mode("Create Direct")
                st.rerun()
            else:
                st.error("Pick 1-5.")

        # Download button
        st.subheader("Post-Story Options")
        st.download_button(
            label="📥 Download Story",
            data=st.session_state.generated_story,
            file_name="create_direct_story.txt",
            mime="text/plain",
        )




# 3) STORYLINE (chat-style, stable & rerun-safe)
elif mode == "Storyline":
    import re, random

    S = st.session_state.STORYLINE
    G = st.session_state.GLOBAL
    active_quip = get_active_quip("Storyline")

    # ---------- init ----------
    if "chat" not in S:
        S["chat"] = []                    # list[(role, content)]
    if "emitted" not in S:
        S["emitted"] = set()              # which prompts already shown
    if G.get("MODE") != "Storyline":
        G["MODE"] = "Storyline"
        G["CURRENT_STEP"] = 1
    if "STYLE_SELECTED" not in S:
        S["STYLE_SELECTED"] = None
    if "ABSURDITY_SELECTED" not in S:
        S["ABSURDITY_SELECTED"] = None
    if "USER_STORYLINE" not in S:
        S["USER_STORYLINE"] = None
    if "generated_story" not in st.session_state:
        st.session_state.generated_story = None
    if "STORY_SEEDS" not in S:
        S["STORY_SEEDS"] = None

    step = G.get("CURRENT_STEP", 1)

    def say(role, content, quipify=False):
        """Append a chat message. If assistant + quipify, prepend narrator voice."""
        if role == "assistant" and quipify:
            content = f"{active_quip}: {content}"
        S["chat"].append((role, content))

    def emit_once(key, content, quipify=True):
        """Append an assistant message only once per key, rerun to render."""
        if key not in S["emitted"]:
            say("assistant", content, quipify=quipify)
            S["emitted"].add(key)
            st.rerun()

    # ---------- render chat ----------
    for role, content in S["chat"]:
        with st.chat_message(role):
            st.markdown(content)

    # ---------- step prompts ----------
    if step == 1:
        emit_once(
            "storyline_intro",
            "✍️ **Storyline** — set the scene!\n\n"
            "Describe your story idea (simple, detailed, or weird). Examples:\n"
            "- *a goat runs for mayor*\n- *In a world where gravity works backwards...*\n"
            "- *My toaster gained sentience and filed taxes*\n\n"
            "What’s your concept?"
        )

    elif step == 2:
        if "STYLE_OPTIONS" not in S:
            S["STYLE_OPTIONS"] = pick_random_styles()
        styles = S["STYLE_OPTIONS"]
        menu = "\n".join([f"{i+1}. {n} - {d}" for i, (n, d) in enumerate(styles)])
        emit_once(
            "style_prompt",
            "🎨 **Choose a literary style for your concept:**\n\n"
            f"{menu}\n6. Wild Card — surprise!\n7. Reshuffle — new options\n\n"
            "👉 You can type either the number or the style name"
        )

    elif step == 3:
        emit_once(
            "absurdity_prompt",
            f"Style locked: **{S['STYLE_SELECTED']}**.\n\n"
            "🔥 Set the absurdity level:\n"
            "1. Mild — just a sprinkle\n2. Moderate — comfortably ridiculous\n"
            "3. Plaidemonium™ — logic optional\n4. Wild Card\n\nType **1–4**."
        )

    elif step == 4:
        emit_once(
            "generate_prompt",
            f"🎬 Translating your concept through {active_quip}.\n"
            "Type **generate** to create your story."
        )

    elif step == 5 and st.session_state.generated_story:
        emit_once(
            "post_options",
            "📌 **Post-Story Options:**\n"
            "1) Fluff It Up\n2) Dial It Up\n3) New Style\n4) Plaidgerize (max absurd)\n5) Start Over\n\n"
            "Type **1–5**."
        )

    # ---------- single chat input ----------
    placeholder = {
        1: "Your concept…",
        2: "Pick 1–7…",
        3: "Pick 1–4…",
        4: "Type generate…",
        5: "Pick 1–5…",
    }.get(step, "Type here…")

    user_msg = st.chat_input(placeholder)
    if not user_msg:
        # show download/post buttons if story exists
        if st.session_state.generated_story:
            st.subheader("Post-Story Options")
            st.download_button(
                label="📥 Download Story",
                data=st.session_state.generated_story,
                file_name="storyline_story.txt",
                mime="text/plain",
            )
            if st.button("✨ Post Story"):
                st.success("Story has been posted! (integration pending)")
        st.stop()

    # ---------- handle user input ----------
    say("user", user_msg)

    # ---------- Step 1: Concept ----------
    if step == 1:
        txt = user_msg.strip()
        if not txt:
            say("assistant", "❌ Please enter a concept.")
        else:
            S["USER_STORYLINE"] = txt
            say("assistant", "✅ Concept saved.")
            G["CURRENT_STEP"] = 2
        st.rerun()

    # ---------- Step 2: Style ----------
    elif step == 2:
        c = user_msg.strip()
        styles = S["STYLE_OPTIONS"]
    
        if c == "7":
            S.pop("STYLE_OPTIONS", None)
            S["emitted"].discard("style_prompt")
            say("assistant", "🔄 Reshuffling styles…")
    
        elif c == "6":
            S["STYLE_SELECTED"] = random.choice([s[0] for s in styles])
            say("assistant", f"🎨 Style chosen: **{S['STYLE_SELECTED']}**")
            G["CURRENT_STEP"] = 3
    
        elif c in {"1","2","3","4","5"}:
            S["STYLE_SELECTED"] = styles[int(c)-1][0]
            say("assistant", f"🎨 Style chosen: **{S['STYLE_SELECTED']}**")
            G["CURRENT_STEP"] = 3
    
        else:
            # Treat input as a custom style
            S["STYLE_SELECTED"] = c
            say("assistant", f"🎨 Custom style chosen: **{S['STYLE_SELECTED']}**")
            G["CURRENT_STEP"] = 3
    
        st.rerun()


    # ---------- Step 3: Absurdity ----------
    elif step == 3:
        mapping = {"1": "Mild", "2": "Moderate", "3": "Plaidemonium™", "4": "Wild Card"}
        c = user_msg.strip()
        if c in mapping:
            sel = mapping[c]
            if sel == "Wild Card":
                sel = random.choice(["Mild", "Moderate", "Plaidemonium™"])
            S["ABSURDITY_SELECTED"] = sel
            say("assistant", f"✅ Absurdity selected: **{sel}**")
            G["CURRENT_STEP"] = 4
        else:
            say("assistant", "❌ Please pick **1–4**.")
        st.rerun()

    # ---------- Step 4: Generate story ----------
    elif step == 4:
        if user_msg.strip().lower() != "generate":
            say("assistant", "❌ Type **generate** to continue.")
            st.rerun()

        # Build seeds from concept
        def seeds_from_concept(txt):
            words = re.findall(r"[A-Za-z']+", txt)
            caps = re.findall(r"\b[A-Z][a-z']+\b", txt)
            name = caps[0] if caps else random.choice(["Rowan", "Alex", "Miri", "Jax"])
            professions = ["baker","astronomer","detective","ranger","scribe","cartographer","librarian","sailor","pilot"]
            prof = next((w.lower() for w in words if w.lower() in professions), random.choice(professions))
            place = None
            m = re.search(r"\b(in|at|under|inside|near)\s+([A-Za-z][A-Za-z\s']{2,})", txt, flags=re.IGNORECASE)
            if m: place = " ".join(m.group(2).strip().split()[0:2])
            place = place or random.choice(["Harborlight","Northbridge","Glimmerfall","Dockside"])
            adjectives = ["restless","luminous","sardonic","tattered","iridescent"]
            adj = next((w.lower() for w in words if w.lower() in adjectives), random.choice(adjectives))
            obj = random.choice(["lantern","ledger","compass","violin","coin","hourglass"])
            return {
                "name": name, "profession": prof, "place": place, "adjective": adj, "object": obj,
                "name2": random.choice(["Riley","Kestrel","Vee","Nico"]),
                "object2": random.choice(["map","key","ticket","note"]),
                "place2": random.choice(["East Gate","Old Yard","Sun Stairs"]),
                "portal": random.choice(["ripple","threshold","curtain"]),
                "tool": random.choice(["courage","wit","stubbornness"]),
                "trait": random.choice(["grace","grit","candor"]),
                "wild": random.choice(["confetti rain","time hiccup","snack-based destiny"]),
            }

        seeds = seeds_from_concept(S["USER_STORYLINE"])
        S["STORY_SEEDS"] = seeds
        genre = random.choice([g[0] for g in CORE_GENRES + FLEX_GENRES + PLAIDVERSE])
        story = generate_story(
            style=S["STYLE_SELECTED"],
            genre=genre,
            absurdity=S["ABSURDITY_SELECTED"],
            narrator=active_quip,
            seeds=seeds
        )
        st.session_state.generated_story = story
        say("assistant", "✨ **Your story:**\n\n" + story)
        G["CURRENT_STEP"] = 5
        st.rerun()

    # ---------- Step 5: Remix / Post ----------
    elif step == 5:
        v = user_msg.strip()
        if v in {"1","2","3","4"}:
            seeds = S["STORY_SEEDS"]
            style, absurd = S["STYLE_SELECTED"], S["ABSURDITY_SELECTED"]
            genre = random.choice([g[0] for g in CORE_GENRES + FLEX_GENRES + PLAIDVERSE])
            if v == "1": style = "Magic Realism"
            elif v == "2": seeds["trait"] += " (dialect spice)"
            elif v == "3": style = random.choice(["Ballads","Flash Fiction","Scriptlets","Breaking News"])
            elif v == "4": absurd = "Plaidemonium™"

            remixed = generate_story(
                style=style,
                genre=genre,
                absurdity=absurd,
                narrator=active_quip,
                seeds=seeds
            )
            st.session_state.generated_story = remixed
            S["chat"].append(("assistant", f"✨ **Remixed story:**\n\n{remixed}"))
        elif v == "5":
            reset_mode("Storyline")
            st.rerun()
        else:
            say("assistant", "❌ Please pick **1–5**.")
            st.rerun()

        # Post-story buttons
        st.subheader("Post-Story Options")
        st.download_button(
            label="📥 Download Story",
            data=st.session_state.generated_story,
            file_name="storyline_story.txt",
            mime="text/plain",
        )
        if st.button("Restart Storyline"):
            reset_mode("Storyline")
            st.rerun()




# 4) PLAIDPIC (Upload-to-Story Visual Remix)
elif mode == "PlaidPic":
    if "PLAIDPIC" not in st.session_state:
        st.session_state.PLAIDPIC = {
            "IMAGE_UPLOADED": False,
            "uploaded_file": None,       # ✅ new: keep actual file object
            "IMAGE_ANALYSIS": {},
            "QUIP_SELECTED": "MacQuip",
            "STYLE_SELECTED": None,
            "GENRE_SELECTED": None,
            "ABSURDITY_SELECTED": None,
            "TEXT_DESC": "",
            "chat": [],
            "emitted": set(),
        }
    P = st.session_state.PLAIDPIC
    G = st.session_state.GLOBAL
    active_quip = get_active_quip("PlaidPic")

    # --- Safeguards ---
    if "chat" not in P or not isinstance(P["chat"], list):
        P["chat"] = []
    if "emitted" not in P or not isinstance(P["emitted"], set):
        P["emitted"] = set()

    # --- Helpers ---
    def say(role, content, quipify=False):
        if role == "assistant" and quipify:
            content = f"{active_quip}: {content}"
        P["chat"].append((role, content))

    def emit_once(key, content, quipify=True):
        if key not in P["emitted"]:
            say("assistant", content, quipify=quipify)
            P["emitted"].add(key)
            st.rerun()

    def analyze_image(desc: str) -> Dict[str, Any]:
        """Simulated quick scan of uploaded image/desc → tags."""
        moods = ["moody", "bright", "mysterious", "playful", "serene", "chaotic"]
        colors = ["plaid red", "golden", "deep blue", "ashen gray", "emerald"]
        subjects = ["figure", "landscape", "animal", "machine", "dreamscape"]
        return {
            "mood": random.choice(moods),
            "color": random.choice(colors),
            "subject": random.choice(subjects),
            "desc": desc,
        }

    # --- Render chat ---
    st.subheader("🖼️ PlaidPic Chat")
    for role, msg in P["chat"]:
        if role == "assistant":
            st.markdown(f"**Assistant:** {msg}")
        else:
            st.markdown(f"**You:** {msg}")

    step = G.get("CURRENT_STEP", 1)

    # STEP 1 – Upload or describe
    if step == 1:
        emit_once("pic_intro", "📷 Welcome to **PlaidPic™**!\n\nUpload an image or paste a text description.")
        uploaded = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png", "webp"])
        desc = st.text_area("Or enter a description", key="plaidpic_desc")

        # ✅ Thumbnail preview
        if uploaded is not None:
            st.image(uploaded, caption="📸 Preview", use_container_width=False, width=300)

        if st.button("Continue"):
            if uploaded:
                P["IMAGE_UPLOADED"] = True
                P["uploaded_file"] = uploaded  # ✅ keep file for later preview
                P["TEXT_DESC"] = f"(Image uploaded: {uploaded.name})"
                P["IMAGE_ANALYSIS"] = analyze_image(uploaded.name)
            elif desc.strip():
                P["TEXT_DESC"] = desc.strip()
                P["IMAGE_ANALYSIS"] = analyze_image(desc.strip())
            else:
                say("assistant", "❌ Please upload an image or enter a description.", quipify=True)
                st.rerun()
            G["CURRENT_STEP"] = 2
            st.rerun()

    # STEP 2 – Style
    elif step == 2:
        # Always refresh styles when entering this step
        if "STYLE_OPTIONS" not in P:
            P["STYLE_OPTIONS"] = pick_random_styles(n=5)
    
        styles = P["STYLE_OPTIONS"]
        menu = "\n".join([f"{i+1}. {n} - {d}" for i, (n, d) in enumerate(styles)])
        emit_once(
            "pic_style",
            f"🎨 Pick a literary style:\n{menu}\n6. Wild Card\n7. Reshuffle"
        )
    
        v = st.text_input("Your choice (1–7)", key="pic_style_pick")
        if st.button("Submit style"):
            say("user", v)
            c = v.strip()
            if c == "7":
                # Force reshuffle: assign new random styles
                P["STYLE_OPTIONS"] = pick_random_styles(n=5)
                new_styles = P["STYLE_OPTIONS"]
                new_menu = "\n".join([f"{i+1}. {n} - {d}" for i, (n, d) in enumerate(new_styles)])
                say("assistant", f"🔄 Reshuffled styles! Pick again:\n{new_menu}\n6. Wild Card\n7. Reshuffle", quipify=True)
                G["CURRENT_STEP"] = 2
                st.rerun()
    
            elif c == "6":
                P["STYLE_SELECTED"] = random.choice([s[0] for s in styles])
                say("assistant", f"🎲 Wild Card → {P['STYLE_SELECTED']}", quipify=True)
                G["CURRENT_STEP"] = 3
                st.rerun()
    
            elif c in {"1","2","3","4","5"}:
                P["STYLE_SELECTED"] = styles[int(c)-1][0]
                say("assistant", f"✅ Selected Style → {P['STYLE_SELECTED']}", quipify=True)
                G["CURRENT_STEP"] = 3
                st.rerun()
    
            else:
                say("assistant", "❌ Pick 1–7.", quipify=True)


    # STEP 3 – Genre
    elif step == 3:
        if "GENRE_MENU" not in P:
            menu, mapping = genre_menu_block()
            P["GENRE_MENU"], P["GENRE_MAPPING"] = menu, mapping
        else:
            menu, mapping = P["GENRE_MENU"], P["GENRE_MAPPING"]

        emit_once("pic_genre", f"📚 Choose your genre:\n{menu}\n(Type 1–8)")

        v = st.text_input("Your choice (1–8)", key="pic_genre_pick")
        if st.button("Submit genre"):
            say("user", v)
            c = v.strip()
            if c == str(len(mapping)):  # Reshuffle
                menu, mapping = genre_menu_block()
                P["GENRE_MENU"], P["GENRE_MAPPING"] = menu, mapping
                say("assistant", "🔄 Genres reshuffled!", quipify=True)
                st.rerun()
            elif c in mapping:
                gsel = mapping[c]
                if gsel == "Wild Card":
                    gsel = random.choice([g[0] for g in CORE_GENRES + FLEX_GENRES + PLAIDVERSE])
                P["GENRE_SELECTED"] = gsel
                say("assistant", f"✅ Selected Genre → {gsel}", quipify=True)
                G["CURRENT_STEP"] = 4
                st.rerun()
            else:
                say("assistant", "❌ Invalid. Pick 1–8.", quipify=True)

    # STEP 4 – Absurdity
    elif step == 4:
    # Show absurdity menu once
        emit_once("pic_absurdity",
            "🎭 Set the absurdity:\n"
            "1. Mild\n"
            "2. Moderate\n"
            "3. Plaidemonium™\n"
            "4. Wild Card (1–4)\n\n"
            "👉 You can type either the **number** or the **absurdity name**."
        )
    
        v = st.text_input("Your choice (1–4 or name)", key="pic_abs_pick")
        if st.button("Submit absurdity"):
            say("user", v)
            choice = v.strip()
    
            mapping = {
                "1": "Mild",
                "2": "Moderate",
                "3": "Plaidemonium™",
                "4": "Wild Card"
            }
    
            sel = None
    
            # Case 1: numeric input
            if choice in mapping:
                sel = mapping[choice]
                if sel == "Wild Card":
                    sel = random.choice(["Mild", "Moderate", "Plaidemonium™"])
                P["ABSURDITY_SELECTED"] = sel
                say("assistant", f"✅ Absurdity set → {sel}", quipify=True)
                G["CURRENT_STEP"] = 5
                st.rerun()
    
            # Case 2: text input (direct absurdity name)
            else:
                normalized = choice.lower()
                valid_options = ["Mild", "Moderate", "Plaidemonium™"]
                match = next((a for a in valid_options if a.lower().startswith(normalized)), None)
    
                if match:
                    P["ABSURDITY_SELECTED"] = match
                    say("assistant", f"✅ Absurdity set → {match}", quipify=True)
                    G["CURRENT_STEP"] = 5
                    st.rerun()
                else:
                    say("assistant", "❌ Please pick 1–4 or type a valid absurdity.", quipify=True)


    # STEP 5 – Generate Story
    elif step == 5:
        summary = (
            f"🖼️ Image/Text: {P['TEXT_DESC']}\n"
            f"🎨 Style: {P['STYLE_SELECTED']}\n"
            f"📚 Genre: {P['GENRE_SELECTED']}\n"
            f"🤪 Absurdity: {P['ABSURDITY_SELECTED']}\n"
            f"🎨 Analysis: {P['IMAGE_ANALYSIS']}"
        )
        emit_once("pic_summary", f"Here’s your setup:\n\n{summary}\nType **generate** to continue.")

        v = st.text_input("Type generate", key="pic_generate")
        if st.button("Generate story"):
            say("user", v)
            if v.strip().lower() == "generate":
                seeds = {"image_desc": P["TEXT_DESC"], **P["IMAGE_ANALYSIS"]}
                story_raw = generate_story(
                    style=P["STYLE_SELECTED"],
                    genre=P["GENRE_SELECTED"],
                    absurdity=P["ABSURDITY_SELECTED"],
                    narrator=P["QUIP_SELECTED"],
                    seeds=seeds
                )
                # wrap in PlaidLibs markers
                story = f"~ /^\n{story_raw}\n^/ ~"
                st.session_state.generated_story = story
                G["CURRENT_STEP"] = 6
                st.rerun()
            else:
                say("assistant", "❌ Please type 'generate'.", quipify=True)

    # STEP 6 – Show story + remix
    elif step == 6:
        st.subheader("✅ Story Generated")
    
        # --- Thumbnail Preview ---
        if P.get("IMAGE_UPLOADED") and P.get("uploaded_file") is not None:
            st.image(P["uploaded_file"], caption="📸 Preview", use_container_width=False, width=300)
        elif P.get("TEXT_DESC") and not P.get("IMAGE_UPLOADED"):
            st.markdown(f"📖 *Description used instead of image:* {P['TEXT_DESC']}")
    
        # --- Show Generated Story ---
        story_text = st.session_state.get("generated_story", None)
        if story_text:
            st.markdown("### 📖 Your Story")
            st.markdown(story_text)
            st.markdown(f"_{active_quip} outro:_ Plaid lens fades, story complete.")
        else:
            st.error("⚠️ No story was generated. Please restart.")
            st.stop()
    
        # --- Remix Menu ---
        st.code(
            "🔄 Remix Options:\n"
            "1. Style It Up\n"
            "2. Dial It Up\n"
            "3. Fluff It Up\n"
            "4. Plaidgerize\n"
            "5. PlaidMagGen-It (visual follow-up)\n"
            "6. New Variation\n",
            language="text",
        )
        choice = st.text_input("Pick 1–6", key="pic_remix")
    
        if st.button("Apply Remix"):
            # ✅ Re-analyze image each remix
            P["IMAGE_ANALYSIS"] = analyze_image(P["TEXT_DESC"])
            seeds = {"image_desc": P["TEXT_DESC"], **P["IMAGE_ANALYSIS"]}
            style, genre, absurd = P["STYLE_SELECTED"], P["GENRE_SELECTED"], P["ABSURDITY_SELECTED"]
    
            if choice.strip() == "1":
                style = random.choice(["Ballads", "Breaking News", "Scriptlets"])
            elif choice.strip() == "2":
                seeds["dialect"] = "humorous"
            elif choice.strip() == "3":
                style = "Magic Realism"
            elif choice.strip() == "4":
                absurd = "Plaidemonium™"
            elif choice.strip() == "5":
                say("assistant", "🎨 Generating PlaidMagGen visual... (bright white background, plaid enforced)", quipify=True)
            
                import base64
                from io import BytesIO
                from PIL import Image
                
                with st.spinner("🎨 Generating PlaidMagGen visuals..."):# PlaidMagGen-It
                    try:
                        response = client.images.generate(
                            model="gpt-image-1",
                            prompt=(
                                f"A surreal illustration based on: {P['TEXT_DESC']}. "
                                f"Mood: {P['IMAGE_ANALYSIS'].get('mood')}, "
                                f"Color scheme: {P['IMAGE_ANALYSIS'].get('color')}, "
                                f"Subject: {P['IMAGE_ANALYSIS'].get('subject')}. "
                                f"Style: {style}, Genre: {genre}, Absurdity: {absurd}. "
                                f"⚪ White background, plaid patterns must be visible."
                            ),
                            size="1024x1024"
                        )
                
                        if hasattr(response, "data") and len(response.data) > 0:
                            img_b64 = response.data[0].b64_json
                            img_bytes = base64.b64decode(img_b64)
                            img = Image.open(BytesIO(img_bytes))
                
                            st.image(img, caption="🖼️ PlaidMagGen-It Result", use_container_width=True)
                            st.download_button(
                                "📥 Download Image",
                                data=img_bytes,
                                file_name="plaidmaggen.png",
                                mime="image/png"
                            )
                        else:
                            st.error("⚠️ No image returned by API. Try a simpler prompt.")
                
                    except Exception as e:
                        st.error(f"❌ Image generation error: {e}")
                
                    st.stop()

    
            elif choice.strip() == "6":
                pass  # regenerate same inputs
            else:
                st.error("❌ Pick 1–6.")
                st.stop()
    
            # --- For 1–4 & 6: regenerate story ---
            new_story_raw = generate_story(style, genre, absurd, active_quip, seeds)
            new_story = f"~ /^\n{new_story_raw}\n^/ ~"
            st.session_state.generated_story = new_story
            st.markdown("### ✨ Remixed Story")
            st.markdown(new_story)
    
        # --- Post-Story Options ---
        st.subheader("Post-Story Options")
        st.download_button(
            label="📥 Download Story",
            data=st.session_state.generated_story,
            file_name="plaidpic_story.txt",
            mime="text/plain",
        )
        if st.button("Restart PlaidPic"):
            reset_mode("PlaidPic")
            st.rerun()






# 5) PLAIDMAGGEN
elif mode == "PlaidMagGen":
    client = OpenAI()
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "generated_image" not in st.session_state:
        st.session_state.generated_image = None
    
    st.title("🎨 PlaidMagGen – Image Generator")
    
    # --- Display chat history ---
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # --- Chat helpers ---
    def assistant_message(content):
        st.session_state.chat_history.append({"role": "assistant", "content": content})
        with st.chat_message("assistant"):
            st.write(content)
    
    def user_message(content):
        st.session_state.chat_history.append({"role": "user", "content": content})
        with st.chat_message("user"):
            st.write(content)
    
    # --- Step prompts ---
    step_prompts = {
        1: "**STEP 1: Choose Format (type 1-5)**\n"
           "1. 3-Panel Comic Scene\n"
           "2. Character Portrait\n"
           "3. Plaid Card (Collectible)\n"
           "4. Scene Illustration\n"
           "5. Wild Card",
    
        3: "**STEP 3: Describe a scene.**\n👉 If you picked *3-Panel Comic*, please write 3 short parts (setup, twist, reveal) separated by `///`. Or type 'surprise me.'",
    
        4: "**STEP 4: Add enhancement tags (comma separated)**\nExamples: Focus on Emotion, Cinematic Lighting, Showcase Plaid Clothing, Add Hidden Detail/Easter Egg, Add Surreal Element, Zoomed Portrait, No Tags"
    }
    
    format_map = {
        "1": "3-Panel Comic Scene",
        "2": "Character Portrait",
        "3": "Plaid Card (Collectible)",
        "4": "Scene Illustration",
        "5": "Wild Card"
    }
    
    # --- Show current step prompt (only for fixed steps) ---
    if st.session_state.step in step_prompts:
        if not any(m["role"]=="assistant" and step_prompts[st.session_state.step] in m["content"] 
                   for m in st.session_state.chat_history):
            assistant_message(step_prompts[st.session_state.step])
    
    # --- User input ---
    user_input = st.chat_input("Type your response...")
    if user_input:
        user_message(user_input)
    
        # --- Step 1: Format ---
        # --- Step 1: Format ---
        if st.session_state.step == 1:
            choice = user_input.strip()
            if choice in format_map:
                if choice == "5":  # Wild Card
                    fmt = random.choice(list(format_map.values())[:-1])
                    st.session_state.answers["format"] = fmt
                    assistant_message(f"🎲 Wild Card format → {fmt}")
                else:
                    st.session_state.answers["format"] = format_map[choice]
        
                # Move to Step 2
                st.session_state.step = 2
                # Reset styles so fresh randoms appear
                st.session_state.STYLE_OPTIONS = pick_random_styles(n=5)
                styles = st.session_state.STYLE_OPTIONS
                wild_idx = len(styles) + 1
                reshuf_idx = len(styles) + 2
                style_lines = [f"{i+1}. {name}" for i, (name, _) in enumerate(styles)]
                style_lines.append(f"{wild_idx}. Wild Card")
                style_lines.append(f"{reshuf_idx}. Reshuffle")
        
                assistant_message("**STEP 2: Choose Style (type number or name)**\n" +
                                  "\n".join(style_lines))
            else:
                assistant_message("❌ Invalid input. Please type 1-5.")
            
    
        # --- Step 2: Style (dynamic) ---
        elif st.session_state.step == 2:
            # Initialize random styles if not already set
            if "STYLE_OPTIONS" not in st.session_state:
                st.session_state.STYLE_OPTIONS = pick_random_styles(n=5)

            styles = st.session_state.STYLE_OPTIONS
            wild_idx = len(styles) + 1
            reshuf_idx = len(styles) + 2

            # Build dynamic style menu
            style_lines = [f"{i+1}. {name}" for i, (name, _) in enumerate(styles)]
            style_lines.append(f"{wild_idx}. Wild Card")
            style_lines.append(f"{reshuf_idx}. Reshuffle")

            # Show menu once
            if not any(m["role"]=="assistant" and "STEP 2: Choose Style" in m["content"]
                       for m in st.session_state.chat_history):
                assistant_message("**STEP 2: Choose Style (type number or name)**\n" +
                                  "\n".join(style_lines))

            choice = user_input.strip()

            # Handle numeric choices
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(styles):
                    sel = styles[choice_num - 1][0]
                    st.session_state.answers["style"] = sel
                    st.session_state.step = 3
                    assistant_message(f"✅ Selected Style → {sel}")
                    assistant_message(step_prompts[3])
                elif choice_num == wild_idx:
                    master = [s[0] for s in pick_random_styles(n=20)]
                    sel = random.choice(master)
                    st.session_state.answers["style"] = sel
                    st.session_state.step = 3
                    assistant_message(f"🎲 Wild Card style → {sel}")
                    assistant_message(step_prompts[3])
                elif choice_num == reshuf_idx:
                    # Reshuffle → regenerate new 5
                    st.session_state.STYLE_OPTIONS = pick_random_styles(n=5)
                    new_styles = st.session_state.STYLE_OPTIONS
                    new_lines = [f"{i+1}. {n}" for i, (n, _) in enumerate(new_styles)]
                    new_lines.append(f"{len(new_styles)+1}. Wild Card")
                    new_lines.append(f"{len(new_styles)+2}. Reshuffle")
                    assistant_message("🔄 Styles reshuffled! Pick again:\n" +
                                      "\n".join(new_lines))
                else:
                    assistant_message("❌ Invalid input. Please type a valid number.")
            else:
                # Handle text input (exact match)
                matches = [s[0] for s in styles if s[0].lower() == choice.lower()]
                if matches:
                    sel = matches[0]
                    st.session_state.answers["style"] = sel
                    st.session_state.step = 3
                    assistant_message(f"✅ Selected Style → {sel}")
                    assistant_message(step_prompts[3])
                else:
                    assistant_message("❌ Not recognized. Enter a valid number or exact style name.")
    
        # --- Step 3: Scene ---
        elif st.session_state.step == 3:
            st.session_state.answers["scene"] = user_input
            st.session_state.step = 4
            assistant_message(step_prompts[4])
    
        # --- Step 4: Enhancement tags & Generate ---
        elif st.session_state.step == 4:
            st.session_state.answers["tags"] = user_input
            st.session_state.step = 5
    
            fmt = st.session_state.answers["format"].lower()
            style = st.session_state.answers["style"]
            scene = st.session_state.answers["scene"]
            tags = st.session_state.answers["tags"]
    
            # --- 3-Panel Comic ---
            if "3-panel" in fmt:
                parts = scene.split("///")
                if len(parts) < 3:
                    parts = ["Setup scene", "Twist scene", "Reveal scene"]
    
                panels = []
                with st.spinner("🎨 Generating 3-panel comic..."):
                    for i, part in enumerate(parts, start=1):
                        prompt = f"Comic Panel {i}: {part.strip()}. Style: {style}. Enhancements: {tags}. Cartoon, PlaidLibs vibe."
                        try:
                            result = client.images.generate(
                                model="gpt-image-1",
                                prompt=prompt[:900],
                                size="1024x1024"
                            )
                            img_b64 = result.data[0].b64_json
                            img_bytes = base64.b64decode(img_b64)
                            img = Image.open(BytesIO(img_bytes))
                            panels.append(img)
                        except Exception as e:
                            assistant_message(f"⚠️ Failed to generate panel {i}: {e}")
    
                if panels:
                    st.session_state.generated_image = panels
                    st.image(panels, caption=["Panel 1", "Panel 2", "Panel 3"], use_container_width=True)
    
            # --- Single image formats ---
            else:
                spec = f"Format: {fmt}\nStyle: {style}\nScene: {scene}\nEnhancements: {tags}"
                assistant_message("✨ Generating your image with this prompt:\n\n" + spec)
                with st.spinner("🎨 Please wait..."):
                    try:
                        result = client.images.generate(
                            model="gpt-image-1",
                            prompt=spec[:900],
                            size="1024x1024"
                        )
                        img_b64 = result.data[0].b64_json
                        img_bytes = base64.b64decode(img_b64)
                        img = Image.open(BytesIO(img_bytes))
                        st.session_state.generated_image = img
                        with st.chat_message("assistant"):
                            st.image(img, caption="Generated with PlaidMagGen", use_container_width=True)
                    except Exception as e:
                        assistant_message(f"⚠️ Failed to generate image: {e}")
    
            assistant_message("✅ Done! Type 'restart' to try again.")
    
        # --- Step 5: Restart ---
        elif st.session_state.step == 5:
            if user_input.strip().lower() == "restart":
                st.session_state.clear()
                st.rerun()




# 6) PLAIDPLAY
elif mode == "PlaidPlay":
    PLY = st.session_state.PLAIDPLAY
    active_quip = get_active_quip("PlaidPlay")

    if step == 1:
        st.subheader("STEP 1: SET PLAYERS & PROMPT")

        # Host selections (from Guide)
        quip_persona = get_active_quip("PlaidPlay")
        style = st.multiselect("Pick Literary Styles (5 random + 1 Wild)", ["BalladsFlash", "Fiction","Satire & Light Parody","Breaking News","Scriptlets","Wild Card"], key="pp_style")
        genre = st.multiselect("Pick Genres (3 core + 2 meta + 1 Plaidverse + Wild)", ["Fantasy", "Sci-Fi", "Romance", "Satire", "Horror", "Plaidverse", "Wild"], key="pp_genre")
        absurdity = st.radio("Absurdity Level", ["Mild", "Moderate", "Plaidemonium™", "Wild Card"], key="pp_absurd")

        emails = st.text_input("Player emails (comma-separated, required)", key="pp_emails")
        n_players = st.number_input("Number of players (4–8)", min_value=4, max_value=8, value=4, step=1, key="pp_n")
        prompt = st.text_area("Master prompt / theme", key="pp_master", height=120,
                              placeholder="e.g., 'A heist involving plaid luggage at a moonlit train station'")

        if st.button("Start Round"):
            PLY["PLAYER_EMAILS"] = [e.strip() for e in emails.split(",") if e.strip()]
            PLY["N_PLAYERS"] = int(n_players)
            PLY["MASTER_PROMPT"] = prompt.strip() or "Plaid heist at dawn"
            PLY["QUIP_PERSONA"] = quip_persona
            PLY["STYLE"] = style
            PLY["GENRE"] = genre
            PLY["ABSURDITY"] = absurdity
            st.session_state.GLOBAL["CURRENT_STEP"] = 2
            st.rerun()

    elif step == 2:
        st.subheader("STEP 2: PLAYER SUBMISSIONS")
    
        # Track current player being prompted
        if "CURRENT_PLAYER" not in PLY:
            PLY["CURRENT_PLAYER"] = 1
            PLY["SUBMISSIONS"] = []
    
        current_player = PLY["CURRENT_PLAYER"]
        n_players = PLY["N_PLAYERS"]
    
        st.markdown(f"🎙️ {active_quip} says: *Player {current_player}, it’s your turn.*")
    
        # Unique prompt for this player
        unique_prompt = f"{PLY['MASTER_PROMPT']} (twist: {PLY['GENRE'][current_player % len(PLY['GENRE'])]})"
        st.info(f"Your prompt: **{unique_prompt}**")
    
        nouns = st.text_input("Enter 3 nouns (comma-separated)", key=f"pp_nouns_{current_player}")
        adjs = st.text_input("Enter 2 adjectives (comma-separated)", key=f"pp_adjs_{current_player}")
        wild = st.text_input("Enter 1 wildcard word/phrase", key=f"pp_wild_{current_player}")
    
        if st.button("Submit Entry"):
            sub = {
                "player": f"Player {current_player}",
                "prompt": unique_prompt,
                "nouns": [n.strip() for n in nouns.split(",") if n.strip()],
                "adjs": [a.strip() for a in adjs.split(",") if a.strip()],
                "wild": wild.strip()
            }
            PLY["SUBMISSIONS"].append(sub)
    
            if current_player < n_players:
                # Move to next player
                PLY["CURRENT_PLAYER"] += 1
                st.rerun()
            else:
                # All submissions done
                PLY["SUBMISSIONS_RECEIVED"] = len(PLY["SUBMISSIONS"])
                st.success("✅ All players submitted!")
                st.session_state.GLOBAL["CURRENT_STEP"] = 3
                st.rerun()

    elif step == 3:
        st.subheader("STEP 3: VOTING & RESULTS")

        # Enhanced vote system (2pt / 1pt scoring)
        tally = {s["player"]: 0 for s in PLY["SUBMISSIONS"]}
        for voter in PLY["SUBMISSIONS"]:
            picks = random.sample(list(tally.keys()), 2)  # mock voting
            tally[picks[0]] += 2
            tally[picks[1]] += 1

        PLY["VOTE_TALLY"] = tally
        winner = max(tally.items(), key=lambda kv: kv[1])[0] if tally else "No one"

        st.markdown("### Vote Tally")
        for k, v in tally.items():
            st.markdown(f"- **{k}**: {v} points")

        # Add Quip bonus Plaid Point™
        quip_bonus_cat = random.choice(["Most Sarcastic Sabotage", "Best Threat", "Most Emotionally Devastating", "Weirdest Syntax Spiral"])
        st.info(f"🎭 {active_quip} awards a Plaid Point™ for: **{quip_bonus_cat}**")
        tally[winner] += 1  # apply bonus
        st.success(f"🏆 Winner: {winner} (+ Plaid Point™)")

        if st.button("Show Encore Snippets"):
            st.session_state.GLOBAL["CURRENT_STEP"] = 4
            st.rerun()

    elif step == 4:
        st.subheader("STEP 4: ENCORE SNIPPETS (SCRIPTLETS)")
        for s in PLY["SUBMISSIONS"]:
            snippet = (
                f"~ /^\n"
                f"[{s['player']}] ({', '.join(s['adjs'])}) — "
                f"'We trade the {s['nouns'][0]} for a {s['nouns'][1]}; if the {s['nouns'][2]} sings, we run.'\n"
                f"^/ ~"
            )
            st.code(snippet, language="markdown")

        st.markdown(f"_{active_quip} aside:_ Democracy by giggle. I approve.")

        # Expanded remix menu
        st.code("1) Rematch\n2) Switch Quip\n3) Replay Winning Entry\n4) Generate Visual\n5) Jump to Lib-Ate™\n6) Share to PlaidStage™", language="text")
        v = st.text_input("Pick 1–6", key="ply_remix")

        if st.button("Apply"):
            if v.strip() == "1":
                st.session_state.GLOBAL["CURRENT_STEP"] = 1
                st.rerun()
            elif v.strip() == "2":
                PLY["QUIP_PERSONA"] = random.randint(1, 7)
                st.success("🔄 Quip switched!")
                st.session_state.GLOBAL["CURRENT_STEP"] = 1
                st.rerun()
            elif v.strip() == "3":
                st.info(f"Replaying winning entry: {PLY['VOTE_TALLY']}")
            elif v.strip() == "4":
                st.info("📸 Visual generation coming soon...")
            elif v.strip() == "5":
                reset_mode("Lib-Ate")  # jump to solo mode
                st.rerun()
            elif v.strip() == "6":
                st.info("🌐 Shared to PlaidStage™ (mock)")
            else:
                st.error("Pick 1–6.")



# 7) PLAIDCHAT

elif mode == "PlaidChat":
    # --- Init state ---
    if "PLAIDCHAT" not in st.session_state:
        st.session_state.PLAIDCHAT = {
            "messages": [],
            "QUIP_SELECTED": "MacQuip",  # default narrator
        }
    PC = st.session_state.PLAIDCHAT

    if "PLAIDMAGGEN" not in st.session_state:
        st.session_state.PLAIDMAGGEN = {"step": 0, "answers": {}}

    st.subheader("PlaidChat™ — Quip-fueled conversation")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # ------------------------
    # Helper
    # ------------------------
    def assistant_message(text):
        with st.chat_message("assistant"):
            st.markdown(f"**{PC['QUIP_SELECTED']}:** {text}")
        PC["messages"].append({"role": "assistant", "content": text})

    # ------------------------
    # Narrator-flavored story generator
    # ------------------------
    def generate_story(prompt, quip=None):
        system_msg = "You are a witty, creative storyteller."
        if quip:
            system_msg += f" Tell the story in the style of {quip}, with their quirks, humor, and personality."
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            max_tokens=700,
            temperature=1.0
        )
        return response.choices[0].message.content.strip()

    # ------------------------
    # PlaidMagGen definitions
    # ------------------------
    step_prompts = {
        1: "🎨 Pick a format (1-5):\n1. Single Image\n2. 3-Panel Comic\n3. Poster\n4. Logo\n5. Scene Sketch",
        2: "✨ Pick a style (1-5):\n1. Limericks\n2. Flash Fiction\n3. Fables\n4. Scriptlets\n5. Realistic",
        3: "📖 Describe your scene (separate panels with `///` for 3-panel comic):"
    }

    format_map = {
        "1": "Single Image",
        "2": "3-Panel Comic",
        "3": "Poster",
        "4": "Logo",
        "5": "Scene Sketch"
    }

    style_map = {
        "1": "Limericks",
        "2": "Flash Fiction",
        "3": "Fables",
        "4": "Scriptlets",
        "5": "Realistic"
    }

    def handle_plaidmaggen(user_input=None):
        pm = st.session_state.PLAIDMAGGEN

        if pm["step"] == 0:
            pm["step"] = 1
            assistant_message(step_prompts[1])
            return

        if user_input:
            # STEP 1: Format
            if pm["step"] == 1:
                choice = user_input.strip()
                if choice in format_map:
                    pm["answers"]["format"] = format_map[choice]
                    pm["step"] = 2
                    assistant_message(step_prompts[2])
                else:
                    assistant_message("❌ Invalid input. Type 1-5 for format.")
                return

            # STEP 2: Style
            elif pm["step"] == 2:
                choice = user_input.strip()
                if choice in style_map:
                    pm["answers"]["style"] = style_map[choice]
                    pm["step"] = 3
                    assistant_message(step_prompts[3])
                else:
                    assistant_message("❌ Invalid input. Type 1-5 for style.")
                return

            # STEP 3: Scene description & generate
            elif pm["step"] == 3:
                pm["answers"]["scene"] = user_input
                pm["step"] = 4
                fmt = pm["answers"]["format"].lower()
                style = pm["answers"]["style"]
                scene = pm["answers"]["scene"]

                # 3-panel comic
                if "3-panel" in fmt:
                    parts = scene.split("///")
                    if len(parts) < 3:
                        parts = ["Setup scene", "Twist scene", "Reveal scene"]
                    panels = []
                    with st.spinner("🎨 Generating 3-panel comic..."):
                        for i, part in enumerate(parts, start=1):
                            prompt = f"Comic Panel {i}: {part.strip()}. Style: {style}. Cartoon, PlaidLibs vibe."
                            try:
                                result = client.images.generate(
                                    model="gpt-image-1",
                                    prompt=prompt[:900],
                                    size="1024x1024"
                                )
                                img_b64 = result.data[0].b64_json
                                img_bytes = base64.b64decode(img_b64)
                                img = Image.open(BytesIO(img_bytes))
                                panels.append(img)
                            except Exception as e:
                                assistant_message(f"⚠️ Failed to generate panel {i}: {e}")
                    if panels:
                        st.session_state.generated_image = panels
                        with st.chat_message("assistant"):
                            st.image(panels, caption=["Panel 1", "Panel 2", "Panel 3"], use_container_width=True)

                # Single image
                else:
                    prompt = f"Format: {fmt}\nStyle: {style}\nScene: {scene}"
                    with st.spinner("🎨 Generating image..."):
                        try:
                            result = client.images.generate(
                                model="gpt-image-1",
                                prompt=prompt[:900],
                                size="1024x1024"
                            )
                            img_b64 = result.data[0].b64_json
                            img_bytes = base64.b64decode(img_b64)
                            img = Image.open(BytesIO(img_bytes))
                            st.session_state.generated_image = img
                            with st.chat_message("assistant"):
                                st.image(img, caption="Generated with PlaidMagGen", use_container_width=True)
                        except Exception as e:
                            assistant_message(f"⚠️ Failed to generate image: {e}")

                assistant_message("✅ Done! You can continue chatting or type 'restart'.")
                # Reset step for next chat
                pm["step"] = 0
                pm["answers"] = {}
                return

    # ------------------------
    # Workflow definitions
    # ------------------------
    WORKFLOW_QUESTIONS = {
        "Lib-Ate": [
            "🎭 Libate at your service! First, choose a style (e.g., Classic, Modern, Parody):",
            "📚 Now pick a genre (Sci-Fi, Horror, Romance, Fable, Comedy…):",
            "🎛️ What absurdity level? (Low, Medium, High):",
            "✍️ Give me some words (nouns, places, verbs, anything fun):"
        ],
        "Create_Direct": [
            "🎭 Great! Choose a style for Create Direct (e.g., Classic, Modern, Parody):",
            "📚 Now pick a genre (Sci-Fi, Horror, Romance, Fable, Comedy…):",
            "🎛️Pick a chaos level (Low, Medium, High):"
        ],
        "Storyline": [
            "🎭 Storyline Lover! What’s your concept?",
            "📚Choose a style (e.g., Classic, Modern, Parody)",
            "🎛️Pick an absurdity level (Low, Medium, High):"
        ]
    }

    # ------------------------
    # Workflow runner
    # ------------------------
    def handle_workflow(workflow, user_input=None):
        if "WF" not in PC:
            # Start workflow
            PC["WF"] = {"name": workflow, "step": 0, "answers": []}
            first_q = WORKFLOW_QUESTIONS[workflow][0]
            PC["messages"].append({"role": "assistant", "content": first_q})
            with st.chat_message("assistant"):
                st.markdown(f"**{PC['QUIP_SELECTED']}:** {first_q}")
            return

        wf = PC["WF"]

        # Save answer
        if user_input:
            wf["answers"].append(user_input)

        # Move to next step
        if len(wf["answers"]) < len(WORKFLOW_QUESTIONS[wf["name"]]):
            next_q = WORKFLOW_QUESTIONS[wf["name"]][len(wf["answers"])]
            PC["messages"].append({"role": "assistant", "content": next_q})
            with st.chat_message("assistant"):
                st.markdown(f"**{PC['QUIP_SELECTED']}:** {next_q}")
        else:
            # All answers collected → build story
            prompt = f"Workflow: {wf['name']}\nAnswers: {wf['answers']}\nGenerate a fun story."
            story = generate_story(prompt, PC["QUIP_SELECTED"])
            PC["messages"].append({"role": "assistant", "content": story})
            with st.chat_message("assistant"):
                st.markdown(f"**{PC['QUIP_SELECTED']}:** {story}")
            del PC["WF"]

    # ------------------------
    # Render history
    # ------------------------
    for msg in PC["messages"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(f"**{'You' if msg['role']=='user' else PC['QUIP_SELECTED']}:** {msg['content']}")

    # ------------------------
    # Handle new input
    # ------------------------
    user_input = st.chat_input("Say something to your Quip guide…")
    if user_input:
        normalized = user_input.strip().lower()

        # Reset command
        if normalized in ["reset", "restart", "clear"]:
            PC["messages"] = []
            if "WF" in PC:
                del PC["WF"]
            st.session_state.PLAIDMAGGEN = {"step": 0, "answers": {}}
            with st.chat_message("assistant"):
                st.markdown(f"**{PC['QUIP_SELECTED']}:** Reset complete! Fresh start. 🚀")
        else:
            # Save user message
            PC["messages"].append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(f"**You:** {user_input}")

            if normalized.startswith("lets libate") or normalized.startswith("lets lib-ate"):
                handle_workflow("Lib-Ate")
            elif normalized.startswith("lets create direct") or normalized.startswith("lets direct"):
                handle_workflow("Create_Direct")
            elif normalized.startswith("lets storyline"):
                handle_workflow("Storyline")
            elif normalized.startswith("lets plaidmaggen it") or normalized.startswith("maggen it"):
                handle_plaidmaggen()
            elif "WF" in PC:
                handle_workflow(PC["WF"]["name"], user_input)
            elif st.session_state.PLAIDMAGGEN["step"] > 0:
                handle_plaidmaggen(user_input)
            # --- NEW FEATURE: Generate Image ---
            elif normalized.startswith("generate image"):
                # Get the text after "generate image"
                text_after = user_input[len("generate image"):].strip()

                if text_after:
                    scene_text = text_after
                else:
                    # Use last assistant message
                    last_assistant_msgs = [m["content"] for m in PC["messages"] if m["role"] == "assistant"]
                    if last_assistant_msgs:
                        scene_text = last_assistant_msgs[-1]
                    else:
                        assistant_message("⚠️ No text available to generate an image from.")
                        scene_text = None
                
                if scene_text:
                    prompt = f"Illustration of: {scene_text}\nStyle: whimsical, PlaidLibs vibe."
                    with st.spinner("🎨 Generating image..."):
                        try:
                            result = client.images.generate(
                                model="gpt-image-1",
                                prompt=prompt[:900],
                                size="1024x1024"
                            )
                            img_b64 = result.data[0].b64_json
                            img_bytes = base64.b64decode(img_b64)
                            img = Image.open(BytesIO(img_bytes))
                            st.session_state.generated_image = img
                            with st.chat_message("assistant"):
                                st.image(img, caption="Generated Image", use_container_width=True)
                        except Exception as e:
                            assistant_message(f"⚠️ Failed to generate image: {e}")

            else:
                # Regular persona reply
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": f"You are {PC['QUIP_SELECTED']}, a playful narrator."},
                        *[
                            {"role": "assistant" if m["role"]=="assistant" else "user", "content": m["content"]}
                            for m in PC["messages"]
                        ]
                    ],
                    max_tokens=300,
                    temperature=0.9
                )
                reply = response.choices[0].message.content.strip()
                PC["messages"].append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.markdown(f"**{PC['QUIP_SELECTED']}:** {reply}")

















































