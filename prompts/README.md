# Prompts System

This directory contains prompt templates for different agents in the chatbot system.

## Structure

```
prompts/
├── __init__.py              # Package initialization
├── prompt_manager.py        # Prompt management system
├── car_sales_agent.py       # Car sales agent prompt template
└── README.md               # This file
```

## Usage

### Using the Prompt Manager (Recommended)

```python
from prompts.prompt_manager import prompt_manager

# Get a specific prompt
prompt = prompt_manager.get_car_sales_agent_prompt()

# List all available prompts
available_prompts = prompt_manager.list_prompts()

# Add a new prompt
prompt_manager.add_prompt("my_agent", "Your prompt text here")
```

### Using Direct Functions

```python
from prompts.car_sales_agent import get_car_sales_agent_prompt

prompt = get_car_sales_agent_prompt()
```

## Adding New Prompts

1. Create a new file in the `prompts/` directory (e.g., `my_agent.py`)
2. Define your prompt template as a constant
3. Create a function to return the prompt
4. Add the prompt to the `PromptManager` in `prompt_manager.py`

Example:

```python
# prompts/my_agent.py
MY_AGENT_PROMPT = """
Your prompt template here...
"""

def get_my_agent_prompt() -> str:
    return MY_AGENT_PROMPT.strip()
```

Then update `prompt_manager.py`:

```python
from .my_agent import get_my_agent_prompt

def _load_default_prompts(self):
    self._prompts['car_sales_agent'] = get_car_sales_agent_prompt()
    self._prompts['my_agent'] = get_my_agent_prompt()  # Add this line
```

## Integration with Seeders

The seeder system uses the prompt manager to get prompts when creating agents:

```python
from prompts.prompt_manager import prompt_manager

# In your seeder
instruction = prompt_manager.get_car_sales_agent_prompt()
```

This ensures consistency and makes it easy to update prompts without modifying the seeder code. 