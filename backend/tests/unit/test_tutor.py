from app.services.tutor import plan_tutor_request


def test_tutor_plan_routes_step_by_step_document_request():
    plan = plan_tutor_request("Explain this step by step in my uploaded document")
    assert plan.intent == "step_by_step"
    assert plan.strategy == "step_by_step_explanation"
    assert plan.document_only is True
    assert plan.needs_web is False


def test_tutor_plan_routes_current_question_to_web_compatible_strategy():
    plan = plan_tutor_request("What is the latest news about physics?")
    assert plan.intent == "explain"
    assert plan.needs_web is True


def test_tutor_plan_routes_learning_actions():
    assert plan_tutor_request("summarize this").intent == "summary"
    assert plan_tutor_request("give me an example").intent == "example"
    assert plan_tutor_request("make flashcards").intent == "flashcards"