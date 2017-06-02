def is_it_answer_to_life_universe_and_everything(integer):
    if isinstance(integer, int):
        return integer == 42
    else:
        raise NameError("Hint: it's a number! :P")
