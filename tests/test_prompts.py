import unittest
from prompts import conversation_summary, catalog_search, agent, prompt_manager

class TestConversationSummaryPrompts(unittest.TestCase):
    def test_get_conversation_summary_prompt(self):
        prompt = conversation_summary.get_conversation_summary_prompt(
            old_summary="Resumen previo", conversation_text="Texto nuevo", summary_length_words=50
        )
        self.assertIn("Resumen previo", prompt)
        self.assertIn("Texto nuevo", prompt)
        self.assertIn("50 palabras", prompt)

    def test_get_conversation_summary_system_prompt(self):
        system_prompt = conversation_summary.get_conversation_summary_system_prompt()
        self.assertIsInstance(system_prompt, str)
        self.assertIn("especialista en resumir", system_prompt)

    def test_get_kavak_info_summary_prompt(self):
        prompt = conversation_summary.get_kavak_info_summary_prompt("consulta", "contenido")
        self.assertIn("consulta", prompt)
        self.assertIn("contenido", prompt)

    def test_get_kavak_info_summary_system_prompt(self):
        system_prompt = conversation_summary.get_kavak_info_summary_system_prompt()
        self.assertIsInstance(system_prompt, str)
        self.assertIn("experto en resumir", system_prompt)

class TestCatalogSearchPrompts(unittest.TestCase):
    def test_get_catalog_search_normalization_prompt(self):
        brands = "Chevrolet, Ford, Toyota"
        prompt = catalog_search.get_catalog_search_normalization_prompt(brands)
        self.assertIn(brands, prompt)
        self.assertIn("normalizar y corregir", prompt)
        self.assertIn("Chevrolet", prompt)

class TestAgentPrompts(unittest.TestCase):
    def test_get_car_sales_agent_prompt(self):
        prompt = agent.get_car_sales_agent_prompt()
        self.assertIsInstance(prompt, str)
        self.assertIn("agente de ventas de Kavak", prompt)
        self.assertIn("PESOS MEXICANOS", prompt)

class TestPromptManager(unittest.TestCase):
    def test_prompt_manager_get_prompt(self):
        pm = prompt_manager.PromptManager()
        self.assertIn("car_sales_agent", pm.list_prompts())
        self.assertIsInstance(pm.get_prompt("car_sales_agent"), str)

    def test_prompt_manager_add_and_get(self):
        pm = prompt_manager.PromptManager()
        pm.add_prompt("test", "test prompt")
        self.assertEqual(pm.get_prompt("test"), "test prompt")

    def test_prompt_manager_get_car_sales_agent_prompt(self):
        pm = prompt_manager.PromptManager()
        prompt = pm.get_car_sales_agent_prompt()
        self.assertIn("agente de ventas de Kavak", prompt)

    def test_prompt_manager_get_conversation_summary_prompt(self):
        pm = prompt_manager.PromptManager()
        prompt = pm.get_conversation_summary_prompt("old", "new", 42)
        self.assertIn("old", prompt)
        self.assertIn("new", prompt)
        self.assertIn("42 palabras", prompt)

    def test_prompt_manager_get_conversation_summary_system_prompt(self):
        pm = prompt_manager.PromptManager()
        system_prompt = pm.get_conversation_summary_system_prompt()
        self.assertIn("especialista en resumir", system_prompt)

if __name__ == "__main__":
    unittest.main() 