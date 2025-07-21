import os
from openai import OpenAI
from prompts.evaluator import get_evaluator_prompt

class EvaluatorAgent:
    def __init__(self, model="gpt-3.5-turbo", openai_client=None):
        self.model = model
        self.client = openai_client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt_template = get_evaluator_prompt()

    def evaluate(self, user_query, agent_response, tools_invoked, expected, expected_tools):
        prompt = self.prompt_template.format(
            user_query=user_query,
            agent_response=agent_response,
            tools_invoked=tools_invoked,
            expected=expected,
            expected_tools=expected_tools
        )
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": "Eres un evaluador de interacciones de agentes conversacionales."},
                      {"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0
        )
        return completion.choices[0].message.content