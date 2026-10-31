import unittest
from i18n import MESSAGES, translate

class TranslationTests(unittest.TestCase):
    def test_catalog_and_dynamic_values(self):
        for german, translations in MESSAGES.items():
            self.assertEqual(set(translations), {'en', 'zh_CN'}, german)
            self.assertTrue(all(translations.values()), german)
        self.assertEqual(translate('Frames: 1.234', 'en'), 'Frames: 1.234')
        self.assertEqual(translate('Frames: 1.234', 'zh_CN'), '报文数：1.234')
        self.assertEqual(translate('0x123 · Bytes ab 0: keine Nutzdaten', 'en'), '0x123 · Bytes from 0: no payload')

    def test_validation_errors_and_user_data(self):
        self.assertEqual(translate('CAN-ID passt nicht zum gewählten Format.', 'en'), 'CAN ID does not match the selected format.')
        self.assertEqual(translate('Meine Batterie', 'zh_CN'), 'Meine Batterie')
        self.assertEqual(translate('Frames: 2', 'unknown'), 'Frames: 2')
