import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from api_requirements import candidate, classify, extract


class RequirementsTests(unittest.TestCase):
    def test_examples_are_selected_but_real_env_and_vendor_are_not(self):
        for name in ('backend/.env.example', 'env.sample', '.env.template', 'config.example.json', 'docker-compose.yml'):
            self.assertTrue(candidate(name), name)
        for name in ('.env', '.env.production', 'node_modules/demo/.env.example', 'docs/readme-home.png', ''):
            self.assertFalse(candidate(name), name)

    def test_secrets_never_leave_extractor(self):
        rows = extract('OPENAI_API_KEY=real-secret-value\n# GEMINI_API_KEY=another-secret\n  - TOKEN: ${BOT_TOKEN}\n', '.env.example')
        self.assertEqual({r['name'] for r in rows}, {'OPENAI_API_KEY', 'GEMINI_API_KEY', 'TOKEN', 'BOT_TOKEN'})
        self.assertNotIn('secret-value', str(rows))
        self.assertNotIn('another-secret', str(rows))

    def test_key_is_not_automatically_required_or_external(self):
        self.assertEqual(classify('JWT_SECRET'), (None, 'local_secret'))
        self.assertEqual(classify('POSTGRES_PASSWORD'), (None, 'local_service'))
        self.assertEqual(classify('GOOGLE_API_KEY'), ('google_unknown', 'external_credential'))
        self.assertEqual(extract('GROQ_API_KEY=', '.env.example')[0]['required'], 'unknown')


if __name__ == '__main__':
    unittest.main()
