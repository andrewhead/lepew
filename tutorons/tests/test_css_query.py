#! /usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
import logging
import unittest
import json
from tutorons.common.htmltools import HtmlDocument
from django.test import Client


logging.basicConfig(level=logging.INFO, format="%(message)s")


class TestRenderDescription(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def get_resp_texts(self, document):
        resp = self.client.post('/css', data={'origin': 'www.test.com', 'document': document})
        respData = json.loads(resp.content)
        texts = {k: HtmlDocument(v).text for k, v in respData.items()}
        return texts

    def get_example_html(self, document):
        resp = self.client.post('/css', data={'origin': 'www.test.com', 'document': document})
        respData = json.loads(resp.content)
        return respData

    def get_text_short(self, selector):
        return self.get_resp_texts('\n'.join(["<code>", selector, "</code>"]))

    def get_example_short(self, selector):
        return self.get_example_html('\n'.join(["<code>", selector, "</code>"]))

    def test_describe_preamble(self):
        texts = self.get_text_short('$(".klazz")')
        text = texts['.klazz']
        self.assertIn("You found a CSS selector", text)
        self.assertIn("selectors pick sections of HTML pages", text)

    def test_describe_single_class(self):
        texts = self.get_text_short('$(".watch-view-count")')
        self.assertEqual(len(texts.keys()), 1)
        text = texts['.watch-view-count']
        self.assertIn("chooses elements of class 'watch-view-count'", text)

    def test_render_example_html(self):
        doms = self.get_example_html('<code>$("div p");</code>')
        dom = doms['div p']
        self.assertIn("\n".join([
            "&lt;div&gt;<br>",
            "<span class='tutoron_selection'>",
            "&nbsp;&nbsp;&nbsp;&nbsp;&lt;p&gt;<br>",
            "&nbsp;&nbsp;&nbsp;&nbsp;&lt;/p&gt;<br>",
            "</span>",
            "&lt;/div&gt;<br>",
        ]), dom)

    def test_describe_code_in_pre_element(self):
        texts = self.get_resp_texts("<pre>$('p');</pre>")
        self.assertEqual(len(texts.keys()), 1)


class TestFetchExplanationForPlaintext(unittest.TestCase):

    def setUp(self):
        self.client = Client()

    def get_explanation(self, text):
        resp = self.client.post('/explain/css', data={'origin': 'www.test.com', 'text': text})
        return resp.content

    def test_explain_css_selector_from_plaintext(self):
        resp = self.get_explanation('div.klazz')
        self.assertIn("chooses containers of class", resp)

    def test_fail_to_explain_invalid_selector_from_plaintext(self):
        resp = self.get_explanation('invalid....selector')
        self.assertIn("'invalid....selector' could not be explained as a CSS selector", resp)
