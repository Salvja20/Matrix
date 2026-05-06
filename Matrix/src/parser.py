from lexer import (
    INTEGER, FLOAT, STRING, BOOLEAN, IDENTIFIER,
    PLUS, MINUS, STAR, SLASH, DOUBLESLASH, PERCENT, POWER, AT,
    EQEQ, NEQ, LT, LTE, GT, GTE,
    EQUAL, SEMICOLON, COMMA, DOT,
    LPAREN, RPAREN, LBRACE, RBRACE, LBRACKET, RBRACKET,
    PRINT, IF, ELSE, WHILE, FUNCTION, RETURN,
    CLASS, MODULE, IMPORT, AND, OR, NOT,
    NULL, BREAK, EOF
)
from ast_nodes import (
    Program, AssignmentStatement, PrintStatement,
    IfStatement, WhileStatement, ReturnStatement, BreakStatement,
    ExpressionStatement, FunctionDeclaration, ClassDeclaration,
    ModuleDeclaration, ImportStatement,
    BinaryExpression, UnaryExpression, CallExpression,
    MemberExpression, IndexExpression,
    IntegerLiteral, FloatLiteral, StringLiteral, BooleanLiteral,
    NullLiteral, ArrayLiteral, Identifier
)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ── Helpers ───────────────────────────────────────────────────────────────

    def current(self):
        return self.tokens[self.pos]

    def peek_next(self):
        idx = self.pos + 1
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, token_type):
        tok = self.current()
        if tok.type != token_type:
            raise ParseError(
                f"Line {tok.line}: Expected {token_type} but got {tok.type}('{tok.value}')"
            )
        return self.advance()

    def match(self, *types):
        return self.current().type in types

    # ── Program ───────────────────────────────────────────────────────────────

    def parse_program(self):
        stmts = []
        while not self.match(EOF):
            stmts.append(self.parse_statement())
        return Program(stmts)

    # ── Statements ────────────────────────────────────────────────────────────

    def parse_statement(self):
        t = self.current().type

        if t == PRINT:
            return self.parse_print()
        elif t == IF:
            return self.parse_if()
        elif t == WHILE:
            return self.parse_while()
        elif t == FUNCTION:
            return self.parse_function()
        elif t == CLASS:
            return self.parse_class()
        elif t == MODULE:
            return self.parse_module()
        elif t == IMPORT:
            return self.parse_import()
        elif t == RETURN:
            return self.parse_return()
        elif t == BREAK:
            self.advance()
            self.expect(SEMICOLON)
            return BreakStatement()
        elif t == IDENTIFIER:
            # Could be assignment or expression statement (call)
            return self.parse_identifier_statement()
        else:
            tok = self.current()
            raise ParseError(f"Line {tok.line}: Unexpected token {tok.type}('{tok.value}')")

    def parse_identifier_statement(self):
        """Either  identifier = expr;  or  expr;  (e.g. a function call)."""
        expr = self.parse_expression()

        # Assignment
        if self.match(EQUAL):
            if not isinstance(expr, (Identifier, MemberExpression, IndexExpression)):
                raise ParseError("Invalid assignment target")
            self.advance()   # consume '='
            value = self.parse_expression()
            self.expect(SEMICOLON)
            return AssignmentStatement(expr, value)

        # Bare expression statement (e.g. function call)
        self.expect(SEMICOLON)
        return ExpressionStatement(expr)

    def parse_print(self):
        self.expect(PRINT)
        expr = self.parse_expression()
        self.expect(SEMICOLON)
        return PrintStatement(expr)

    def parse_if(self):
        self.expect(IF)
        self.expect(LPAREN)
        condition = self.parse_expression()
        self.expect(RPAREN)
        then_block = self.parse_block()
        else_block = None
        if self.match(ELSE):
            self.advance()
            else_block = self.parse_block()
        return IfStatement(condition, then_block, else_block)

    def parse_while(self):
        self.expect(WHILE)
        self.expect(LPAREN)
        condition = self.parse_expression()
        self.expect(RPAREN)
        body = self.parse_block()
        return WhileStatement(condition, body)

    def parse_function(self):
        self.expect(FUNCTION)
        name = self.expect(IDENTIFIER).value
        self.expect(LPAREN)
        params = []
        if not self.match(RPAREN):
            params.append(self.expect(IDENTIFIER).value)
            while self.match(COMMA):
                self.advance()
                params.append(self.expect(IDENTIFIER).value)
        self.expect(RPAREN)
        body = self.parse_block()
        return FunctionDeclaration(name, params, body)

    def parse_class(self):
        self.expect(CLASS)
        name = self.expect(IDENTIFIER).value
        body = self.parse_block()
        return ClassDeclaration(name, body)

    def parse_module(self):
        self.expect(MODULE)
        name = self.expect(IDENTIFIER).value
        body = self.parse_block()
        return ModuleDeclaration(name, body)

    def parse_import(self):
        self.expect(IMPORT)
        name = self.expect(IDENTIFIER).value
        self.expect(SEMICOLON)
        return ImportStatement(name)

    def parse_return(self):
        self.expect(RETURN)
        expr = None
        if not self.match(SEMICOLON):
            expr = self.parse_expression()
        self.expect(SEMICOLON)
        return ReturnStatement(expr)

    def parse_block(self):
        """Parse { statement* }"""
        self.expect(LBRACE)
        stmts = []
        while not self.match(RBRACE) and not self.match(EOF):
            stmts.append(self.parse_statement())
        self.expect(RBRACE)
        return stmts

    # ── Expressions (precedence climbing) ────────────────────────────────────
    #
    #  or_expr → and_expr ('or' and_expr)*
    #  and_expr → not_expr ('and' not_expr)*
    #  not_expr → 'not' not_expr | comparison
    #  comparison → addition (('=='|'!='|'<'|'<='|'>'|'>=') addition)*
    #  addition → term (('+' | '-') term)*
    #  term → power (('*'|'/'|'//'|'%'|'@') power)*
    #  power → unary ('**' unary)*
    #  unary → '-' unary | postfix
    #  postfix → primary ('.' IDENTIFIER | '(' args ')' | '[' expr ']')*
    #  primary → literal | identifier | '(' expr ')' | '[' elems ']'

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.match(OR):
            op = self.advance().value
            right = self.parse_and()
            left = BinaryExpression(left, op, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.match(AND):
            op = self.advance().value
            right = self.parse_not()
            left = BinaryExpression(left, op, right)
        return left

    def parse_not(self):
        if self.match(NOT):
            op = self.advance().value
            return UnaryExpression(op, self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_addition()
        while self.match(EQEQ, NEQ, LT, LTE, GT, GTE):
            op = self.advance().value
            right = self.parse_addition()
            left = BinaryExpression(left, op, right)
        return left

    def parse_addition(self):
        left = self.parse_term()
        while self.match(PLUS, MINUS):
            op = self.advance().value
            right = self.parse_term()
            left = BinaryExpression(left, op, right)
        return left

    def parse_term(self):
        left = self.parse_power()
        while self.match(STAR, SLASH, DOUBLESLASH, PERCENT, AT):
            op = self.advance().value
            right = self.parse_power()
            left = BinaryExpression(left, op, right)
        return left

    def parse_power(self):
        base = self.parse_unary()
        if self.match(POWER):
            op = self.advance().value
            exp = self.parse_unary()   # right-associative
            return BinaryExpression(base, op, exp)
        return base

    def parse_unary(self):
        if self.match(MINUS):
            op = self.advance().value
            return UnaryExpression(op, self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        """Handle  expr.member  /  expr(args)  /  expr[index]  chains."""
        node = self.parse_primary()
        while True:
            if self.match(DOT):
                self.advance()
                member = self.expect(IDENTIFIER).value
                node = MemberExpression(node, member)
            elif self.match(LPAREN):
                self.advance()
                args = []
                if not self.match(RPAREN):
                    args.append(self.parse_expression())
                    while self.match(COMMA):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(RPAREN)
                node = CallExpression(node, args)
            elif self.match(LBRACKET):
                self.advance()
                index = self.parse_expression()
                self.expect(RBRACKET)
                node = IndexExpression(node, index)
            else:
                break
        return node

    def parse_primary(self):
        tok = self.current()

        if tok.type == INTEGER:
            self.advance()
            return IntegerLiteral(tok.value)

        elif tok.type == FLOAT:
            self.advance()
            return FloatLiteral(tok.value)

        elif tok.type == STRING:
            self.advance()
            return StringLiteral(tok.value)

        elif tok.type == BOOLEAN:
            self.advance()
            return BooleanLiteral(tok.value)

        elif tok.type == NULL:
            self.advance()
            return NullLiteral()

        elif tok.type == IDENTIFIER:
            self.advance()
            return Identifier(tok.value)

        elif tok.type == LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(RPAREN)
            return expr

        elif tok.type == LBRACKET:
            return self.parse_array()

        else:
            raise ParseError(
                f"Line {tok.line}: Unexpected token {tok.type}('{tok.value}') in expression"
            )

    def parse_array(self):
        self.expect(LBRACKET)
        elements = []
        if not self.match(RBRACKET):
            elements.append(self.parse_expression())
            while self.match(COMMA):
                self.advance()
                elements.append(self.parse_expression())
        self.expect(RBRACKET)
        return ArrayLiteral(elements)
