import pydantic
import enum
import random
import os
from typing import Dict, Generator, List, Optional, Tuple


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


def questions_generator(section: int, randomize: bool) -> Generator[Question, None, None]:
    sections = get_organized_questions()
    if section:
        keys = {f"{index}":key for index, key in enumerate(sections.keys())}
        questions = sections[keys[str(section)]]
    else:
        questions = []
        for sec in sections:
            questions += sections[sec]
            
    if randomize:
        random.shuffle(questions)
    yield from questions


if __name__ == "__main__":
    randomize = input("random? y|n: ").lower() == 'y'
    section = input("section number 0...n: ") if input("section? y|n: ").lower() == 'y' else None
    questions = questions_generator(section, randomize)
    right, wrong = 0, 0
    stop = False
    input("Try to answer questions in depth OK?")
    while not stop:
        question = next(questions, None)
        if question is None:
            stop = True
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
