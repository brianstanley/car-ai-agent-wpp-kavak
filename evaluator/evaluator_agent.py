from kavak_chatbot.services import LLMClientProtocol
from kavak_chatbot.prompts.prompt_manager import prompt_manager

class EvaluatorAgent:
    def __init__(self, model="gpt-3.5-turbo", llm_client: LLMClientProtocol = None):
        self.model = model
        self.llm_client = llm_client
        self.prompt_template = prompt_manager.get_evaluator_prompt()

    def evaluate(self, user_query, agent_response, tools_invoked, expected, expected_tools):
        prompt = self.prompt_template.format(
            user_query=user_query,
            agent_response=agent_response,
            tools_invoked=tools_invoked,
            expected=expected,
            expected_tools=expected_tools
        )
        completion = self.llm_client.chat_completion(
            model=self.model,
            messages=[{"role": "system", "content": "Eres un evaluador de interacciones de agentes conversacionales."},
                      {"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0
        )
        return completion.choices[0].message.content