"""Builds the static rescue of Academics For You (academicsforyou.weebly.com, made in 2015).

Run: python3 build.py   (writes the .html files next to this script)

Everything here was read from the Weebly editor on 3 Nov 2026:
- The look (look/) is a hand-made recreation of the original Weebly theme: every image is my own
  SVG or CSS. No Weebly theme files are included.
- Each page keeps its original header type (landing, tall header, short header).
- Text keeps its original formatting, written in a small markup:
    {font c#ff0000 s5}...{/font}  {u}..{/u}  {strong}..{/strong}  {span wbold}..{/span}
    {a hUwww.example.com}..{/a}   {br}   ~ (non-breaking space)
- Typos are kept on purpose. Only quiz links that pointed at the wrong page were fixed.
"""
import json
import random
import re
from collections import Counter
from html import escape, unescape
from pathlib import Path

OUT = Path(__file__).parent
YT_CHANNEL = "https://www.youtube.com/@academicsforyoucompany9468"
KA = "https://www.khanacademy.org/science/biology/chemistry--of-life"

# Page index (as in the Weebly page list) -> file name
SLUGS = [
    "index", "about", "math", "addition",
    "addition-q1", "addition-q1-retry", "addition-q2", "addition-q2-retry", "addition-q3", "addition-q3-retry",
    "addition-q4-retry", "addition-q4", "addition-q5", "addition-q5-retry", "addition-done",
    "subtraction", "multiplication", "division",
    "english", "nouns", "adjectives", "verbs",
    "english-quiz", "english-q1-retry", "english-q2", "english-q2-retry", "english-q3", "english-q3-retry",
    "english-q4", "english-q4-retry", "english-q5", "english-q5-retry", "english-bonus", "english-done",
    "french", "atoms", "atoms-info", "atoms-more", "atoms-quiz", "contact", "subjects",
]

# Navigation, as shown in the original menu ("Group excess pages under More...")
NAV = [
    ("Home", 0, []),
    ("About", 1, []),
    ("Math", 2, [("Addition", 3, []), ("Subtraction", 15, []), ("Multiplication", 16, []), ("Division", 17, [])]),
    ("English", 18, [("Nouns", 19, []), ("Adjectives", 20, []), ("Verbs", 21, []), ("Quick Fun Quiz For English!", 22, [])]),
    ("French", 34, []),
    ("more...", None, [
        ("Atoms (Science)", 35, [("Information Based On Atoms", 36, []), ("Quick Fun Quiz For Atoms!", 38, [])]),
        ("Contact", 39, []),
    ]),
]


def href(target):
    if target is None:
        return None
    if isinstance(target, int):
        return f"{SLUGS[target]}.html"
    return target


def conv(markup):
    """Turn the stored markup back into the HTML Weebly saved."""
    out = []
    pos = 0
    for m in re.finditer(r"\{(/?)([a-z0-9]+)((?: [^{}]*)?)\}", markup):
        out.append(escape(markup[pos:m.start()], quote=False).replace("~", "&nbsp;"))
        pos = m.end()
        closing, tag, attrs = m.group(1), m.group(2), m.group(3).split()
        if tag == "br":
            out.append("<br>")
            continue
        if closing:
            out.append(f"</{tag}>")
            continue
        html_attrs, style = [], []
        for a in attrs:
            if tag == "font" and a.startswith("c"):
                html_attrs.append(f'color="{a[1:]}"')
            elif tag == "font" and a.startswith("s"):
                html_attrs.append(f'size="{a[1:]}"')
            elif a.startswith("w"):
                style.append(f"font-weight:{a[1:]}")
            elif a.startswith("c"):
                style.append(f"color:{a[1:]}")
            elif tag == "a" and a.startswith("hU"):
                html_attrs.append(f'href="http://{a[2:]}" target="_blank" rel="noopener"')
        if style:
            html_attrs.append(f'style="{";".join(style)}"')
        out.append(f"<{tag}{' ' if html_attrs else ''}{' '.join(html_attrs)}>")
    out.append(escape(markup[pos:], quote=False).replace("~", "&nbsp;"))
    return "".join(out)


# ---------------------------------------------------------------- elements

def T(al, m):
    return ("T", al, m)


def P(al, m):
    return ("P", al, m)


def B(al, size, style, target, text):
    return ("B", al, size, style, target, text)


def COLS(*cols):
    return ("COLS", cols)


WRONG_A = "{font c#ff0000 s3}You Got The Answer Wrong, Why Don't You Try Again!{/font}{br}{br}{font c#0034ff}{font s4}If You Don't Know The Answer, Click Below To Move On To The Next Question!{/font}{/font}"
WRONG_A2 = "{font c#ff0000 s3}You Got The Answer Wrong, Why Don't You Try Again!{/font}{br}{br}{font c#0034ff}{font s4}If You Don't Know The Answer, Click Below{span}~To Move On To The Next Question{/span}!{/font}{/font}"
WRONG_E = "{font c#ff0000}You Got The Answer Wrong, Why Don't You Try Again!{/font}{br}{br}{font c#0034ff}{font s4}If You Don't Know The Answer, Click Below To Move On To The Next Question!{/font}{/font}"
DONT_KNOW = "Don't Know, Click Here To Move On"


def answers(*pairs):
    return [B("left", "small", "normal", t, label) for label, t in pairs]


def retry_page(question, first, rest, wrong, nxt, dk_align="center"):
    """The 'Try Again' layout: question and first answer on the left, the message on the right."""
    left = [T("left", question)] + ([first] if first else [])
    right = [P("left", wrong), B(dk_align, "small", "highlight", nxt, DONT_KNOW)]
    return [COLS(left, right)] + rest


def add_q(n, sum_, opts, wrong_to, right_to, retry=False, wrong=WRONG_A):
    q = f"Question {n}:~{{br}}{{br}}{sum_}"
    btns = answers(*[(o, right_to if ok else wrong_to) for o, ok in opts])
    if not retry:
        return [T("left", q)] + btns
    return retry_page(q, btns[0], btns[1:], wrong, right_to)


def eng_q(n, question, opts, wrong_to, right_to, retry=False, first_in_left=True, dk_align="left"):
    q = "{font s6}Question " + str(n) + ":~{br}{br}" + question + "{/font}"
    btns = answers(*[(o, right_to if ok else wrong_to) for o, ok in opts])
    if not retry:
        return [T("left", q)] + btns
    first = btns[0] if first_in_left else None
    rest = btns[1:] if first_in_left else btns
    return retry_page(q, first, rest, WRONG_E, right_to, dk_align=dk_align)


LESSON_TAIL = "{br}{br}{font}{font c#00e4fe}Now we have our Answer.{/font}{br}{br}{font c#2a2a2a s6}"

PAGES = {}

# 0 Home (landing layout)
PAGES[0] = ("Home", "landing", [
    T("left", "Hi Guys!{br}{br}Welcome To Academics For You where the more you learn, the better!"),
    B("left", "large", "highlight", 40, "Click Here To Select A Subject"),
])
LANDING = {
    "headline": "Begin Learnin{font s6}g{/font}",
    "paragraph": "Have NO time to talk to teachers!{br}Teachers TOO busy to talk to you!{br}Well, you have landed on the right website!",
    "button": ("large", "highlight", 40, "Pick A Subject"),
}

# 1 About (short header)
PAGES[1] = ("About", "short", [
    T("center", "{font c#fa0000}FOR{/font} {font c#0016fa}THE{/font} {font c#fa9100}BEST{/font} {font c#0efa00}LEARNING {/font}{font c#6d00fa}EXPERIENCE!~{/font}"),
    P("left", "{font c#fa0000}Hi there!{/font}{br}{br}{font c#0024fa}Academics For You was made for those boys and girls who don't understand what they learn in class and also the teachers have no time to talk you (Due to their usual excuses \"I have another class,\" \"Sorry, I'm busy,\" and \"Sorry, I have to go.\") or when you have no time to talk to the teacher. It is a FREE website which gives learning and activities for the most important subjects.{/font}{br}{br}{font c#ff9b00}When there is no time children can come to this website as it is child-friendly and super safe. We have four subjects to teach which are math, English, French and science. This website can also be used as a tutor or could be used for practicing.{/font}{br}{br}{font c#00ff00}Happy Learning!{/font}"),
    COLS(
        [("COUNTER", "{font c#5040ae}Recommended By:{/font}", 27, "{font c#508d24}Teachers{/font}", False)],
        [("COUNTER", "{font c#4caac9}Adored By:{/font}", 16, "{font c#d061c7}Parents{/font}", False)],
    ),
    ("COUNTER", "{font c#da8044}Our Total:{/font}", 43, "Lovers! (Of The Website, Of Course!)", True),
])

# 2 Math
PAGES[2] = ("Math", "tall", [
    T("center", "Pick The Unit From The Following:"),
    B("center", "small", "normal", 3, "Addition"),
    B("center", "large", "highlight", 15, "Subtraction"),
    B("center", "large", "normal", 16, "Multipication"),
    B("center", "small", "highlight", 17, "Division"),
])

# 3 Addition lesson
PAGES[3] = ("Addition", "tall", [
    T("center", "{u}{font c#00f4ff}Addition{/font}{/u}"),
    P("left", "{u}{font c#ff0000}{font s5}What Does Addition Mean?{/font}{/font}{/u}{br}{font c#0419fb}Addition is when you put two or more values together.{/font}{br}{br}{u}{font}{font s5}{font c#fa9100}When To Do Addition?{/font}{/font}{/font}{/u}{br}{font}{font c#04fb36}You do Addition when you see the plus sign like this:{/font}{br}{font s4}~ ~ ~ ~ ~ ~ ~1{/font} {strong}{font s7}+{/font}{/strong} {font c#2a2a2a}1 ={/font}{br}{u}{font}{font s5}{font c#9b00ff}How To Do Addition?{/font}{/font}{/font}{/u}{br}{font}{font c#00cfff}F{font s4}{/font}irst of all, here is an question:{/font}{br}{br}{font}{font}{font}{font s6}5 + 3 = ?{/font}{/font}{br}{font}{font}{font}{font}{br}{font s3}{font c#00edff}Secondly, you count 5 more than 3, like this:{/font}{/font}{br}{br}{u}{font s6}{font c#2a2a2a}5 6 7 {/font}{font c#ae40a5}8{/font}{/font}{/u}{br}{font c#2a2a2a s6}0 1 2 3{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}" + LESSON_TAIL + "5 + 3 = 8{/font}{br}{br}{font c#00e4fe}Play The Video For More!{/font}{/font}"),
    ("YT", "vj0fBV1E420"),
    B("center", "small", "highlight", 4, "QUICK FUN QUIZ ON ADDITION"),
])

# 4-14 Addition quiz
ADD = [
    (1, "3 + 5 = ?", [("4", 0), ("6", 0), ("8", 1), ("10", 0)]),
    (2, "9 + 4 = ?", [("15", 0), ("13", 1), ("5", 0), ("10", 0)]),
    (3, "14 + 3 = ?", [("20", 0), ("11", 0), ("25", 0), ("17", 1)]),
    (4, "17 + 14 = ?", [("38", 0), ("26", 0), ("31", 1), ("19", 0)]),
    (5, "24 + 26 = ?", [("4", 0), ("33", 0), ("97", 0), ("50", 1)]),
]
ADD_PAGES = {1: (4, 5), 2: (6, 7), 3: (8, 9), 4: (11, 10), 5: (12, 13)}  # question -> (page, retry page)
for n, s, opts in ADD:
    page, retry = ADD_PAGES[n]
    nxt = ADD_PAGES[n + 1][0] if n < 5 else 14
    wrong = WRONG_A if n <= 2 else WRONG_A2
    PAGES[page] = (f"Question {n} - Addition", "tall", add_q(n, s, opts, retry, nxt))
    PAGES[retry] = (f"Question {n} - Try Again - Addition", "tall", add_q(n, s, opts, retry, nxt, retry=True, wrong=wrong))

CONGRATS = "CONGRATULATIONS!{br}YOU HAVE FINISHED THE {quiz} QUIZ!{br}{br}LOOK ON THE NAVIGATION BAR FOR MORE ACTIVITIES!"
PAGES[14] = ("Congrats, You've Finished The + Quiz", "tall", [
    T("center", CONGRATS.replace("{quiz}", "ADDITION")),
    ("CONGRATS_CARD",),
])

# 15-17 Maths lessons
PAGES[15] = ("Subtraction", "tall", [
    T("center", "{u}{font c#00f4ff}Subtraction{/font}{/u}"),
    P("left", "{u}{font c#ff0000}{font s5}What Does Subtraction Mean?{/font}{/font}{/u}{br}{font c#0419fb}Addition is the process of taking one number or amount away from another.{/font}{br}{br}{u}{font}{font s5}{font c#fa9100}When To Do Subraction?{/font}{/font}{/font}{/u}{br}{font}{font c#04fb36}You do Subtraction when you see the plus sign like this:{/font}{br}{font s4}~ ~ ~ ~ ~ ~ ~1{/font}~{font s7}{span}{strong}-{/strong}{/span}{/font}~{font c#2a2a2a}1 ={/font}{br}{u}{font}{font s5}{font c#9b00ff}How To Do Subtraction?{/font}{/font}{/font}{/u}{br}{font}{font c#00cfff}First of all, here is an question:{/font}{br}{br}{font}{font}{font}{font s6}5 - 3 = ?{/font}{/font}{br}{font}{font}{font}{font}{br}{font s3}Secondly, you count 3 less than 5, like this:{/font}{br}{br}{u}{font s6}{font c#2a2a2a}5 4 3 {/font}{font c#ae40a5}2{/font}{/font}{/u}{br}{font c#2a2a2a s6}0 1 2 3{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}" + LESSON_TAIL + "5 - 3 = 2{/font}{br}{br}{font c#00e4fe}Play The Video For More!{/font}{/font}"),
    ("YT", "lPtOpq0mnzQ"),
    T("center", "{u}HERE IS A QUICK MATH QUIZ:{/u}"),
    ("SCRATCH", "80235648"),
])

PAGES[16] = ("Multiplication", "tall", [
    T("center", "{u}{font c#00f4ff}Multiplication{/font}{/u}"),
    P("left", "{u}{font c#ff0000}{font s5}What Does Multiplication Mean?{/font}{/font}{/u}{br}{font c#0419fb}Multiplication is when you add a number a certain number of times.{/font}{br}{br}{u}{font}{font s5}{font c#fa9100}When To Do Multiplication?{/font}{/font}{/font}{/u}{br}{font}{font c#04fb36}You do Multiplication when you see the plus sign like this:{/font}{br}{font s4}~ ~ ~ ~ ~ ~ ~1{/font}~{font s7}{span}{strong}x{/strong}{/span}{/font}~{font c#2a2a2a}1 ={/font}{br}{u}{font}{font s5}{font c#9b00ff}How To Do Multiplication?{/font}{/font}{/font}{/u}{br}{font}{font c#00cfff}First of all, here is an question:{/font}{br}{br}{font}{font}{font}{font s6}3 x 5 = ?{/font}{/font}{br}{font}{font}{font}{font}{br}{font s3}{font c#00ebf5}Secondly, you make 3 groups of 5, like this:{/font}{/font}{br}{br}{u}{font s6}{font c#2a2a2a}Group 1{/font}{/font}{/u}{font s6}{font c#2a2a2a} ~{/font}{/font}{u}{font s6}{font c#2a2a2a}Group 2{/font}{/font}{/u}{font s6}{font c#2a2a2a} ~{/font}{/font}{u}{font s6}{font c#2a2a2a}Group 3{/font}{/font}{/u}{br}{font c#2a2a2a s6}[*****] ~~{span}[*****] ~ ~[*****]{/span}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{br}{br}{font}{font c#00e4fe}{span}Thirdly, you add every thing in the box:{br}{br}{/span}{font s6}{font c#2a2a2a}5 + 5 + 5 = 15{/font}{/font}{span}{br}{/span}{br}Now we have our Answer.{/font}{br}{br}{font c#2a2a2a s6}3 x 5 = 15{/font}{br}{br}{font c#00e4fe}Play The Video For More!{/font}{/font}"),
    ("YT", "vKKxBPt5MW8"),
    ("SCRATCH", "80240120"),
])

PAGES[17] = ("Division", "tall", [
    T("center", "{u}{font c#00f4ff}Division{/font}{/u}"),
    P("left", "{u}{font c#ff0000}{font s5}What Does Division Mean?{/font}{/font}{/u}{br}{font c#0419fb}Division is the process of~separating~an amount and~{/font}{br}{br}{u}{font}{font s5}{font c#fa9100}When To Do Division?{/font}{/font}{/font}{/u}{br}{font}{font c#04fb36}You do Addition when you see the plus sign like this:{/font}{br}{font s4}~ ~ ~ ~ ~ ~ ~1{/font}~{font s7}{span}{strong}/{/strong}{/span}{/font}~{font c#2a2a2a}1 ={/font}{br}{u}{font}{font s5}{font c#5040ae}How To Do Division?{/font}{/font}{/font}{/u}{br}{font}{font c#00ddfe}First of all, here is an question:{/font}{br}{br}{font}{font}{font c#2a2a2a}{font}{font s6}6~{/font}{/font}{a hUwww.rapidtables.com/math/symbols/Division_Sign.htm}{font s6}÷{/font}{/a}~{/font}{font}{font s6}{font c#2a2a2a}3 =?{/font}{/font}{/font}{br}{font}{font}{font}{font}{br}{font s3}{font c#00ffed}Secondly, you make groups of 3 out of six, like this:{/font}{/font}{br}{br}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{font c#2a2a2a s6}{span}[123] [456]{/span}{/font}{br}{br}{font}{font c#00e4fe}Now we have our Answer.{/font}{br}{br}{font c#2a2a2a s6}{font s6}6~{/font}{a hUwww.rapidtables.com/math/symbols/Division_Sign.htm}{font s6}÷{/font}{/a}~{font s6}3 = 2{/font}{/font}{br}{br}{font c#00e4fe}Play The Video For More!{/font}{/font}"),
    ("YT", "Xjek_c9kPKE"),
    ("SCRATCH", "80241794"),
])

# 18-21 English
PAGES[18] = ("English", "tall", [
    T("center", "Pick The Unit From The Following:"),
    B("center", "small", "normal", 19, "Nouns"),
    B("center", "small", "highlight", 20, "Adjectives"),
    B("center", "large", "normal", 21, "Verbs"),
    B("center", "large", "highlight", 22, "Quick Fun Quiz"),
])


def examples_heading(word):
    return P("center", "{u}{font c#ff0000 s5}What Are Some Examples Of The Types~{/font}{font c#ff0000}{font s5}Of " + word + "?{/font}{/font}{/u}")


PAGES[19] = ("Nouns", "tall", [
    T("center", "{font c#8640ae}{u}Nouns{/u}{/font}"),
    P("left", "{span}{font s5}{span}{u}{font c#ff0000}What Is The Definition Of Nouns?{/font}{/u}{/span}{/font}{br}{font c#0007ff}A word used to identify a of person, places, or things.{/font}{/span}{br}{br}{font s5}{u}{font c#fb8300}What Types Of Nouns Are There?{/font}{/u}{/font}{br}{font c#00ff07}There are two types of nouns:{br}1. ~ ~ ~Proper Nouns.{br}2. ~ ~ ~Common Nouns.{br}Proper Nouns use particular names of people and places.{br}Common Nouns use broad~names of people and places.{/font}"),
    examples_heading("Nouns"),
    COLS(
        [P("right", "{u}{font s5}{font c#00fffb}Proper Nouns{/font}{/font}{/u}{br}{font s4}{font c#218308}1. ~ ~ ~ ~ ~ ~ ~ ~Thomas.{br}2.{/font}{span}{font c#218308}~ ~ ~ ~ ~ ~ ~ ~ ~ ~Kenya.{br}3. ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ Jerry.{br}4. ~ ~ ~ ~ ~ ~ New York.{br}5. ~ ~ ~ ~ ~ ~ ~ ~ ~ ~Harry.{br}6. ~ ~ ~ ~ ~ ~ ~ Australia{/font}.{/span}{/font}{br}{font s5}{/font}")],
        [P("left", "{u}{font s5}{font c#00faef}Common Nouns{/font}{/font}{/u}{br}{font s4}{font c#218308}1. ~ ~ ~ ~ ~ ~ ~ ~ ~ Table.{br}2.{/font}{font c#218308}~ ~ ~ ~ ~ ~ ~ ~ ~ ~Boy.{br}3. ~ ~ ~ ~ ~ ~ ~ ~ ~ Tower.{br}4. ~ ~ ~ ~ ~ ~ ~ ~ ~ Girls.{br}5. ~ ~ ~ ~ ~ ~ ~ ~ ~ Chair.{br}6. ~ ~ ~ ~ ~ ~ ~ ~ ~ House{/font}.{/font}{br}{font s5}{/font}")],
    ),
])

PAGES[20] = ("Adjectives", "tall", [
    T("center", "{font c#8640ae}{u}Adjectives{/u}{/font}"),
    P("left", "{span}{font s5}{span}{u}{font c#ff0000}What Is The Definition Of Adjective?{/font}{/u}{/span}{/font}{br}{font c#0007ff}A word used to describe a of noun.{/font}{/span}{br}{br}{font s5}{u}{font c#fb8300}What Types Of Adjectives Are There?{/font}{/u}{/font}{br}{font c#00ff07}There are two types of adjectives:{br}1. ~ ~ ~Quality Adjectives.{br}2. ~ ~ ~Quantity~{span}Adjectives{/span}.{br}{span}Quality Adjectives{/span}~are used to describe the~characteristics~of a noun.{br}{span}Quantity~{/span}{span}Adjectives{/span}~are used to~{span}show a broad amount of the noun being described{/span}.{/font}"),
    examples_heading("Adjectives"),
    COLS(
        [P("right", "{u}{font s5}{font c#00fffb}Quality Adjectives{/font}{/font}{/u}{br}{font s4}{font c#218308}1. ~ ~ ~ ~ ~ ~ ~ ~Honest.{br}2.{/font}{span}{font c#218308}~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~Kind.{br}3. ~ ~ ~ ~ ~ ~ ~ ~ ~ Large.{br}4. ~ ~ ~ ~ ~ ~ ~ ~ ~ Bulky.{br}5. ~ ~ ~ ~ ~ ~ Beautiful.{br}6. ~ ~ ~ ~ ~ ~ ~ ~ ~ ~Ugly{/font}.{/span}{/font}{br}{font s5}{/font}")],
        [P("left", "{u}{font s5}{font c#00fffb}Quality Adjectives{/font}{/font}{/u}{br}{font s4}{font c#218308}1. ~ ~ ~ ~ ~ ~ ~ ~ ~ All.{br}2.{/font}{font c#218308}~ ~ ~ ~ ~ ~ ~ ~ ~ ~Half.{br}3. ~ ~ ~ ~ ~ ~ ~ ~ ~ Many.{br}4. ~ ~ ~ ~ ~ ~ ~ ~ ~ Few.{br}5. ~ ~ ~ ~ ~ ~ ~ ~ ~ Little.{br}6. ~ ~ ~ ~ ~ ~ ~ ~ ~ Enough{/font}.{/font}{br}{font s5}{/font}")],
    ),
])

PAGES[21] = ("Verbs", "tall", [
    T("center", "{font c#8640ae}{u}Verbs{/u}{/font}"),
    P("left", "{span}{font s5}{span}{u}{font c#ff0000}What Is The Definition Of Verbs?{/font}{/u}{/span}{/font}{br}{font c#0007ff}A word use to describe the action of a noun.{/font}{/span}{br}{br}{font s5}{u}{font c#fb8300}What Types Of Verbs Are There?{/font}{/u}{/font}{br}{font c#00ff07}There are two types of verbs:{br}1. ~ ~ ~Action~{span}Verb{/span}s.{br}2. ~ ~ ~Linking~{span}Verb{/span}s.{br}{span}Action~{/span}{span}Verb{/span}{span}s{/span}~are used to show what{span}~the subject is doing at that time in the sentence.{/span}{br}{span}Linking~{/span}{span}Verb{/span}{span}s{/span}~are used to {span}in describing or providing additional information about the subject.{/span}{/font}"),
    examples_heading("Verbs"),
    COLS(
        [P("right", "{u}{font s5}{font c#00fffb}Action Verbs{/font}{/font}{/u}{br}{font s4}{font c#218308}1. ~ ~ ~ ~ ~ ~ ~ ~Work.{br}2.{/font}{span}{font c#218308}~ ~ ~ ~ ~ ~ ~ ~ ~Paint.{br}3. ~ ~ ~ ~ ~ ~ ~ ~Sleep.{br}4. ~ ~ ~ ~ ~ ~ ~ ~ Stop.{br}5. ~ ~ ~ ~ ~ ~ ~ ~ ~Run.{br}6. ~ ~ ~ ~ ~ ~ ~Throw{/font}.{/span}{/font}{br}{font s5}{/font}")],
        [P("left", "{u}{font s5}{font c#00fffb}Linking Verbs{/font}{/font}{/u}{br}{font s4}{font c#218308}1. ~ ~ ~ ~ ~ ~ ~ ~ ~ Is.{br}2.{/font}{font c#218308}~ ~ ~ ~ ~ ~ ~ ~ ~ ~Are.{br}3. ~ ~ ~ ~ ~ ~ ~ ~ ~ Am.{br}4. ~ ~ ~ ~ ~ ~ ~ ~ ~ Were.{br}5. ~ ~ ~ ~ ~ ~ ~ ~ ~ Does.{br}6. ~ ~ ~ ~ ~ ~ ~ ~ ~ Did{/font}.{/font}{br}{font s5}{/font}")],
    ),
])

# 22-33 English quiz (links fixed so each answer goes where it should)
RAINBOW_QUIZ = "{span wbold}{font c#ff0000 s7}Q{/font}{font s6}{font c#ff0000}UICK{/font}{font c#508d24}~{/font}{/font}{font c#1d00fa s7}F{/font}{font s6}{font c#1d00fa}UN{/font} {/font}{font c#fff406 s7}Q{/font}{font s6}{font c#fff406}UIZ{/font}{font c#16920a}~{/font}{/font}{font c#508d24 s7}O{/font}{font s6}{font c#508d24}N{/font} {/font}"
Q3 = "What is the underlined word?{br}{br}{u}{/u}{strong}\"{/strong}{u}{strong}Thomas{/strong}{/u}{strong}~ran into a deep, dark cave.\"{/strong}~"
Q4 = "Which word fits in the dash ( ____ ) properly?{br}{br}{strong}\"The Car is very~{/strong}{font s6}{strong}____ and modern{/strong}{/font}{strong}.\"{/strong}~"
Q5 = "What is the underlined word?{br}{br}{strong}\"Sally {u}sells{/u} sea shells by the sea shore{/strong}{strong}.\"{/strong}~"

PAGES[22] = ("Quick Fun Quiz For English!", "tall",
             [T("center", RAINBOW_QUIZ + "{font c#8640ae s7}E{/font}{font s6}{font c#8640ae}NGLISH{/font}{/font}{/span}")]
             + eng_q(1, "What is a Verb?", [("Words used to identify a person, etc.", 0), ("A Giant CattleFish", 0), ("Word used to portray what a noun does", 1), ("A word used to describe a of noun.", 0)], 23, 24))
PAGES[23] = ("Question 1 - Try Again - English", "tall",
             eng_q(1, "What is a Verb?", [("A Giant CattleFish", 0), ("Words used to identify a person, etc", 0), ("Word used to portray what a noun does", 1), ("A word used to describe a of noun", 0)], 23, 24, retry=True))
PAGES[24] = ("Question 2 - English", "tall", eng_q(2, "Which of the following is a Adjective?", [("Baby", 0), ("John", 0), ("Tall", 1), ("Run", 0)], 25, 26))
PAGES[25] = ("Question 2 - Try Again - English", "tall", eng_q(2, "Which of the following is a Adjective?", [("Baby", 0), ("John", 0), ("Tall", 1), ("Run", 0)], 25, 26, retry=True, first_in_left=False))
PAGES[26] = ("Question 3 - English", "tall", eng_q(3, Q3, [("A Noun", 1), ("A Cat", 0), ("An Adjective", 0), ("A Verb", 0)], 27, 28))
PAGES[27] = ("Question 3 - Try Again - English", "tall", eng_q(3, Q3, [("A Noun", 1), ("A Cat", 0), ("An Adjective", 0), ("A Verb", 0)], 27, 28, retry=True, first_in_left=False))
PAGES[28] = ("Question 4 - English", "tall", eng_q(4, Q4, [("Jumping", 0), ("Red", 1), ("Lion", 0), ("Jerry", 0)], 29, 30))
PAGES[29] = ("Question 4 - Try Again- English", "tall", eng_q(4, Q4, [("Jumping", 0), ("Red", 1), ("Lion", 0), ("Jerry", 0)], 29, 30, retry=True, first_in_left=False))
PAGES[30] = ("Question 5 - English", "tall", eng_q(5, Q5, [("A Noun", 0), ("A Type of Shell", 0), ("An Adjective", 0), ("A Verb", 1)], 31, 32))
PAGES[31] = ("Question 5 - Try Again - English", "tall", eng_q(5, Q5, [("A Noun", 0), ("A Type of Shell", 0), ("An Adjective", 0), ("A Verb", 1)], 31, 32, retry=True, first_in_left=False))
PAGES[32] = ("Bonus Question - English", "tall", [
    T("left", "{font s6}Bonus Question:{/font}{br}{font s6}{br}Pick one phrase from each column below and write a story. Try to use as many as Nouns, Adjectives and verbs is your story. After you have~completed~writing your story you can give it to your teacher or parent to mark and see for grammatical errors. You may also send it to us by email (with adult permission) and we will mark and send it back to you as fast as we can. (Click the email button above of the page to email us){br}{br}{/font}{font s5}A Old Man ~ ~ - ~ ~Who Went To China ~ ~ ~ - ~ ~ ~ And Became Leader An Area.{br}A Young Lad ~- ~ ~Who Fell Into A Well ~ ~ ~ - ~ ~ ~ ~ ~ ~And Met A New~Species.~{br}{/font}{font s5}Two Siblings ~- ~ ~Who Traveled The World ~- ~ ~ ~ ~ ~ Looking For Their Father.{br}{br}{/font}{font s6}{span}Write your story suggestion down on paper and begin to write your story. Remember to give it a title and write in paragraphs. Punctuation and Grammar will be marked.{/span}{/font}"),
    B("center", "small", "highlight", 33, "Click To Move On To The Next Page"),
])
PAGES[33] = ("Congrats, You've Finished The English Quiz", "tall", [
    T("center", CONGRATS.replace("{quiz}", "ENGLISH")),
    ("CONGRATS_CARD",),
])

# 34 French
PAGES[34] = ("French", "tall", [
    T("center", "{span wbold}{font c#ff0000 s7}F{/font}{font s6}{font c#ff0000}IRST{/font}{font c#508d24}~{/font}{/font}{font c#1d00fa s7}W{/font}{font s6}{font c#1d00fa}ORDS{/font}~{/font}{font c#fff406 s7}I{/font}{font s6}{font c#fff406}N{/font}{font c#16920a}~{/font}{/font}{font c#508d24 s7}F{/font}{font s6}{font c#508d24}RE{/font}{/font}{font s6}{font c#508d24}NCH -{/font}{/font}{font s6}{font c#8640ae}-{/font}{/font}{font s6}~{/font}{font c#8640ae s7}K{/font}{font s6}{font c#8640ae}I{/font}{/font}{font s6}{font c#8640ae}NDLY~{/font}{/font}{font c#da8044 s7}P{/font}{font s6}{font c#da8044}ROVIDED{/font}{font c#8640ae}~{/font}{/font}{font c#d061c7 s7}B{/font}{font s6}{font c#d061c7}Y{/font}{font c#8640ae}~{/font}{/font}{font c#248d6c}{font s7}E{/font}{font s6}U{/font}{/font}{font s6}{font c#248d6c}RO{/font}{/font}{font c#248d6c}{font s7}T{/font}{/font}{font s6}{font c#248d6c}ALK{/font}{/font}{/span}"),
    ("GONE", 676, 418, "The EuroTalk “First Words in French” app was embedded here. It no longer loads."),
    P("center", "{font s4}This Application Helps To Learn 'First' And Easy French Words And There Is An Easy Quiz Based On What You Have Learned.{br}~{br}{font s3}To Buy The Full Disk / USB ( With Adult Permission ) , Please Go To:{br}{/font}{/font}"),
    B("center", "large", "highlight", "https://www.eurotalk.com/en/store/learn/french", "Learn French | EuroTalk"),
])

# 35-38 Atoms
PAGES[35] = ("Atoms (Science)", "tall", [
    T("center", "{u}{font s7}{span}{font c#24678d}THE{/font} {font c#a82e2e}SELF{/font} {font c#c2a43b}LEARNING{/font} {font c#5fa233}PROCESS{/font}{/span}{/font}{/u}{br}{font s5}Here at Academics For You, we try to encourage children to use different learning techniques to help them gain~knowledge~from anywhere. These places could be texts and TV shows. One effective learning process is The Self Learning Process.~{br}{br}In our atoms unit, we expect children to watch the videos and read the texts kindly provided by Khan Academy, and try to take notes on what they learned and what is most important in that subject.{/font}"),
    P("left", "{font c#f90505}CAUTION / WARNING: IN THIS UNIT, YOU WILL SEE SOMETHING LIKE THIS:{/font}{br}{br}{font s5}{font c#2a2a2a}1^1{/font}{/font}{br}{br}{font s3}{font c#f90505}THIS WOULD MEAN:{br}{br}{/font}{/font}{span}{font s5}{font c#2a2a2a}One To The Power Of One{br}{br}{/font}{/font}{font c#f90404}OR:{/font}{/span}{br}"),
    ("IMG", "left", "images/power-example.jpg", "auto", "100%"),
    T("center", "{font s7}P{font s6}ICK~{/font}W{font s6}HAT~{font s7}Y{font s6}OU~{font s7}W{font s6}ANT~{font s7}T{font s6}O~{font s7}D{font s6}O~{font s7}F{font s6}ROM~{font s7}T{font s6}HE ~{font s7}F{font s6}OLLOWING:{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}{/font}"),
    B("center", "small", "normal", 36, "Interesting Information"),
    B("center", "large", "highlight", 38, "Quick Fun Quiz"),
])

KA_NOTE = "The articles for this page come from Khan Academy. Read them there:"
PAGES[36] = ("Information Based On Atoms", "tall", [
    T("center", "{u}{font s7}ELEMENTS & ATOMS{/font}{/u}"),
    ("YT", "IFKnq9QM6_A"),
    ("KA", KA_NOTE, [("Matter, elements, and atoms", f"{KA}/elements-and-atoms/a/matter-elements-atoms-article"),
                     ("Atomic number, atomic mass, and isotopes", f"{KA}/elements-and-atoms/a/atomic-number-atomic-mass-and-isotopes-article")]),
    ("YT", "1xSQlwWGT8M"),
    B("right", "large", "highlight", 37, "Click To Go To The Next Page ->"),
])
PAGES[37] = ("More Information Based On Atoms", "tall", [
    T("center", "{u}{font s7}ELECTRON SHELLS & ORBITALS{/font}{/u}"),
    ("YT", "yBrp8uvNAhI"), ("YT", "FmQoSenbtnU"), ("YT", "NYtPw0WiUCo"), ("YT", "UXOcWAfBdZg"),
    ("KA", KA_NOTE, [("The periodic table, electron shells, and orbitals", f"{KA}/electron-shells-and-orbitals/a/the-periodic-table-electron-shells-and-orbitals-article")]),
    B("right", "large", "highlight", 38, "Click To Go To The Next Page ->"),
])
PAGES[38] = ("Quick Fun Quiz For Atoms!", "tall", [
    T("center", RAINBOW_QUIZ + "{font c#8640ae s7}A{/font}{font s6}{font c#8640ae}TOMS{/font}{/font}{/span}"),
    ("GONE", 600, 600, "The quiz and flashcards were embedded here from another quiz website. They no longer load."),
    P("center", "{strong}{font c#0629f9}THE~QUIZ WILL TEST YOU ON WHAT YOU HAVE LEARNED ON THE INTERESTING INFORMATION PAGE.{/font}{br}{br}{font c#26fa0a}THE FLASHCARDS WILL ALSO TEST YOU BUT GIVE YOU THE DIRECTLY AFTER THE QUESTION WILL BE GIVEN.{/font}{br}{br}{font c#731161}WE RECOMMEND YOU BEGIN WITH THE FLASHCARDS AND THEN MOVE ON TO THE QUIZ AFTER YOU HAVE READ AND UNDERSTOOD THE INFORMATION.{/font}{br}{br}{font c#f90606}CAUTION: PLEASE DO NOT WANDER AROUND ON THIS QUIZ WEBSITE. YOU MIGHT NOT BE ABLE TO FIND THE QUIZ YOU ARE CURRENTLY AT AGAIN.{/font}{/strong}"),
])

# 39 Contact (short header)
PAGES[39] = ("Contact", "short", [
    T("center", "{u}{font c#06f922 s7}HOW TO CONTACT US{/font}{/u}"),
    COLS(
        [T("left", "Direct E-Mail To Our Inbox"),
         ("GONE", None, 180, "A contact form was here. Weebly forms don't work outside Weebly."),
         P("left", "Hi Guys, It would really be appreciated if you recommended this site to your friends."),
         T("center", "Rating"),
         ("GONE", None, 90, "A star-rating form was here.")],
        [P("left", "{font s5}OUR SOCIAL WEB FEED{br}{/font}{font c#f80404}{font s3}ONLY TO BE USED WITH ADULT SUPERVISION{/font}{/font}"),
         B("left", "small", "highlight", YT_CHANNEL, "Academics For You on YouTube"),
         T("left", "A Few Questions We Would Like To Ask You..."),
         ("GONE", None, 220, "A short survey form was here.")],
    ),
])

# 40 Subject Selection (hidden from the menu)
PAGES[40] = ("Subject Selection", "tall", [
    T("center", "Pick The Subject From The Following:"),
    B("center", "small", "normal", 2, "Math"),
    B("center", "large", "highlight", 18, "English"),
    B("center", "large", "normal", 34, "French"),
    B("center", "small", "highlight", 35, "Atoms (Science)"),
])

# ---------------------------------------------------------------- rendering

def button(size, style, target, text):
    cls = f"button {style}" + (" large" if size == "large" else "")
    ext = ' target="_blank" rel="noopener"' if isinstance(target, str) else ""
    return f'<a class="{cls}" href="{href(target)}"{ext}><span>{escape(text)}</span></a>'


def spacer(px=10):
    return f'<div style="height:{px}px;overflow:hidden"></div>'


def congrats_card():
    """The 'Congrats!' picture on the quiz-finished pages, drawn in HTML and CSS.
    (The original was a GIF of someone else's lettering, so this is a new one in the same spirit.)"""
    rnd = random.Random(2015)
    bits = []
    for _ in range(46):
        x, y = rnd.uniform(2, 96), rnd.uniform(3, 94)
        if 22 < y < 72 and 8 < x < 90 and rnd.random() < 0.75:
            continue  # keep the middle fairly clear for the word
        shape = rnd.choice(["squiggle", "squiggle", "dot"])
        colour = rnd.choice(["#4a8fd3", "#d9ac3f"])
        bits.append(f'<i class="{shape}" style="left:{x:.1f}%;top:{y:.1f}%;--r:{rnd.randint(0, 359)}deg;'
                    f'--c:{colour};animation-delay:-{rnd.random():.2f}s"></i>')
    return ('<div class="image" style="text-align:center"><div class="congrats-card" role="img" aria-label="Congrats!">'
            + "".join(bits) + '<span class="congrats-word">Congrats!</span></div></div>')


def render(el):
    kind = el[0]
    if kind == "T":
        return f'<h2 style="text-align:{el[1]};">{conv(el[2])}</h2>'
    if kind == "P":
        return f'<div class="paragraph" style="text-align:{el[1]};">{conv(el[2])}</div>'
    if kind == "B":
        _, al, size, style, target, text = el
        return f'<div style="text-align:{al};">{spacer()}{button(size, style, target, text)}{spacer()}</div>'
    if kind == "CONGRATS_CARD":
        return congrats_card()
    if kind == "IMG":
        _, al, src, w, maxw = el
        return f'<div class="image" style="text-align:{al}"><img src="{src}" alt="" style="width:{w};max-width:{maxw}"></div>'
    if kind == "YT":
        return (f'<div class="video"><div class="ratio"><iframe src="https://www.youtube.com/embed/{el[1]}" '
                f'title="YouTube video" allowfullscreen loading="lazy"></iframe></div></div>')
    if kind == "SCRATCH":
        return (f'<div class="embed"><iframe width="485" height="402" title="Scratch quiz" '
                f'src="https://scratch.mit.edu/projects/{el[1]}/embed" allowfullscreen loading="lazy"></iframe></div>')
    if kind == "COLS":
        width = 100 / len(el[1])
        tds = "".join(f'<td style="width:{width:.2f}%">' + "".join(render(c) for c in col) + "</td>" for col in el[1])
        return f'<table class="columns"><tr>{tds}</tr></table>'
    if kind == "COUNTER":
        _, top, n, bottom, bold = el
        return (f'<div class="counter"><div class="paragraph">{conv(top)}</div>'
                f'<div class="counter-number{" counter-bold" if bold else ""}" data-to="{n}">{n}</div>'
                f'<div class="paragraph">{conv(bottom)}</div></div>')
    if kind == "GONE":
        _, w, h, note = el
        size = f"width:{w}px;max-width:100%;" if w else ""
        return f'<div class="gone" style="{size}min-height:{h}px">{escape(note)}</div>'
    if kind == "KA":
        _, note, links = el
        items = "".join(f'<li><a href="{u}" target="_blank" rel="noopener">{escape(t)} (Khan Academy)</a></li>' for t, u in links)
        return f'<div class="paragraph ka-note"><p>{escape(note)}</p><ul>{items}</ul></div>'
    raise ValueError(kind)


def menu(items, current, top=True):
    lis = []
    for label, idx, kids in items:
        active = top and (idx == current or any(k[1] == current for k in kids))
        link = f' href="{href(idx)}"' if idx is not None else ""
        arrow = '<span class="arrow">&gt;</span>' if kids and not top else ""
        sub = f'<ul class="submenu">{menu(kids, current, False)}</ul>' if kids else ""
        lis.append(f'<li{" class=\"active\"" if active else ""}><a{link}>{escape(label)}{arrow}</a>{sub}</li>')
    return "".join(lis)


ICONS = {
    "Facebook": '<path d="M9.5 16V9h2.3l.4-2.7H9.5V4.6c0-.8.2-1.3 1.3-1.3h1.4V.9C11.9.8 11.1.7 10.2.7 8.2.7 6.8 1.9 6.8 4.2v2.1H4.5V9h2.3v7z"/>',
    "Email": '<path d="M1 3h14v10H1zM2.2 4.2v.3L8 8.6l5.8-4.1v-.3zM2.2 6v5.8h11.6V6L8 10.1z"/>',
    "Google+": '<path d="M5.5 7.2v1.9h2.6c-.2 1-1.1 2-2.6 2a3 3 0 0 1 0-6c.8 0 1.4.3 1.9.7l1.3-1.3A4.8 4.8 0 0 0 5.5 3.3a4.8 4.8 0 1 0 0 9.6c2.8 0 4.6-2 4.6-4.7l-.1-1zM16 7.2h-1.6V5.6h-1.3v1.6h-1.6v1.3h1.6v1.6h1.3V8.5H16z"/>',
    "YouTube": '<path d="M15.7 4.6a2 2 0 0 0-1.4-1.4C13 2.9 8 2.9 8 2.9s-5 0-6.3.3A2 2 0 0 0 .3 4.6 21 21 0 0 0 0 8a21 21 0 0 0 .3 3.4 2 2 0 0 0 1.4 1.4c1.3.3 6.3.3 6.3.3s5 0 6.3-.3a2 2 0 0 0 1.4-1.4A21 21 0 0 0 16 8a21 21 0 0 0-.3-3.4zM6.4 10.4V5.6L10.6 8z"/>',
}


# The 2015 header had four social buttons. Only YouTube still works.
DEAD = {
    "Facebook": "Facebook: this page has left the chat.",
    "Email": "Email: retired. Find me on YouTube instead.",
    "Google+": "Google+ (2011 to 2019). Gone, but not forgotten. 🪦",
}


def social():
    out = []
    for name, path in ICONS.items():
        svg = f'<svg viewBox="0 0 16 16" aria-hidden="true">{path}</svg>'
        if name == "YouTube":
            out.append(f'<a class="social-icon" href="{YT_CHANNEL}" target="_blank" rel="noopener" title="Academics For You on YouTube">{svg}</a>')
        else:
            out.append(f'<span class="social-icon dead" title="{escape(DEAD[name])}" aria-label="{escape(DEAD[name])}">{svg}</span>')
    return f'<span class="social-icons">{"".join(out)}</span>'


def banner(kind):
    if kind == "landing":
        h, p, (size, style, target, text) = LANDING["headline"], LANDING["paragraph"], LANDING["button"]
        return f"""
        <div id="bannerleft" class="frame">
          <div class="picture wordcloud"></div>
          <div class="clip"></div>
        </div>
        <div id="bannerright">
          <div class="middle">
            <h2>{conv(h)}</h2>
            <p>{conv(p)}</p>
            {button(size, style, target, text)}
          </div>
        </div>"""
    return """
        <div class="frame">
          <div class="picture"></div>
          <div class="clip"></div>
        </div>"""

# The home page picture is a word cloud of the site's own words (drawn by wordcloud.js).
# Small, everyday and quiz-instruction words are left out.
CLOUD_SKIP = set("""
the a an and or of to in is it you your for on this that be are as with at by from if i we our can will
what which do don't know click here move next question try again got answer wrong why there these those
has have was were they them their its it's so not all more some how when where who out up about just like
into than then also but very other any each one two three four five used below does page no see khan
academy following mean go pick secondly now first come amount us would give after another email form
contact based hi thomas use time places unit sign group person common examples linking run identify
definition flashcards finished underlined adult proper write read words
you've could most new look sorry bar eurotalk etc
""".split())


def cloud_words(limit=70):
    text = []
    for title, _, elements in PAGES.values():
        text.append(title)
        text.extend(render(e) for e in elements)
    joined = re.sub(r"</?(font|span|u|strong|b|i|em|a)\b[^>]*>", "", " ".join(text))  # inline tags: no gap
    plain = unescape(re.sub(r"<[^>]+>", " ", joined))
    counts = Counter(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z']+", plain) if w.lower() not in CLOUD_SKIP)
    return [[w, n] for w, n in counts.most_common(limit)]


FOOTER = f"""<div class="footer-note">
      <p>I made Academics For You on Weebly in 2015, aged 13, with a <a href="{YT_CHANNEL}" target="_blank" rel="noopener">YouTube channel</a> to go with it.</p>
      <p>Weebly shut down in Kenya in 2026, so I rescued it here and redrew its look by hand.</p>
      <p>The words are the originals, typos and all. Only a few broken quiz links were fixed.</p>
    </div>"""


# A parody of the "Powered by Weebly" tab that free Weebly sites had pinned to the bottom-left corner.
# Plain text in this site's own font: no Weebly logo, artwork or styling is copied.
WEEBLY_TAB = """<aside class="weebly-tab" aria-label="About Weebly">
  <div class="weebly-tab-panel">
    <p>Weebly hosted this site from 2015 to 2026.</p>
    <p>Gone, but not forgotten. 🪦</p>
  </div>
  <div class="weebly-tab-bar">POWERED BY <span class="rip">Weebly</span></div>
</aside>"""


def cloud_script(kind):
    if kind != "landing":
        return ""
    return f"""\n<script type="application/json" id="cloud-words">{json.dumps(cloud_words())}</script>\n<script src="wordcloud.js" defer></script>"""


def page_html(i):
    title, kind, elements = PAGES[i]
    body = "\n".join(render(e) for e in elements)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=980">
<title>{escape(title)} - Academics For You</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Coming+Soon&family=Nunito:wght@300;400;700&family=Yellowtail&display=swap" rel="stylesheet">
<link rel="stylesheet" href="look/style.css">
</head>
<body class="{kind}">
  <div id="header-wrap">
    <div id="header-wrap-inner">
      <div class="container">
        <table id="header"><tr><td class="phone"></td><td class="social">{social()}</td></tr></table>
      </div>
    </div>
  </div>

  <div id="nav-wrap">
    <div class="container">
      <table><tr>
        <td id="logo"><a href="index.html"><img src="images/logo.png" alt="Academics For You: The More You Know, The Better"></a></td>
        <td id="menu"><ul class="menu">{menu(NAV, i)}</ul></td>
      </tr></table>
    </div>
  </div>

  <div id="banner-wrap">
    <div class="container">
      <div id="banner">
        <div id="banner-top"></div>
{banner(kind)}
        <div class="clear"></div>
        <div class="scissors"></div>
      </div>
    </div>
  </div>

  <div id="main-wrap">
    <div class="container">
      <div id="content">
{body}
      </div>
    </div>
    <div id="main-wrap-image"></div>
  </div>

  <div id="footer-wrap">
    <div id="footer-wrap-inner"></div>
    <div class="container">
      {FOOTER}
    </div>
  </div>
{WEEBLY_TAB}
<script src="counter.js" defer></script>{cloud_script(kind)}
</body>
</html>
"""


def main():
    assert sorted(PAGES) == list(range(len(SLUGS))), "every page needs content"
    for i, slug in enumerate(SLUGS):
        (OUT / f"{slug}.html").write_text(page_html(i), encoding="utf-8")
    print(f"Wrote {len(SLUGS)} pages")


if __name__ == "__main__":
    main()
