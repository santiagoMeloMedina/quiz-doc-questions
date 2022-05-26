import pydantic
import enum
import random
import os
from typing import Generator, List, Optional, Tuple


class TextType(enum.Enum):
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"


class Text(pydantic.BaseModel):
    text: str
    type: TextType


class Question(pydantic.BaseModel):
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
        if len(line) and not line.startswith("Section"):
            yield Text(
                text=line,
                type=TextType.QUESTION if line.endswith("?") else TextType.ANSWER,
            )


def get_organized_questions() -> List[Question]:
    all_lines = filter_text()

    questions: List[Question] = []
    question = Question()
    stop = False
    while not stop:
        current = next(all_lines, None)
        if current is None:
            stop = True
            if question.is_valid():
                questions.append(question)

        elif current.type == TextType.QUESTION:
            if question.is_valid():
                questions.append(question)
            question = Question(question=current.text)

        elif current.type == TextType.ANSWER:
            question.answers.append(current.text)

    return questions


def randomize_questions() -> Generator[Question, None, None]:
    questions = get_organized_questions()
    random.shuffle(questions)
    yield from questions


if __name__ == "__main__":
    questions = randomize_questions()
    right, wrong = 0, 0
    stop = False
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
            print(question.question)
            input()
            print("\n".join(question.answers))
            input()
            veredict = input("Got it right? y|n: ")
            if veredict.lower() == "y":
                right += 1
            else:
                wrong += 1
