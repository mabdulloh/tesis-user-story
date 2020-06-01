import re
import os
import nltk
from yattag import Doc
from src.defect import *

try:
	nltk.data.find('tokenizers/punkt')
except:
	nltk.download('punkt')

try:
	nltk.data.find('taggers/averaged_perceptron_tagger')
except:
	nltk.download('averaged_perceptron_tagger')

doc, tag, text = Doc().tagtext()

ROLE_INDICATORS = ["^As ", "^As a ", "^As an "]
MEANS_INDICATORS = ["[, ]I want ", "[, ]I would like", "[, ]I can ", "[, ]I don't want", 
                    "[, ]I should be able to ", "[, ]I am able to ", "[, ]I'm able to "]
ENDS_INDICATORS = ["[, ]So that ", "[, ]In order to ","[, ]So "]
CONJUNCTIONS = [' and ', ' or ', '&', '/', '>', '<']
PUNCTUATION = ['.', ';', ':', '‒', '–', '—', '―', '‐', '-', '?', '*']
BRACKETS = [['(', ')'], ['[', ']'], ['{', '}'], ['⟨', '⟩']]
NEGATIVE_WORDS = [" no "," not ", " don't ", " can't "]
SUBJECTIVE_WORDS = [" efficient ", " simple ", " enough "]
ERRORS = {
          'well_formed': [
            { 'subkind': 'means', 'rule': 'Analyzer.well_formed_content_rule(story.means, "means", ["means"])', 'severity':'medium', 'highlight':'str("Make sure the means includes a verb and a noun. Our analysis shows the means currently includes: ") + Analyzer.well_formed_content_highlight(story.means, "means")'},
            { 'subkind': 'role', 'rule': 'Analyzer.well_formed_content_rule(story.role, "role", ["NP"])', 'severity':'medium', 'highlight':'str("Make sure the role includes a person noun. Our analysis shows the role currently includes: ") + Analyzer.well_formed_content_highlight(story.role, "role")'},
          ],
          'clear': [
            { 'subkind': 'comparative', 'rule': 'Analyzer.comparative_rule(story)', 'severity': 'medium', 'highlight':"Analyzer.highlight_text_clear(story, 'medium')"},
            { 'subkind': 'superlative', 'rule': 'Analyzer.superlative_rule(story)', 'severity': 'medium', 'highlight':"Analyzer.highlight_text_clear(story, 'medium')"},
            { 'subkind': 'negative_statement', 'rule': 'Analyzer.negative_statement_rule(story)', 'severity': 'high', 'highlight':"Analyzer.highlight_text(story, NEGATIVE_WORDS, 'high')"},
            { 'subkind': 'subjective', 'rule': 'Analyzer.subjective_rule(story)', 'severity': 'medium', 'highlight':"Analyzer.highlight_text(story, SUBJECTIVE, 'medium')"},
            { 'subkind': 'ambiguous', 'rule': 'Analyzer.ambiguous_rule(story)', 'severity': 'medium', 'highlight':"Analyzer.highlight_text(story, AMBIGUOUS, 'medium')"},
            { 'subkind': 'loopholes', 'rule': 'Analyzer.loopholes_rule(story)', 'severity': 'medium', 'highlight':"Analyzer.highlight_text(story, LOOPHOLES, 'medium')"}
          ],
          'consistent': [
            { 'subkind':'conjunctions', 'rule':"Analyzer.atomic_rule(getattr(story,chunk), chunk)", 'severity':'high', 'highlight':"Analyzer.highlight_text(story, CONJUNCTIONS, 'high')"},
            { 'subkind':'identical', 'rule':"Analyzer.identical_rule(story,allStories)", 'severity':'high', 'highlight':'str("Remove all duplicate user stories")' }
          ],
          'atomic': [
            { 'subkind':'conjunctions', 'rule':"Analyzer.atomic_rule(getattr(story,chunk), chunk)", 'severity':'high', 'highlight':"Analyzer.highlight_text(story, CONJUNCTIONS, 'high')"}
          ]}

CHUNK_GRAMMAR = """
      NP: {<DT|JJ|NN.*>}
      NNP: {<NNP.*>}
      AP: {<RB.*|JJ.*>}
      VP: {<VB.*><NP>*}
      MEANS: {<AP>?<VP>}
      ENDS: {<AP>?<VP>}
    """

SPECIAL_WORDS = {'import': 'VP', "export": 'VP', 'select': 'VP', 'support': 'VP'}

defects = []

def init_format(output_format):
  global oformat
  oformat = output_format

def extract_indicator_phrases(txt, indicator_type):
  if txt:
    indicator_phrases = []
    for indicator in eval(indicator_type.upper() + '_INDICATORS'):
      if re.compile('(%s)' % indicator.lower().replace('[, ]', '')).search(text.lower()): 
        indicator_phrase += [indicator.replace('^', '').replace('[, ]', '')]
    return max(indicator_phrase, key=len) if indicator_phrase else None
  else:
    return txt

def add_defect(story_id, kind, subkind, message, story_title):
  defects.append(Defect(story_id, kind, subkind, message, story_title))