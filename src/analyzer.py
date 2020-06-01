import os
import nltk
from nltk.corpus import wordnet
from nltk.metrics import edit_distance
import re
import operator
import collections
from src.globals import *
from src.dictionaries import *
from src.stories import *

class Analyzer:
  def generate_defects(kind, story, allStories=[], **kwargs):
    for kwarg in kwargs:
      exec(kwarg+ '=' + str(kwargs[kwarg]))
    for defect_type in ERRORS[kind]:
      if eval(defect_type['rule']):
        add_defect(str(story.id), kind, defect_type['subkind'], eval(defect_type['highlight']), story.title)
  
  def clear(story):
    Analyzer.generate_defects('clear', story)
    return story
  
  def consistent(story, allStories):
    Analyzer.generate_defects('consistent', story, allStories)
    return story
  
  def atomic(story):
    for chunk in ['"role"', '"means"', '"ends"']:
      Analyzer.generate_defects('atomic', story, chunk=chunk)
    return story
  
  def well_formed(story):
    Analyzer.generate_defects('well_formed', story)
    return story

  def content_chunking(chunk, kind):
    sentence = nltk.word_tokenize(chunk)
    sentence = nltk.pos_tag(sentence)
    sentence = Analyzer.remove_indicators_pos(chunk, sentence, kind)
    sentence = Analyzer.replace_special_word_tag(sentence)
    cp = nltk.RegexpParser(CHUNK_GRAMMAR)
    result = cp.parse(sentence)
    return result

  def remove_indicators_pos(text, pos_text, indicator_type):
    for indicator in eval(indicator_type.upper() + '_INDICATORS'):
      if indicator.lower().strip() in text.lower():
        indicator_words = nltk.word_tokenize(indicator)
        pos_text = [x for x in pos_text if x[0] not in indicator_words]
    return pos_text
  
  def replace_special_word_tag(sentence):
    index = 0
    for word in sentence:
      if word[0] in SPECIAL_WORDS:  
        lst = list(sentence[index])
        lst[1] = SPECIAL_WORDS[word[0]]
        sentence[index] = tuple(lst)
      index+=1
    return sentence

  def symbol_in_role_exception(chunk, conjunction):
    surrounding_words = Analyzer.get_surrounding_words(chunk, conjunction)
    exception = [False, False, False]
    exception[0] = Analyzer.space_before_or_after_conjunction(chunk, conjunction)
    exception[1] = Analyzer.surrounding_words_bigger_than(3, surrounding_words)
    exception[2] = Analyzer.surrounding_words_valid(surrounding_words)
    return exception.count(True) >= 2

  def space_before_or_after_conjunction(chunk, conjunction):
    idx = chunk.lower().index(conjunction.lower())
    space = chunk[idx-1].isspace() or chunk[idx+len(conjunction)].isspace()
    return space

  def surrounding_words_bigger_than(number, word_array):
    result = False
    for word in word_array:
      if len(word) > number: result = True
    return result

  def surrounding_words_valid(word_array):
    result = False
    for word in word_array:
      if not wordnet.sysnet(word): result = True
    return result

  def get_common_format(all_stories):
    most_common_format = []
    for chunk in ['role', 'means', 'ends']:
      chunks = [extract_indicator_phrases(getattr(story,chunk), chunk) for story in all_stories.stories]
      chunks = list(filter(None, chunks))
      try:
        most_common_format += [collections.Counter(chunks).most_common(1)[0][0].strip()]
      except:
        print('')
      all_stories.format = ', '.join(most_common_format)
    if all_stories.format == "": all_stories.format = "As a, I want to, So that"
    return all_stories

  def highlight_text(story, word_array, severity):
    indices = []
    for word in word_array:
      if word in story.title.lower(): indices += [ [story.title.lower().index(word), word] ]
    return Analyzer.highlight_text_with_indices(story.title, indices, severity)

  def highlight_text_with_indices(text, indices, severity):
    indices.sort(reverse=True)
    for index, word in indices:
      text = text[:index] + " [*" + word + "*] " + text[index+len(word):]
    return text
  
  def highlight_text_clear(story, severity):
    signs = ['RBR', 'RBS', 'JJR', 'JJS']
    indices = []
    word_to_highlight = ""
    sentence = Analyzer.chunk_means(story.means)
    for word,tag in sentence:
      if tag in signs: word_to_highlight = " " +word+ " "
    if word_to_highlight in story.title.lower(): indices += [ [story.title.lower().index(word_to_highlight), word_to_highlight] ]
    return Analyzer.highlight_text_with_indices(story.title, indices, severity)

  def chunk_means(means):
    sentence = nltk.word_tokenize(means)
    sentence = nltk.pos_tag(sentence)
    return sentence

  #rule
  def well_formed_content_rule(story_part, kind, tags):
    result = Analyzer.content_chunking(story_part, kind)
    well_formed = True
    for tag in tags:
      for x in result.subtrees():
        if tag.upper() in x.label(): well_formed = False
    return well_formed

  def identical_rule(story, allStories):
    if allStories.has_story(story):
      return True
    return False

  def atomic_rule(chunk, kind):
    invalid_sentences = []
    if chunk:
      for x in CONJUNCTIONS:
        if x in chunk.lower():
          if kind == 'means':
            for means in re.split(x, chunk, flags=re.IGNORECASE):
              if means:
                invalid_sentences.append(Analyzer.well_formed_content_rule(means, 'means', ['MEANS']))
          if kind == 'role':
            kontinue = True
            if x in ['&', '+']: kontinue = Analyzer.symbol_in_role_exception(chunk, x)
            if kontinue:
              for role in re.split(x, chunk, flags=re.IGNORECASE):
                if role:
                  invalid_sentences.append(Analyzer.well_formed_content_rule(role, "role", ["NP"]))
      return invalid_sentences.count(False) > 1

  def comparative_rule(story):
    signs = ['RBR', 'JJR']
    result = False
    sentence = Analyzer.chunk_means(story.means)
    for word,tag in sentence:
      if tag in signs: result = True
    return result

  def superlative_rule(story):
    signs = ['RBS', 'JJS']
    result = False
    sentence = Analyzer.chunk_means(story.means)
    for word,tag in sentence:
      if tag in signs: result = True
    return result

  def negative_statement_rule(story):
    result = False
    for x in NEGATIVE_WORDS:
      if x in story.means:
        result = True
    return result

  def subjective_rule(story):
    result = False
    for x in SUBJECTIVE:
      if x in story.means:
        result = True
    return result
  
  def ambiguous_rule(story):
    result = False
    for x in AMBIGUOUS:
      if x in story.means:
        result = True
    return result

  def loopholes_rule(story):
    result = False
    for x in LOOPHOLES:
      if x in story.means:
        result = True
    return result

class MinimalAnalyzer:
  def minimal_check(story):
    MinimalAnalyzer.check_punctuation(story)
    MinimalAnalyzer.check_bracket(story)
    return story

  def check_punctuation(story):
    if any(re.compile('(\%s .)' % x).search(story.title.lower()) for x in PUNCTUATION):
      highlight = MinimalAnalyzer.punctuation_highlight(story, 'high')
      add_defect(str(story.id), 'minimal', 'punctuation', highlight, story.title)
    return story

  def highlight_punctuation(story, severity):
    highlighted_text = story.title
    indices = []
    for word in PUNCTUATION:
      if re.search('(\%s .)' % word, story.title.lower()): indices += [ [story.title.index(word), word] ]
    first_punct = min(indices)
    highlighted_text = highlighted_text[:first_punct[0]] + " [*" + highlighted_text[first_punct[0]:] + "*] "
    return highlighted_text

  def check_bracket(story):
    if any(re.compile('(\%s' % x[0] + '.*\%s(\W|\Z))' % x[1]).search(story.title.lower()) for x in BRACKETS):
      highlight = MinimalAnalyzer.brackets_highlight(story, 'high')
      add_defect(str(story.id), 'minimal', 'brackets', highlight, story.title)
    return story

  def highlight_bracket(story, severity):
    highlighted_text = story.title
    matches = []
    for x in BRACKETS:
      split_string = '[^\%s' % x[1] + ']+\%s' % x[1]
      strings = re.findall(split_string, story.title)
      match_string = '(\%s' % x[0] + '.*\%s(\W|\Z))' % x[1]
      string_length = 0
      for string in strings:
        result = re.compile(match_string).search(string.lower())
        if result:
          span = tuple(map(operator.add, result.span(), (string_length, string_length)))
          matches += [ [span, result.group()] ]
        string_length += len(string)
    matches.sort(reverse=True)
    for index, word in matches:
      highlighted_text = highlighted_text[:index[0]] + " [*" + word + "*] " + highlighted_text[index[1]:]
    return highlighted_text

class UniqueAnalyzer:
  def identical_rule(story, allStories):
    if allStories.has_story(story):
      return True
    return False
  
  def unique(story, allStories):
    Analyzer.generate_defects('unique', story, allStories)
    return story

class ClearAnalyzer:
  def clear(story, allStories):
    Analyzer.generate_defects('clear', story, allStories)
    return story

  def check_superlative(story):
    tokenized = nltk.word_tokenize(story)
    tagged = nltk.pos_tag(tokenized)
    for word,pos in tagged:
      if pos == 'JJS':
        return True
    return False
  
  def check_comparative(story):
    tokenized = nltk.word_tokenize(story)
    tagged = nltk.pos_tag(tokenized)
    for word,pos in tagged:
      if pos == 'JJR':
        return True
    return False

  def check_negative(story):
    for word in NEGATIVE_WORDS:
      if word in story:
        return True
    return False