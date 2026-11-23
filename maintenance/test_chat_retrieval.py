"""Run against a local UniFit preview with python maintenance/test_chat_retrieval.py."""

import json
import os
import unittest
from urllib.request import Request, urlopen


URL = os.environ.get("UNIFIT_TEST_CHAT_URL", "http://127.0.0.1:8091/api/chat")


def ask(question, history=()):
    body = json.dumps({"question": question, "history": history}).encode()
    with urlopen(Request(URL, data=body, headers={"Content-Type": "application/json"}), timeout=12) as response:
        return json.load(response)


class ChatRetrievalTests(unittest.TestCase):
    def test_guide_paraphrases_and_scope(self):
        cases = (
            ("Who can apply for remote learning?", 153, "2026 matriculation"),
            ("Do I qualify for study from home?", 153, "2026 matriculation"),
            ("What can I study if I study from home?", 155, "B.A. Law"),
            ("အဝေးသင် ဘာမေဂျာတွေ သင်လို့ရလဲ", 155, "ဥပဒေပညာ"),
            ("How much are remote learning course fees?", 179, "20000"),
            ("အဝေးသင် သင်တန်းကြေး ဘယ်လောက်လဲ", 179, "၂၀၀၀၀"),
            ("ကျောင်းလခ ဘယ်လောက်လဲ", 149, "၅၀၀၀"),
            ("How much sick leave can I get with a doctor’s note?", 147, "21 days"),
            ("I missed the deadline", 129, "Thaton Road"),
            ("Do I need the original marksheet?", 130, "original matriculation marks sheet"),
        )
        for question, page, phrase in cases:
            with self.subTest(question=question):
                reply = ask(question)
                self.assertEqual(reply["pages"], [page])
                self.assertIn(phrase, reply["text"].replace(",", ""))

    def test_computing_comparison_and_followup(self):
        first = "What are the computing entry requirements at UCSY?"
        reply = ask(first)
        self.assertIn("450 total or 140", reply["text"])
        self.assertEqual(reply["pages"], [51, 52, 53])
        history = [{"user": True, "text": first}, {"user": False, "text": reply["text"]}]
        reply = ask("What about UCSM?", history)
        self.assertIn("430 total or 140", reply["text"])
        self.assertEqual(reply["pages"], [54, 55])
        reply = ask("Compare computing entry requirements at UCSY, UCSM, and NSPU.")
        self.assertEqual(len(reply["links"]), 3)
        self.assertEqual(reply["text"].count("450 total or 140"), 2)
        self.assertIn("430 total or 140", reply["text"])

    def test_published_scores_and_gaps(self):
        question = "What were Hmawbi’s lowest and highest admitted scores in 2024?"
        reply = ask(question)
        self.assertIn("330", reply["text"])
        self.assertIn("479", reply["text"])
        self.assertTrue(reply["sources"])
        reply = ask("What about 2026?", [{"user": True, "text": question}])
        self.assertIn("no verified", reply["text"])
        self.assertIn("awaiting review", ask("What does page 95 say?")["text"])
        self.assertIn("does not have a copy", ask("What does page 80 say?")["text"])

    def test_informal_and_mixed_language(self):
        cases = (
            ("NSPU computing ဘယ်နှမှတ်လိုလဲ", (), 37, "၄၅၀"),
            ("အဝေး သင် course fees ဘယ်လောက်လဲ", (), 179, "၂၀၀၀၀"),
            ("အဝေးသင် စာမေးပွဲ ပြန်ဖြေလို့ရလား", (), 181, "နောက်ဆက်တွဲ"),
            ("အဝေးသင်မှာ မေဂျာပြောင်းချင်တယ်", (), 183, "အဝေးသင်ဌာနခွဲ"),
            ("What about the exam rules?", [{"user": True, "text": "Who can apply for remote learning?"}], 181, "75%"),
            ("What about location?", [{"user": True, "text": "Compare YTU and Bago University"}], None, "Gyogone"),
        )
        for question, history, page, phrase in cases:
            with self.subTest(question=question):
                reply = ask(question, history)
                if page is not None:
                    self.assertIn(page, reply["pages"])
                self.assertIn(phrase, reply["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
