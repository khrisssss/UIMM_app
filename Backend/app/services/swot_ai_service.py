from app.services.swot_generator import generate_fake_swot_from_context


def generate_swot_draft(swot_context: dict) -> dict:
    """
    This function is the central place for SWOT generation.

    For now, it uses the fake generator.
    Later, we will replace this with Azure OpenAI / Azure AI Foundry.
    """

    generated_swot = generate_fake_swot_from_context(swot_context)

    return {
        "strengths": generated_swot["strengths"],
        "weaknesses": generated_swot["weaknesses"],
        "opportunities": generated_swot["opportunities"],
        "threats": generated_swot["threats"],
        "generation_source": "fake_ai",
        "generated_by_ai": True,
        "ai_model": "fake-generator-v1",
        "status": "draft"
    }