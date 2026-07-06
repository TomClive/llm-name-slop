"""Name extraction from completions: spaCy PERSON NER + capitalised-token fallback."""

import re
from functools import lru_cache

# Professional/honorific titles: a single following name is a SURNAME
# ("Dr. Mercer" -> surname Mercer, "Detective Chen" -> surname Chen).
PROFESSIONAL_TITLES = {
    "dr", "mr", "mrs", "ms", "miss", "sir", "dame", "lady", "lord",
    "captain", "capt", "professor", "prof", "sergeant", "sgt", "detective",
    "inspector", "officer", "agent", "colonel", "major", "general",
    "king", "queen", "prince", "princess", "duke", "duchess",
    "reverend", "rev", "saint", "st", "master", "madame",
    "mademoiselle", "señor", "señora", "herr", "frau", "constable", "pc",
}

# Kinship/familiar/role prefixes: stripped, but a single following name is a
# FIRST name ("Aunt Mira" -> Mira, "DJ Flynn" -> Flynn), unlike professional
# titles. Also "Old Kael" -> Kael.
KINSHIP_PREFIXES = {
    "father", "mother", "sister", "brother", "aunt", "uncle", "grandma",
    "grandpa", "granny", "nan", "nana", "mum", "mom", "dad", "cousin",
    "old", "young", "little", "big", "dj", "mc",
}

TITLES = PROFESSIONAL_TITLES | KINSHIP_PREFIXES  # union, for membership tests
ADJ_PREFIXES = KINSHIP_PREFIXES  # backward-compat alias

# Building/place words: a PERSON span ending in one of these is a location
# ("Ravenswood Lighthouse"), not a character. Kept conservative to avoid
# dropping real surnames (Hall, Forest, Bay, Park are intentionally absent).
STRUCTURE_WORDS = {
    "lighthouse", "manor", "station", "tavern", "inn", "abbey", "cathedral",
    "university", "college", "academy", "hospital", "prison", "palace",
    "castle", "harbour", "harbor", "cottage", "monastery", "asylum",
}

# Words NER or the fallback sometimes surfaces that are never character names.
STOPLIST = {
    "the", "a", "an", "god", "gods", "heaven", "hell", "earth", "moon", "sun",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "christmas", "easter", "halloween", "thanksgiving",
    "fantasy", "romance", "thriller", "horror", "mystery",
    "opening", "sentences", "sentence", "story", "chapter", "prologue",
    "title", "protagonist", "character", "part",
    "london", "york", "paris", "america", "england", "britain", "uk", "usa",
    "north", "south", "east", "west", "street", "avenue", "road",
    "i", "he", "she", "they", "it", "we", "you", "her", "his", "their",
    "but", "and", "or", "when", "then", "now", "here", "there", "yet",
    "as", "at", "by", "in", "on", "of", "if", "so", "no", "not", "with",
    "before", "after", "every", "each", "still", "even", "only", "just",
    "inside", "outside", "beneath", "beyond", "behind", "above", "below",
    "suddenly", "meanwhile", "tonight", "today", "tomorrow", "yesterday",
    "nobody", "someone", "everyone", "nothing", "something", "everything",
    "for", "from", "that", "this", "these", "those", "what", "who", "how",
    "why", "where", "which", "all", "both", "her.", "his.",
}


@lru_cache(maxsize=1)
def _nlp():
    import spacy
    return spacy.load("en_core_web_sm", disable=["lemmatizer"])


def _clean_token(tok: str) -> str:
    # possessive first: "Taylor's" must not degrade to "Taylors"
    tok = re.sub(r"(’s|'s|’|')$", "", tok.strip())
    tok = re.sub(r"[\"'‘’“”()\[\],.;:!?*_]+", "", tok)
    return tok.strip("-–— ")


def _parse_person(raw: str, preceded_by_title: bool = False) -> list[tuple[str, str]]:
    """Split one PERSON span into (first, surname) pairs; '' if unknown.

    Returns a list because a cleaned span is occasionally empty.
    """
    tokens = [_clean_token(t) for t in raw.split()]
    # A span ending in a building/place word is a location, not a person.
    if tokens and tokens[-1].lower() in STRUCTURE_WORDS:
        return []
    had_title = preceded_by_title
    while tokens:
        head = tokens[0].lower().rstrip(".")
        if head in PROFESSIONAL_TITLES:
            tokens.pop(0)
            had_title = True          # single remaining token -> surname
        elif head in KINSHIP_PREFIXES:
            tokens.pop(0)             # single remaining token -> first name
        else:
            break
    tokens = [t for t in tokens if t and t[0].isupper() and len(t) >= 2
              and t.lower() not in STOPLIST]
    if not tokens:
        return []
    if len(tokens) == 1:
        # "Dr. Chen" -> surname; bare "Elara" or "Aunt Mira" -> first name
        return [("", tokens[0])] if had_title else [(tokens[0], "")]
    return [(tokens[0], tokens[-1])]


def _fallback_names(text: str) -> list[tuple[str, str]]:
    """Capitalised-token heuristic for outputs where NER finds nothing.

    Takes runs of capitalised words that are not sentence-initial (or are
    sentence-initial but repeat elsewhere mid-sentence), filters the stoplist.
    """
    words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", text)
    sentence_starts = set(re.findall(r"(?:^|[.!?]\s+)([A-Z][a-z]+)", text))
    mid_sentence = {w for w in re.findall(r"[a-z,;]\s+([A-Z][a-z]+)", text)}
    pairs = []
    for run in words:
        toks = run.split()
        if toks and toks[-1].lower() in STRUCTURE_WORDS:
            continue                  # "Ravenswood Lighthouse" = place
        toks = [t for t in toks if t.lower() not in STOPLIST
                and t.lower().rstrip(".") not in TITLES]
        toks = [t for t in toks
                if t in mid_sentence or t not in sentence_starts]
        if not toks:
            continue
        if len(toks) == 1:
            pairs.append((toks[0], ""))
        else:
            pairs.append((toks[0], toks[-1]))
    return pairs


def extract_names(text: str,
                  known_first: set[str] | None = None) -> list[tuple[str, str]]:
    """All (first_name, surname) pairs found in text; '' marks an unknown half.

    known_first (casefolded gazetteer, e.g. SSA names) rescues names the small
    NER model mislabels (e.g. "Elena" tagged ORG): any mid-sentence proper
    noun matching the gazetteer is added as a first name.
    """
    if not text or not text.strip():
        return []
    doc = _nlp()(text)
    pairs = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # spaCy usually leaves "Dr."/"Captain" outside the span; a
            # title-preceded single token is a surname, not a first name.
            prev = doc[ent.start - 1] if ent.start > 0 else None
            # "the Wilsons"/"the Joneses" = family reference -> surname,
            # singularised
            if (prev is not None and prev.text.lower() == "the"
                    and len(ent) == 1 and ent.text.endswith("s")
                    and len(ent.text) > 3):
                singular = (ent.text[:-2] if ent.text.endswith(("ses", "xes", "zes"))
                            else ent.text[:-1])
                pairs.extend(_parse_person(singular, preceded_by_title=True))
                continue
            titled = (prev is not None
                      and prev.text.lower().rstrip(".") in PROFESSIONAL_TITLES)
            pairs.extend(_parse_person(ent.text, preceded_by_title=titled))
    if not pairs:
        pairs = _fallback_names(text)
    if known_first:
        have = {n.casefold() for pair in pairs for n in pair if n}
        for tok in doc:
            key = _clean_token(tok.text).casefold()
            if (tok.pos_ == "PROPN" and not tok.is_sent_start
                    and tok.text[:1].isupper()
                    and key in known_first and key not in have
                    and key not in STOPLIST and key not in TITLES):
                pairs.append((_clean_token(tok.text), ""))
                have.add(key)
    return pairs


def names_in_sample(text: str,
                    known_first: set[str] | None = None) -> set[tuple[str, str]]:
    """Distinct (type, display_name) present in one sample.

    type is 'first' or 'surname'; keys are deduped case-insensitively but the
    first-seen display case is kept.
    """
    seen: dict[tuple[str, str], tuple[str, str]] = {}
    for first, last in extract_names(text, known_first):
        for typ, name in (("first", first), ("surname", last)):
            if not name:
                continue
            if name.isupper():  # shouty outputs: JAMES -> James for display
                name = name.title()
            seen.setdefault((typ, name.casefold()), (typ, name))
    return set(seen.values())


def ordered_characters(text: str,
                       known_first: set[str] | None = None) -> list[dict]:
    """Distinct characters in order of first appearance.

    The prompt asks for a protagonist then one secondary character, so the
    first-appearing named person is the protagonist and the second is the
    secondary. Returns dicts {first, surname} deduped so that a bare "Elara"
    and a later "Elara Voss" merge into one character (richest display kept).
    """
    if not text or not text.strip():
        return []
    doc = _nlp()(text)
    cands: list[tuple[int, str, str]] = []  # (char pos, first, surname)
    for ent in doc.ents:
        if ent.label_ != "PERSON":
            continue
        prev = doc[ent.start - 1] if ent.start > 0 else None
        titled = (prev is not None
                  and prev.text.lower().rstrip(".") in PROFESSIONAL_TITLES)
        for first, last in _parse_person(ent.text, preceded_by_title=titled):
            if first or last:
                cands.append((ent.start_char, first, last))
    if known_first:
        have = {c[1].casefold() for c in cands if c[1]}
        for tok in doc:
            key = _clean_token(tok.text).casefold()
            if (tok.pos_ == "PROPN" and not tok.is_sent_start
                    and tok.text[:1].isupper() and key in known_first
                    and key not in have and key not in STOPLIST
                    and key not in TITLES):
                cands.append((tok.idx, _clean_token(tok.text), ""))
                have.add(key)
    cands.sort(key=lambda c: c[0])

    chars: list[dict] = []
    seen_first: dict[str, int] = {}
    seen_sur: dict[str, int] = {}
    for _pos, first, last in cands:
        fk, lk = first.casefold(), last.casefold()
        idx = seen_first.get(fk) if first else None
        if idx is None and last:
            idx = seen_sur.get(lk)
        if idx is not None:
            if first and not chars[idx]["first"]:
                chars[idx]["first"] = first
            if last and not chars[idx]["surname"]:
                chars[idx]["surname"] = last
        else:
            chars.append({"first": first, "surname": last})
            if first:
                seen_first[fk] = len(chars) - 1
            if last:
                seen_sur[lk] = len(chars) - 1
    return chars
