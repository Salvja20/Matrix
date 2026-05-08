"""
Matrix Language Evaluator
Walks the AST and executes each node, enforcing strict typing and immutability.
"""

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


# ── Exceptions used for control flow ─────────────────────────────────────────

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass


# ── Matrix Runtime Errors ─────────────────────────────────────────────────────

class MatrixError(Exception):
    pass

class TypeError_(MatrixError):
    pass

class ImmutabilityError(MatrixError):
    pass

class UndefinedError(MatrixError):
    pass

class DivisionByZeroError(MatrixError):
    pass

class IndexError_(MatrixError):
    pass

class ArgumentError(MatrixError):
    pass


# ── Runtime values ────────────────────────────────────────────────────────────

class MatrixFunction:
    """A user-defined function."""
    def __init__(self, name, parameters, body, closure):
        self.name       = name
        self.parameters = parameters
        self.body       = body
        self.closure    = closure   # environment where function was defined

    def __repr__(self):
        return f"<function {self.name}>"

class MatrixClass:
    """A user-defined class definition."""
    def __init__(self, name, body, closure):
        self.name    = name
        self.body    = body
        self.closure = closure

    def __repr__(self):
        return f"<class {self.name}>"

class MatrixInstance:
    """An instance of a user-defined class."""
    def __init__(self, class_def, evaluator):
        self.class_def  = class_def
        self.attributes = {}   # mutable instance attributes
        self.methods    = {}

        # Execute the class body in a fresh environment to populate methods
        env = Environment(parent=class_def.closure)
        env.set_instance(self)
        for stmt in class_def.body:
            if isinstance(stmt, FunctionDeclaration):
                fn = MatrixFunction(stmt.name, stmt.parameters, stmt.body, env)
                self.methods[stmt.name] = fn
            elif isinstance(stmt, AssignmentStatement):
                name = stmt.identifier.name if isinstance(stmt.identifier, Identifier) else None
                if name:
                    val = evaluator.eval_expr(stmt.expression, env)
                    self.attributes[name] = val

    def get(self, name):
        if name in self.attributes:
            return self.attributes[name]
        if name in self.methods:
            return self.methods[name]
        raise UndefinedError(f"'{self.class_def.name}' has no attribute '{name}'")

    def set(self, name, value):
        # Instance attributes are mutable
        self.attributes[name] = value

    def __repr__(self):
        return f"<{self.class_def.name} instance>"

class MatrixModule:
    """A module — a named namespace of functions and values."""
    def __init__(self, name, members):
        self.name    = name
        self.members = members   # dict of name → value

    def get(self, name):
        if name not in self.members:
            raise UndefinedError(f"Module '{self.name}' has no member '{name}'")
        return self.members[name]

    def __repr__(self):
        return f"<module {self.name}>"

class MatrixArray:
    """A Matrix array — immutable after creation."""
    def __init__(self, elements):
        self.elements = list(elements)

    def get(self, index):
        if not isinstance(index, int):
            raise TypeError_(f"Array index must be an integer, got {type_name(index)}")
        if index < 0 or index >= len(self.elements):
            raise IndexError_(f"Index {index} out of bounds for array of length {len(self.elements)}")
        return self.elements[index]

    def __repr__(self):
        return f"[{', '.join(repr(e) for e in self.elements)}]"

    def __len__(self):
        return len(self.elements)


# ── Environment (scope) ───────────────────────────────────────────────────────

class Environment:
    def __init__(self, parent=None):
        self.vars     = {}       # name → value
        self.parent   = parent
        self._instance = None   # set when inside a class instance

    def set_instance(self, instance):
        self._instance = instance

    def get_instance(self):
        if self._instance:
            return self._instance
        if self.parent:
            return self.parent.get_instance()
        return None

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise UndefinedError(f"Undefined variable '{name}'")

    def define(self, name, value):
        """Define a new variable — strict immutability: can't redefine in same scope."""
        if name in self.vars:
            raise ImmutabilityError(
                f"Variable '{name}' is already defined and cannot be reassigned. "
                f"Variables cannot be reassigned."
            )
        self.vars[name] = value

    def update(self, name, value):
        """Update an existing variable in the nearest enclosing scope that has it.
        Used for loop counter updates — walks up the scope chain."""
        if name in self.vars:
            self.vars[name] = value
            return True
        if self.parent:
            return self.parent.update(name, value)
        return False

    def assign(self, name, value):
        """Used internally (loops, instance attrs) — bypasses immutability."""
        self.vars[name] = value

    def force_define(self, name, value):
        """Force-set without immutability check (used for parameters, loop vars)."""
        self.vars[name] = value


# ── Type helpers ──────────────────────────────────────────────────────────────

def type_name(value):
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, int):
        return 'integer'
    if isinstance(value, float):
        return 'float'
    if isinstance(value, str):
        return 'string'
    if value is None:
        return 'null'
    if isinstance(value, MatrixArray):
        return 'array'
    if isinstance(value, MatrixFunction):
        return 'function'
    if isinstance(value, MatrixClass):
        return 'class'
    if isinstance(value, MatrixInstance):
        return value.class_def.name
    if isinstance(value, MatrixModule):
        return 'module'
    return type(value).__name__

def display(value):
    """Convert a runtime value to its string representation."""
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return 'null'
    if isinstance(value, MatrixArray):
        return '[' + ', '.join(display(e) for e in value.elements) + ']'
    if isinstance(value, float):
        formatted = f'{value:.10g}'
        if '.' not in formatted and 'e' not in formatted:
            formatted += '.0'
        return formatted
    return str(value)


# ── Evaluator ─────────────────────────────────────────────────────────────────

class Evaluator:
    def __init__(self):
        self.output  = []          # collected print output
        self.modules = {}          # globally registered modules
        self.global_env = self._make_global_env()

    def _make_global_env(self):
        """Set up the global environment with built-in functions."""
        env = Environment()
        # Built-ins
        env.force_define('len',   self._builtin_len)
        env.force_define('int',   self._builtin_int)
        env.force_define('float', self._builtin_float)
        env.force_define('str',   self._builtin_str)
        env.force_define('bool',  self._builtin_bool)
        env.force_define('type',  self._builtin_type)
        return env

    # ── Built-in functions ────────────────────────────────────────────────────

    def _builtin_len(self, args):
        if len(args) != 1:
            raise ArgumentError("len() takes exactly 1 argument")
        v = args[0]
        if isinstance(v, MatrixArray):
            return len(v)
        if isinstance(v, str):
            return len(v)
        raise TypeError_(f"len() not supported for type '{type_name(v)}'")

    def _builtin_int(self, args):
        if len(args) != 1:
            raise ArgumentError("int() takes exactly 1 argument")
        v = args[0]
        if isinstance(v, int) and not isinstance(v, bool):
            return v
        if isinstance(v, float):
            return int(v)
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                raise TypeError_(f"Cannot convert string '{v}' to integer")
        raise TypeError_(f"Cannot convert '{type_name(v)}' to integer")

    def _builtin_float(self, args):
        if len(args) != 1:
            raise ArgumentError("float() takes exactly 1 argument")
        v = args[0]
        if isinstance(v, float):
            return v
        if isinstance(v, int) and not isinstance(v, bool):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                raise TypeError_(f"Cannot convert string '{v}' to float")
        raise TypeError_(f"Cannot convert '{type_name(v)}' to float")

    def _builtin_str(self, args):
        if len(args) != 1:
            raise ArgumentError("str() takes exactly 1 argument")
        return display(args[0])

    def _builtin_bool(self, args):
        if len(args) != 1:
            raise ArgumentError("bool() takes exactly 1 argument")
        v = args[0]
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return v != 0
        if isinstance(v, float):
            return v != 0.0
        if isinstance(v, str):
            return len(v) > 0
        if v is None:
            return False
        return True

    def _builtin_type(self, args):
        if len(args) != 1:
            raise ArgumentError("type() takes exactly 1 argument")
        return type_name(args[0])

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self, program):
        """Execute a Program node and return collected output."""
        self.output = []
        self.global_env = self._make_global_env()
        try:
            self.exec_block(program.statements, self.global_env)
        except MatrixError as e:
            self.output.append(f"Error: {e}")
        return '\n'.join(self.output)

    # ── Statement execution ───────────────────────────────────────────────────

    def exec_block(self, statements, env):
        for stmt in statements:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, stmt, env):
        if isinstance(stmt, AssignmentStatement):
            self.exec_assignment(stmt, env)

        elif isinstance(stmt, PrintStatement):
            val = self.eval_expr(stmt.expression, env)
            self.output.append(display(val))

        elif isinstance(stmt, ExpressionStatement):
            self.eval_expr(stmt.expression, env)

        elif isinstance(stmt, IfStatement):
            self.exec_if(stmt, env)

        elif isinstance(stmt, WhileStatement):
            self.exec_while(stmt, env)

        elif isinstance(stmt, FunctionDeclaration):
            fn = MatrixFunction(stmt.name, stmt.parameters, stmt.body, env)
            env.define(stmt.name, fn)

        elif isinstance(stmt, ClassDeclaration):
            cls = MatrixClass(stmt.name, stmt.body, env)
            env.define(stmt.name, cls)

        elif isinstance(stmt, ModuleDeclaration):
            mod = self.exec_module(stmt, env)
            env.define(stmt.name, mod)

        elif isinstance(stmt, ImportStatement):
            if stmt.module_name not in self.modules:
                raise UndefinedError(f"Module '{stmt.module_name}' not found")
            env.define(stmt.module_name, self.modules[stmt.module_name])

        elif isinstance(stmt, ReturnStatement):
            val = self.eval_expr(stmt.expression, env) if stmt.expression else None
            raise ReturnException(val)

        elif isinstance(stmt, BreakStatement):
            raise BreakException()

        else:
            raise MatrixError(f"Unknown statement type: {type(stmt).__name__}")

    def exec_assignment(self, stmt, env):
        value = self.eval_expr(stmt.expression, env)

        target = stmt.identifier

        # Simple variable assignment
        if isinstance(target, Identifier):
            # Only allow updating existing vars if we're inside a loop/function scope
            # (env has a parent). At global scope, always enforce immutability.
            if env.parent is not None and env.update(target.name, value):
                pass  # loop counter update succeeded
            else:
                env.define(target.name, value)

        # Instance attribute assignment  obj.attr = value
        elif isinstance(target, MemberExpression):
            obj = self.eval_expr(target.obj, env)
            if not isinstance(obj, MatrixInstance):
                raise TypeError_(f"Cannot assign attribute on type '{type_name(obj)}'")
            obj.set(target.member, value)

        # Array index assignment — STRICT: arrays are immutable
        elif isinstance(target, IndexExpression):
            raise ImmutabilityError("Arrays are immutable in Matrix. You cannot modify elements after creation.")

        else:
            raise MatrixError("Invalid assignment target")

    def exec_if(self, stmt, env):
        condition = self.eval_expr(stmt.condition, env)
        if not isinstance(condition, bool):
            raise TypeError_(
                f"If condition must be a boolean, got '{type_name(condition)}'. "
                f"Use a comparison expression like (x > 0)."
            )
        if condition:
            block_env = Environment(parent=env)
            self.exec_block(stmt.then_block, block_env)
        elif stmt.else_block is not None:
            block_env = Environment(parent=env)
            self.exec_block(stmt.else_block, block_env)

    def exec_while(self, stmt, env):
        while True:
            condition = self.eval_expr(stmt.condition, env)
            if not isinstance(condition, bool):
                raise TypeError_(
                    f"While condition must be a boolean, got '{type_name(condition)}'"
                )
            if not condition:
                break
            block_env = Environment(parent=env)
            try:
                self.exec_block(stmt.body, block_env)
            except BreakException:
                break

    def exec_module(self, stmt, env):
        mod_env = Environment(parent=env)
        self.exec_block(stmt.body, mod_env)
        members = {}
        for name, val in mod_env.vars.items():
            members[name] = val
        return MatrixModule(stmt.name, members)

    # ── Expression evaluation ─────────────────────────────────────────────────

    def eval_expr(self, node, env):
        if isinstance(node, IntegerLiteral):
            return node.value

        elif isinstance(node, FloatLiteral):
            return node.value

        elif isinstance(node, StringLiteral):
            return node.value

        elif isinstance(node, BooleanLiteral):
            return node.value

        elif isinstance(node, NullLiteral):
            return None

        elif isinstance(node, ArrayLiteral):
            elements = [self.eval_expr(e, env) for e in node.elements]
            return MatrixArray(elements)

        elif isinstance(node, Identifier):
            return env.get(node.name)

        elif isinstance(node, BinaryExpression):
            return self.eval_binary(node, env)

        elif isinstance(node, UnaryExpression):
            return self.eval_unary(node, env)

        elif isinstance(node, CallExpression):
            return self.eval_call(node, env)

        elif isinstance(node, MemberExpression):
            return self.eval_member(node, env)

        elif isinstance(node, IndexExpression):
            return self.eval_index(node, env)

        else:
            raise MatrixError(f"Unknown expression type: {type(node).__name__}")

    def eval_binary(self, node, env):
        op    = node.operator
        left  = self.eval_expr(node.left,  env)
        right = self.eval_expr(node.right, env)

        # Boolean logic
        if op == 'and':
            self._require_bool(left,  'and')
            self._require_bool(right, 'and')
            return left and right

        if op == 'or':
            self._require_bool(left,  'or')
            self._require_bool(right, 'or')
            return left or right

        # Arithmetic
        if op in ('+', '-', '*', '/', '//', '%', '**', '@'):
            return self.eval_arithmetic(op, left, right)

        # Comparisons
        if op in ('==', '!=', '<', '<=', '>', '>='):
            return self.eval_comparison(op, left, right)

        raise MatrixError(f"Unknown operator '{op}'")

    def eval_arithmetic(self, op, left, right):
        lt = type_name(left)
        rt = type_name(right)

        # String concatenation with +
        if op == '+' and lt == 'string' and rt == 'string':
            return left + right

        # Strict: no mixing types in arithmetic
        if lt != rt:
            raise TypeError_(
                f"Cannot apply '{op}' to '{lt}' and '{rt}'. Types must match."
            )

        # Only numeric types allowed for arithmetic
        if lt not in ('integer', 'float'):
            raise TypeError_(f"Operator '{op}' not supported for type '{lt}'")

        if op == '+':  return left + right
        if op == '-':  return left - right
        if op == '*':  return left * right
        if op == '**': return left ** right
        if op == '%':  return left % right

        if op == '/':
            if right == 0:
                raise DivisionByZeroError("Division by zero is not allowed")
            result = left / right
            # Strict: int / int stays float in Matrix (like real math)
            return result

        if op == '//':
            if right == 0:
                raise DivisionByZeroError("Integer division by zero is not allowed")
            return left // right

        if op == '@':
            # Matrix multiplication — both must be arrays
            if lt != 'array' or rt != 'array':
                raise TypeError_(f"@ operator requires arrays, got '{lt}' and '{rt}'")
            return self.matrix_multiply(left, right)

        raise MatrixError(f"Unknown arithmetic operator '{op}'")

    def eval_comparison(self, op, left, right):
        lt = type_name(left)
        rt = type_name(right)

        # Strict: can only compare same types (except null == null)
        if lt != rt:
            if not (left is None and right is None):
                raise TypeError_(
                    f"Cannot compare '{lt}' and '{rt}'. "
                    f"Cannot compare '{lt}' and '{rt}'."
                )

        if op == '==': return left == right
        if op == '!=': return left != right

        # Ordering comparisons only for numbers and strings
        if lt not in ('integer', 'float', 'string'):
            raise TypeError_(f"Operator '{op}' not supported for type '{lt}'")

        if op == '<':  return left <  right
        if op == '<=': return left <= right
        if op == '>':  return left >  right
        if op == '>=': return left >= right

    def eval_unary(self, node, env):
        op  = node.operator
        val = self.eval_expr(node.operand, env)

        if op == '-':
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                return -val
            raise TypeError_(f"Unary '-' not supported for type '{type_name(val)}'")

        if op == 'not':
            if not isinstance(val, bool):
                raise TypeError_(f"'not' requires a boolean, got '{type_name(val)}'")
            return not val

        raise MatrixError(f"Unknown unary operator '{op}'")

    def eval_call(self, node, env):
        callee = self.eval_expr(node.callee, env)
        args   = [self.eval_expr(a, env) for a in node.arguments]

        # Built-in function (Python callable)
        if callable(callee) and not isinstance(callee, (MatrixFunction, MatrixClass)):
            return callee(args)

        # User-defined function
        if isinstance(callee, MatrixFunction):
            return self.call_function(callee, args)

        # Class instantiation
        if isinstance(callee, MatrixClass):
            return MatrixInstance(callee, self)

        raise TypeError_(f"'{type_name(callee)}' is not callable")

    def call_function(self, fn, args):
        if len(args) != len(fn.parameters):
            raise ArgumentError(
                f"Function '{fn.name}' expects {len(fn.parameters)} argument(s), "
                f"got {len(args)}"
            )
        fn_env = Environment(parent=fn.closure)
        for param, arg in zip(fn.parameters, args):
            fn_env.force_define(param, arg)
        try:
            self.exec_block(fn.body, fn_env)
        except ReturnException as r:
            return r.value
        return None

    def eval_member(self, node, env):
        obj    = self.eval_expr(node.obj, env)
        member = node.member

        if isinstance(obj, MatrixInstance):
            return obj.get(member)

        if isinstance(obj, MatrixModule):
            return obj.get(member)

        raise TypeError_(f"Cannot access member '{member}' on type '{type_name(obj)}'")

    def eval_index(self, node, env):
        obj   = self.eval_expr(node.obj,   env)
        index = self.eval_expr(node.index, env)

        if isinstance(obj, MatrixArray):
            return obj.get(index)

        if isinstance(obj, str):
            if not isinstance(index, int):
                raise TypeError_("String index must be an integer")
            if index < 0 or index >= len(obj):
                raise IndexError_(f"String index {index} out of bounds")
            return obj[index]

        raise TypeError_(f"Type '{type_name(obj)}' does not support indexing")

    def _require_bool(self, value, op):
        if not isinstance(value, bool):
            raise TypeError_(
                f"Operator '{op}' requires booleans, got '{type_name(value)}'"
            )

    # ── Matrix multiplication ─────────────────────────────────────────────────

    def matrix_multiply(self, a, b):
        """Multiply two 2D Matrix arrays."""
        def to_2d(arr):
            if not arr.elements:
                return []
            if isinstance(arr.elements[0], MatrixArray):
                return [row.elements for row in arr.elements]
            return [arr.elements]   # treat 1D as row vector

        A = to_2d(a)
        B = to_2d(b)

        rows_A, cols_A = len(A), len(A[0]) if A else 0
        rows_B, cols_B = len(B), len(B[0]) if B else 0

        if cols_A != rows_B:
            raise TypeError_(
                f"Matrix dimensions incompatible for @: ({rows_A}x{cols_A}) @ ({rows_B}x{cols_B})"
            )

        result = []
        for i in range(rows_A):
            row = []
            for j in range(cols_B):
                total = 0
                for k in range(cols_A):
                    total += A[i][k] * B[k][j]
                row.append(total)
            result.append(MatrixArray(row))
        return MatrixArray(result)
