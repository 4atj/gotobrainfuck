from __future__ import annotations
import sys
from typing import Sequence, TextIO, BinaryIO


class SourceCode:
    def __init__(self, code: bytes) -> None:
        self.code = code
        self.ptr = 0

    def read_next_token(self) -> bytes:
        token = self.code[self.ptr:self.ptr+1]
        self.ptr += 1
        return token

class Context:
    def __init__(self, 
            input_file:  TextIO | BinaryIO | None = sys.stdin, 
            output_file: TextIO | BinaryIO = sys.stdout,
            buffer_size: int = 2 ** 16,
            num_cycles_limit: int = 2 ** 24) -> None:
            
        self.buffer = bytearray([0]) * buffer_size
        self.ptr = 0

        self.input_file = input_file
        self.output_file = output_file

        self.num_cycles_left = num_cycles_limit

    def exec(self, token: Token) -> int:
        if self.num_cycles_left == 0:
            raise TimeoutError

        self.num_cycles_left -= 1
        return token.exec(self)

    def read(self, n: int = -1, /) -> bytes:
        if self.input_file is None:
            return b""

        if isinstance(self.input_file, BinaryIO):
            return self.input_file.read(n)

        return bytes(map(ord,self.input_file.read(n)))

    def write(self, bytes_: bytes, /) -> None:
        from io import TextIOWrapper, StringIO

        # TODO XXX
        if ( isinstance(self.output_file, TextIO) or
             isinstance(self.output_file, TextIOWrapper) or
             isinstance(self.output_file, StringIO)):
            
            string_ = "".join(map(chr,bytes_))
            self.output_file.write(string_)

        else:
            self.output_file.write(bytes_)

        self.output_file.flush()
        
    @property
    def current_value(self) -> int:
        return self.buffer[self.ptr]

    @current_value.setter
    def current_value(self, value: int):
        # Allow overflow
        self.buffer[self.ptr] = value & 255

    @property
    def pointer(self) -> int:
        return self.ptr

    @pointer.setter
    def pointer(self, value: int):
        # Allow overflow
        self.ptr = value % len(self.buffer)

class Token:
    def exec(self, context: Context) -> int:
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

class Code:
    def __init__(self, tokens: Sequence[Token]) -> None:
        self.tokens = tuple(tokens)

    @classmethod
    def parse(cls, source_code: SourceCode) -> Code:
        tokens = []

        while token := source_code.read_next_token():
            if   token == b".":
                new_token = PrintToken()

            elif token == b",":
                new_token = ReadToken()

            elif token == b"+":
                new_token = PlusToken()

            elif token == b"-":
                new_token = MinusToken()

            elif token == b">":
                new_token = ForwardToken()

            elif token == b"<":
                new_token = BackwardToken()

            elif token == b"^":
                new_token = GoToToken()

            elif token == b";":
                new_token = ExitToken()
            
            else:
                raise SyntaxError

            tokens.append(new_token)

        return Code(tokens)

    def exec(self, context: Context):
        code_pt = 0
        while type(token := self.tokens[code_pt]) is not ExitToken:
            pt = context.exec(token)
            code_pt = code_pt + 1 if pt < 0 else pt

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.tokens}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.tokens}"
    
class ExitToken(Token):
    pass

class GoToToken(Token):
    def exec(self, context: Context) -> int:
        return context.current_value

class PlusToken(Token):
    def exec(self, context: Context) -> int:
        context.current_value += 1
        return -1

class MinusToken(Token):
    def exec(self, context: Context) -> int:
        context.current_value -= 1
        return -1

class ForwardToken(Token):
    def exec(self, context: Context) -> int:
        context.pointer += 1
        return -1

class BackwardToken(Token):
    def exec(self, context: Context) -> int:
        context.pointer -= 1
        return -1

class PrintToken(Token):
    def exec(self, context: Context) -> int:
        context.write(bytes([context.current_value]))
        return -1

class ReadToken(Token):
    def exec(self, context: Context) -> int:
        context.current_value = ord(context.read(1) or b"\0")
        return -1

def éxec(
        source_code: bytes, 
        input_file:  TextIO | BinaryIO | None = sys.stdin,
        output_file: TextIO | BinaryIO = sys.stdout,
        buffer_size: int = 2 ** 16, num_cycles_limit: int = 2 ** 24):

    context = Context(input_file = input_file, output_file = output_file, buffer_size = buffer_size, num_cycles_limit = num_cycles_limit)
    code = Code.parse(source_code = SourceCode(source_code))

    code.exec(context)

if __name__ == "__main__":
    éxec(b"<+.>^;")
