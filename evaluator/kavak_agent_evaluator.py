import os
import json

from kavak_chatbot.services.llm_openai_adapter import OpenAIClientAdapter
from kavak_chatbot.services.prompt_builder import PromptBuilder
from kavak_chatbot.services import UserService, ChatService, MemoryService
from evaluator.evaluator_agent import EvaluatorAgent

def run_kavak_evaluator():
    llm_client = OpenAIClientAdapter()
    user_service = UserService()
    chat_service = ChatService()
    memory_service = MemoryService(llm_client=llm_client)
    prompt_builder = PromptBuilder()

    user = user_service.get_or_create_user("1111")
    session_info = chat_service.initialize_chat("1111")
    chat_session_id = str(session_info['session'].id)
    memory_agent_id = "22222222-2222-2222-2222-222222222222"

    from kavak_chatbot.services import AgentService
    persona, instruction = AgentService.fetch_memory_agent_data(memory_agent_id)
    agent = AgentService(
        persona=persona,
        instruction=instruction,
        model="gpt-4",
        memory_agent_i=memory_agent_id,
        user=user,
        llm_client=llm_client,
        memory_service=memory_service,
        chat_service=chat_service,
        user_service=user_service,
        prompt_builder=prompt_builder
    )

    test_cases_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
    with open(test_cases_path, "r") as f:
        test_cases = json.load(f)

    evaluator = EvaluatorAgent(llm_client=llm_client)

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
