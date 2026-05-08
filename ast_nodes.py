# ── Literals ──────────────────────────────────────────────────────────────────

class IntegerLiteral:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"IntegerLiteral({self.value})"

class FloatLiteral:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"FloatLiteral({self.value})"

class StringLiteral:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"StringLiteral({self.value!r})"

class BooleanLiteral:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"BooleanLiteral({self.value})"

class NullLiteral:
    def __repr__(self):
        return "NullLiteral"

class ArrayLiteral:
    def __init__(self, elements):
        self.elements = elements
    def __repr__(self):
        return f"ArrayLiteral({self.elements})"


# ── Identifier ────────────────────────────────────────────────────────────────

class Identifier:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Identifier({self.name})"


# ── Expressions ───────────────────────────────────────────────────────────────

class BinaryExpression:
    def __init__(self, left, operator, right):
        self.left     = left
        self.operator = operator
        self.right    = right
    def __repr__(self):
        return f"BinaryExpression({self.operator}, {self.left}, {self.right})"

class UnaryExpression:
    def __init__(self, operator, operand):
        self.operator = operator
        self.operand  = operand
    def __repr__(self):
        return f"UnaryExpression({self.operator}, {self.operand})"

class CallExpression:
    """Function call:  name(arg1, arg2, ...)"""
    def __init__(self, callee, arguments):
        self.callee    = callee      # Identifier or MemberExpression
        self.arguments = arguments   # list of expressions
    def __repr__(self):
        return f"CallExpression({self.callee}, {self.arguments})"

class MemberExpression:
    """Dot access:  object.member"""
    def __init__(self, obj, member):
        self.obj    = obj
        self.member = member
    def __repr__(self):
        return f"MemberExpression({self.obj}.{self.member})"

class IndexExpression:
    """Array index:  array[index]"""
    def __init__(self, obj, index):
        self.obj   = obj
        self.index = index
    def __repr__(self):
        return f"IndexExpression({self.obj}[{self.index}])"


# ── Statements ────────────────────────────────────────────────────────────────

class Program:
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self):
        return f"Program({self.statements})"

class AssignmentStatement:
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression
    def __repr__(self):
        return f"AssignmentStatement({self.identifier}, {self.expression})"

class PrintStatement:
    def __init__(self, expression):
        self.expression = expression
    def __repr__(self):
        return f"PrintStatement({self.expression})"

class IfStatement:
    def __init__(self, condition, then_block, else_block=None):
        self.condition  = condition
        self.then_block = then_block   # list of statements
        self.else_block = else_block   # list of statements or None
    def __repr__(self):
        return f"IfStatement({self.condition})"

class WhileStatement:
    def __init__(self, condition, body):
        self.condition = condition
        self.body      = body          # list of statements
    def __repr__(self):
        return f"WhileStatement({self.condition})"

class ReturnStatement:
    def __init__(self, expression=None):
        self.expression = expression
    def __repr__(self):
        return f"ReturnStatement({self.expression})"

class BreakStatement:
    def __repr__(self):
        return "BreakStatement"

class ExpressionStatement:
    """A bare expression used as a statement, e.g. a function call."""
    def __init__(self, expression):
        self.expression = expression
    def __repr__(self):
        return f"ExpressionStatement({self.expression})"


# ── Declarations ──────────────────────────────────────────────────────────────

class FunctionDeclaration:
    def __init__(self, name, parameters, body):
        self.name       = name         # string
        self.parameters = parameters   # list of strings
        self.body       = body         # list of statements
    def __repr__(self):
        return f"FunctionDeclaration({self.name}, {self.parameters})"

class ClassDeclaration:
    def __init__(self, name, body):
        self.name = name
        self.body = body               # list of statements / function declarations
    def __repr__(self):
        return f"ClassDeclaration({self.name})"

class ModuleDeclaration:
    def __init__(self, name, body):
        self.name = name
        self.body = body
    def __repr__(self):
        return f"ModuleDeclaration({self.name})"

class ImportStatement:
    def __init__(self, module_name):
        self.module_name = module_name
    def __repr__(self):
        return f"ImportStatement({self.module_name})"
