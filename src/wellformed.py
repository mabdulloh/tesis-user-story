from src.globals import *

class WellFormedAnalyzer:
  def well_formed(story):
    WellFormedAnalyzer.means(story)
    WellFormedAnalyzer.role(story)
    return story

  def means(story):
    if (not story.means):
      add_defect(str(story.id), 'well_formed', 'no_means', 'Add what you want to achieve', story.title)
    return story

  def role(story):
    if (not story.role):
      add_defect(str(story.id), 'well_formed', 'no_role', 'Add for who this story is', story.title)
    return story

  def only_indicator_role(story):
    indicator_in_story = ""
    if story.role:
      for indicator in ROLE_INDICATORS:
        if indicator in story.role:
          indicator_in_story = indicator
    return story.role.replace(indicator_in_story, '').strip() == ""

  def only_indicator_means(story):
    indicator_in_story = ""
    if story.means:
      for indicator in MEANS_INDICATORS:
        if indicator in story.means:
          indicator_in_story = indicator
    return story.means.replace(indicator_in_story, '').strip() == ""
