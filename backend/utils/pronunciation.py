"""
Pronunciation dictionary builder for Retell voice agents.

Scans restaurant menu items for commonly mispronounced food words
and generates a CMU phoneme dictionary for Retell's TTS engine.

Requires voice_model="eleven_turbo_v2" on the agent for the dictionary to take effect.
"""

import re

# Words that are ALWAYS included regardless of menu content
ALWAYS_INCLUDE = {
    "fries":   "F R AY1 Z",
    "salad":   "S AE1 L AH0 D",
    "caesar":  "S IY1 Z ER0",
    "basil":   "B EY1 Z AH0 L",
}

# Master lookup: Italian, French, and other commonly mispronounced food words
CMU_FOOD_WORDS: dict[str, str] = {
    **ALWAYS_INCLUDE,

    # Italian
    "marinara":      "M AE2 R AH0 N AA1 R AH0",
    "margherita":    "M AA2 R G AH0 R IY1 T AH0",
    "mozzarella":    "M AA2 T S AH0 R EH1 L AH0",
    "ricotta":       "R IH0 K AA1 T AH0",
    "parmesan":      "P AA1 R M AH0 Z AA2 N",
    "provolone":     "P R OW0 V OW1 L OW2 N",
    "prosciutto":    "P R AH0 SH UW1 T OW0",
    "focaccia":      "F OW0 K AA1 CH AH0",
    "caprese":       "K AH0 P R EY1 Z EY0",
    "bruschetta":    "B R UW0 SK EH1 T AH0",
    "calzone":       "K AE0 L Z OW1 N",
    "calzones":      "K AE0 L Z OW1 N Z",
    "stromboli":     "S T R AA1 M B AH0 L IY0",
    "arugula":       "AH0 R UW1 G Y AH0 L AH0",
    "calamari":      "K AE2 L AH0 M AA1 R IY0",
    "gorgonzola":    "G AO2 R G AH0 N Z OW1 L AH0",
    "fontina":       "F AA0 N T IY1 N AH0",
    "penne":         "P EH1 N EY0",
    "ziti":          "Z IY1 T IY0",
    "rigatoni":      "R IH2 G AH0 T OW1 N IY0",
    "linguine":      "L IH0 NG G W IY1 N IY0",
    "fettuccine":    "F EH2 T AH0 CH IY1 N IY0",
    "ravioli":       "R AE2 V IY0 OW1 L IY0",
    "lasagna":       "L AH0 Z AA1 N Y AH0",
    "pesto":         "P EH1 S T OW0",
    "aioli":         "AY0 OW1 L IY0",
    "panini":        "P AH0 N IY1 N IY0",
    "gelato":        "JH EH0 L AA1 T OW0",
    "tiramisu":      "T IH2 R AH0 M IY0 S UW1",
    "cannoli":       "K AH0 N OW1 L IY0",
    "neapolitan":    "N IY0 AH0 P AA1 L AH0 T AH0 N",
    "pepperoncini":  "P EH2 P ER0 AA0 N CH IY1 N IY0",
    "calabrian":     "K AH0 L EY1 B R IY0 AH0 N",
    "bianco":        "B IY0 AA1 NG K OW0",
    "kalamata":      "K AE2 L AH0 M AA1 T AH0",
    "sicilian":      "S IH0 S IH1 L IY0 AH0 N",
    "genoa":         "JH EH1 N OW0 AH0",
    "salami":        "S AH0 L AA1 M IY0",
    "capicola":      "K AE2 P IH0 K OW1 L AH0",
    "sopressata":    "S OW2 P R EH0 S AA1 T AH0",
    "portabella":    "P AO2 R T AH0 B EH1 L AH0",
    "ciabatta":      "CH AH0 B AA1 T AH0",
    "zucchini":      "Z UW0 K IY1 N IY0",

    # French
    "vinaigrette":   "V IH2 N AH0 G R EH1 T",
    "croissant":     "K R AH0 S AA1 N T",
    "bechamel":      "B EY2 SH AH0 M EH1 L",
    "filet":         "F IH0 L EY1",

    # Other
    "sriracha":      "S IH0 R AA1 CH AH0",
    "jalapeno":      "HH AA2 L AH0 P EY1 N Y OW0",
    "chipotle":      "CH IH0 P OW1 T L EY0",
    "quesadilla":    "K EY2 S AH0 D IY1 AH0",
    "tortilla":      "T AO0 R T IY1 AH0",
    "gyro":          "Y IH1 R OW0",
    "pho":           "F AH1",
    "acai":          "AH0 S AA0 IY1",
    "quattro formaggi": "K W AA1 T R OW0 F AO0 R M AA1 JH IY0",
}


def build_pronunciation_dictionary(menu_items: list[dict]) -> list[dict]:
    """
    Scan menu item names and descriptions for words that need pronunciation help.

    Args:
        menu_items: List of dicts with "name" and optionally "description" keys.

    Returns:
        Retell-format pronunciation_dictionary list:
        [{"word": "caesar", "alphabet": "cmu", "phoneme": "S IY1 Z ER0"}, ...]
    """
    text_blob = " ".join(
        f"{item.get('name', '')} {item.get('description', '')}"
        for item in menu_items
    ).lower()

    words_in_menu = set(re.findall(r"[a-z]+", text_blob))

    matched = set()
    for word in CMU_FOOD_WORDS:
        if " " in word:
            if word in text_blob:
                matched.add(word)
        elif word in words_in_menu:
            matched.add(word)

    matched.update(ALWAYS_INCLUDE.keys())

    return [
        {"word": w, "alphabet": "cmu", "phoneme": CMU_FOOD_WORDS[w]}
        for w in sorted(matched)
    ]


def build_pronunciation_dictionary_from_db(db, restaurant_id: int) -> list[dict]:
    """
    Fetch menu items from DB and build pronunciation dictionary.

    Args:
        db: SupabaseDB instance
        restaurant_id: The restaurant account ID

    Returns:
        Retell-format pronunciation_dictionary list
    """
    menus = db.query_all("menus", {"account_id": restaurant_id})
    if not menus:
        return build_pronunciation_dictionary([])

    items = []
    for menu in menus:
        categories = db.query_all("menu_categories", {"menu_id": menu["id"]})
        for cat in categories:
            cat_items = db.query_all("menu_items", {"category_id": cat["id"]})
            items.extend(cat_items)

    return build_pronunciation_dictionary(items)
