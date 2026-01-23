"""Few-shot learning examples for TouchDesigner context."""

FEW_SHOT_EXAMPLES = """
User: How do I create a feedback loop in TouchDesigner?
Assistant: To create a feedback loop in TouchDesigner, you need to use a Feedback TOP. Here's how:

1. Add your effect operators (like Blur TOP, Level TOP, etc.)
2. Add a Feedback TOP after your effects
3. Connect the output back to the beginning of your chain
4. Adjust the Feedback TOP's Target TOP parameter to control the feedback strength

This creates a temporal feedback effect where previous frames influence current frames.

User: What's the difference between CHOPs and TOPs?
Assistant: CHOPs and TOPs are two fundamental operator families in TouchDesigner:

- **TOPs (Texture Operators)**: Process images and video. Work with 2D pixel data. Examples: Movie In, Blur, Composite.
- **CHOPs (Channel Operators)**: Process numerical data and control signals. Work with channels over time. Examples: Math, Filter, LFO.

Think of TOPs as your visual layer and CHOPs as your control/data layer. You often use CHOPs to control TOP parameters.

User: How do I access operator parameters in Python?
Assistant: You can access operator parameters in Python using the `par` attribute. Here's an example:

```python
# Get a reference to an operator
op_ref = op('blur1')

# Read a parameter value
blur_amount = op_ref.par.blur.val

# Set a parameter value
op_ref.par.blur = 5.0

# Access parameter properties
op_ref.par.blur.mode = ParMode.EXPRESSION
op_ref.par.blur.expr = 'abs(sin(absTime.seconds))'
```
"""


def get_few_shot_examples() -> str:
    """Get the few-shot examples string.

    Returns:
        Few-shot examples for prompt construction
    """
    return FEW_SHOT_EXAMPLES


def get_examples_enabled() -> bool:
    """Check if examples are available.

    Returns:
        True if examples exist and are non-empty
    """
    return bool(FEW_SHOT_EXAMPLES.strip())
