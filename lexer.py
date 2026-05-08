# ── Token types ──────────────────────────────────────────────────────────────

# Literals
INTEGER    = 'INTEGER'
FLOAT      = 'FLOAT'
STRING     = 'STRING'
BOOLEAN    = 'BOOLEAN'

# Identifiers
IDENTIFIER = 'IDENTIFIER'

# Arithmetic operators
PLUS       = 'PLUS'
MINUS      = 'MINUS'
STAR       = 'STAR'
SLASH      = 'SLASH'
DOUBLESLASH = 'DOUBLESLASH'   # //  integer division
PERCENT    = 'PERCENT'        # %   remainder
POWER      = 'POWER'          # **  power
AT         = 'AT'             # @   matrix multiply

# Comparison operators
EQEQ       = 'EQEQ'          # ==
NEQ        = 'NEQ'            # !=
LT         = 'LT'             # <
LTE        = 'LTE'            # <=
GT         = 'GT'             # >
GTE        = 'GTE'            # >=

# Assignment
EQUAL      = 'EQUAL'          # =

# Punctuation
SEMICOLON  = 'SEMICOLON'      # ;
COLON      = 'COLON'          # :
COMMA      = 'COMMA'          # ,
DOT        = 'DOT'            # .
LPAREN     = 'LPAREN'         # (
RPAREN     = 'RPAREN'         # )
LBRACE     = 'LBRACE'         # {
RBRACE     = 'RBRACE'         # }
LBRACKET   = 'LBRACKET'       # [
RBRACKET   = 'RBRACKET'       # ]

# Keywords
PRINT      = 'PRINT'
IF         = 'IF'
ELSE       = 'ELSE'
WHILE      = 'WHILE'
FUNCTION   = 'FUNCTION'
RETURN     = 'RETURN'
CLASS      = 'CLASS'
MODULE     = 'MODULE'
IMPORT     = 'IMPORT'
AND        = 'AND'
OR         = 'OR'
NOT        = 'NOT'
TRUE       = 'TRUE'
FALSE      = 'FALSE'
NULL       = 'NULL'
BREAK      = 'BREAK'

EOF        = 'EOF'

# ── Keyword map ───────────────────────────────────────────────────────────────
KEYWORDS = {
    'print':    PRINT,
    'if':       IF,
    'else':     ELSE,
    'while':    WHILE,
    'function': FUNCTION,
    'return':   RETURN,
    'class':    CLASS,
    'module':   MODULE,
    'import':   IMPORT,
    'and':      AND,
    'or':       OR,
    'not':      NOT,
    'true':     TRUE,
    'false':    FALSE,
    'null':     NULL,
    'break':    BREAK,
}


# ── Token ─────────────────────────────────────────────────────────────────────
class Token:
    def __init__(self, type_, value, line=1):
        self.type  = type_
        self.value = value
        self.line  = line          # track line number for error messages

    def __repr__(self):
        return f"{self.type}({self.value})"


# ── Errors ────────────────────────────────────────────────────────────────────
class LexerError(Exception):
    pass


# ── Lexer ─────────────────────────────────────────────────────────────────────
class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0
        self.line   = 1

    # ── Helpers ───────────────────────────────────────────────────────────────
    def error(self, msg):
        raise LexerError(f"Line {self.line}: {msg}")

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def skip_whitespace_and_comments(self):
        while self.peek() is not None:
            ch = self.peek()
            # Whitespace
            if ch.isspace():
                self.advance()
            # Single-line comment  #...
            elif ch == '#':
                while self.peek() is not None and self.peek() != '\n':
                    self.advance()
            else:
                break

    # ── Readers ───────────────────────────────────────────────────────────────
    def read_number(self):
        """Read an integer or float literal."""
        digits = ''
        while self.peek() is not None and self.peek().isdigit():
            digits += self.advance()

        if self.peek() == '.' and (self.peek(1) is not None and self.peek(1).isdigit()):
            digits += self.advance()   # consume '.'
            while self.peek() is not None and self.peek().isdigit():
                digits += self.advance()
            return Token(FLOAT, float(digits), self.line)

        return Token(INTEGER, int(digits), self.line)

    def read_string(self):
        """Read a double-quoted string literal."""
        self.advance()   # consume opening "
        chars = ''
        while self.peek() is not None and self.peek() != '"':
            ch = self.advance()
            if ch == '\\':           # escape sequences
                nxt = self.advance()
                escape = {'n': '\n', 't': '\t', '\\': '\\', '"': '"'}
                chars += escape.get(nxt, nxt)
            else:
                chars += ch
        if self.peek() is None:
            self.error("Unterminated string literal")
        self.advance()   # consume closing "
        return Token(STRING, chars, self.line)

    def read_identifier(self):
        """Read an identifier or keyword."""
        chars = ''
        while self.peek() is not None and (self.peek().isalnum() or self.peek() == '_'):
            chars += self.advance()
        token_type = KEYWORDS.get(chars, IDENTIFIER)
        # Map true/false to boolean values
        if token_type == TRUE:
            return Token(BOOLEAN, True, self.line)
        if token_type == FALSE:
            return Token(BOOLEAN, False, self.line)
        return Token(token_type, chars, self.line)

    # ── Main tokenize loop ────────────────────────────────────────────────────
    def tokenize(self):
        tokens = []

        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break

            ch  = self.peek()
            ln  = self.line

            # Numbers
            if ch.isdigit():
                tokens.append(self.read_number())

            # Strings
            elif ch == '"':
                tokens.append(self.read_string())

            # Identifiers / keywords
            elif ch.isalpha() or ch == '_':
                tokens.append(self.read_identifier())

            # Two-character operators first
            elif ch == '*' and self.peek(1) == '*':
                self.advance(); self.advance()
                tokens.append(Token(POWER, '**', ln))

            elif ch == '/' and self.peek(1) == '/':
                self.advance(); self.advance()
                tokens.append(Token(DOUBLESLASH, '//', ln))

            elif ch == '=' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token(EQEQ, '==', ln))

            elif ch == '!' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token(NEQ, '!=', ln))

            elif ch == '<' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token(LTE, '<=', ln))

            elif ch == '>' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token(GTE, '>=', ln))

            # Single-character operators
            elif ch == '+':
                self.advance(); tokens.append(Token(PLUS,      '+', ln))
            elif ch == '-':
                self.advance(); tokens.append(Token(MINUS,     '-', ln))
            elif ch == '*':
                self.advance(); tokens.append(Token(STAR,      '*', ln))
            elif ch == '/':
                self.advance(); tokens.append(Token(SLASH,     '/', ln))
            elif ch == '%':
                self.advance(); tokens.append(Token(PERCENT,   '%', ln))
            elif ch == '@':
                self.advance(); tokens.append(Token(AT,        '@', ln))
            elif ch == '<':
                self.advance(); tokens.append(Token(LT,        '<', ln))
            elif ch == '>':
                self.advance(); tokens.append(Token(GT,        '>', ln))
            elif ch == '=':
                self.advance(); tokens.append(Token(EQUAL,     '=', ln))
            elif ch == ';':
                self.advance(); tokens.append(Token(SEMICOLON, ';', ln))
            elif ch == ':':
                self.advance(); tokens.append(Token(COLON,     ':', ln))
            elif ch == ',':
                self.advance(); tokens.append(Token(COMMA,     ',', ln))
            elif ch == '.':
                self.advance(); tokens.append(Token(DOT,       '.', ln))
            elif ch == '(':
                self.advance(); tokens.append(Token(LPAREN,    '(', ln))
            elif ch == ')':
                self.advance(); tokens.append(Token(RPAREN,    ')', ln))
            elif ch == '{':
                self.advance(); tokens.append(Token(LBRACE,    '{', ln))
            elif ch == '}':
                self.advance(); tokens.append(Token(RBRACE,    '}', ln))
            elif ch == '[':
                self.advance(); tokens.append(Token(LBRACKET,  '[', ln))
            elif ch == ']':
                self.advance(); tokens.append(Token(RBRACKET,  ']', ln))

            else:
                self.error(f"Unknown character: '{ch}'")

        tokens.append(Token(EOF, 'EOF', self.line))
        return tokens
