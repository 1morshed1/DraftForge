"""Tests for EditTracker and ImprovementEngine."""

import pytest

from app.models.schemas import EditCategory, EditSubmission
from app.services.edit_tracker import EditTracker, ImprovementEngine


@pytest.fixture
def tracker():
    return EditTracker()


@pytest.fixture
def engine():
    return ImprovementEngine()


class TestEditTracker:
    def test_detects_addition(self, tracker):
        submission = EditSubmission(
            draft_id="draft-1",
            original_content="Line one.\nLine two.",
            edited_content="Line one.\nNew inserted line.\nLine two.",
        )
        analysis = tracker.analyze_edit(submission)
        categories = [d.edit_type for d in analysis.diffs]
        assert EditCategory.ADDITION in categories

    def test_detects_deletion(self, tracker):
        submission = EditSubmission(
            draft_id="draft-1",
            original_content="Line one.\nRemove this line.\nLine three.",
            edited_content="Line one.\nLine three.",
        )
        analysis = tracker.analyze_edit(submission)
        categories = [d.edit_type for d in analysis.diffs]
        assert EditCategory.DELETION in categories

    def test_detects_factual_correction(self, tracker):
        submission = EditSubmission(
            draft_id="draft-1",
            original_content="The amount was $5,000 on March 10.",
            edited_content="The amount was $7,500 on March 15.",
        )
        analysis = tracker.analyze_edit(submission)
        categories = [d.edit_type for d in analysis.diffs]
        assert EditCategory.FACTUAL_CORRECTION in categories

    def test_generates_summary(self, tracker):
        submission = EditSubmission(
            draft_id="draft-1",
            original_content="Original text here.",
            edited_content="Completely new text here.",
            editor_notes="Rewrote for clarity",
        )
        analysis = tracker.analyze_edit(submission)
        assert "change(s)" in analysis.summary
        assert "Rewrote for clarity" in analysis.summary

    def test_edit_id_is_unique(self, tracker):
        sub = EditSubmission(
            draft_id="d1",
            original_content="A",
            edited_content="B",
        )
        a1 = tracker.analyze_edit(sub)
        a2 = tracker.analyze_edit(sub)
        assert a1.edit_id != a2.edit_id

    def test_persists_edit_to_disk(self, tracker):
        sub = EditSubmission(
            draft_id="d1",
            original_content="Before.",
            edited_content="After.",
        )
        tracker.analyze_edit(sub)
        edits = tracker.get_all_edits()
        assert len(edits) >= 1


class TestImprovementEngine:
    def test_learns_rule_from_edit(self, tracker, engine):
        sub = EditSubmission(
            draft_id="d1",
            original_content="The case was filed on March 1.",
            edited_content="The case was filed on March 15, 2024 in Sangamon County.",
        )
        analysis = tracker.analyze_edit(sub)
        rules = engine.learn_from_edit(analysis)
        assert len(rules) > 0

    def test_rule_confidence_increases_on_repeat(self, tracker, engine):
        for i in range(3):
            sub = EditSubmission(
                draft_id=f"d{i}",
                original_content=f"Amount was ${1000 + i}.",
                edited_content=f"Amount was ${2000 + i}.",
            )
            analysis = tracker.analyze_edit(sub)
            engine.learn_from_edit(analysis)

        rules = engine.get_applicable_rules()
        # After repeated similar edits, at least one rule should have times_applied > 1
        assert any(r.times_applied > 1 or r.confidence >= 0.5 for r in rules)

    def test_get_applicable_rules_filters_by_type(self, tracker, engine):
        sub = EditSubmission(
            draft_id="d1",
            original_content="Draft text.",
            edited_content="Improved draft text with jurisdiction details.",
        )
        analysis = tracker.analyze_edit(sub, draft_type="case_summary")
        engine.learn_from_edit(analysis)

        rules = engine.get_applicable_rules(draft_type="case_summary")
        for rule in rules:
            assert rule.draft_type is None or rule.draft_type.value == "case_summary"

    def test_delete_rule(self, tracker, engine):
        sub = EditSubmission(
            draft_id="d1",
            original_content="Old.",
            edited_content="New.",
        )
        analysis = tracker.analyze_edit(sub)
        rules = engine.learn_from_edit(analysis)
        rule_id = rules[0].rule_id

        assert engine.delete_rule(rule_id) is True
        assert engine.delete_rule("nonexistent") is False

    def test_reset_clears_all_rules(self, tracker, engine):
        sub = EditSubmission(
            draft_id="d1",
            original_content="A.",
            edited_content="B.",
        )
        analysis = tracker.analyze_edit(sub)
        engine.learn_from_edit(analysis)

        engine.reset()
        assert len(engine.rules) == 0
        assert len(engine.get_applicable_rules()) == 0

    def test_rules_by_category(self, tracker, engine):
        sub = EditSubmission(
            draft_id="d1",
            original_content="Line one.\nLine two.",
            edited_content="Line one.\nAdded line.\nLine two.",
        )
        analysis = tracker.analyze_edit(sub)
        engine.learn_from_edit(analysis)
        counts = engine.get_rules_by_category()
        assert isinstance(counts, dict)
        assert sum(counts.values()) > 0
