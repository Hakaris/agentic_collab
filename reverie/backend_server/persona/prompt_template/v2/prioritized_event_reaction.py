# priorized_event_reaction.py

from pydantic import BaseModel
import traceback

from utils import debug
from ..common import openai_config
from ..gpt_structure import generate_prompt, safe_generate_structured_response
from ..print_prompt import print_run_prompts

template = """
Task -- given context and the node of interest, decide how much of a priority the event should be on a scale of 0-10 where 0 means

Context: Jane is Liz's house mate. Jane and Liz exchanged a conversation about saying good morning at 07:05am, October 25, 2022. 
Right now, it is 07:09 am, October 25, 2022. 
Jane was on her way to using the bathroom right now. 
My question: Let's think logically. On a scale of 0-10, with 0 being absolutely not a priority, 
4-6 being something that should surely be reacted to but not really ASAP, 
and then 9-10 being highly important events that need our persona's immediate attention,
provide a rating of priority to Jane in regards to the following
observed event: Jane sees Liz fall down the stairs.
Reasoning: Jane wants to use the bathroom, but her house mate Liz has fallen. 
It would be strange for her to not want to check on her house mate immediately since she could be injured.
Liz's fall must be highly prioritized because she is likely in pain, and any potential injury could worsen if there are delays in helping her.
Answer: 10
---
Context: Sam is Sarah's friend. Sam and Sarah exchanged a conversation about favorite movies at 11pm, October 24, 2022. 
Right now, it is 12:40 pm, October 25, 2022. 
Sam is on the way to study for his test. 
My question: Let's think logically. On a scale of 0-10, with 0 being absolutely not a priority, 
4-6 being something that should surely be reacted to but not really ASAP, 
and then 9-10 being highly important events that need our persona's immediate attention,
provide a rating of priority to Sam in regards to the following
observed event: Sam sees Sarah reading a book.
Reasoning: Sam is on his way to study, but he sees his friend Sarah reading a book.
He could stop to say hi to his friend Sarah as this is the social norm, but it is not a high priority event.
He can surely continue on with his day without saying hi, but if he has the time, it could be nice to react and say hi.
Answer: 3
---
Context: !<INPUT 0>!
Right now, it is !<INPUT 1>!.
!<INPUT 2>! 
My question: Let's think logically. On a scale of 0-10, with 0 being absolutely not a priority, 
4-6 being something that should surely be reacted to but not really ASAP, 
and then 9-10 being highly important events that need our persona's immediate attention,
provide a rating of priority to !<INPUT 3>! in regards to the following
observed event: !<INPUT 4>!
Reasoning: 
"""


class EventPriority(BaseModel):
  urgency: int  # ranges from 0-10


def run_gpt_prompt_prioritized_event_reaction(
  init_persona, node, test_input=None, verbose=False
):
  def create_prompt_input(init_persona, node, test_input=None):
    # add context and current time first similar to decide_to_react
    context = ""
    curr_desc = node.description.split(" ")
    curr_desc[2:3] = ["was"]
    curr_desc = " ".join(curr_desc)
    context += f"{curr_desc}. "

    curr_time = init_persona.scratch.curr_time.strftime("%B %d, %Y, %H:%M:%S %p")

    # determine what our persona is currently doing
    init_act_desc = init_persona.scratch.act_description
    if "(" in init_act_desc:
      init_act_desc = init_act_desc.split("(")[-1][:-1]
    if len(init_persona.scratch.planned_path) == 0:
      loc = ""
      if ":" in init_persona.scratch.act_address:
        loc = (
          init_persona.scratch.act_address.split(":")[-1]
          + " in "
          + init_persona.scratch.act_address.split(":")[-2]
        )
      init_p_desc = f"{init_persona.name} is already {init_act_desc} at {loc}"
    else:
      loc = ""
      if ":" in init_persona.scratch.act_address:
        loc = (
          init_persona.scratch.act_address.split(":")[-1]
          + " in "
          + init_persona.scratch.act_address.split(":")[-2]
        )
      init_p_desc = f"{init_persona.name} is on the way to {init_act_desc} at {loc}"
    # now provide info about the node in question
    node_desc = node.description

    prompt_input = []
    prompt_input += [context]
    prompt_input += [curr_time]
    prompt_input += [init_p_desc]
    prompt_input += [init_persona.name]
    prompt_input += [node_desc]

    return prompt_input

  def __func_clean_up(gpt_response: EventPriority, prompt=""):
    print(f"Inside func_clean_up, here is gpt_response.urgency: {gpt_response.urgency}")
    return (
      gpt_response.urgency
      if type(gpt_response.urgency) is int
      else int(gpt_response.urgency)
    )

  def __func_validate(gpt_response, prompt=""):
    try:
      if isinstance(gpt_response, EventPriority) and __func_clean_up(
        gpt_response, prompt
      ) in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        return True
      return False
    except:
      traceback.print_exc()
      return False

  def get_fail_safe():
    fs = "yes"
    return fs

  gpt_param = {
    "engine": openai_config["model"],
    "max_tokens": 100,
    "temperature": 0,
    "top_p": 1,
    "stream": False,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "stop": None,
  }
  prompt_template = "persona/prompt_template/v2/prioritized_event_reaction.py"
  prompt_input = create_prompt_input(init_persona, node, test_input)
  prompt = generate_prompt(prompt_input, prompt_template_str=template)

  fail_safe = get_fail_safe()
  output = safe_generate_structured_response(
    prompt, gpt_param, EventPriority, 5, fail_safe, __func_validate, __func_clean_up
  )
  print(
    f"GPT Safe Generated Output for run_gpt_prompt_prioritized_event_reaction: {output}"
  )

  if debug or verbose:
    print_run_prompts(
      prompt_template, init_persona, gpt_param, prompt_input, prompt, output
    )

  return output, [output, prompt, gpt_param, prompt_input, fail_safe]
