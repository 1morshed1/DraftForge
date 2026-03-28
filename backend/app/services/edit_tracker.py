import difflib
import json
import re
import uuid
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.models.schemas import (
    DraftType,
    EditAnalysis,
    EditCategory,
    EditDiff,
    EditSubmission,
    ImprovementRule,
)


# --- Helper detection functions ---

def _is_structural_change(original: str, edited: str) -> bool:
    orig_headers = bool(re.search(r"^#{1,3}\s", original, re.MULTILINE))
    edit_headers = bool(re.search(r"^#{1,3}\s", edited, re.MULTILINE))
    if orig_headers != edit_headers:
        return True
    orig_bullets = bool(re.search(r"^[\-\*]\s", original, re.MULTILINE))
    edit_bullets = bool(re.search(r"^[\-\*]\s", edited, re.MULTILINE))
    if orig_bullets != edit_bullets:
        return True
    return False


def _is_tone_change(original: str, edited: str) -> bool:
    orig_words = set(re.findall(r"\w+", original.lower()))
    edit_words = set(re.findall(r"\w+", edited.lower()))
    if not orig_words or not edit_words:
        return False
    overlap = len(orig_words & edit_words) / max(len(orig_words), len(edit_words))
    exact = original.strip() == edited.strip()
    return overlap > 0.6 and not exact


def _is_factual_correction(original: str, edited: str) -> bool:
    # Check if numbers, dates, or proper nouns changed
    orig_nums = set(re.findall(r"\d+", original))
    edit_nums = set(re.findall(r"\d+", edited))
    if orig_nums != edit_nums:
        return True
    orig_caps = set(re.findall(r"\b[A-Z][a-z]+\b", original))
    edit_caps = set(re.findall(r"\b[A-Z][a-z]+\b", edited))
    if orig_caps != edit_caps and len(orig_caps.symmetric_difference(edit_caps)) <= 3:
        return True
    return False


def _is_formatting_change(original: str, edited: str) -> bool:
    stripped_orig = re.sub(r"[\s\W]+", "", original)
    stripped_edit = re.sub(r"[\s\W]+", "", edited)
    return stripped_orig == stripped_edit


def _is_more_formal(text: str, reference: str) -> bool:
    informal = {"don't", "won't", "can't", "gonna", "wanna", "kinda", "gotta", "yeah", "ok", "okay"}
    text_words = set(re.findall(r"\w+", text.lower()))
    ref_words = set(re.findall(r"\w+", reference.lower()))
    text_informal = text_words & informal
    ref_informal = ref_words & informal
    return len(text_informal) < len(ref_informal)


def _has_bullet_points(text: str) -> bool:
    return bool(re.search(r"^[\-\*•]\s", text, re.MULTILINE))


# --- EditTracker ---

class EditTracker:
    def __init__(self):
        self.edits_dir = Path(settings.EDITS_DIR)

    def analyze_edit(
        self, submission: EditSubmission, draft_type: str | None = None
    ) -> EditAnalysis:
        edit_id = str(uuid.uuid4())
        raw_diffs = self._compute_diffs(submission.original_content, submission.edited_content)
        classified = [self._classify_diff(d) for d in raw_diffs]

        # Generate summary
        categories = [d.edit_type.value for d in classified]
        cat_counts = {}
        for c in categories:
            cat_counts[c] = cat_counts.get(c, 0) + 1
        summary_parts = [f"{count} {cat} change(s)" for cat, count in cat_counts.items()]
        summary = f"Edit contains {len(classified)} change(s): " + ", ".join(summary_parts)

        if submission.editor_notes:
            summary += f". Editor notes: {submission.editor_notes}"

        dt = None
        if draft_type:
            try:
                dt = DraftType(draft_type)
            except ValueError:
                pass

        analysis = EditAnalysis(
            edit_id=edit_id,
            draft_id=submission.draft_id,
            draft_type=dt,
            diffs=classified,
            summary=summary,
            analyzed_at=datetime.utcnow(),
        )

        # Save
        out_path = self.edits_dir / f"{edit_id}.json"
        out_path.write_text(analysis.model_dump_json(indent=2))

        return analysis

    def get_all_edits(self) -> list[EditAnalysis]:
        edits = []
        for p in sorted(self.edits_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                data = json.loads(p.read_text())
                edits.append(EditAnalysis(**data))
            except Exception:
                continue
        return edits

    def _compute_diffs(self, original: str, edited: str) -> list[dict]:
        original_lines = original.splitlines()
        edited_lines = edited.splitlines()
        matcher = difflib.SequenceMatcher(None, original_lines, edited_lines)
        diffs = []

        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                continue
            diffs.append({
                "operation": op,
                "original": "\n".join(original_lines[i1:i2]),
                "edited": "\n".join(edited_lines[j1:j2]),
                "context": "\n".join(original_lines[max(0, i1 - 2):i1]),
            })

        return diffs

    def _classify_diff(self, diff: dict) -> EditDiff:
        orig = diff["original"]
        edited = diff["edited"]
        operation = diff["operation"]

        if operation == "insert":
            category = EditCategory.ADDITION
            explanation = "New content was added."
        elif operation == "delete":
            category = EditCategory.DELETION
            explanation = "Content was removed."
        elif _is_formatting_change(orig, edited):
            category = EditCategory.FORMATTING
            explanation = "Formatting or whitespace changes only."
        elif _is_structural_change(orig, edited):
            category = EditCategory.STRUCTURAL
            explanation = "Document structure was reorganized."
        elif _is_factual_correction(orig, edited):
            category = EditCategory.FACTUAL_CORRECTION
            explanation = "Factual details were corrected."
        elif _is_tone_change(orig, edited):
            category = EditCategory.TONE
            explanation = "Wording was changed while preserving meaning."
        else:
            category = EditCategory.LEGAL_PRECISION
            explanation = "Legal language was refined for precision."

        return EditDiff(
            edit_type=category,
            original_segment=orig,
            edited_segment=edited,
            context=diff["context"],
            explanation=explanation,
        )


# --- ImprovementEngine ---

class ImprovementEngine:
    def __init__(self):
        self.patterns_dir = Path(settings.PATTERNS_DIR)
        self.rules_path = self.patterns_dir / "rules.json"
        self.rules: list[ImprovementRule] = []
        self._load()

    def _load(self):
        if self.rules_path.exists():
            try:
                data = json.loads(self.rules_path.read_text())
                self.rules = [ImprovementRule(**r) for r in data]
            except Exception:
                self.rules = []

    def _save(self):
        data = [r.model_dump(mode="json") for r in self.rules]
        self.rules_path.write_text(json.dumps(data, indent=2, default=str))

    def learn_from_edit(self, analysis: EditAnalysis) -> list[ImprovementRule]:
        new_or_updated: list[ImprovementRule] = []

        for diff in analysis.diffs:
            existing = self._find_matching_rule(diff)

            if existing:
                existing.times_applied += 1
                existing.confidence = min(1.0, existing.confidence + 0.1)
                existing.examples.append({
                    "before": diff.original_segment[:200],
                    "after": diff.edited_segment[:200],
                })
                if analysis.edit_id not in existing.created_from_edit_ids:
                    existing.created_from_edit_ids.append(analysis.edit_id)
                new_or_updated.append(existing)
            else:
                rule_text = self._generate_rule_text(diff)
                rule = ImprovementRule(
                    rule_id=str(uuid.uuid4()),
                    draft_type=analysis.draft_type,
                    category=diff.edit_type,
                    rule_text=rule_text,
                    examples=[{
                        "before": diff.original_segment[:200],
                        "after": diff.edited_segment[:200],
                    }],
                    confidence=0.5,
                    times_applied=1,
                    created_from_edit_ids=[analysis.edit_id],
                    created_at=datetime.utcnow(),
                )
                self.rules.append(rule)
                new_or_updated.append(rule)

        self._save()
        return new_or_updated

    def get_applicable_rules(
        self, draft_type: DraftType | str | None = None, max_rules: int = 5
    ) -> list[ImprovementRule]:
        if isinstance(draft_type, str):
            try:
                draft_type = DraftType(draft_type)
            except ValueError:
                draft_type = None

        filtered = [
            r for r in self.rules
            if r.draft_type is None or r.draft_type == draft_type
        ]
        filtered.sort(key=lambda r: r.confidence * r.times_applied, reverse=True)
        return filtered[:max_rules]

    def delete_rule(self, rule_id: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
        if len(self.rules) < before:
            self._save()
            return True
        return False

    def reset(self):
        self.rules = []
        self._save()

    def get_rules_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.rules:
            cat = r.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _find_matching_rule(self, diff: EditDiff) -> ImprovementRule | None:
        for rule in self.rules:
            if rule.category != diff.edit_type:
                continue
            # Check word overlap between rule text and diff explanation
            rule_words = set(re.findall(r"\w+", rule.rule_text.lower()))
            diff_words = set(re.findall(r"\w+", diff.explanation.lower()))
            if not rule_words:
                continue
            overlap = len(rule_words & diff_words) / len(rule_words)
            if overlap > 0.3:
                return rule
        return None

    def _generate_rule_text(self, diff: EditDiff) -> str:
        if diff.edit_type == EditCategory.TONE:
            if _is_more_formal(diff.edited_segment, diff.original_segment):
                return "Use formal legal language. Avoid casual phrasing."
            else:
                return "Use plain language. Avoid overly formal or archaic terms."

        elif diff.edit_type == EditCategory.STRUCTURAL:
            if "##" in diff.edited_segment and "##" not in diff.original_segment:
                return "Use section headers (##) to organize content."
            elif _has_bullet_points(diff.edited_segment):
                return "Use bullet points for lists of items or conditions."
            return "Improve document structure and organization."

        elif diff.edit_type == EditCategory.ADDITION:
            added = diff.edited_segment
            if re.search(r"jurisdiction|venue|court", added, re.IGNORECASE):
                return "Always include jurisdiction and venue information."
            elif re.search(r"date|deadline|timeline", added, re.IGNORECASE):
                return "Include relevant dates, deadlines, and timelines."
            elif re.search(r"party|parties|plaintiff|defendant", added, re.IGNORECASE):
                return "Explicitly identify all parties with their full names and roles."
            return "Include additional relevant details and context."

        elif diff.edit_type == EditCategory.DELETION:
            removed = diff.original_segment
            if re.search(r"may|might|possibly|perhaps", removed, re.IGNORECASE):
                return "Avoid hedging language. State findings directly."
            return "Remove unnecessary or redundant content."

        elif diff.edit_type == EditCategory.FACTUAL_CORRECTION:
            return "Double-check all factual claims (dates, amounts, names) against source documents."

        elif diff.edit_type == EditCategory.FORMATTING:
            return "Maintain consistent formatting throughout the document."

        else:
            return "Use precise legal terminology. Be specific about legal concepts."
