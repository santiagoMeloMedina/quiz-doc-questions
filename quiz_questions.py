import pydantic
import enum
import random
import os
from typing import Dict, Generator, List, Optional, Tuple
from itertools import islice
import signal


###########################################################
### THIS CODE COULD BE GREATLY IMPROVED BY USING CLASSES ##
###########################################################

PROGRESS_FILE = "progress.db"


class ConsoleColors(enum.Enum):
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class TextType(enum.Enum):
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    SECTION = "SECTION"


class Text(pydantic.BaseModel):
    text: str
    type: TextType


class Question(pydantic.BaseModel):
    section: Optional[str]
    question: Optional[str]
    answers: List[str] = []

    def is_valid(self) -> bool:
        return self.question is not None


def obtain_questions_text() -> str:
    file = open("questions.txt", "r")
    return "".join(file.readlines())


def filter_text() -> Generator[Text, None, None]:
    only_text = obtain_questions_text().split("\n")
    for line in only_text:
        if len(line):
            if line.startswith("Section"):
                text_type = TextType.SECTION
            elif line.endswith("?"):
                text_type = TextType.QUESTION
            else:
                text_type = TextType.ANSWER

            yield Text(text=line, type=text_type)


def get_organized_questions() -> Dict[str, List[Question]]:
    all_lines = filter_text()

    question = Question()
    section = None
    sections = dict()
    stop = False
    while not stop:
        current = next(all_lines, None)
        if current is None:
            stop = True
            if question.is_valid():
                sections[question.section].append(question)

        elif current.type == TextType.SECTION:
            section = current.text
            sections[section] = []

        elif current.type == TextType.QUESTION:
            if question.is_valid():
                sections[question.section].append(question)
            question = Question(question=current.text, section=section)

        elif current.type == TextType.ANSWER:
            question.answers.append(current.text)

    return sections


def questions_generator(
    section: int, randomize: bool
) -> Generator[Question, None, None]:
    sections = get_organized_questions()
    if section:
        keys = {f"{index}": key for index, key in enumerate(sections.keys())}
        questions = sections[keys[str(section)]]
    else:
        questions = []
        for sec in sections:
            questions += sections[sec]

    if randomize:
        random.shuffle(questions)
    yield from questions


def get_progress():
    result = (None, None)
    try:
        progress_file = open(PROGRESS_FILE, "r")
        lines = progress_file.read().split()
        section = lines[0].split("-")[1]
        question = lines[1].split("-")[1]
        result = (section, question)
    except:
        print("Could not read progress")

    return result


def save_progress(question: int = 0, section: int = None):
    try:
        file = open(PROGRESS_FILE, "w")
        file.write(f"section-{section}\nquestion-{question}")
    except:
        print("Could not save progress")


def exit_handler(*args, **kwargs):
    global prog_question, prog_section, randomize
    if not randomize:
        save_progress(prog_question, prog_section)
    exit()


def newly_take():
    global randomize, prog_section
    randomize = input("random? y|n: ").lower() == "y"
    prog_section = (
        input("section number 0...n: ")
        if input("section? y|n: ").lower() == "y"
        else None
    )
    return questions_generator(prog_section, randomize)


def decide_questions():
    global prog_question, prog_section, randomize
    prog_question, prog_section, randomize = 0, None, True
    progress_section, progress_question = get_progress()
    progress_section, progress_question = eval(progress_section), eval(
        progress_question
    )
    if progress_section or progress_question:
        if input("reset? y|n: ").lower() == "y":
            questions = newly_take()
        else:
            randomize = False
            progress_question = progress_question or 0
            questions = questions_generator(progress_section or 0, False)
            for _ in range(int(progress_question)):
                next(questions)
            prog_question, prog_section = progress_question, progress_section
    else:
        questions = newly_take()

    return questions


def start_quiz(questions: Generator[Question, None, None]):
    global prog_question
    input("Try to answer questions in depth OK?")
    right, wrong = 0, 0
    stop = False
    while not stop:
        question = next(questions, None)
        prog_question += 1
        if question is None:
            stop = True
            save_progress()
            os.system("clear")
            print("Finished!")
            print(f"Results:\n    Correct: {right}\n    Incorrect: {wrong}")
            print(f"Score: {'{:.2f}'.format(100/(right+wrong)*right)} / 100")
        else:
            os.system("clear")
            print(
                f"{ConsoleColors.OKCYAN.value}{question.section}{ConsoleColors.ENDC.value}"
            )
            print(
                f"{ConsoleColors.OKGREEN.value}{question.question}{ConsoleColors.ENDC.value}"
            )
            input()
            print(
                ConsoleColors.OKBLUE.value,
                "\n".join(question.answers),
                ConsoleColors.ENDC.value,
            )
            input()
            veredict = input("Got it right? y|n: ")
            if veredict.lower() == "y":
                right += 1
            else:
                wrong += 1


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)
    start_quiz(decide_questions())
