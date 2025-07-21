import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.user_service import UserService
from services.chat_service import ChatService
from services.memory_service import MemoryService
from services.prompt_builder import PromptBuilder
from openai import OpenAI
from evaluator.evaluator_agent import EvaluatorAgent

if __name__ == "__main__":
    user_service = UserService()
    chat_service = ChatService()
    memory_service = MemoryService()
    openai_client = OpenAI()
    prompt_builder = PromptBuilder()

    user = user_service.get_or_create_user("1111")
    session_info = chat_service.initialize_chat("1111")
    chat_session_id = str(session_info['session'].id)
    memory_agent_id = "22222222-2222-2222-2222-222222222222"

    from services.agent_service import AgentService
    persona, instruction = AgentService.fetch_memory_agent_data(memory_agent_id)
    agent = AgentService(
        persona=persona,
        instruction=instruction,
        model="gpt-4",
        memory_agent_i=memory_agent_id,
        user=user,
        openai_client=openai_client,
        memory_service=memory_service,
        chat_service=chat_service,
        user_service=user_service,
        prompt_builder=prompt_builder
    )

    test_cases_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
    with open(test_cases_path, "r") as f:
        test_cases = json.load(f)

    evaluator = EvaluatorAgent()

    for idx, case in enumerate(test_cases):
        user_query = case["user_query"]
        expected = case["expected"]
        expected_tools = case["expected_tools"]
        print(f"\nCaso {idx+1}: {user_query}")
        eval_data = agent.evaluate(user_query, chat_session_id)
        agent_response = eval_data["agent_response"]
        tools_invoked = eval_data["tools_invoked"]
        analysis = evaluator.evaluate(
            user_query=user_query,
            agent_response=agent_response,
            tools_invoked=tools_invoked,
            expected=expected,
            expected_tools=expected_tools
        )
        print("Análisis del evaluador:")
        print(analysis)