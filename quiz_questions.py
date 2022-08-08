import pydantic
import enum
import random
import os
from typing import Dict, Generator, List, Optional, Tuple
from itertools import islice
import signal
from voice import SpeechTranslator


###########################################################
### THIS CODE COULD BE GREATLY IMPROVED BY USING CLASSES ##
###########################################################


SPEECH = SpeechTranslator()
SPEECH.set_default_translate(to_lang="en", from_lang="en", name="Samantha")

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


def questions_generator(randomize: bool) -> Generator[Question, None, None]:
    global prog_section
    sections = get_organized_questions()

    if input("section? y|n: ").lower() == "y":
        print("\n".join(sections.keys()))
        prog_section = int(input(f"\nsection number 3...{len(sections)}: ")) - 3

    if prog_section:
        keys = {f"{index}": key for index, key in enumerate(sections.keys())}
        questions = sections[keys[str(prog_section)]]
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
    global randomize, prog_section, with_voice
    with_voice = input("want questions to be read? y|n: ").lower() == "y"
    randomize = input("random? y|n: ").lower() == "y"
    return questions_generator(randomize)


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
            questions = questions_generator(False)
            for _ in range(int(progress_question)):
                next(questions)
            prog_question, prog_section = progress_question, progress_section
    else:
        questions = newly_take()

    return questions


def display_question(question: Question):
    global with_voice
    os.system("clear")
    print(f"{ConsoleColors.OKCYAN.value}{question.section}{ConsoleColors.ENDC.value}")
    print(f"{ConsoleColors.OKGREEN.value}{question.question}{ConsoleColors.ENDC.value}")
    if with_voice:
        SPEECH.default_read_translate(question.question)
    input()
    print(
        ConsoleColors.OKBLUE.value,
        "\n".join(question.answers),
        ConsoleColors.ENDC.value,
    )
    if with_voice:
        for answer in question.answers:
            SPEECH.default_read_translate(answer)
    input("\n\nSiguiente pregunta -->")


def start_quiz(questions: Generator[Question, None, None]):
    global prog_question
    stop = False
    while not stop:
        question = next(questions, None)
        prog_question += 1
        if question is None:
            stop = True
            save_progress()
            os.system("clear")
            print("Finished!")
        else:
            display_question(question)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)
    start_quiz(decide_questions())
