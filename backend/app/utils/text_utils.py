import re


def clean_text(raw_text: str) -> str:
    text = raw_text

    # OCR artifact fixes
    text = re.sub(r"(?<=[a-z])\bl\b(?=[a-z])", "I", text)
    text = re.sub(r"(?<=[a-z])0(?=[a-z])", "o", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # Whitespace normalization
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)

    # Sentence repair: join lines broken mid-sentence
    lines = text.split("\n")
    repaired = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            i + 1 < len(lines)
            and line
            and lines[i + 1]
            and line[-1].islower()
            and lines[i + 1][0].islower()
        ):
            repaired.append(line.rstrip() + " " + lines[i + 1].lstrip())
            i += 2
        else:
            repaired.append(line)
            i += 1

    return "\n".join(repaired).strip()


def extract_structured_data(text: str) -> dict:
    data: dict = {}

    # Dates
    date_patterns = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
    ]
    dates = []
    for pat in date_patterns:
        dates.extend(re.findall(pat, text, re.IGNORECASE))
    data["dates_found"] = list(set(dates))

    # Case numbers
    data["case_references"] = re.findall(
        r"(?:Case|No\.|Docket|File)\s*#?\s*[\w-]+", text, re.IGNORECASE
    )

    # Parties
    data["parties"] = re.findall(r"([A-Z][A-Z\s]+)\s+v\.?\s+([A-Z][A-Z\s]+)", text)

    # Dollar amounts
    data["monetary_amounts"] = re.findall(r"\$[\d,]+(?:\.\d{2})?", text)

    # Section headers
    data["sections"] = re.findall(
        r"^(?:SECTION|Article|§)\s*.+$", text, re.MULTILINE | re.IGNORECASE
    )

    return data
