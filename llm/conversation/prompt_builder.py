"""Prompt building with system instructions and examples."""

from typing import Optional


class PromptBuilder:
    """Builds prompts with system instructions and examples.

    Assembles system instructions and optional few-shot examples
    to create effective prompts for the LLM.
    """

    def __init__(
        self,
        instruction_template: str = "default",
        include_examples: bool = True
    ) -> None:
        """Initialize the prompt builder.

        Args:
            instruction_template: Name of system instruction template to use
            include_examples: Whether to include few-shot examples
        """
        self._instruction_template = instruction_template
        self._include_examples = include_examples

    def build_system_prompt(
        self,
        custom_context: Optional[str] = None
    ) -> str:
        """Build the complete system prompt.

        Args:
            custom_context: Optional custom context to add

        Returns:
            Complete system prompt string
        """
        from ..prompts.system_instructions import get_system_instruction
        from ..prompts.examples import get_few_shot_examples

        components = []

        # Add system instruction
        instruction = get_system_instruction(self._instruction_template)
        components.append(instruction)

        # Add custom context if provided
        if custom_context:
            components.append(custom_context)

        # Add few-shot examples
        if self._include_examples:
            examples = get_few_shot_examples()
            if examples:
                components.append("\n# Examples:\n")
                components.append(examples)

        return "\n\n".join(components)

    def set_template(self, template_name: str) -> None:
        """Change the instruction template.

        Args:
            template_name: Name of the template to use
        """
        self._instruction_template = template_name

    def set_include_examples(self, include: bool) -> None:
        """Toggle inclusion of few-shot examples.

        Args:
            include: Whether to include examples in prompts
        """
        self._include_examples = include

    def get_current_template(self) -> str:
        """Get the name of the current template.

        Returns:
            Current template name
        """
        return self._instruction_template
